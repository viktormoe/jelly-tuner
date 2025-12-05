# 🎵 Jellyfin Auto-Tune

**Jellyfin Auto-Tune** is a containerized tool designed to benchmark and optimize your Jellyfin hardware transcoding settings. It wraps the [jellybench](https://github.com/jellyfin/jellybench) tool in a user-friendly Web UI, making it easy to run tests, view real-time logs, and analyze results without needing to mess with complex command-line arguments.

## ✨ Features

*   **Web Interface:** A modern, dark-themed Web UI to control the benchmark and view progress.
*   **Dockerized:** Runs in a container with all dependencies (FFmpeg, Python, drivers) pre-configured.
*   **Real-time Logging:** Stream benchmark logs directly to your browser.
*   **Interactive:** Handle prompts (e.g., "Continue? y/n") directly from the Web UI.
*   **Hardware Support:** Pre-configured for NVIDIA GPU passthrough (requires setup).
*   **Result Access:** Downloaded videos and benchmark results are saved to a mounted volume for easy access.

## 🚀 Prerequisites

*   **Docker** and **Docker Compose** installed on your system.
*   **NVIDIA Container Toolkit** (if using NVIDIA GPU for transcoding).
*   A running **Jellyfin** server (local or remote).
*   A **Jellyfin API Key** (Generate one in Jellyfin Dashboard > API Keys).

## 🛠️ Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/viktormoe/jelly-tuner.git
    cd jelly-tuner
    ```

2.  **Configure Environment Variables:**
    Copy the example environment file and edit it:
    ```bash
    cp .env.example .env
    nano .env
    ```
    Fill in your details:
    *   `JELLYFIN_URL`: The URL of your Jellyfin server (e.g., `http://192.168.1.100:8096`).
    *   `JELLYFIN_API_KEY`: Your Jellyfin API key.
    *   `PORT`: The port to run the Web UI on (default: `5000`).

3.  **Configure Hardware Acceleration (Important!):**
    Open `docker-compose.yml`:
    ```bash
    nano docker-compose.yml
    ```
    *   **NVIDIA Users:** Ensure the `runtime: nvidia` and `deploy` sections are uncommented (they are by default).
    *   **Intel/AMD Users:** You may need to comment out the NVIDIA sections and map `/dev/dri` devices instead.

## ▶️ Usage

1.  **Start the Container:**
    ```bash
    docker-compose up --build
    ```

2.  **Access the Web UI:**
    Open your browser and navigate to:
    `http://localhost:5000` (or the port you configured).

3.  **Run the Benchmark:**
    *   Click the **Start Benchmark** button.
    *   The status will change to "Running" and logs will appear in the terminal window.

4.  **Interacting with the Benchmark:**
    *   If the benchmark asks for input (e.g., "Continue (y/n):"), type your response in the input box below the start button and click **Send** (or press Enter).
    *   Common prompts include confirming disclaimers or handling connection warnings.

## 📂 Accessing Results

All benchmark data, including downloaded test videos and result files, is stored in the `jellybench_data` folder in your project directory. This folder is mounted to the container, so files persist even after the container stops.

```bash
ls jellybench_data/
```

## ❓ Troubleshooting

*   **"Connection failed":** Ensure your `JELLYFIN_URL` is reachable from within the container. If running Jellyfin on the same host, use the host's IP address, not `localhost`.
*   **"GPU not found":**
    *   Check if NVIDIA Container Toolkit is installed.
    *   Verify `docker-compose.yml` has the correct `runtime` and `capabilities` set.
    *   Check container logs for driver errors.
*   **"404 Error" for FFmpeg:** The container automatically downloads and caches the correct FFmpeg version. If this fails, check your internet connection and try rebuilding.

## 📜 License

This project is open-source. Feel free to modify and distribute.
