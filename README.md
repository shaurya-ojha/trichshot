# TrichShot — Visual Alerts to Prevent Hair-Pulling Episodes

[![Releases](https://img.shields.io/github/v/release/shaurya-ojha/trichshot?label=Releases&color=ff6f61)](https://github.com/shaurya-ojha/trichshot/releases)

A lightweight tool that watches your webcam and shows visual warnings to help stop trichotillomania (hair-pulling) episodes. TrichShot runs locally. It uses a simple image-difference method to detect hand-to-head motion and flashes a visual cue when it detects risk behavior.

- Topics: compulsivity, control, docker, impulse, local, python3, shell, trichotillomania, visual, warning, webcam

<!-- TOC -->
- [Why TrichShot](#why-trichshot)
- [Key features](#key-features)
- [How it works](#how-it-works)
- [Screenshots](#screenshots)
- [Install — local (Python 3)](#install---local-python-3)
- [Install — releases (download and run)](#install---releases-download-and-run)
- [Install — Docker](#install---docker)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Usage examples](#usage-examples)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [Contributing](#contributing)
- [License](#license)
<!-- TOC -->

## Why TrichShot
- Treats trichotillomania as a momentary impulse that you can interrupt.
- Keeps everything local. No cloud. No data leaves your machine.
- Low CPU use. Works on modest laptops and single-board computers.
- Flexible: run from Python or Docker, adjust sensitivity, choose overlay style.

## Key features
- Real-time webcam monitoring using OpenCV.
- Simple motion filter tuned for hand-to-head gestures.
- Visual warning overlays: full-screen flash, colored frame, or on-screen icon.
- Log events for personal tracking.
- Config via file or CLI flags.
- Supports Linux, macOS, Windows (Python 3.8+).
- Optional Docker image for isolated runs.

## How it works
1. Capture frames from your webcam.
2. Convert to grayscale and blur to reduce noise.
3. Compare new frames to a background frame using absolute difference.
4. Threshold the difference, find contours, and measure motion in regions near the head.
5. If motion passes the configured threshold, trigger a visual alert and write a timestamped event to logs.

This approach uses classic computer vision primitives. It avoids face recognition and keeps the processing simple and fast.

## Screenshots
![Webcam warning overlay](https://images.unsplash.com/photo-1515879218367-8466d910aaa4?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=60)
![Red frame warning](https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Warning_font_awesome.svg/512px-Warning_font_awesome.svg.png)

## Install — local (Python 3)
Requirements:
- Python 3.8 or later
- pip
- Webcam access

Steps:
1. Clone the repo:
   ```
   git clone https://github.com/shaurya-ojha/trichshot.git
   cd trichshot
   ```
2. Create a virtual environment and activate it:
   ```
   python3 -m venv .venv
   source .venv/bin/activate    # macOS / Linux
   .venv\Scripts\activate       # Windows
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy or edit the sample config:
   ```
   cp config.example.yaml config.yaml
   ```
5. Run:
   ```
   python trichshot/main.py --config config.yaml
   ```

## Install — releases (download and run)
Download the packaged release asset from the Releases page and run the provided executable or script. Visit and download the file here: https://github.com/shaurya-ojha/trichshot/releases

After you download the release asset, make it executable (if applicable) and run it:
- Linux / macOS:
  ```
  chmod +x trichshot-release-*.run
  ./trichshot-release-*.run
  ```
- Windows:
  - Double-click the downloaded .exe or run from PowerShell:
    ```
    .\trichshot-release-setup.exe
    ```

If the release contains a single script, run it as directed in the release notes. The release package will include a README with platform-specific steps.

## Install — Docker
Run the official image or build locally.

1. Pull the image:
   ```
   docker pull ghcr.io/shaurya-ojha/trichshot:latest
   ```
2. Run with device access (Linux):
   ```
   docker run --rm --device=/dev/video0:/dev/video0 \
     -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
     ghcr.io/shaurya-ojha/trichshot:latest
   ```
3. If you build locally:
   ```
   docker build -t trichshot:local .
   docker run --rm --device=/dev/video0:/dev/video0 trichshot:local
   ```

Notes:
- Grant container access to your webcam device.
- On macOS and Windows, use Docker Desktop with appropriate device passthrough or share the camera via host integration.

## Quick start
Start with a low sensitivity and test gestures:
```
python trichshot/main.py --sensitivity 0.6 --overlay frame
```
- overlay: frame | full | icon
- sensitivity: 0.1 (low) — 1.0 (high)

Move your hand toward your head to test. The app will display the selected overlay and log events to logs/events.log.

## Configuration
You can configure TrichShot via CLI flags or a YAML file. Example config.yaml:
```yaml
camera:
  index: 0
  width: 640
  height: 480

detection:
  sensitivity: 0.6
  min_contour_area: 500
  head_region:
    x_pct: 0.3
    y_pct: 0.1
    width_pct: 0.4
    height_pct: 0.5

alert:
  style: frame
  color: "#FF3B30"
  duration_ms: 700

logging:
  path: logs/events.log
  rotate: daily
```
Key fields:
- camera.index: webcam device index
- detection.sensitivity: motion threshold
- detection.min_contour_area: ignore small motion blobs
- alert.style: frame | full | icon
- alert.duration_ms: how long to show the visual cue

Adjust the head_region percentages to fit your camera framing.

## Usage examples
- Run with default config:
  ```
  python trichshot/main.py
  ```
- Run with CLI overrides:
  ```
  python trichshot/main.py --sensitivity 0.4 --overlay icon --camera 1
  ```
- Run and log events to a custom file:
  ```
  python trichshot/main.py --log ./mylogs/trich_events.log
  ```
- Use a test mode that flashes alerts without webcam input:
  ```
  python trichshot/main.py --test-mode
  ```

## Development
- Code layout:
  - trichshot/main.py — entry point
  - trichshot/detector.py — motion detection logic
  - trichshot/alert.py — overlay rendering
  - trichshot/config.py — config loader
  - requirements.txt — pinned dependencies
- Style:
  - Follow PEP8
  - Keep functions small and well-named
- Local build:
  ```
  python -m pip install -r requirements-dev.txt
  pre-commit run --all-files
  ```

## Testing
- Unit tests use pytest.
- Run tests:
  ```
  pytest tests/
  ```
- CI will run tests and basic lint checks on push.

## Troubleshooting & FAQ
Q: The app does not detect my webcam.
A: Check camera.index in config. Test camera with another app (e.g., cheese, Photo Booth). Ensure OS grants camera permission.

Q: I get false positives when I move in the background.
A: Lower sensitivity and increase min_contour_area. Tighten head_region to focus detection near your head.

Q: The overlay does not appear on top.
A: On some systems X11 or window manager settings block fullscreen overlays. Try the frame or icon overlay. Use Docker host display sharing for container runs.

Q: How private is this?
A: TrichShot runs locally and does not send images off your machine. Logs only contain timestamps and basic event metadata.

Q: Can I change the alert visuals?
A: Yes. Edit the alert.color and alert.style in config.yaml. You can replace icon assets in assets/icons/.

## Contributing
- Fork the repo.
- Create a feature branch.
- Write tests for new behaviors.
- Open a pull request with a clear description and screenshots if you change visuals.
- Keep commits small and focused.

Code of conduct: Be respectful in issue threads and PR reviews.

## Releases
Find packaged builds, installers, and release notes on the Releases page. Download the release asset and run it on your platform: https://github.com/shaurya-ojha/trichshot/releases

The Releases page contains platform-specific assets and a short install script for each supported OS.

## Credits
- Core CV logic built with OpenCV.
- Icons and imagery from public sources.
- Test feedback from the trichotillomania support community.

## License
MIT License — see LICENSE file for details

Contact: Open an issue for questions, feature requests, or bug reports.