# Use a stable python slim image
FROM python:3.11-slim

# 1. Install FFmpeg (Required for MoviePy) and other system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory
WORKDIR /app

# 3. Copy requirements first (optimizes caching)
COPY requirements.txt .

# 4. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your project code
COPY . .

# 6. Run the script
CMD ["python", "run_agent.py"]