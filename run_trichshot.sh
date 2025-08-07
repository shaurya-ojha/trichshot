#!/bin/bash
# run_trichshot.sh - script to run TrichShot with smart camera detection and performance tuning

set -e

echo "TrichShot Docker Runner"
echo "==========================================="

# Parse command line arguments
REBUILD=false
PERFORMANCE_MODE="balanced"
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild)
            REBUILD=true
            shift
            ;;
        --performance-mode)
            PERFORMANCE_MODE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --rebuild           Force rebuild of Docker image"
            echo "  --performance-mode  Set performance mode (low|balanced|high)"
            echo "  --verbose           Enable verbose output"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate performance mode
case $PERFORMANCE_MODE in
    low|balanced|high)
        ;;
    *)
        echo "Error: Invalid performance mode '$PERFORMANCE_MODE'. Use: low, balanced, or high"
        exit 1
        ;;
esac

echo "Configuration:"
echo "  Performance Mode: $PERFORMANCE_MODE"
echo "  Verbose Output: $VERBOSE"
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the image if it doesn't exist or if requested
if [[ "$REBUILD" == "true" ]] || ! docker images | grep -q "trichshot"; then
    echo "🔨 Building Docker image (this may take a few minutes)..."
    if [[ "$VERBOSE" == "true" ]]; then
        docker build -t trichshot .
    else
        docker build -t trichshot . > /dev/null 2>&1
        echo "   Build completed successfully"
    fi
    echo
fi

# Allow X11 forwarding (for GUI)
echo "🔧 Setting up X11 forwarding..."
xhost +local:docker > /dev/null 2>&1

# Check system capabilities
echo "📊 System Analysis:"
echo "  Host OS: $(uname -s)"
echo "  Architecture: $(uname -m)"
echo "  CPU cores: $(nproc)"
echo "  Available memory: $(free -h | grep '^Mem:' | awk '{print $7}')"
echo

# Detect available cameras with enhanced analysis
echo "📹 Camera Detection:"
CAMERA_ARGS=""
CAMERA_COUNT=0
EXTERNAL_CAMERAS=()
INTEGRATED_CAMERAS=()

for i in {0..9}; do
    if [ -e "/dev/video$i" ]; then
        if [[ "$VERBOSE" == "true" ]]; then
            echo "  Found camera device: /dev/video$i"
        fi
        CAMERA_ARGS="$CAMERA_ARGS --device=/dev/video$i:/dev/video$i"
        CAMERA_COUNT=$((CAMERA_COUNT + 1))
        
        # Enhanced camera classification
        if command -v v4l2-ctl >/dev/null 2>&1; then
            CAMERA_NAME=$(v4l2-ctl --device=/dev/video$i --info 2>/dev/null | grep "Card type" | cut -d':' -f2 | xargs || echo "Unknown")
            
            if [[ "$VERBOSE" == "true" ]]; then
                echo "    Name: $CAMERA_NAME"
                
                # Get supported formats for performance analysis
                FORMATS=$(v4l2-ctl --device=/dev/video$i --list-formats-ext 2>/dev/null | grep -E "Size:" | head -3 || true)
                if [ ! -z "$FORMATS" ]; then
                    echo "    Top resolutions:"
                    echo "$FORMATS" | sed 's/^/      /'
                fi
            fi
            
            # Classify camera type with enhanced heuristics
            if echo "$CAMERA_NAME" | grep -qi "usb\\|logitech\\|microsoft\\|creative\\|webcam\\|external\\|hd pro\\|c920\\|c922\\|c930\\|c270\\|brio"; then
                EXTERNAL_CAMERAS+=($i)
                if [[ "$VERBOSE" == "false" ]]; then
                    echo "  📹 Camera $i: $CAMERA_NAME (External - Preferred)"
                fi
            elif echo "$CAMERA_NAME" | grep -qi "integrated\\|built-in\\|internal\\|laptop\\|chicony\\|realtek\\|asus\\|hp truevision\\|lenovo\\|dell"; then
                INTEGRATED_CAMERAS+=($i)
                if [[ "$VERBOSE" == "false" ]]; then
                    echo "  💻 Camera $i: $CAMERA_NAME (Integrated)"
                fi
            else
                # Index-based classification
                if [ $i -gt 0 ]; then
                    EXTERNAL_CAMERAS+=($i)
                    if [[ "$VERBOSE" == "false" ]]; then
                        echo "  📹 Camera $i: $CAMERA_NAME (Likely External)"
                    fi
                else
                    INTEGRATED_CAMERAS+=($i)
                    if [[ "$VERBOSE" == "false" ]]; then
                        echo "  💻 Camera $i: $CAMERA_NAME (Likely Integrated)"
                    fi
                fi
            fi
        else
            # Fallback when v4l2-ctl is not available
            if [ $i -gt 0 ]; then
                EXTERNAL_CAMERAS+=($i)
            else
                INTEGRATED_CAMERAS+=($i)
            fi
            echo "  📷 Camera $i: Available (type unknown - v4l2-ctl not found)"
        fi
    fi
