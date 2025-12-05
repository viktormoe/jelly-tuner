from flask import Flask, render_template, jsonify, request
import threading
import os
import optimizer

app = Flask(__name__)

# Global state
class State:
    status = "Idle"
    logs = []
    results = None

state = State()

def log_callback(msg):
    state.logs.append(msg)

optimizer.set_log_callback(log_callback)

def run_benchmark_thread():
    state.status = "Running"
    state.logs = []
    state.results = None
    
    try:
        url = os.environ.get('JELLYFIN_URL')
        api_key = os.environ.get('JELLYFIN_API_KEY')
        optimizer.run_optimization_process(url, api_key)
        state.status = "Complete"
    except Exception as e:
        state.status = "Error"
        state.logs.append(f"Error: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_benchmark():
    if state.status == "Running":
        return jsonify({"error": "Benchmark already running"}), 400
    
    thread = threading.Thread(target=run_benchmark_thread)
    thread.start()
    return jsonify({"message": "Benchmark started"})

@app.route('/api/input', methods=['POST'])
def send_input():
    if state.status != "Running":
        return jsonify({"error": "Benchmark not running"}), 400
    
    data = request.json
    text = data.get('input')
    if text is None:
        return jsonify({"error": "No input provided"}), 400
        
    optimizer.send_input(text)
    return jsonify({"message": "Input sent"})

@app.route('/api/stop', methods=['POST'])
def stop_benchmark():
    if state.status != "Running":
        return jsonify({"error": "Benchmark not running"}), 400
        
    optimizer.stop_benchmark()
    return jsonify({"message": "Benchmark stop requested"})

@app.route('/api/backups', methods=['GET'])
def list_backups():
    backups = optimizer.list_backups()
    return jsonify(backups)

@app.route('/api/backup', methods=['POST'])
def create_backup():
    data = request.json or {}
    custom_name = data.get('name')
    
    url = os.environ.get('JELLYFIN_URL')
    api_key = os.environ.get('JELLYFIN_API_KEY')
    filename = optimizer.backup_settings(url, api_key, custom_name)
    if filename:
        return jsonify({"message": "Backup created", "filename": filename})
    else:
        return jsonify({"error": "Backup failed"}), 500

@app.route('/api/restore', methods=['POST'])
def restore_backup():
    data = request.json
    filename = data.get('filename')
    if not filename:
        return jsonify({"error": "Filename required"}), 400
        
    url = os.environ.get('JELLYFIN_URL')
    api_key = os.environ.get('JELLYFIN_API_KEY')
    success = optimizer.restore_settings(url, api_key, filename)
    
    if success:
        return jsonify({"message": "Settings restored successfully"})
    else:
        return jsonify({"error": "Restore failed"}), 500

@app.route('/api/apply', methods=['POST'])
def apply_settings():
    data = request.json
    config = data.get('config')
    if not config:
        return jsonify({"error": "Config required"}), 400
        
    url = os.environ.get('JELLYFIN_URL')
    api_key = os.environ.get('JELLYFIN_API_KEY')
    success = optimizer.apply_recommendations(url, api_key, config)
    
    if success:
        return jsonify({"message": "Settings applied successfully"})
    else:
        return jsonify({"error": "Failed to apply settings"}), 500

@app.route('/api/backup/delete', methods=['POST'])
def delete_backup():
    data = request.json
    filename = data.get('filename')
    if not filename:
        return jsonify({"error": "Filename required"}), 400
        
    success = optimizer.delete_backup(filename)
    if success:
        return jsonify({"message": "Backup deleted successfully"})
    else:
        return jsonify({"error": "Failed to delete backup"}), 500

@app.route('/api/backup/download/<filename>', methods=['GET'])
def download_backup(filename):
    backup_dir = "/app/jellybench_data/backups"
    filepath = os.path.join(backup_dir, filename)
    if os.path.exists(filepath):
        from flask import send_file
        return send_file(filepath, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404

@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    url = os.environ.get('JELLYFIN_URL')
    api_key = os.environ.get('JELLYFIN_API_KEY')
    
    info = optimizer.get_system_info(url, api_key)
    if info:
        return jsonify({"status": "success", "info": info})
    else:
        return jsonify({"status": "error", "message": "Failed to connect to Jellyfin"}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    url = os.environ.get('JELLYFIN_URL')
    api_key = os.environ.get('JELLYFIN_API_KEY')
    
    config = optimizer.get_jellyfin_config(url, api_key)
    if config:
        return jsonify(config)
    else:
        return jsonify({"error": "Failed to fetch configuration"}), 500

@app.route('/api/results', methods=['GET'])
def list_results():
    results = optimizer.list_results()
    return jsonify(results)

@app.route('/api/results/<path:filename>', methods=['GET'])
def get_result(filename):
    content = optimizer.get_result_content(filename)
    if content is not None:
        return jsonify({"filename": filename, "content": content})
    else:
        return jsonify({"error": "File not found"}), 404

@app.route('/api/results/download/<path:filename>', methods=['GET'])
def download_result(filename):
    content = optimizer.get_result_content(filename)
    if content is not None:
        # Create a file-like object
        from io import BytesIO
        buffer = BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)
        
        download_name = os.path.basename(filename)
        if not download_name.endswith('.log') and not download_name.endswith('.txt'):
            download_name += ".log"
            
        return send_file(
            buffer,
            as_attachment=True,
            download_name=download_name,
            mimetype='text/plain'
        )
    else:
        return jsonify({"error": "File not found"}), 404

@app.route('/api/status')
def get_status():
    return jsonify({
        "status": state.status,
        "logs": state.logs,
        "results": state.results
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
