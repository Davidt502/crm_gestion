"""
server.py - Servidor HTTP para el Frontend (desarrollo)
Para producción usa Nginx o Apache como servidor estático.
Ejecuta: python server.py
El frontend estará disponible en: http://localhost:3000
"""

import http.server
import socketserver
import os

PORT      = int(os.environ.get("PORT", 3000))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class SecureHandler(http.server.SimpleHTTPRequestHandler):
    """Servidor estático con cabeceras de seguridad básicas."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Deshabilitar caché para desarrollo
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        # Cabeceras de seguridad HTTP
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()

    def log_message(self, format, *args):  # noqa: A002
        # Suprimir logs de 304 Not Modified para no saturar la consola
        if args and str(args[1]) == "304":
            return
        super().log_message(format, *args)


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), SecureHandler) as httpd:
        httpd.allow_reuse_address = True
        print("=" * 60)
        print("  CRM Ing Software - Frontend Server")
        print(f"  Servidor corriendo en: http://localhost:{PORT}")
        print("  ⚠  Solo para desarrollo. En producción usa Nginx.")
        print("  Presiona Ctrl+C para detener")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
