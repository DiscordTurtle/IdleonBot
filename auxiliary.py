import json
import requests

def load_config(path: str = "config.json") -> dict:
    """
    Load and return JSON config from `path`.
    Returns empty dict on error.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config '{path}': {e}")
        return {}

def fetch_data(profile_name: str) -> dict:
    """
    Fetch profile JSON from the remote API.
    Returns {} on any request error.
    """
    url = "https://profiles.idleontoolbox.workers.dev/api/profiles/"
    params = {"profile": profile_name}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"[{profile_name}] Request error: {e}")
        return {}
#TODO
def upload_public_profile(profile_name: str, data: dict) -> bool:
    """
    Uploads the profile data to the public API.
    Returns True on success, False on failure.
    """
    url = "https://profiles.idleontoolbox.workers.dev/api/profiles/upload/"
    payload = {"profile": profile_name, "data": data}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[{profile_name}] Upload error: {e}")
        return False
    
#TODO
def fetch_fresh_data(profile_name: str) -> dict:
    """
    Fetches the profile, uploads it, and returns the data.
    Returns {} on any error.
    """
    upload_public_profile(profile_name, {})
    
    data = fetch_data(profile_name)
    if not data:
        return {}

    if upload_public_profile(profile_name, data):
        print(f"[{profile_name}] Profile uploaded successfully.")
    else:
        print(f"[{profile_name}] Failed to upload profile.")

    return data