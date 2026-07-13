import json, traceback
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class TranslationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/auto_translator/api/translations':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            locales_dir = Path(__file__).parent / "locales"
            master_file = locales_dir / "master.zh.json"

            try:
                if master_file.exists():
                    with open(master_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.wfile.write(json.dumps(data).encode('utf-8'))
                else:
                    self.wfile.write(json.dumps({}).encode('utf-8'))
            except Exception as e:
                print(f"[AutoTranslator] API error: {e}")
                traceback.print_exc()
                self.wfile.write(json.dumps({}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def start_translation_server(port=0):
    try:
        server = HTTPServer(('127.0.0.1', port), TranslationHandler)
        actual_port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"[AutoTranslator] API server started on port {actual_port}")
        return server
    except Exception as e:
        print(f"[AutoTranslator] API server failed: {e}")
        traceback.print_exc()
        return None
