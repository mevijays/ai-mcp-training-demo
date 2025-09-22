import os
from typing import Any, Dict

from flask import Flask, render_template_string, request, redirect, url_for, flash
from dotenv import load_dotenv
import requests
from openai import OpenAI


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_URL = f"http://{MCP_HOST}:{MCP_PORT}"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")


def mcp_call(method: str, params: Dict[str, Any] | None = None):
    resp = requests.post(MCP_URL, json={"method": method, "params": params or {}})
    # Try to parse JSON even on error status to expose DB error messages
    try:
        data = resp.json()
    except Exception:
        resp.raise_for_status()
        # If status OK but no JSON, fallback
        raise RuntimeError("Invalid MCP response")
    if "result" in data:
        return data["result"]
    if "error" in data:
        raise RuntimeError(str(data["error"]))
    # If no result or error key, use HTTP status as last resort
    resp.raise_for_status()
    raise RuntimeError("Unknown MCP error")


def is_db_like_prompt(prompt: str) -> bool:
  p = prompt.lower()
  keywords = [
    "sql", "select", "from", "where", "join", "group by", "order by",
    "table", "tables", "column", "columns", "database", "schema",
    "customer", "customers", "order", "orders", "paid", "refunded",
    "count", "sum", "avg", "total", "limit"
  ]
  return any(k in p for k in keywords)


def generate_llm_answer(prompt: str) -> str:
  if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not configured")
  client = OpenAI(api_key=OPENAI_API_KEY)
  system = (
    "You are a helpful assistant. Answer the user's question clearly and concisely."
  )
  completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
    temperature=0.3,
  )
  return completion.choices[0].message.content.strip()


def get_schema_markdown() -> str:
  # Fetch all columns across non-system schemas
  col_res = mcp_call(
    "run_query",
    {
      "sql": (
        "SELECT table_schema, table_name, column_name, data_type "
        "FROM information_schema.columns "
        "WHERE table_schema NOT IN ('pg_catalog','information_schema') "
        "ORDER BY table_schema, table_name, ordinal_position"
      )
    },
  )
  # Fetch foreign keys to inform correct join keys
  fk_res = mcp_call(
    "run_query",
    {
      "sql": (
        "SELECT tc.table_schema, tc.table_name, kcu.column_name, "
        "       ccu.table_schema AS foreign_table_schema, "
        "       ccu.table_name   AS foreign_table_name, "
        "       ccu.column_name  AS foreign_column_name "
        "FROM information_schema.table_constraints AS tc "
        "JOIN information_schema.key_column_usage AS kcu "
        "  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema "
        "JOIN information_schema.constraint_column_usage AS ccu "
        "  ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema "
        "WHERE tc.constraint_type = 'FOREIGN KEY' "
        "ORDER BY tc.table_schema, tc.table_name, kcu.column_name"
      )
    },
  )

  # Organize columns per table
  cols_by_table: Dict[str, list] = {}
  for row in col_res.get("rows", []):
    key = f"{row['table_schema']}.{row['table_name']}"
    cols_by_table.setdefault(key, []).append((row["column_name"], row["data_type"]))

  # Organize FKs per table
  fks_by_table: Dict[str, list] = {}
  for row in fk_res.get("rows", []):
    src = f"{row['table_schema']}.{row['table_name']}"
    tgt = f"{row['foreign_table_schema']}.{row['foreign_table_name']}"
    fks_by_table.setdefault(src, []).append((row["column_name"], tgt, row["foreign_column_name"]))

  # Build markdown
  lines = ["Tables and columns (with foreign keys):"]
  for table in sorted(cols_by_table.keys()):
    col_str = ", ".join([f"{c}:{t}" for c, t in cols_by_table[table]])
    lines.append(f"- {table} ({col_str})")
    if table in fks_by_table:
      for col, tgt, tgt_col in fks_by_table[table]:
        lines.append(f"  FK: {table}.{col} -> {tgt}.{tgt_col}")
  return "\n".join(lines)


def generate_sql(prompt: str, dialect: str = "postgresql") -> str:
  if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not configured")
  client = OpenAI(api_key=OPENAI_API_KEY)
  schema = get_schema_markdown()
  system = (
    "You are an expert SQL generator. "
    "Return only a single valid SQL query (no prose). "
    f"Target dialect: {dialect}. Use existing tables and columns only. "
    "Use explicit JOINs and prefer join keys indicated by foreign keys. "
    "Qualify columns with table aliases (e.g., c.id) and avoid referencing non-existent columns."
  )
  user = f"Database schema:\n{schema}\n\nUser request: {prompt}\nSQL:"
  completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    temperature=0.1,
  )
  sql = completion.choices[0].message.content.strip()
  # Strip Markdown code fences like ```sql ... ``` safely
  if sql.startswith("```"):
    lines = sql.splitlines()
    # drop opening fence line (e.g., ``` or ```sql)
    if lines and lines[0].startswith("```"):
      lines = lines[1:]
    # drop closing fence
    if lines and lines[-1].strip().startswith("```"):
      lines = lines[:-1]
    # if first content line is just a language tag (rare), drop it
    if lines and lines[0].strip().lower() in ("sql", "postgresql", "psql"):
      lines = lines[1:]
    sql = "\n".join(lines).strip()
  # simple sanitation: disallow dangerous statements for demo
  banned = ["drop ", "truncate ", "alter ", "delete ", "update "]
  lower = sql.lower()
  if any(b in lower for b in banned):
    raise RuntimeError("Refusing to run potentially destructive SQL in demo.")
  return sql



