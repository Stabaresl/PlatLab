"""
Objetivo intencionalmente vulnerable para el laboratorio "SQL Injection:
Bypass de Login" — corre DENTRO del contenedor de práctica del estudiante
(lab_environments), aislado de red (network_disabled) y solo alcanzable
por loopback desde el propio contenedor. Sin dependencias externas
(stdlib únicamente) para que la imagen sea liviana y rápida de construir.

La vulnerabilidad es real y deliberada: la consulta se arma concatenando
strings en vez de usar parámetros — exactamente el patrón que describe el
material teórico del laboratorio.
"""
import http.server
import os
import socketserver
import sqlite3
import urllib.parse

DB_PATH = "/tmp/app.db"
FLAG = os.environ.get("LAB_FLAG", "FLAG{sql_injection_1s_ez}")

LOGIN_FORM = b"""<!doctype html>
<html><body>
<form method="POST" action="/login.php">
  <input type="text" name="username" placeholder="usuario">
  <input type="password" name="password" placeholder="contrasena">
  <button type="submit">Ingresar</button>
</form>
</body></html>"""


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    conn.execute("DELETE FROM users")
    conn.execute("INSERT INTO users VALUES ('admin', 'S3cr3tP4ss!')")
    conn.commit()
    conn.close()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/login", "/login.php"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(LOGIN_FORM)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path not in ("/login", "/login.php"):
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        params = urllib.parse.parse_qs(body)
        username = params.get("username", [""])[0]
        password = params.get("password", [""])[0]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # Vulnerable a propósito: concatenación directa de la entrada del
        # usuario dentro de la consulta SQL (nunca hacer esto en código real).
        query = (
            "SELECT username FROM users WHERE username = '"
            + username
            + "' AND password = '"
            + password
            + "'"
        )
        row = None
        try:
            cur.execute(query)
            row = cur.fetchone()
        except sqlite3.Error:
            row = None
        conn.close()

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        if row:
            usuario = row[0]
            self.wfile.write(
                (
                    f"<div class='success'>Bienvenido, {usuario}. "
                    f"Autenticacion bypassed.\n{FLAG}</div>"
                ).encode()
            )
        else:
            self.wfile.write(b"<div class='error'>Credenciales invalidas</div>")

    def log_message(self, format, *args):  # noqa: A002 - firma fija de BaseHTTPRequestHandler
        pass


if __name__ == "__main__":
    init_db()
    with socketserver.TCPServer(("127.0.0.1", 5000), Handler) as httpd:
        httpd.serve_forever()
