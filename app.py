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

@app.route('/api/status')
def get_status():
    return jsonify({
        "status": state.status,
        "logs": state.logs,
        "results": state.results
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
