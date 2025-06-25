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

def fetch_profile(profile_name: str) -> dict:
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