# IMX179 Recording Program

## Overview
This program is designed for recording videos using the IMX179 camera (DFRobot FIT0729) along with temperature and humidity data collection. It supports the TrackBox v2.0 framework and is optimized for high-resolution video recording and real-time environmental data monitoring.

---

## Features
- **Camera Specifications**:
  - Max Resolution: 3264x2448 (8 Megapixels)
  - Video Output Format: AVI
  - Supported Resolutions & Frame Rates:
    - 3264x2448 @ 15fps
    - 2592x1944 @ 15fps
    - 1920x1080 @ 30fps
    - Additional resolutions supported.

- **Environment Data Logging**:
  - Reads temperature and humidity data via a serial connection.
  - Supports export to `.xlsx` files and visualizes data with plots.

- **Customizable Settings**:
  - Adjustable resolution, exposure, and recording duration.
  - Automatic and manual exposure control.
  - Configurable file output directories.

---

## Tested condition
- **Operating System**: Windows 11
- **Python Version**: 3.12.6
- **Hardware**: 
  - IMX179 Camera (DFRobot FIT0729)
  - MCU + AHT10 device for environment data collection (e.g., CH340 module)

### Python Dependencies
Install the required packages from the provided `requirements.txt` file:
pip install -r requirements.txt
