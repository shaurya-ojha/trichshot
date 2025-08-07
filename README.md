# TrichShot 🎯

A real-time hand detection system that helps prevent trichotillomania (hair-pulling) episodes by providing visual warnings when hands approach the face area. Features smart camera detection, external camera prioritization, and performance optimizations for various hardware configurations.

![TrichShot Demo](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Docker](https://img.shields.io/badge/Docker-Supported-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

### Core Functionality

- 🖐️ **Real-time hand detection** using MediaPipe
- 🚨 **Visual warning system** with full-screen overlay
- 🎯 **Customizable danger zones** for face area detection
- 📊 **Session statistics** and monitoring
- 🔄 **Automatic camera prioritization** (external cameras first)

### Performance Optimizations

- ⚡ **Configurable frame rates** (10-20 FPS)
- 🎬 **Frame skipping** for better performance
- 💾 **Detection result caching** to reduce CPU usage
- 🖥️ **Multi-threaded processing** with resource management

### Smart Camera Detection

- 🔍 **Automatic camera discovery** and classification
- 📹 **External camera prioritization** over integrated cameras
- 🏷️ **Camera type identification** (USB, Logitech, etc.)
- 📊 **Format and resolution detection**
- 🔧 **Performance optimization per camera type**

## 🚀 Quick Start

### Prerequisites

- Docker installed on your system
- X11 forwarding support (Linux/macOS)
- At least one camera connected to your system
- Camera permissions properly configured

### Installation & Running

1. **Clone the repository:**

   ```bash
   git clone https://github.com/virualbeck/trichshot.git
   cd trichshot
   ```

2. **Make the run script executable:**

   ```bash
   chmod +x run_trichshot.sh
   ```

3. **Run with default settings:**

   ```bash
   ./run_trichshot.sh
   ```

4. **Or choose a performance mode:**

   ```bash
   # For older hardware
   ./run_trichshot.sh --performance-mode low

   # For balanced performance (default)
   ./run_trichshot.sh --performance-mode balanced

   # For high-end systems
   ./run_trichshot.sh --performance-mode high
   ```

## 🎮 Usage

### Starting the Application

The application provides a comprehensive GUI for configuration and monitoring:

1. **Camera Selection**: Choose from automatically detected cameras
2. **Performance Settings**: Adjust FPS, resolution, and frame skip
3. **Detection Configuration**: Customize danger zone areas
4. **Session Monitoring**: Track warnings and session time

### Performance Modes

| Mode         | Resolution | FPS | Frame Skip | Best For                           |
| ------------ | ---------- | --- | ---------- | ---------------------------------- |
| **Low**      | 320x240    | 10  | 3          | Older hardware, integrated cameras |
| **Balanced** | 640x480    | 15  | 2          | Most systems, recommended default  |
| **High**     | 800x600    | 20  | 1          | Powerful systems, external cameras |

### Command Line Options

```bash
./run_trichshot.sh [OPTIONS]

Options:
  --rebuild              Force rebuild of Docker image
  --performance-mode     Set performance mode (low|balanced|high)
  --verbose              Enable verbose output and debugging
  --help                 Show help message and exit
```

### GUI Controls

- **Start/Stop Monitoring**: Begin or end the detection session
- **Camera Selection**: Switch between available cameras
- **Refresh Cameras**: Re-detect available cameras
- **Danger Zone Sliders**: Adjust the detection area
- **Performance Settings**: Modify FPS, resolution, and frame skip in real-time

## 🔧 Configuration

### Camera Setup

The application automatically detects and prioritizes cameras in this order:

1. **External USB cameras** (Logitech, Microsoft, Creative, etc.)
2. **Unknown cameras** with index > 0
3. **Integrated laptop cameras**

### Performance Tuning

For optimal performance, consider:

- **External cameras** generally perform better than integrated ones
- **Lower resolutions** (640x480) for older hardware
- **Higher frame skip values** (2-3) for CPU-constrained systems
- **Reduced FPS** (10-15) for smoother operation

### Danger Zone Configuration

- **Top Slider**: Adjusts the upper boundary of the detection zone
- **Bottom Slider**: Adjusts the lower boundary of the detection zone
- **Default**: Top 75% to bottom 75% of the screen (face area)

## 🐳 Docker Details

### Container Features

- **Lightweight**: Based on Python 3.10 slim image
- **Secure**: Runs as non-root user with minimal permissions
- **Optimized**: Pre-configured environment variables for performance
- **Smart**: Automatic camera device mapping and detection

### Environment Variables

The container supports several performance tuning variables:

```bash
OPENCV_LOG_LEVEL=ERROR                 # Reduce OpenCV logging
MEDIAPIPE_DISABLE_GPU=1               # Force CPU-only processing
OPENCV_VIDEOIO_PRIORITY_V4L2=1        # Prioritize V4L2 backend
OMP_NUM_THREADS=2                     # Limit OpenMP threads
PYTHONUNBUFFERED=1                    # Real-time Python output
```

### Resource Limits

Resource limits are automatically set based on performance mode:

- **Low**: 512MB RAM, 1 CPU core
- **Balanced**: 1GB RAM, 2 CPU cores
- **High**: 2GB RAM, 4 CPU cores

## 🛠️ Development

### File Structure

```
trichshot/
├── trichshot.py          # Main application
├── Dockerfile            # Docker container configuration
├── run_trichshot.sh      # Launch script with smart detection
├── LICENSE               # Standard MIT License
└── README.md             # This file
```

### Local Development

To run without Docker:

1. **Install dependencies:**

   ```bash
   pip install opencv-python mediapipe numpy tkinter
   ```

2. **Install system dependencies (Linux):**

   ```bash
   sudo apt-get install python3-tk v4l-utils
   ```

3. **Run directly:**
   ```bash
   python3 trichshot.py
   ```

### Building the Docker Image

```bash
# Build with default settings
docker build -t trichshot .

# Build with verbose output
docker build -t trichshot . --progress=plain
```

## 📊 Performance Tips

### Hardware Recommendations

- **CPU**: Multi-core processor (2+ cores recommended)
- **RAM**: 1GB+ available memory
- **Camera**: External USB camera for best performance
- **OS**: Linux (Ubuntu/Debian) for optimal V4L2 support

### Troubleshooting Performance Issues

1. **Low FPS**: Reduce resolution or increase frame skip
2. **High CPU usage**: Lower FPS or enable more frame skipping
3. **Camera not detected**: Check permissions and V4L2 support
4. **Laggy GUI**: Try performance mode "low"

### Camera Compatibility

**Best Performance:**

- Logitech C920, C922, C930e
- Microsoft LifeCam series
- Creative Live! Cam series

**Good Performance:**

- Most USB webcams
- External cameras with V4L2 support

**Limited Performance:**

- Integrated laptop cameras
- Cameras without V4L2 drivers

## 🔒 Privacy & Security

- **Local Processing**: All detection happens locally, no data sent externally
- **No Recording**: Frames are processed in memory and not stored
- **Minimal Permissions**: Docker container runs with least-privilege access
- **Camera Access**: Only accesses cameras you explicitly grant access to

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Submit a pull request

### Reporting Issues

When reporting issues, please include:

- System specifications (OS, CPU, RAM)
- Camera information (model, type)
- Performance mode used
- Error messages or logs
- Steps to reproduce

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MediaPipe** team for the excellent hand detection framework
- **OpenCV** community for computer vision tools
- **Docker** for containerization platform
- Contributors and users who provide feedback and improvements

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/virtualbeck/trichshot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/virtualbeck/trichshot/discussions)
- **Documentation**: This README and inline code comments

---

**Disclaimer**: TrichShot is a tool designed to assist with awareness of hand-to-face movements. It is not a medical device and should not replace professional medical advice or treatment. If you're struggling with trichotillomania or similar conditions, please consult with a healthcare professional.

Also, TrichShot was vibe-coded into existence. I'm putting this out there after I spent a few hours tweaking it. It has greatly minimized my compulsion to twist/pull while at the computer, and I'm already seeing positive results away from the computer. Hopefully this will be a positive reinforcement loop that can help me (and you!) to alleviate this impulse control disorder.