INDEX_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AI DB Assistant</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }
      header { margin-bottom: 1rem; }
      .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
      textarea { width: 100%; min-height: 90px; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #ddd; padding: 6px 8px; }
      th { background: #fafafa; }
      .flash { color: #b00; margin-bottom: .5rem; }
      code { background: #f4f4f4; padding: 2px 4px; }
    </style>
  </head>
  <body>
    <header>
      <h1>AI Database Assistant</h1>
      <p>Backed by MCP server at <code>{{ mcp_url }}</code></p>
      {% for m in get_flashed_messages() %}
        <div class="flash">{{ m }}</div>
      {% endfor %}
    </header>
    <section class="grid">
      <div>
        <h3>Tables</h3>
        <ul>
        {% for t in tables %}
          <li>{{ t.table_schema }}.{{ t.table_name }}</li>
        {% endfor %}
        </ul>
      </div>
      <div>
        <h3>Ask anything</h3>
        <form method="post" action="{{ url_for('ask') }}">
          <textarea name="prompt" placeholder="e.g., total paid order amount per customer"></textarea>
          <div style="margin-top:.5rem;">
            <button type="submit">Generate & Run</button>
          </div>
        </form>
      </div>
    </section>

    {% if sql %}
    <section>
      <h3>Generated SQL</h3>
      <pre><code>{{ sql }}</code></pre>
    </section>
    {% endif %}

    {% if llm_answer %}
    <section>
      <h3>LLM Answer</h3>
      <div>{{ llm_answer }}</div>
    </section>
    {% endif %}

    {% if result and result.rows %}
    <section>
      <h3>Results</h3>
      <table>
        <thead>
          <tr>
          {% for col in result.columns %}
            <th>{{ col }}</th>
          {% endfor %}
          </tr>
        </thead>
        <tbody>
        {% for row in result.rows %}
          <tr>
            {% for col in result.columns %}
              <td>{{ row[col] }}</td>
            {% endfor %}
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </section>
    {% elif result and result.rowcount is not none %}
      <p>Affected rows: {{ result.rowcount }}</p>
    {% endif %}
  </body>
</html>
"""


@app.get("/")
def index():
  try:
    tables = mcp_call("list_tables")
  except Exception as e:
    flash(f"MCP error: {e}")
    tables = []
  return render_template_string(
    INDEX_HTML,
    tables=tables,
    sql=None,
    result=None,
    llm_answer=None,
    mcp_url=MCP_URL,
  )


@app.post("/ask")
def ask():
    prompt = request.form.get("prompt", "").strip()
    if not prompt:
        flash("Please enter a prompt.")
        return redirect(url_for("index"))
    # Route general knowledge prompts to LLM directly
    if not is_db_like_prompt(prompt):
        try:
            answer = generate_llm_answer(prompt)
            # Try to fetch tables for sidebar, but ignore errors
            try:
                tables = mcp_call("list_tables")
            except Exception:
                tables = []
            return render_template_string(INDEX_HTML, tables=tables, sql=None, result=None, llm_answer=answer, mcp_url=MCP_URL)
        except Exception as e:
            flash(str(e))
            return redirect(url_for("index"))

    # DB-like prompt: try SQL path first, else fall back to LLM if MCP unreachable
    try:
        sql = generate_sql(prompt)
        result = mcp_call("run_query", {"sql": sql})
        tables = mcp_call("list_tables")
        return render_template_string(INDEX_HTML, tables=tables, sql=sql, result=result, llm_answer=None, mcp_url=MCP_URL)
    except requests.exceptions.RequestException:
        # MCP unreachable; answer from LLM with a friendly notice
        flash("MCP Server is not reachable so answering from the LLM")
        try:
            answer = generate_llm_answer(prompt)
            # no tables since MCP is unreachable
            return render_template_string(INDEX_HTML, tables=[], sql=None, result=None, llm_answer=answer, mcp_url=MCP_URL)
        except Exception as e:
            flash(str(e))
            return redirect(url_for("index"))
    except Exception as e:
        # Other errors (e.g., SQL errors) are shown to user
        flash(str(e))
        return redirect(url_for("index"))


if __name__ == "__main__":
  port = int(os.getenv("FLASK_PORT", "5050"))
  app.run(host="0.0.0.0", port=port, debug=bool(int(os.getenv("FLASK_DEBUG", "1"))))
