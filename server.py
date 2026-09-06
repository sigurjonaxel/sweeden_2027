#!/usr/bin/env python3
"""
Einfaldur vefþjónn fyrir Svíþjóðarferð 2027 kosningasíðuna.
Geymir öll atkvæði í votes.json svo allir í fjölskyldunni sjái svör hvers annars.
Keyrsla: python3 server.py
"""

import http.server
import socketserver
import json
import os
import sys

PORT = 8080
VOTES_FILE = "votes.json"

if not os.path.exists(VOTES_FILE):
    with open(VOTES_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

class VoteHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/votes":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            with open(VOTES_FILE, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))
            return
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/vote":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            try:
                payload = json.loads(post_body.decode("utf-8"))
                person = payload.get("person")
                data = payload.get("data")
                if person and data:
                    votes = {}
                    if os.path.exists(VOTES_FILE):
                        with open(VOTES_FILE, "r", encoding="utf-8") as f:
                            votes = json.load(f)
                    votes[person] = data
                    with open(VOTES_FILE, "w", encoding="utf-8") as f:
                        json.dump(votes, f, indent=2, ensure_ascii=False)
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
                    return
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
                return
        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"==================================================")
    print(f"🇸🇪 Vefþjónn fyrir Svíþjóðarferð 2027 er ræstur!")
    print(f"👉 Slóð í vafra: http://localhost:{PORT}")
    print(f"==================================================")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), VoteHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nVefþjóni lokað.")
