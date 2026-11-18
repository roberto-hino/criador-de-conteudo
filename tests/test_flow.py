import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from io import BytesIO
from xml.etree import ElementTree
from zipfile import ZipFile

from app import Handler, WORD_MIME
from export import WORD


class QuietHandler(Handler):
    def log_message(self, *_):
        pass


class EditorialFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def request(self, path, data=None):
        connection = HTTPConnection(*self.server.server_address, timeout=5)
        try:
            if data is None:
                connection.request("GET", path)
            else:
                connection.request("POST", path, json.dumps(data), {"Content-Type": "application/json"})
            response = connection.getresponse()
            return response.status, response.getheader("Content-Type"), response.read()
        finally:
            connection.close()

    def post(self, path, data, expected=200):
        code, _, body = self.request("/api/" + path, data)
        self.assertEqual(code, expected, body[:500])
        return json.loads(body)

    def test_interface_assets(self):
        for path in ("/", "/styles.css", "/app.js"):
            code, _, body = self.request(path)
            self.assertEqual(code, 200)
            self.assertTrue(body)
        self.assertIn("Público-alvo", self.request("/")[2].decode())

    def test_complete_editorial_flow(self):
        brief = {
            "theme": "Marketing de conteúdo", "audience": "Pequenos empreendedores",
            "kind": "Apostila", "level": "Intermediário", "pages": 25, "count": 4,
        }
        outline = self.post("plan", {"brief": brief})["outline"]
        self.assertEqual([step["pages"] for step in outline], [7, 6, 6, 6])
        outline[0]["title"] = "Introdução personalizada"
        modules = self.post("write", {"brief": brief, "outline": outline})["modules"]
        self.assertEqual(modules[0]["title"], outline[0]["title"])
        self.assertIn("módulo 1", modules[1]["content"])
        self.assertIn("cafeteria", modules[0]["content"])
        modules[0].update(title="Métricas & conversão", content="Texto editado pelo usuário <exemplo>.")
        reviews = self.post("review", {"modules": modules})["reviews"]
        self.assertTrue(reviews[0]["notes"])
        payload = {"brief": brief, "modules": modules}
        self.assertIn("Aprove todos", self.post("export", payload, expected=400)["error"])
        for module in modules:
            module["approved"] = True
        code, mime, document = self.request("/api/export", payload)
        self.assertEqual((code, mime), (200, WORD_MIME))
        with ZipFile(BytesIO(document)) as package:
            self.assertIsNone(package.testzip())
            for name in package.namelist():
                ElementTree.fromstring(package.read(name))
            root = ElementTree.fromstring(package.read("word/document.xml"))
        texts = [node.text for node in root.iter(f"{{{WORD}}}t")]
        self.assertIn("Sumário", texts)
        self.assertIn("1. Métricas & conversão", texts)
        self.assertIn("Texto editado pelo usuário <exemplo>.", texts)

    def test_invalid_brief_and_outline(self):
        self.post("plan", {"brief": {}}, expected=400)
        brief = {
            "theme": "Fotografia", "audience": "Iniciantes",
            "kind": "Curso", "level": "Introdutório", "pages": 3, "count": 2,
        }
        outline = self.post("plan", {"brief": brief})["outline"]
        outline[0]["pages"] = 55
        self.post("write", {"brief": brief, "outline": outline}, expected=400)
