import os
import decimal
from datetime import date, datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from fastmcp.server import FastMCP


load_dotenv()

PG_USER = os.getenv("POSTGRES_USER", "demo")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "demo_password")
PG_DB = os.getenv("POSTGRES_DB", "demodb")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))


def get_conn():
    return psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT,
    )


def json_safe(val):
    if isinstance(val, decimal.Decimal):
        return float(val)
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    return val


app = FastMCP(name="postgres-mcp")


@app.tool(
    name="list_tables",
    description="List non-system tables in the connected PostgreSQL database (schema and table).",
)
def list_tables() -> list[dict]:
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog','information_schema')
                ORDER BY table_schema, table_name
                """
            )
            data = [dict(r) for r in cur.fetchall()]
            return data
    except Exception as e:
        return {"error": str(e)}


@app.tool(
    name="run_query",
    description="Run a SQL query. Returns either rows+columns for SELECT or rowcount for DML.",
)
def run_query(sql: str) -> dict:
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            if cur.description is None:
                conn.commit()
                return {"rowcount": cur.rowcount}
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]
            safe_rows = []
            for r in rows:
                safe_rows.append({k: json_safe(v) for k, v in dict(r).items()})
            return {"columns": cols, "rows": safe_rows}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    app.settings.host = host
    app.settings.port = port
    print(f"fastmcp server listening on http://{host}:{port}")
    # Use SSE transport for HTTP server
    app.run("sse")
