FROM python:3.11-slim

# Install system dependencies
# ffmpeg is required for transcoding benchmarks
# git is required to install jellybench_py from github
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    lshw \
    pciutils \
    dmidecode \
    wget \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Download Jellyfin FFmpeg tarball for jellybench to use
RUN mkdir -p /app/jellybench_data/ffmpeg \
    && wget https://repo.jellyfin.org/archive/ffmpeg/linux/7.0.2-3/amd64/jellyfin-ffmpeg_7.0.2-3_portable_linux64-gpl.tar.xz -O /app/jellybench_data/ffmpeg/jellyfin-ffmpeg_7.0.2-3_portable_linux64-gpl.tar.xz

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY optimizer.py .
COPY app.py .
COPY templates/ templates/

EXPOSE 5000

ENTRYPOINT ["python", "app.py"]