done

echo
echo "📊 Camera Summary:"
echo "  Total cameras found: $CAMERA_COUNT"
echo "  External cameras: ${#EXTERNAL_CAMERAS[@]} (${EXTERNAL_CAMERAS[*]})"
echo "  Integrated cameras: ${#INTEGRATED_CAMERAS[@]} (${INTEGRATED_CAMERAS[*]})"

if [ $CAMERA_COUNT -eq 0 ]; then
    echo
    echo "❌ WARNING: No cameras detected!"
    echo "   The app may not work properly without a camera."
    echo "   Make sure camera permissions are correct and try:"
    echo "   sudo usermod -a -G video $USER"
    echo "   (then log out and back in)"
    echo
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
elif [ ${#EXTERNAL_CAMERAS[@]} -gt 0 ]; then
    echo "✅ External camera(s) available - optimal performance expected"
    if [ ${#EXTERNAL_CAMERAS[@]} -gt 1 ]; then
        echo "   Multiple external cameras detected - you can switch between them in the app"
    fi
else
    echo "ℹ️  Only integrated camera(s) available - consider using an external USB camera for better performance"
fi

echo

# Performance mode configuration
case $PERFORMANCE_MODE in
    low)
        EXTRA_ENV="--env TRICHSHOT_DEFAULT_FPS=10 --env TRICHSHOT_DEFAULT_RESOLUTION=320x240 --env TRICHSHOT_DEFAULT_SKIP=3"
        echo "⚡ Performance Mode: LOW"
        echo "   Default settings: 320x240 @ 10 FPS, frame skip: 3"
        ;;
    balanced)
        EXTRA_ENV="--env TRICHSHOT_DEFAULT_FPS=15 --env TRICHSHOT_DEFAULT_RESOLUTION=640x480 --env TRICHSHOT_DEFAULT_SKIP=2"
        echo "⚡ Performance Mode: BALANCED (default)"
        echo "   Default settings: 640x480 @ 15 FPS, frame skip: 2"
        ;;
    high)
        EXTRA_ENV="--env TRICHSHOT_DEFAULT_FPS=20 --env TRICHSHOT_DEFAULT_RESOLUTION=800x600 --env TRICHSHOT_DEFAULT_SKIP=1"
        echo "⚡ Performance Mode: HIGH"
        echo "   Default settings: 800x600 @ 20 FPS, frame skip: 1"
        ;;
esac

echo
echo "🚀 Starting TrichShot..."
echo "   The app will automatically prioritize external cameras"
echo "   You can adjust performance settings in the GUI"
echo "   Close the app window or press Ctrl+C to stop"
echo

# Set resource limits based on performance mode
case $PERFORMANCE_MODE in
    low)
        RESOURCE_LIMITS="--memory=512m --cpus=1.0"
        ;;
    balanced)
        RESOURCE_LIMITS="--memory=1g --cpus=2.0"
        ;;
    high)
        RESOURCE_LIMITS="--memory=2g --cpus=4.0"
        ;;
esac

# Run the container
docker run -it --rm \
    --name trichshot \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    $CAMERA_ARGS \
    --privileged \
    --group-add video \
    $RESOURCE_LIMITS \
    --env OPENCV_LOG_LEVEL=ERROR \
    --env MEDIAPIPE_DISABLE_GPU=1 \
    --env OPENCV_VIDEOIO_PRIORITY_V4L2=1 \
    --env PYTHONUNBUFFERED=1 \
    --env OMP_NUM_THREADS=2 \
    $EXTRA_ENV \
    trichshot

# Clean up X11 permissions
echo
echo "🧹 Cleaning up..."
xhost -local:docker > /dev/null 2>&1

echo "✅ TrichShot stopped successfully."

# Show performance tips based on what was detected
if [ ${#EXTERNAL_CAMERAS[@]} -eq 0 ] && [ $CAMERA_COUNT -gt 0 ]; then
    echo
    echo "💡 Performance Tips:"
    echo "   • Consider using an external USB webcam for better performance"
    echo "   • Try lowering the resolution or FPS if the app feels sluggish"
    echo "   • Use --performance-mode low for older hardware"
fi