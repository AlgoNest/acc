import requests, json, base64, os
from dotenv import load_dotenv
load_dotenv()

HEADERS = {
    "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
    "Accept": "application/vnd.github.v3+json"
}
BASE = f"https://api.github.com/repos/{os.getenv('GITHUB_REPO')}/contents/{os.getenv('GITHUB_FILE_PATH')}"

def read_data():
    r = requests.get(BASE, headers=HEADERS)
    if r.status_code == 404:
        return {"students": [], "logs": {}}, None
    data = r.json()
    content = json.loads(base64.b64decode(data["content"]).decode())
    return content, data["sha"]

def write_data(content, sha=None):
    body = {
        "message": "update data",
        "content": base64.b64encode(
            json.dumps(content, indent=2).encode()
        ).decode()
    }
    if sha:
        body["sha"] = sha
    requests.put(BASE, headers=HEADERS, json=body)
