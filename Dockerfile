# Use a stable python slim image
FROM python:3.11-slim

# 1. Install FFmpeg AND ImageMagick (Both are required for subtitles)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    libmagic1 \
    fonts-freefont-ttf \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# 2. Fix ImageMagick security policy (This MUST happen after installing imagemagick)
# This allows MoviePy to use the 'label' and 'caption' methods for subtitles
RUN sed -i 's/domain="path" rights="none" pattern="@\*"/domain="path" rights="read|write" pattern="@\*"/g' /etc/ImageMagick-*/policy.xml

# 3. Set the working directory
WORKDIR /app

# 4. Copy requirements first (optimizes caching so re-runs are faster)
COPY requirements.txt .

# 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of your project code
COPY . .

# 7. Run the script
CMD ["python", "run_agent.py"]