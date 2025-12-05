import os
import requests
import json
import sys

def load_env_file(filepath=".env"):
    """Simple .env loader manually since python-dotenv might not be installed."""
    if not os.path.exists(filepath):
        return
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"').strip("'")
                os.environ[key] = value

def get_transcoding_config():
    # Load .env if present
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, ".env")
    load_env_file(env_path)

    url = os.environ.get('JELLYFIN_URL')
    api_key = os.environ.get('JELLYFIN_API_KEY')

    if not url or not api_key:
        print("Error: JELLYFIN_URL and JELLYFIN_API_KEY must be set in Environment or .env file.")
        return

    print(f"Connecting to Jellyfin at {url}...")
    headers = {'X-Emby-Token': api_key}
    
    try:
        # Fetch encoding specific configuration
        encoding_url = f"{url}/System/Configuration/encoding"
        print(f"Fetching encoding configuration from: {encoding_url}")
        
        r = requests.get(encoding_url, headers=headers, timeout=10)
        r.raise_for_status()
        
        print("\n--- Encoding Configuration ---")
        print(json.dumps(r.json(), indent=4))

    except Exception as e:
        print(f"Failed to fetch config: {e}")

if __name__ == "__main__":
    get_transcoding_config()
