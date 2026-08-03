import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self,*a): pass
    def reply(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Set-Cookie","session=abc123secret")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path.startswith("/invoices/"): self.reply(200, {"id": self.path.rsplit("/",1)[-1], "total": 1250})
        elif self.path == "/invoices": self.reply(200, {"items":[1,2,3]})
        else: self.reply(404, {"error":"not found"})
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); self.rfile.read(n)
        self.reply(201, {"created": True})
ThreadingHTTPServer(("127.0.0.1", 9911), H).serve_forever()
