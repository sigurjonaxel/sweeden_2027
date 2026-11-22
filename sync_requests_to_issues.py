#!/usr/bin/env python3
"""
Sækir óafgreiddar ábendingar/beiðnir (userRequests) úr dulkóðaða skýinu (kvdb.io)
og stofnar þær sjálfkrafa sem GitHub Issues í sigurjonaxel/sweeden_2027.
"""

import os
import json
import base64
import urllib.request
import urllib.error
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

CLOUD_SYNC_URL = "https://kvdb.io/SKmnoosJYG9rrzQ9ioVJEn/family_sync"

def get_pin():
    pin = os.environ.get("FAMILY_PIN")
    if pin:
        return pin.strip()
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("FAMILY_PIN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "2027"

def decrypt_payload(pin, enc_dict):
    salt = base64.b64decode(enc_dict["salt"])
    iv = base64.b64decode(enc_dict["iv"])
    ciphertext = base64.b64decode(enc_dict["data"])

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    key = kdf.derive(pin.encode("utf-8"))
    aesgcm = AESGCM(key)
    raw = aesgcm.decrypt(iv, ciphertext, None)
    return json.loads(raw.decode("utf-8"))

def encrypt_payload(pin, data_dict):
    raw_bytes = json.dumps(data_dict, ensure_ascii=False).encode("utf-8")
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

    return {
        "salt": base64.b64encode(salt).decode("utf-8"),
        "iv": base64.b64encode(iv).decode("utf-8"),
        "data": base64.b64encode(ciphertext).decode("utf-8")
    }

def fetch_cloud_data(pin):
    try:
        req = urllib.request.Request(CLOUD_SYNC_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            if not content.strip():
                return {}
            enc_dict = json.loads(content)
        if not isinstance(enc_dict, dict) or "data" not in enc_dict:
            return {}
        return decrypt_payload(pin, enc_dict)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("ℹ️ Engin gögn fundust í skýinu (404 - skýjageymsla tóm eða útrunnin).")
            return {}
        print(f"⚠️ Villa við að sækja skýjagögn: HTTP {e.code}")
        return {}
    except Exception as e:
        print(f"⚠️ Villa við að sækja eða afkóða skýjagögn: {e}")
        return {}

def save_cloud_data(pin, data_dict):
    try:
        encrypted = encrypt_payload(pin, data_dict)
        req = urllib.request.Request(
            CLOUD_SYNC_URL,
            data=json.dumps(encrypted).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        print(f"⚠️ Ekki tókst að vista í ský: {e}")
        return False

def create_github_issue(repo, token, req):
    category = req.get("category", "💡 Hugmynd")
    prefix = category.split()[0] if category else "💡"
    title = f"[{prefix}] {req.get('title', 'Ábending af vef')} ({req.get('person', 'Óþekktur')})"

    body = (
        f"### 💡 Ábending / Beiðni af vefnum (GitHub Pages)\n\n"
        f"- **Sendandi:** {req.get('person', 'Fjölskyldumeðlimur')}\n"
        f"- **Tegund:** {category}\n"
        f"- **Dags:** {req.get('createdAt', '')}\n\n"
        f"#### Nánari lýsing:\n"
        f"{req.get('details') or '_Engin nánari lýsing skráð._'}\n\n"
        f"---\n"
        f"*Þetta verkefni var sjálfkrafa búið til úr ábendingu á [Svíþjóðarvefnum](https://sigurjonaxel.github.io/sweeden_2027/).*"
    )

    labels = ["family-ask", "user-request"]
    if "🐛" in category:
        labels.append("bug")
    else:
        labels.append("enhancement")

    api_url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "sweeden-sync-script"
    }
    payload = {
        "title": title,
        "body": body,
        "labels": labels
    }

    req_obj = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req_obj) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data
    except urllib.error.HTTPError as e:
        print(f"❌ Villa við að búa til issue: HTTP {e.code} - {e.read().decode('utf-8')}")
        return None

def main():
    pin = get_pin()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY") or "sigurjonaxel/sweeden_2027"

    print(f"🔍 Athuga skýjagögn á {CLOUD_SYNC_URL}...")
    data = fetch_cloud_data(pin)
    if not isinstance(data, dict) or not data:
        print("✅ Engin gögn eða engar ábendingar í skýinu. Allt í lagi!")
        return

    user_requests = data.get("userRequests", [])
    if not isinstance(user_requests, list):
        print("✅ Engar ábendingar fundust í gögnunum. Allt í lagi!")
        return
    print(f"📋 Fann {len(user_requests)} skráðar ábendingar í heildina.")

    pending = [r for r in user_requests if not r.get("issueCreated")]
    print(f"⏳ {len(pending)} ábendingar í bið eftir að verða GitHub Issues.")

    if not pending:
        print("✅ Engin ný verkefni bíða. Allt samstillt!")
        return

    if not token:
        print("ℹ️ GITHUB_TOKEN fannst ekki í umhverfisbreytum. Sýni verkefni í bið:")
        for p in pending:
            print(f" - [{p.get('category')}] {p.get('title')} (frá {p.get('person')})")
        return

    created_count = 0
    for req in pending:
        print(f"🚀 Stofna GitHub Issue fyrir: {req.get('title')}...")
        issue = create_github_issue(repo, token, req)
        if issue:
            req["issueCreated"] = True
            req["issueNumber"] = issue.get("number")
            req["issueUrl"] = issue.get("html_url")
            print(f"   ✅ Búið til: Issue #{issue.get('number')} ({issue.get('html_url')})")
            created_count += 1

    if created_count > 0:
        data["updatedAt"] = data.get("updatedAt") or "now"
        print("💾 Uppfæri skýjagögn með tenglum í GitHub Issues...")
        save_cloud_data(pin, data)
        print("🎉 Samstillingu lokið!")

if __name__ == "__main__":
    main()
