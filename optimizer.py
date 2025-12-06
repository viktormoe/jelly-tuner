import os
import sys
import requests
import subprocess
import json
import time

import shutil
import glob
from datetime import datetime

# Global logger callback
_log_callback = None

def set_log_callback(callback):
    global _log_callback
    _log_callback = callback

def log(msg):
    print(f"[Auto-Tune] {msg}", flush=True)
    if _log_callback:
        _log_callback(msg)

def setup_ffmpeg():
    target_dir = "/app/jellybench_data/ffmpeg"
    cache_file = "/usr/local/share/jellybench_cache/jellyfin-ffmpeg_7.0.2-3_portable_linux64-gpl.tar.xz"
    target_file = os.path.join(target_dir, os.path.basename(cache_file))
    
    if not os.path.exists(target_file):
        log("FFmpeg not found in data directory. Copying from cache...")
        try:
            os.makedirs(target_dir, exist_ok=True)
            if os.path.exists(cache_file):
                shutil.copy2(cache_file, target_file)
                log("FFmpeg copied successfully.")
            else:
                log("Error: Cached FFmpeg not found.")
        except Exception as e:
            log(f"Failed to copy FFmpeg: {e}")
    else:
        log("FFmpeg found in data directory.")

def get_jellyfin_config(url, api_key):
    headers = {'X-Emby-Token': api_key}
    try:
        encoding_url = f"{url}/System/Configuration/encoding"
        r = requests.get(encoding_url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"Failed to fetch config: {e}")
        return None

def set_jellyfin_config(url, api_key, config):
    headers = {'X-Emby-Token': api_key, 'Content-Type': 'application/json'}
    try:
        encoding_url = f"{url}/System/Configuration/encoding"
        r = requests.post(encoding_url, headers=headers, json=config, timeout=10)
        r.raise_for_status()
        log("Configuration updated successfully.")
        return True
    except Exception as e:
        log(f"Failed to update config: {e}")
        return False

def backup_settings(url, api_key, custom_name=None):
    log("Backing up current settings...")
    config = get_jellyfin_config(url, api_key)
    if not config:
        return False
    
    backup_dir = "/app/jellybench_data/backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if custom_name:
        # Sanitize name
        safe_name = "".join([c for c in custom_name if c.isalnum() or c in ('-', '_')]).strip()
        if not safe_name:
            safe_name = "jelly-tune"
        filename = f"{safe_name}_{timestamp}.json"
    else:
        filename = f"jelly-tune-{timestamp}.json"
        
    filepath = os.path.join(backup_dir, filename)
    
    try:
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=4)
        log(f"Backup saved to {filename}")
        return filename
    except Exception as e:
        log(f"Failed to save backup: {e}")
        return False

def list_backups():
    backup_dir = "/app/jellybench_data/backups"
    if not os.path.exists(backup_dir):
        return []
    
    files = glob.glob(os.path.join(backup_dir, "*.json"))
    backups = []
    for f in files:
        backups.append({
            "filename": os.path.basename(f),
            "path": f,
            "date": datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
        })
    # Sort by date descending
    backups.sort(key=lambda x: x['filename'], reverse=True)
    return backups

def restore_settings(url, api_key, filename):
    log(f"Restoring settings from {filename}...")
    backup_dir = "/app/jellybench_data/backups"
    filepath = os.path.join(backup_dir, filename)
    
    if not os.path.exists(filepath):
        log("Backup file not found.")
        return False
        
    try:
        with open(filepath, 'r') as f:
            config = json.load(f)
        return set_jellyfin_config(url, api_key, config)
    except Exception as e:
        log(f"Failed to load backup: {e}")
        return False

def delete_backup(filename):
    log(f"Deleting backup {filename}...")
    backup_dir = "/app/jellybench_data/backups"
    filepath = os.path.join(backup_dir, filename)
    
    if not os.path.exists(filepath):
        log("Backup file not found.")
        return False
        
    try:
        os.remove(filepath)
        log(f"Backup {filename} deleted.")
        return True
    except Exception as e:
        log(f"Failed to delete backup: {e}")
        return False

def apply_recommendations(url, api_key, recommendations):
    log("Applying recommended settings...")
    # For now, recommendations is expected to be a full config object
    # In the future, this might merge specific changes into the current config
    return set_jellyfin_config(url, api_key, recommendations)

def list_results():
    data_dir = "/app/jellybench_data"
    results_dir = os.path.join(data_dir, "results") # Keep my own logs too?
    
    items = []
    
    # 1. Look for jellybench native results (results_run-...)
    if os.path.exists(data_dir):
        for name in os.listdir(data_dir):
            path = os.path.join(data_dir, name)
            if os.path.isdir(path) and name.startswith("results_run-"):
                # Parse timestamp from name: results_run-YYYY-MM-DD_HH-MM-SS
                try:
                    date_part = name.replace("results_run-", "")
                    # Format: YYYY-MM-DD_HH-MM-SS
                    dt = datetime.strptime(date_part, "%Y-%m-%d_%H-%M-%S")
                    date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    timestamp = dt.timestamp()
                    items.append({
                        "filename": name, # Use directory name as ID
                        "date": date_str,
                        "timestamp": timestamp,
                        "type": "native"
                    })
                except ValueError:
                    pass # Ignore if format doesn't match

    # 2. Look for my own console logs in results/
    if os.path.exists(results_dir):
        for filename in os.listdir(results_dir):
            if filename.endswith(".log"):
                filepath = os.path.join(results_dir, filename)
                timestamp = os.path.getmtime(filepath)
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                items.append({
                    "filename": "results/" + filename, # distinct path
                    "date": date_str + " (Console)",
                    "timestamp": timestamp,
                    "type": "console"
                })
    
    # Sort by timestamp descending
    items.sort(key=lambda x: x['timestamp'], reverse=True)
    return items

