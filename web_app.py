"""
Elden Ring Save to MapGenie (FMG) Web Server
Built-in zero-dependency local server using standard library http.server.
"""

import os
import sys
import json
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from er_save_parser import EldenRingSave, find_default_save_path
from mapgenie_sync import MapGenieSyncEngine

current_save: EldenRingSave | None = None
sync_engine: MapGenieSyncEngine | None = None

class SyncRequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/' or path == '/index.html':
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            index_path = os.path.join(curr_dir, 'web', 'index.html')
            if os.path.exists(index_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(index_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "index.html not found")
            return

        elif path == '/api/detect-save':
            default_path = find_default_save_path()
            if not default_path:
                # Check sample save in DataTemp
                curr = os.path.dirname(os.path.abspath(__file__))
                sample = os.path.join(curr, '..', 'DataTemp', 'ER0000.sl2')
                if os.path.exists(sample):
                    default_path = os.path.abspath(sample)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'save_path': default_path}).encode('utf-8'))
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        global current_save, sync_engine
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get('Content-Length', 0))

        if path == '/api/load-save':
            body = self.rfile.read(content_len).decode('utf-8')
            data = json.loads(body)
            save_path = data.get('save_path')
            if not save_path or not os.path.exists(save_path):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f"File save không tồn tại: {save_path}"}).encode('utf-8'))
                return

            try:
                current_save = EldenRingSave(save_path)
                profiles = current_save.get_profiles()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'profiles': profiles}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        elif path == '/api/upload-save':
            raw_data = self.rfile.read(content_len)
            content_type = self.headers.get('Content-Type', '')

            # Extract raw bytes from multipart if present
            if 'multipart/form-data' in content_type:
                # Find boundary
                boundary = content_type.split('boundary=')[1].encode('utf-8')
                parts = raw_data.split(boundary)
                file_bytes = None
                for p in parts:
                    if b'filename=' in p and b'\r\n\r\n' in p:
                        header, file_bytes = p.split(b'\r\n\r\n', 1)
                        if file_bytes.endswith(b'\r\n--'):
                            file_bytes = file_bytes[:-4]
                        elif file_bytes.endswith(b'\r\n'):
                            file_bytes = file_bytes[:-2]
                        break
                if not file_bytes:
                    file_bytes = raw_data
            else:
                file_bytes = raw_data

            try:
                current_save = EldenRingSave(file_bytes)
                profiles = current_save.get_profiles()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'profiles': profiles}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        elif path == '/api/sync':
            if not current_save:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': "Chưa nạp file save!"}).encode('utf-8'))
                return

            body = self.rfile.read(content_len).decode('utf-8')
            req_data = json.loads(body)
            slot_idx = int(req_data.get('slot_index', 0))
            map_id = int(req_data.get('map_id', 413))
            user_id = int(req_data.get('user_id', 7764114))
            options = req_data.get('options')
            existing_fmg = req_data.get('existing_fmg_data')

            try:
                slot_data = current_save.parse_slot(slot_idx)
                if not sync_engine:
                    sync_engine = MapGenieSyncEngine()
                res = sync_engine.sync_slot(
                    slot_data,
                    map_id=map_id,
                    user_id=user_id,
                    options=options,
                    existing_fmg_data=existing_fmg
                )
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        self.send_error(404, "Not Found")


def run_server(port: int = 8088, auto_open: bool = True):
    server = HTTPServer(('127.0.0.1', port), SyncRequestHandler)
    url = f"http://127.0.0.1:{port}"
    print("=" * 60)
    print(f"  ELDEN RING -> MAPGENIE SYNC TOOL")
    print(f"  Web Server running at: {url}")
    print("=" * 60)
    if auto_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()

if __name__ == '__main__':
    port = 8088
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port=port, auto_open=False)
