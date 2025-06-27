import json
import requests
import os

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

def fetch_data(profile_name: str, save_to_file: bool = True) -> dict:
    """
    Fetch profile JSON from the remote API.
    Optionally saves the data to a JSON file.
    Returns {} on any request error.
    """
    url = "https://profiles.idleontoolbox.workers.dev/api/profiles/"
    params = {"profile": profile_name}
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Save to JSON file if requested and data is not empty
        if save_to_file and data:
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            filename = f"data/{profile_name}_profile.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[{profile_name}] Data saved to {filename}")
        
        return data
        
    except requests.RequestException as e:
        print(f"[{profile_name}] Request error: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[{profile_name}] JSON decode error: {e}")
        return {}
    except IOError as e:
        print(f"[{profile_name}] File save error: {e}")
        return data  # Return data even if file save fails
        
    except requests.RequestException as e:
        print(f"[{profile_name}] Request error: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[{profile_name}] JSON decode error: {e}")
        return {}
    except IOError as e:
        print(f"[{profile_name}] File save error: {e}")
        return data  # Return data even if file save fails
        
    except requests.RequestException as e:
        print(f"[{profile_name}] Request error: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[{profile_name}] JSON decode error: {e}")
        return {}
    except IOError as e:
        print(f"[{profile_name}] File save error: {e}")
        return data  # Return data even if file save fails
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


if __name__ == "__main__":
    # Example usage
    config = load_config()
    if config:
        print("Config loaded successfully.")
    else:
        print("Failed to load config.")

    profile_name = config.get("profile_name")
    data = fetch_data(profile_name)
    if data:
        print(f"Data fetched for {profile_name}.")
    else:
        print(f"Failed to fetch data for {profile_name}.")
    
    if upload_public_profile(profile_name, data):
        print(f"Profile {profile_name} uploaded successfully.")
    else:
        print(f"Failed to upload profile {profile_name}.")