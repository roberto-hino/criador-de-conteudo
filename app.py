"""Local HTTP entry point for the editorial workspace."""
import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from editorial import DemoProvider, validate_brief, validate_modules, validate_outline
from export import build_docx

WEB = Path(__file__).resolve().parent / "web"
ASSETS = {"/": "index.html", "/app.js": "app.js", "/styles.css": "styles.css"}
WORD_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class Handler(BaseHTTPRequestHandler):
    provider = DemoProvider()

    def reply(self, code, data, content_type, filename=None):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; object-src 'none'; frame-ancestors 'none'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def json_reply(self, code, data):
        self.reply(code, json.dumps(data, ensure_ascii=True).encode(), "application/json")

    def do_GET(self):
        asset = ASSETS.get(self.path)
        if not asset:
            return self.json_reply(404, {"error": "Página indisponível."})
        file = WEB / asset
        self.reply(200, file.read_bytes(), mimetypes.guess_type(file)[0] + "; charset=utf-8")

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", 0))
            if not 0 < size <= 8_000_000:
                raise ValueError("Tamanho de solicitação inválido.")
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError("Formato de solicitação inválido.")
            if self.path == "/api/plan":
                brief = validate_brief(data.get("brief"))
                return self.json_reply(200, {"outline": self.provider.plan(brief)})
            if self.path == "/api/write":
                brief = validate_brief(data.get("brief"))
                outline = validate_outline(data.get("outline"), brief)
                return self.json_reply(200, {"modules": self.provider.write(brief, outline)})
            if self.path == "/api/review":
                return self.json_reply(200, {"reviews": self.provider.review(validate_modules(data.get("modules")))})
            if self.path == "/api/export":
                brief = validate_brief(data.get("brief"))
                modules = validate_modules(data.get("modules"), require_approval=True)
                if len(modules) != brief["count"]:
                    raise ValueError("O número de módulos difere do definido no projeto.")
                return self.reply(200, build_docx(brief, modules), WORD_MIME, "material.docx")
            self.json_reply(404, {"error": "Operação indisponível."})
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.json_reply(400, {"error": "Formato de solicitação inválido."})
        except ValueError as error:
            self.json_reply(400, {"error": str(error)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Criador Automático de Conteúdo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    with ThreadingHTTPServer((args.host, args.port), Handler) as server:
        print(f"Servidor em http://{args.host}:{args.port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
