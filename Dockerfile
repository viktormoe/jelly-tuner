FROM python:3.11-slim

# Install system dependencies
# ffmpeg is required for transcoding benchmarks
# git is required to install jellybench_py from github
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY optimizer.py .
COPY app.py .
COPY templates/ templates/

EXPOSE 5000

ENTRYPOINT ["python", "app.py"]
