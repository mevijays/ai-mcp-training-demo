import os
import json
import socket
import decimal
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


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


def list_tables():
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog','information_schema')
            ORDER BY table_schema, table_name
            """
        )
        return [dict(r) for r in cur.fetchall()]


def _json_safe(val):
    if isinstance(val, decimal.Decimal):
        return float(val)
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    return val


def run_query(sql: str):
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql)
        if cur.description is None:
            conn.commit()
            return {"rowcount": cur.rowcount}
        rows = cur.fetchall()
        cols = [d.name for d in cur.description]
        safe_rows = []
        for r in rows:
            safe_rows.append({k: _json_safe(v) for k, v in dict(r).items()})
        return {"columns": cols, "rows": safe_rows}


class JSONRPCHandler(BaseHTTPRequestHandler):
    def _send(self, code=200, payload=None):
        body = json.dumps(payload or {}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path == "/healthz":
            return self._send(200, {"ok": True})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = self.rfile.read(length)
            req = json.loads(data or b"{}")
            method = req.get("method")
            params = req.get("params") or {}

            if method == "list_tables":
                result = list_tables()
                return self._send(200, {"result": result})
            elif method == "run_query":
                sql = params.get("sql", "")
                if not sql:
                    return self._send(400, {"error": "sql is required"})
                result = run_query(sql)
                return self._send(200, {"result": result})
            else:
                return self._send(400, {"error": f"unknown method {method}"})
        except Exception as e:
            return self._send(500, {"error": str(e)})


def run_server():
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    srv = HTTPServer((host, port), JSONRPCHandler)
    print(f"postgres-mcp-server listening on http://{host}:{port}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    run_server()
