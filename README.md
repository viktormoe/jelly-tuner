# 🎵 Jellyfin Auto-Tune

Automated Transcoding Benchmark & Optimizer for Jellyfin

Jellyfin Auto-Tune is a Dockerized utility designed to take the guesswork out of configuring your media server. It runs a dedicated, isolated container to benchmark your hardware's transcoding capabilities (using jellybench_py) and uses the Jellyfin API to analyze your current settings, providing clear optimization recommendations.

## 🚀 Why use this?

*   **Isolate Risk:** Benchmarking is resource-intensive. By running this in a separate container, you avoid crashing or stalling your main Jellyfin server process.
*   **Data-Driven:** Stop guessing if VAAPI or QSV is faster. This tool runs the numbers ($1.5x$ vs $5.0x$) and tells you the truth.
*   **Simple Setup:** No need to install Python, FFmpeg, or git on your host machine. Docker handles everything.

## 🛠️ Project Structure

This project consists of four core files. Ensure these exist in your project directory before running:

*   `Dockerfile`: Builds the environment with Python 3, FFmpeg, and the benchmark tools.
*   `requirements.txt`: Lists Python dependencies (requests, flask).
*   `optimizer.py`: The "brain" script that talks to the API and runs the benchmark.
*   `app.py`: The Flask server that powers the Web UI.
*   `docker-compose.yml`: configuration for running the container with hardware access.

## 📋 Prerequisites

*   Docker & Docker Compose installed on your host machine.
*   Hardware Drivers installed on the host (NVIDIA Drivers or Intel/AMD VAAPI drivers).
*   **Jellyfin API Key:**
    1.  Go to **Dashboard > Advanced > API Keys**.
    2.  Create a new key named **Auto-Tune**.

## ⚡ Quick Start

### 1. Configuration

1.  Copy the example configuration file:
    ```bash
    cp .env.example .env
    ```
2.  Open `.env` and update the variables with your actual details:

    ```env
    JELLYFIN_URL=http://192.168.1.50:8096
    JELLYFIN_API_KEY=your_api_key_here
    ```

    *   `JELLYFIN_URL`: Your server's local IP address. **Do not use localhost.**
    *   `JELLYFIN_API_KEY`: The key you generated in the prerequisites.

### 2. Enable Hardware Access

You must uncomment the hardware section in `docker-compose.yml` that matches your GPU:

*   **Intel / AMD:** Uncomment the `devices: - /dev/dri:/dev/dri` section.
*   **NVIDIA:** Uncomment the `deploy: resources: reservations...` section.

### 3. Run the Optimizer

Open your terminal in the project folder and run:

```bash
docker-compose up --build
```

### 4. Access the Web UI

Open your browser and navigate to:
[http://localhost:5000](http://localhost:5000)

Click **"Start Benchmark"** to begin the tests. The logs and results will be displayed in the web interface.

## 🐳 Docker Desktop & Docker Instructions

This project is designed to run anywhere Docker runs, including Docker Desktop (Windows/Mac/Linux) and standard Docker Engine (Linux).

### Running on Linux (Standard Docker)
1.  Ensure `docker` and `docker-compose` are installed.
2.  Verify hardware drivers (e.g., `ls /dev/dri` for Intel/AMD).
3.  Run `docker-compose up --build`.

### Running on Docker Desktop (Windows/Mac)
1.  Install Docker Desktop.
2.  Ensure the Docker engine is running.
3.  Open a terminal (PowerShell, CMD, or Terminal).
4.  Navigate to the project folder.
5.  Run `docker-compose up --build`.
    *   **Note:** Hardware passthrough on Windows/Mac (especially for GPU) can be complex.
        *   **Windows (WSL2):** Ensure you have the latest GPU drivers and WSL2 kernel updates. GPU passthrough works for NVIDIA (CUDA) and Intel (Compute), but VAAPI/QSV might have limitations depending on the WSL2 backend.
        *   **Mac:** GPU passthrough is generally not supported for transcoding in the same way as Linux. This tool is best run on the actual server hardware hosting Jellyfin.

## 🗺️ Roadmap

*   **Phase 1 (Current):** Read settings via API, run Benchmark, Report Findings.
*   **Phase 2 (Next):** Implement "Safe Backup" to save current Jellyfin config via API.
*   **Phase 3 (Advanced):** Add "Auto-Apply" feature to update transcoding settings automatically via API POST request.

## ⚠️ Disclaimer

*   **High Load:** This tool runs stress tests. Your CPU/GPU usage will spike to 100% during the benchmark.
*   **Beta Software:** `jellybench_py` is an alpha tool. Always monitor your server during the first run.

## 🤝 Credits

*   Powered by `jellybench_py` for the benchmarking engine.
*   Built for the Jellyfin community.
