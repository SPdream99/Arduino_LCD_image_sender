# Arduino LCD Image Sender

Welcome to the project for displaying animations on a 16x2 character LCD using Arduino and Python! This project allows you to convert image sequences or GIF files into custom character data and display them on your LCD screen.

## ✨ Key Features

* **Robust Image Processing:** Convert various popular image formats (PNG, JPG, GIF, BMP, WEBP) and image sequences (folders containing numbered images, GIF files) into custom character data suitable for a character LCD.
* **Efficient Serial Communication:** Quickly send processed frame data from your computer to the Arduino over a serial connection.
* **Animation Speed Control:** Adjust the animation speed on the LCD by skipping frames using the `FRAMES_PER_PRINT` setting.
* **Script File Generation/Loading:** Save processed frame data to a binary file (`.bin`) to avoid reprocessing images on subsequent runs, saving initial image processing time.
* **Seamless Arduino Integration:**
    * Automatically detect common Arduino COM ports.
    * Option to compile and upload the Arduino sketch directly from the Python script (requires [Arduino CLI](https://arduino.github.io/arduino-cli/latest/) installation).
* **Idle State:** The Python script can enter an idle state after the animation finishes (if not looping), keeping the serial connection open until you manually exit.

## 🔌 Hardware Requirements

* **Arduino Board:** Compatible boards include Arduino Uno, Nano, Pro Mini, etc.
* **16x2 Character LCD:** A standard 16-column, 2-row character LCD.
* **I2C Adapter (PCF8574):** A common I2C backpack for 16x2 LCDs to simplify wiring.
* **USB Cable:** To connect the Arduino to your computer.

## 💻 Software Requirements

* **Python 3.x:** Ensure Python is installed on your computer.
* **Pillow Library:** For image processing. Install using pip:
    ```bash
    pip install Pillow
    ```
* **PySerial Library:** For serial communication. Install using pip:
    ```bash
    pip install pyserial
    ```
* **Arduino IDE or Arduino CLI:** Necessary to upload the `ino.ino` sketch to your Arduino.

## 🚀 Quick Start

### 1. Prepare Your Arduino

1.  Open the `ino.ino` sketch in the Arduino IDE.
2.  Install the `LiquidCrystal_I2C` library if you haven't already. You can find it in the Library Manager (`Sketch` > `Include Library` > `Manage Libraries...`) and search for "LiquidCrystal_I2C".
3.  Connect your Arduino board to your computer via USB cable.
4.  Select the correct board and COM port in the Arduino IDE (`Tools` menu).
5.  Upload the `ino.ino` sketch to your Arduino board.

### 2. Set up the Python Environment

1.  Ensure Python 3.x is installed.
2.  Install the required Python libraries using pip:
    ```bash
    pip install Pillow pyserial
    ```
3.  Place the `main.py` and `ImageToDigit.py` files in the same directory on your computer.
4.  Create a new folder named `Scripts` in this same directory. This folder will store the processed binary animation files.

### 3. (Optional) Install Arduino CLI

* If you wish to use the `INSTALL_ARDUINO_SKETCH = True` option in `main.py` to upload the sketch directly from the script, you need to install [Arduino CLI](https://arduino.github.io/arduino-cli/latest/). Follow the official installation instructions for your operating system. Ensure the `arduino-cli` command is accessible in your system's PATH.

## ⚙️ Configuration (`main.py`)

Open the `main.py` file in a text editor and adjust the variables in the `--- Configuration ---` section:

* `FOLDER_PATH`: Set the path to your image source. This can be a folder containing sequentially numbered image files (e.g., `"Bad Apple"`) or a single image/GIF file (e.g., `"Test/animation.gif"`).
* `COM_PORT`: Specify your Arduino's serial port (e.g., `"COM3"` on Windows, `"/dev/ttyACM0"` on Linux). Leave as `""` to attempt auto-detection.
* `BAUDRATE`: **Crucially, this must match the `Serial.begin()` speed in your `ino.ino` sketch.** The default is `500000`. Higher values can be faster but might be unstable depending on your Arduino and USB-to-Serial converter.
* `INSTALL_ARDUINO_SKETCH`: Set to `True` to automatically compile and upload the sketch using Arduino CLI before starting the animation. Set to `False` if you prefer to upload manually via the Arduino IDE.
* `ARDUINO_BOARD_MODEL`: Specify the Fully Qualified Board Name (FQBN) for your Arduino board if `INSTALL_ARDUINO_SKETCH` is `True` (e.g., `"arduino:avr:uno"`).
* `TARGET_FPS`: Your desired theoretical frames per second. This value is primarily used for reporting in the console output. The actual animation speed is controlled by `FRAMES_PER_PRINT`.
* `FRAMES_PER_PRINT`: **This is the key setting for controlling animation speed.** It determines how many frames from your source are skipped for each frame that is actually sent to and displayed on the LCD.
    * Set to `1` to send every frame (fastest possible animation, limited by hardware).
    * Set to `2` to send every 2nd frame (skipping one frame between each sent frame).
    * Set to `N` to send every Nth frame.
    * Higher values result in a slower animation but might look smoother if the source FPS is much higher than the LCD's refresh rate.
* `BLACK_PIXEL_VALUE` / `WHITE_PIXEL_VALUE`: Define the byte values (0 or 1) used to represent black and white pixels in the data sent to the Arduino. These typically correspond to the bit values used to define custom characters.
* `COLOR_BINARIZATION_THRESHOLD`: Set the threshold (0-255) used to convert color or grayscale images to black and white. Pixels with intensity >= threshold become white, < threshold become black. Set to `-1` for automatic threshold calculation based on the image's mean intensity.
* `LOOP_ANIMATION`: Set to `True` to make the animation repeat continuously. Set to `False` to play the animation once and then enter an idle state.
* `ENABLE_PRINTOUT`: Set to `True` to display a text representation of each processed frame in your terminal. This can be helpful for debugging but can significantly slow down processing.
* `AUTO_LOAD_SCRIPT`: Set to `True` to load the processed frame data from the binary script file (`Scripts/[folder_name].bin`) instead of reprocessing images. This is much faster for repeated runs. The script file is automatically created on the first run if this is `False`.
* `START_FRAME_INDEX` / `END_FRAME_INDEX`: Define the range of frames from your image source to include in the animation (0-based index, `END_FRAME_INDEX` is exclusive).

## ▶️ Running the Animation

1.  Save the changes to `main.py`.
2.  Open a terminal or command prompt.
3.  Navigate to the directory where your `main.py` file is located.
4.  Run the script using the command:
    ```bash
    python main.py
    ```
5.  The script will start, process/load frames, connect to the Arduino, and begin sending data.
6.  Observe the animation on your LCD!
7.  To stop the animation and enter the idle state, press `Ctrl+C` in the terminal.
8.  In the idle state, press `Enter` to close the serial connection and exit the script.

---

## 📄 File Descriptions

* `main.py`: The main control script. Handles configuration, file management, serial communication, animation loop, frame skipping, and idle state.
* `ImageToDigit.py`: Contains the core logic for loading images, resizing, binarization, and converting pixel data into the 64-byte format for LCD custom characters.
* `ino.ino`: The Arduino sketch that receives the 64-byte frame data over serial, updates the LCD's custom characters, and displays them. It also sends an "OK" confirmation back to the Python script.
* `Scripts/`: A directory automatically created by `main.py` to store the binary script files (`.bin`).

## 💡 Notes and Troubleshooting

* **Animation Speed:** The actual speed is ultimately limited by your Arduino's processing power and the I2C communication speed. If `FRAMES_PER_PRINT` is 1, you are running at the maximum possible speed for your hardware. Increasing `FRAMES_PER_PRINT` will make the animation slower.
* **Serial Issues:** If you encounter serial errors, double-check the `COM_PORT` and `BAUDRATE` settings. Ensure no other application is using the COM port. Try a slightly lower `BAUDRATE` if communication is unstable.
* **LCD Address:** The `0x27` in `LiquidCrystal_I2C lcd(0x27, 16, 2);` is the default I2C address for many PCF8574 adapters. If your LCD doesn't work, you might need to find the correct I2C address (you can use an I2C scanner sketch for this).
* **Image Naming:** For image sequences in a folder, ensure files are named such that sorting alphabetically or numerically results in the correct frame order (e.g., `001.png`, `002.png`, `010.png` is better than `1.png`, `2.png`, `10.png`).
