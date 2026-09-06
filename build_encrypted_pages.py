#!/usr/bin/env python3
"""
Byggir dulkóðaða gagnaskrá fyrir GitHub Pages.
Öll gögn (hús, nöfn fjölskyldu, vikur) eru dulkóðuð með AES-256 (PBKDF2 SHA-256)
með fjölskyldu PIN-númerinu. Á GitHub Pages er ómögulegt að lesa gögnin án PIN.
Keyrsla: python3 build_encrypted_pages.py
"""

import os
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ENV_FILE = ".env"

def get_pin():
    pin = os.environ.get("FAMILY_PIN")
    if pin:
        return pin.strip()
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("FAMILY_PIN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "2027"

def build():
    pin = get_pin()
    print(f"🔒 Dulkóða gögn fyrir GitHub Pages með PIN: {pin}")

    # Lesa húsagögn
    with open("houses.json", "r", encoding="utf-8") as f:
        houses = json.load(f)

    family_members = [
        "Sigurjón Axel",
        "Ólafía Rósbjörg (Lóa)",
        "Axel Bjarkar",
        "Rannveig Arna",
        "Þórhildur Soffía",
        "Birkir Evan",
        "Viktor Ingi",
        "Vala Björk",
        "Sara Kristín"
    ]

    weeks = [
        { "id": "w25", "num": "Vika 25", "dates": "15. jún – 22. jún 2027", "tag": "Skólaslit" },
        { "id": "w26", "num": "Vika 26", "dates": "22. jún – 29. jún 2027", "tag": "🇸🇪 Midsommar!" },
        { "id": "w27", "num": "Vika 27", "dates": "29. jún – 06. júl 2027", "tag": "" },
        { "id": "w28", "num": "Vika 28", "dates": "06. júl – 13. júl 2027", "tag": "" },
        { "id": "w29", "num": "Vika 29", "dates": "13. júl – 20. júl 2027", "tag": "Háannatími" },
        { "id": "w30", "num": "Vika 30", "dates": "20. júl – 27. júl 2027", "tag": "Háannatími" },
        { "id": "w31", "num": "Vika 31", "dates": "27. júl – 03. ágú 2027", "tag": "Verslunarmannahelgi" },
        { "id": "w32", "num": "Vika 32", "dates": "03. ágú – 10. ágú 2027", "tag": "" },
        { "id": "w33", "num": "Vika 33", "dates": "10. ágú – 17. ágú 2027", "tag": "" },
        { "id": "w34", "num": "Vika 34", "dates": "17. ágú – 24. ágú 2027", "tag": "" },
        { "id": "w35", "num": "Vika 35", "dates": "24. ágú – 31. ágú 2027", "tag": "Lok ágúst" }
    ]

    payload = {
        "familyMembers": family_members,
        "weeks": weeks,
        "houses": houses
    }

    raw_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    # AES-256 GCM með PBKDF2
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    key = kdf.derive(pin.encode("utf-8"))
    iv = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, raw_bytes, None)

    encrypted_payload = {
        "salt": base64.b64encode(salt).decode("utf-8"),
        "iv": base64.b64encode(iv).decode("utf-8"),
        "data": base64.b64encode(ciphertext).decode("utf-8")
    }

    with open("encrypted_data.json", "w", encoding="utf-8") as f:
        json.dump(encrypted_payload, f, indent=2)

    print("✅ encrypted_data.json búin til! Gögnin eru 100% dulkóðuð fyrir GitHub Pages.")

if __name__ == "__main__":
    build()
