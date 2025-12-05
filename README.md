🎵 Jellyfin Auto-Tune

Automated Transcoding Benchmark & Optimizer for Jellyfin

Jellyfin Auto-Tune is a Dockerized utility designed to take the guesswork out of configuring your media server. It runs a dedicated, isolated container to benchmark your hardware's transcoding capabilities (using jellybench_py) and uses the Jellyfin API to analyze your current settings, providing clear optimization recommendations.

🚀 Why use this?

Isolate Risk: Benchmarking is resource-intensive. By running this in a separate container, you avoid crashing or stalling your main Jellyfin server process.

Data-Driven: Stop guessing if VAAPI or QSV is faster. This tool runs the numbers ($1.5x$ vs $5.0x$) and tells you the truth.

Simple Setup: No need to install Python, FFmpeg, or git on your host machine. Docker handles everything.

🛠️ Project Structure

This project consists of four core files. Ensure these exist in your project directory before running:

Dockerfile: Builds the environment with Python 3, FFmpeg, and the benchmark tools.

requirements.txt: Lists Python dependencies (requests).

optimizer.py: The "brain" script that talks to the API and runs the benchmark.

docker-compose.yml: configuration for running the container with hardware access.

📋 Prerequisites

Docker & Docker Compose installed on your host machine.

Hardware Drivers installed on the host (NVIDIA Drivers or Intel/AMD VAAPI drivers).

Jellyfin API Key:

Go to Dashboard > Advanced > API Keys.

Create a new key named Auto-Tune.

⚡ Quick Start (Phase 1)

1. Configuration

Open docker-compose.yml and update the environment variables:

JELLYFIN_URL: Your server's local IP address (e.g., http://192.168.1.50:8096). Do not use localhost.

JELLYFIN_API_KEY: The key you generated in the prerequisites.

2. Enable Hardware Access

You must uncomment the hardware section in docker-compose.yml that matches your GPU:

Intel / AMD: Uncomment the devices: - /dev/dri:/dev/dri section.

NVIDIA: Uncomment the deploy: resources: reservations... section.

3. Run the Optimizer

Open your terminal in the project folder and run:

docker-compose up --build


4. View Results

The container will start, run the benchmark, and print logs to your console. Look for the [BENCH] and [ANALYSIS] tags.

[1/3] Connecting to Jellyfin...
   -> Success! Current Mode: VAAPI

[2/3] Starting Jellybench...
   [BENCH] h264_vaapi: 65fps
   [BENCH] h264_qsv: 240fps  <-- WINNER

[3/3] Analysis Complete
   Recommendation: Your QSV performance is significantly higher than your current VAAPI setting.


🗺️ Roadmap

Phase 1 (Current): Read settings via API, run Benchmark, Report Findings.

Phase 2 (Next): Implement "Safe Backup" to save current Jellyfin config via API.

Phase 3 (Advanced): Add "Auto-Apply" feature to update transcoding settings automatically via API POST request.

⚠️ Disclaimer

High Load: This tool runs stress tests. Your CPU/GPU usage will spike to 100% during the benchmark.

Beta Software: jellybench_py is an alpha tool. Always monitor your server during the first run.

🤝 Credits

Powered by jellybench_py for the benchmarking engine.

Built for the Jellyfin community.