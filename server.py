#!/usr/bin/env python3
"""
Öruggur vefþjónn fyrir Svíþjóðarferð 2027.
Krefst PIN-númers til að skoða eða skrá dagsetningar og atkvæði.
Enginn utanaðkomandi getur séð hvenær fólk er í fríi eða hvaða hús eru skoðuð án PIN-númers.
"""

import http.server
import socketserver
import json
import os
import sys

PORT = 8080
VOTES_FILE = "votes.json"
HOUSES_FILE = "houses.json"
ENV_FILE = ".env"

def load_pin():
    pin = os.environ.get("FAMILY_PIN")
    if pin:
        return pin.strip()
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("FAMILY_PIN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "2027"  # Sjálfgefið PIN ef ekkert er stillt

PIN = load_pin()

if not os.path.exists(VOTES_FILE):
    with open(VOTES_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

class SecureVoteHandler(http.server.SimpleHTTPRequestHandler):
    def check_auth(self):
        user_pin = self.headers.get("X-Family-PIN")
        # Leyfa líka query parameter ?pin=... ef þarf
        if not user_pin and "?" in self.path:
            query = self.path.split("?", 1)[1]
            params = dict(qc.split("=") for qc in query.split("&") if "=" in qc)
            user_pin = params.get("pin")
        return user_pin == PIN

    def send_unauthorized(self):
        self.send_response(401)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Óheimill aðgangur. Sláðu inn rétt fjölskyldu-PIN."}).encode("utf-8"))

    def do_GET(self):
        # Loka á beinan aðgang að json skrám án PIN
        if self.path in [f"/{VOTES_FILE}", f"/{HOUSES_FILE}"]:
            if not self.check_auth():
                return self.send_unauthorized()

        if self.path == "/api/verify-pin":
            if self.check_auth():
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"valid": True}).encode("utf-8"))
            else:
                self.send_unauthorized()
            return

        if self.path.startswith("/api/votes"):
            if not self.check_auth():
                return self.send_unauthorized()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            with open(VOTES_FILE, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))
            return

        if self.path.startswith("/api/houses"):
            if not self.check_auth():
                return self.send_unauthorized()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            with open(HOUSES_FILE, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))
            return

        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/vote":
            if not self.check_auth():
                return self.send_unauthorized()

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
    print("=" * 55)
    print("🔒 Öruggur vefþjónn fyrir Svíþjóðarferð 2027")
    print(f"🔑 Virkt fjölskyldu-PIN: {PIN} (hægt að breyta í .env skránni)")
    print(f"👉 Slóð í vafra: http://localhost:{PORT}")
    print("=" * 55)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SecureVoteHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nVefþjóni lokað.")
