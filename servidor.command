#!/bin/bash
# Servidor local del proyecto — doble clic y listo.
# Sirve el sitio en http://localhost:8000 y permite que editor.html
# GUARDE directamente fichas.json y logros.json (solo esos dos).
cd "$(dirname "$0")"
( sleep 1 && open "http://localhost:8000/editor.html" ) &
echo "Servidor en http://localhost:8000  —  editor: /editor.html · generador: /index.html"
echo "Para detenerlo: Ctrl+C o cierra esta ventana."
python3 - << 'PY'
import http.server, socketserver, os

PERMITIDOS = {"/fichas.json", "/logros.json"}

class H(http.server.SimpleHTTPRequestHandler):
    def do_PUT(self):
        if self.path.split("?")[0] not in PERMITIDOS:
            self.send_response(403); self.end_headers(); return
        n = int(self.headers.get("Content-Length", 0))
        cuerpo = self.rfile.read(n)
        import json
        try:
            json.loads(cuerpo)  # nunca escribir JSON inválido
        except Exception:
            self.send_response(400); self.end_headers(); return
        destino = self.path.split("?")[0].lstrip("/")
        with open(destino, "wb") as f:
            f.write(cuerpo)
        print(f"  ✓ guardado {destino} ({n:,} bytes)")
        self.send_response(204); self.end_headers()
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

with socketserver.TCPServer(("127.0.0.1", 8000), H) as s:
    s.allow_reuse_address = True
    s.serve_forever()
PY
