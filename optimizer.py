import os
import sys
import requests
import subprocess
import json
import time

# Global logger callback
_log_callback = None

def set_log_callback(callback):
    global _log_callback
    _log_callback = callback

def log(msg):
    print(f"[Auto-Tune] {msg}", flush=True)
    if _log_callback:
        _log_callback(msg)

def check_jellyfin_connection(url, api_key):
    log("Connecting to Jellyfin...")
    headers = {'X-Emby-Token': api_key}
    
    try:
        # Check basic info
        info_url = f"{url}/System/Info"
        r = requests.get(info_url, headers=headers, timeout=10)
        r.raise_for_status()
        log("Connected to Jellyfin successfully.")
        
        # Fetch transcoding config
        encoding_url = f"{url}/System/Configuration/encoding"
        r = requests.get(encoding_url, headers=headers, timeout=10)
        r.raise_for_status()
        config = r.json()
        
        log("Transcoding Configuration retrieved.")
        log(f"Hardware Acceleration Type: {config.get('HardwareAccelerationType', 'None')}")
        log(f"VAAPI Device: {config.get('VaapiDevice', 'N/A')}")
        log(f"QSV Device: {config.get('QsvDevice', 'N/A')}")
        
        return True
    except Exception as e:
        log(f"Failed to connect to Jellyfin or retrieve config: {e}")
        response = wait_for_input("Connection failed. Continue anyway? (y/n)")
        if response and response.lower().strip() == 'y':
            return True
        return False

import threading

# Global variables
_process = None
_master_fd = None
_input_event = threading.Event()
_last_input = None
_waiting_for_input = False

def wait_for_input(prompt):
    global _waiting_for_input, _last_input
    log(prompt)
    _waiting_for_input = True
    _input_event.clear()
    _input_event.wait()
    _waiting_for_input = False
    return _last_input

def send_input(text):
    global _master_fd, _waiting_for_input, _last_input
    
    if _waiting_for_input:
        _last_input = text
        _input_event.set()
        log(f"Received input: {text}")
        return

    if _master_fd is not None:
        try:
            log(f"Sending input: {text}")
            os.write(_master_fd, (text + "\n").encode())
        except Exception as e:
            log(f"Failed to write to pty: {e}")
    else:
        log("No active process to receive input.")

def run_benchmark():
    global _process, _master_fd
    log("Starting Jellybench...")
    
    import pty
    import select
    
    # Create a pseudo-terminal
    master_fd, slave_fd = pty.openpty()
    _master_fd = master_fd
    
    try:
        # Check if jellybench is available as a command
        cmd = ["jellybench", "--ffmpeg", "/app/jellybench_data/ffmpeg"]
        
        log("Running benchmark command: " + " ".join(cmd))
        
        _process = subprocess.Popen(
            cmd,
            stdout=slave_fd,
            stderr=slave_fd,
            stdin=slave_fd,
            text=True,
            bufsize=1,
            universal_newlines=True,
            preexec_fn=os.setsid # Create new session
        )
        
        os.close(slave_fd) # Close slave in parent
        
        # Read loop
        buffer = ""
        while True:
            try:
                r, w, e = select.select([master_fd], [], [], 0.1)
                if master_fd in r:
                    data = os.read(master_fd, 1024)
                    if not data:
                        break
                    
                    text = data.decode('utf-8', errors='replace')
                    buffer += text
                    
                    # Process buffer for lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        log(line.strip())
                    
                    # If buffer has data but no newline (e.g. prompt), log it if it's been a while?
                    # Or just log it immediately if it looks like a prompt?
                    # For simplicity, let's just log whatever remains if it doesn't end in newline 
                    # but we want to avoid spamming partial chars.
                    # Actually, for the prompt "Continue (y/n): ", we want to see it.
                    if buffer.strip().endswith(":"): # Heuristic for prompts
                         log(buffer.strip())
                         buffer = ""
                         
            except OSError:
                break
                
            if _process.poll() is not None:
                # Process finished, read remaining
                # But select should handle it.
                # If poll is not None, we should continue reading until EOF (read returns empty)
                # But with PTY, read might throw EIO on close.
                pass

    except FileNotFoundError:
        log("Error: 'jellybench' command not found.")
        return {}
    except Exception as e:
        log(f"Benchmark failed: {e}")
        return {}
    finally:
        if _process and _process.poll() is None:
            _process.terminate()
        if _master_fd:
            try:
                os.close(_master_fd)
            except:
                pass
        _process = None
        _master_fd = None
        log("Benchmark process finished.")

def analyze_results(results):
    log("Analyzing results...")
    if not results:
        log("No results to analyze.")
        return

    # Simple logic: find max fps
    best_codec = max(results, key=results.get)
    best_fps = results[best_codec]
    
    log(f"Analysis Complete")
    log(f"Recommendation: {best_codec} is the fastest with {best_fps}fps.")

def run_optimization_process(url, api_key):
    if not url or not api_key:
        log("Error: JELLYFIN_URL and JELLYFIN_API_KEY must be set.")
        return
        
    if not check_jellyfin_connection(url, api_key):
        return
        
    results = run_benchmark()
    analyze_results(results)

def main():
    url = os.environ.get('JELLYFIN_URL')
    api_key = os.environ.get('JELLYFIN_API_KEY')
    run_optimization_process(url, api_key)

if __name__ == "__main__":
    main()