def get_result_content(identifier):
    data_dir = "/app/jellybench_data"
    
    # Check if it's one of my console logs
    if identifier.startswith("results/"):
        filepath = os.path.join(data_dir, identifier)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
        return "File not found."

    # Otherwise assume it's a directory name (results_run-...)
    dir_path = os.path.join(data_dir, identifier)
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        # Logs are in a 'log' subdirectory
        log_dir = os.path.join(dir_path, "log")
        if os.path.exists(log_dir) and os.path.isdir(log_dir):
            log_content = ""
            found_log = False
            
            # Try to read jellybench.log
            jb_log = os.path.join(log_dir, "jellybench.log")
            if os.path.exists(jb_log):
                found_log = True
                log_content += "--- jellybench.log ---\n"
                try:
                    with open(jb_log, 'r') as f:
                        log_content += f.read()
                except Exception as e:
                    log_content += f"Error reading file: {e}\n"
                log_content += "\n\n"

            # Try to read jellybench-ffmpeg.log
            ffmpeg_log = os.path.join(log_dir, "jellybench-ffmpeg.log")
            if os.path.exists(ffmpeg_log):
                found_log = True
                log_content += "--- jellybench-ffmpeg.log ---\n"
                try:
                    with open(ffmpeg_log, 'r') as f:
                        log_content += f.read()
                except Exception as e:
                    log_content += f"Error reading file: {e}\n"
                log_content += "\n\n"
            
            # Fallback: read any .log file in log_dir if specific ones aren't found
            if not found_log:
                for fname in os.listdir(log_dir):
                    if fname.endswith(".log"):
                        found_log = True
                        log_path = os.path.join(log_dir, fname)
                        log_content += f"--- {fname} ---\n"
                        with open(log_path, 'r') as f:
                            log_content += f.read()
                        log_content += "\n\n"

            if not found_log:
                return "No .log files found in the 'log' subdirectory."
            
            return log_content
        else:
             # Fallback for older runs or different structure: check root of result dir
            log_content = ""
            found_log = False
            for fname in os.listdir(dir_path):
                if fname.endswith(".log"):
                    found_log = True
                    log_path = os.path.join(dir_path, fname)
                    log_content += f"--- {fname} ---\n"
                    with open(log_path, 'r') as f:
                        log_content += f.read()
                    log_content += "\n\n"
            
            if found_log:
                return log_content
            
            return None # No logs found
            
    return None # Result not found

def create_result_zip(identifier):
    import zipfile
    from io import BytesIO
    
    data_dir = "/app/jellybench_data"
    
    # Check if it's one of my console logs
    if identifier.startswith("results/"):
        filepath = os.path.join(data_dir, identifier)
        if os.path.exists(filepath):
            buffer = BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write(filepath, os.path.basename(filepath))
            buffer.seek(0)
            return buffer
        return None

    # Otherwise assume it's a directory name (results_run-...)
    dir_path = os.path.join(data_dir, identifier)
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        log_dir = os.path.join(dir_path, "log")
        target_dir = log_dir if (os.path.exists(log_dir) and os.path.isdir(log_dir)) else dir_path
        
        buffer = BytesIO()
        has_files = False
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for fname in os.listdir(target_dir):
                if fname.endswith(".log") or fname.endswith(".txt"):
                    file_path = os.path.join(target_dir, fname)
                    zip_file.write(file_path, fname)
                    has_files = True
        
        if has_files:
            buffer.seek(0)
            return buffer
            
    return None

def get_system_info(url, api_key):
    headers = {'X-Emby-Token': api_key}
    try:
        info_url = f"{url}/System/Info"
        r = requests.get(info_url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"Failed to fetch system info: {e}")
        return None

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

def stop_benchmark():
    global _process
    if _process:
        log("Stopping benchmark...")
        _process.terminate()
    else:
        log("No benchmark running to stop.")

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
    
    # Setup results directory and log file
    results_dir = "/app/jellybench_data/results"
    os.makedirs(results_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"run_{timestamp}.log"
    log_filepath = os.path.join(results_dir, log_filename)
    
    try:
        # Check if jellybench is available as a command
        cmd = ["jellybench", "--ffmpeg", "/app/jellybench_data/ffmpeg"]
        
        log(f"Running benchmark command: {' '.join(cmd)}")
        log(f"Saving logs to: {log_filename}")
        
        with open(log_filepath, 'w') as log_file:
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
                        
                        # Write to file
                        log_file.write(text)
                        log_file.flush()
                        
                        buffer += text
                        
                        # Process buffer for lines
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            log(line.strip())
                        
                        # Heuristic for prompts
                        if buffer.strip().endswith(":"): 
                             log(buffer.strip())
                             buffer = ""
                             
                except OSError:
                    break
                    
                if _process.poll() is not None:
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
        
    setup_ffmpeg()
    results = run_benchmark()
    analyze_results(results)

def main():
    url = os.environ.get('JELLYFIN_URL')
    api_key = os.environ.get('JELLYFIN_API_KEY')
    run_optimization_process(url, api_key)

if __name__ == "__main__":
    main()
