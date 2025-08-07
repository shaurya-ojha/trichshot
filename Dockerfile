# Use Python slim image for faster builds and smaller size
FROM python:3.10-slim

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists with retries and install minimal system dependencies
RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends \
    # Core system packages
    python3-tk \
    python3-dev \
    pkg-config \
    # Minimal OpenCV/video dependencies
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Minimal GUI dependencies
    libgtk-3-0 \
    libcanberra-gtk-module \
    libcanberra-gtk3-module \
    # Video device access and utilities
    v4l-utils \
    udev \
    # X11 forwarding (minimal)
    x11-apps \
    # Networking tools for debugging
    wget \
    curl \
    # Process utilities
    procps \
    # Performance monitoring tools
    htop \
    # Clean up immediately
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python packages with pre-built wheels (much faster)
# Pin versions for better stability with optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    opencv-python-headless==4.8.1.78 \
    mediapipe==0.10.8 \
    numpy==1.24.3

# Create app directory
WORKDIR /app

# Copy the application (expects file named trichshot.py)
COPY trichshot.py .

# Create a non-root user for security and add to video group
RUN useradd -m -s /bin/bash appuser && \
    usermod -a -G video appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables for GUI and performance optimization
ENV DISPLAY=:0
ENV QT_X11_NO_MITSHM=1
ENV OPENCV_LOG_LEVEL=ERROR
ENV MEDIAPIPE_DISABLE_GPU=1
# Performance tuning environment variables
ENV OPENCV_VIDEOIO_PRIORITY_V4L2=1
ENV PYTHONUNBUFFERED=1
ENV OMP_NUM_THREADS=2

# Create startup script with enhanced camera detection and performance info
USER root
RUN echo '#!/bin/bash\n\
echo "TrichShot"\n\
echo "================================"\n\
echo "Performance Mode: Enabled"\n\
echo\n\
\n\
# Check system resources\n\
echo "System Information:"\n\
echo "  CPU cores: $(nproc)"\n\
echo "  Memory: $(free -h | grep Mem | awk '\''{print $2}'\'')"\n\
echo\n\
\n\
# Check available cameras with enhanced detection\n\
echo "Checking available cameras:"\n\
CAMERA_COUNT=0\n\
EXTERNAL_COUNT=0\n\
INTEGRATED_COUNT=0\n\
\n\
for i in {0..9}; do\n\
    if [ -e "/dev/video$i" ]; then\n\
        echo "  /dev/video$i - Available"\n\
        CAMERA_COUNT=$((CAMERA_COUNT + 1))\n\
        \n\
        # Try to get detailed camera info\n\
        if command -v v4l2-ctl >/dev/null 2>&1; then\n\
            CAMERA_INFO=$(v4l2-ctl --device=/dev/video$i --info 2>/dev/null | grep "Card type" | cut -d":" -f2- | xargs || echo "Unknown")\n\
            echo "    Name: $CAMERA_INFO"\n\
            \n\
            # Try to get supported formats and resolutions\n\
            FORMATS=$(v4l2-ctl --device=/dev/video$i --list-formats-ext 2>/dev/null | grep -E "Size:|fps" | head -6 || true)\n\
            if [ ! -z "$FORMATS" ]; then\n\
                echo "    Supported formats (sample):"\n\
                echo "$FORMATS" | sed "s/^/      /"\n\
            fi\n\
            \n\
            # Classify camera type\n\
            if echo "$CAMERA_INFO" | grep -qi "usb\\|logitech\\|microsoft\\|creative\\|webcam\\|external\\|hd pro\\|c920\\|c922\\|c930\\|c270"; then\n\
                echo "    Type: External Camera (Preferred)"\n\
                EXTERNAL_COUNT=$((EXTERNAL_COUNT + 1))\n\
            elif echo "$CAMERA_INFO" | grep -qi "integrated\\|built-in\\|internal\\|laptop\\|chicony\\|realtek\\|asus\\|hp truevision\\|lenovo\\|dell"; then\n\
                echo "    Type: Integrated Camera"\n\
                INTEGRATED_COUNT=$((INTEGRATED_COUNT + 1))\n\
            else\n\
                if [ $i -gt 0 ]; then\n\
                    echo "    Type: Likely External (index > 0)"\n\
                    EXTERNAL_COUNT=$((EXTERNAL_COUNT + 1))\n\
                else\n\
                    echo "    Type: Likely Integrated (index 0)"\n\
                    INTEGRATED_COUNT=$((INTEGRATED_COUNT + 1))\n\
                fi\n\
            fi\n\
        fi\n\
        echo\n\
    fi\n\
done\n\
\n\
echo "Camera Summary:"\n\
echo "  Total cameras: $CAMERA_COUNT"\n\
echo "  External cameras: $EXTERNAL_COUNT"\n\
echo "  Integrated cameras: $INTEGRATED_COUNT"\n\
echo\n\
\n\
if [ $CAMERA_COUNT -eq 0 ]; then\n\
    echo "❌ WARNING: No camera devices found!"\n\
    echo "   Make sure to run with camera devices mapped:"\n\
    echo "   docker run --device=/dev/video0 --device=/dev/video1 ..."\n\
    echo\n\
elif [ $EXTERNAL_COUNT -gt 0 ]; then\n\
    echo "✅ External camera(s) detected - optimal performance expected"\n\
    echo\n\
else\n\
    echo "ℹ️  Using integrated camera - performance may vary"\n\
    echo\n\
fi\n\
\n\
# Check if X11 is forwarded\n\
if [ -z "$DISPLAY" ]; then\n\
    echo "❌ WARNING: No DISPLAY environment variable set"\n\
    echo "   Make sure to run with: docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix"\n\
    echo\n\
else\n\
    echo "✅ Display forwarding configured: $DISPLAY"\n\
    echo\n\
fi\n\
\n\
# Performance recommendations\n\
echo "Performance Tips:"\n\
echo "  • Start with default settings (640x480 @ 15 FPS)"\n\
echo "  • Increase frame skip if performance is poor"\n\
echo "  • Lower resolution/FPS for older hardware"\n\
echo "  • External cameras generally perform better"\n\
echo\n\
\n\
echo "Starting TrichShot..."\n\
echo "========================================"\n\
python3 /app/trichshot.py\n\
' > /app/start.sh && chmod +x /app/start.sh

USER appuser

# Default command
CMD ["/app/start.sh"]