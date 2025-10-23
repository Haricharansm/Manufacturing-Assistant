
import os, requests
API_URL = os.environ.get("MFG_API_URL", "http://localhost:8000")
def api_up()->bool:
    try:
        r = requests.get(f"{API_URL}/health", timeout=1.2); return r.ok
    except Exception: return False
def get_metrics()->dict|None:
    try:
        r = requests.get(f"{API_URL}/metrics", timeout=5); 
        if r.ok: return r.json()
    except Exception: return None
def post_action(label:str)->str:
    try:
        r = requests.post(f"{API_URL}/simulate/action", json={"action": label}, timeout=6)
        if r.ok: return r.json().get("message","OK")
        return f"Error: {r.text}"
    except Exception as e: return f"API not reachable: {e}"
def reset()->None:
    try: requests.post(f"{API_URL}/reset", timeout=3)
    except Exception: pass
