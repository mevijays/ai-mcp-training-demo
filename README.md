# MCP DB Demo: AI Database Assistant with Postgres

This demo showcases a Flask-based AI assistant that connects to a local PostgreSQL running in Docker via a fastmcp MCP server over SSE. The assistant can list tables, generate SQL from natural language, execute it, and return results.

## Stack
- Docker Compose: PostgreSQL
- `scripts/setup.sh`: initializes DB with sample schema/data (via `scripts/sample.sql`)
- `postgres-mcp-fastmcp.py`: fastmcp server exposing `list_tables` and `run_query` over SSE
- `app.py`: Flask UI + OpenAI-powered SQL generation calling the MCP server

## Prereqs
- Docker Desktop
- Python 3.10+
- An OpenAI API key

## Quick Start
1. Copy env file and edit values:
```bash
cp .env.example .env
chmod +x scripts/*.sh
```

2. Start Postgres and seed sample data (uses docker-compose):
```bash
bash scripts/setup.sh
```

3. Create venv and install deps:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Run the MCP server (separate terminal):
```bash
python postgres-mcp-fastmcp.py
```

5. Run the Flask app:
```bash
python app.py
```

Visit http://localhost:5050.

Optional check via the fastmcp client:
```bash
python - <<'PY'
from fastmcp import Client
import asyncio

async def main():
	async with Client('http://127.0.0.1:8000/sse') as c:
		tools = await c.list_tools()
		print('tools:', [t.name for t in tools])
		r = await c.call_tool('list_tables', _return_raw_result=True)
		print('list_tables raw:', r)
		r2 = await c.call_tool('run_query', {'sql': 'select * from customers limit 1'}, _return_raw_result=True)
		print('run_query raw:', r2)

asyncio.run(main())
PY
```

## Environment Variables
See `.env.example`. Sensitive values are loaded from `.env`.

MCP server respects `MCP_HOST` and `MCP_PORT` (defaults 127.0.0.1:8000). Flask app uses them to call the server. Flask serves on `FLASK_PORT` (default 5050).


## Notes
- This demo is for local exploration only. Do not expose it publicly.
- Error handling is minimal for clarity. Improve before production use.
Note: The fastmcp server speaks SSE on `/sse`. Traditional JSON-RPC curl calls to `/` are not supported.

## Prompts for demo 
here are solid demo prompts that exercise joins, grouping, filters, and windows without being destructive:  

- "Total paid order amount per customer, show customer name and total, sorted desc."
- "Average order amount by status (paid, pending, refunded), highest first."
- "List customers with no orders."
- "Top 5 customers by total paid amount in the last 30 days."
- "Daily paid revenue for the last 7 days."
- "Pending orders older than 7 days (id, customer_id, amount, created_at)."
- "Refund amount and refund rate per customer (refunded/total)."
- "Email domain breakdown of customers with counts (e.g., example.com)."
- "First order date per customer alongside customer name."
- "Running total of paid amount per customer over time (customer, date, running_total)."
- "Customers with lifetime paid spend greater than 200, sorted by spend."
- "Top 5 customers by average paid order value with at least 2 paid orders."
- "Monthly paid revenue for the current year (YYYY-MM and total)."
- "Paid vs refunded totals per customer in separate columns."
- "Show the column names and data types for public.customers and public.orders."
