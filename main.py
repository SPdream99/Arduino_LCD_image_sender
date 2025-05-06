import sys
import serial.tools.list_ports
import serial
from PIL import Image, ImageSequence
# Import the updated convert function which returns bytes
from ImageToDigit import convert
from time import sleep, time
import os
import math

# --- Configuration ---
# Default Folder containing image sequence or path to a single image/gif
# This will be overridden if a file or folder is dragged and dropped onto the script
DEFAULT_FOLDER_PATH = "Bad Apple"
# COM port for Arduino (leave empty to auto-detect common boards)
COM_PORT = ""
# Serial baud rate (must match Arduino sketch)
BAUDRATE = 500000
# Set to True to compile and upload Arduino sketch using arduino-cli
INSTALL_ARDUINO_SKETCH = False
# Arduino board model for arduino-cli
ARDUINO_BOARD_MODEL = "arduino:avr:uno"

# Target Frames Per Second - This is now a theoretical value for reporting only.
# The script will run as fast as the hardware allows, limited by FRAMES_PER_PRINT.
TARGET_FPS = 30
# Frames Per Print: controls how many frames are SKIPPED between each frame that is SENT to the Arduino.
# Setting FRAMES_PER_PRINT to N means only every Nth frame (0, N, 2N, ...) is sent.
# This directly affects the animation speed on the LCD.
# You can adjust this value directly, or calculate it based on a desired FPS if needed.
# Example calculation (adjust the denominator 8 based on your hardware's actual max FPS):
FRAMES_PER_PRINT = math.floor(TARGET_FPS / 8)
if FRAMES_PER_PRINT < 1:
    FRAMES_PER_PRINT = 1
# FRAMES_PER_PRINT = 1 # Set to 1 for maximum speed by default

# Pixel values for black and white in the generated data (0 or 1)
BLACK_PIXEL_VALUE = 0
WHITE_PIXEL_VALUE = 1
# Threshold for determining black/white pixels (0-255). Use -1 for auto calculation.
COLOR_BINARIZATION_THRESHOLD = -1

# Set to True to loop the animation continuously
LOOP_ANIMATION = True
# Set to True to print a text representation of the image during conversion
ENABLE_PRINTOUT = False

# Set to True to load from a pre-built binary script file instead of processing images
AUTO_LOAD_SCRIPT = False

# File/Folder parameters: define the range of frames to process/send
START_FRAME_INDEX = 0   # Starting frame index (inclusive, 0-based)
END_FRAME_INDEX = 1000   # Ending frame index (exclusive)

# --- Constants ---
# Expected number of bytes per frame (8 custom characters * 8 bytes/character)
BYTES_PER_FRAME = 64

# --- Helper Functions ---
def auto_detect_com_port():
    """Auto-detects the COM port for common Arduino/USB-to-Serial chips."""
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        # Look for common descriptions
        if "Arduino" in p.description or "USB-SERIAL CH340" in p.description or "Serial" in p.description:
            return p.device
    return None

def install_arduino_sketch(com_port, model):
    """Compiles and uploads the Arduino sketch using arduino-cli."""
    print("Installing Arduino sketch...")
    sketch_path = "ino/ino.ino"
    if not os.path.exists(sketch_path):
        print(f"Error: Arduino sketch '{sketch_path}' not found. Please ensure it's in the correct location.")
        return False

    # Use subprocess to run the command and capture output
    import subprocess
    try:
        result = subprocess.run(
            ["arduino-cli", "compile", "--upload", "--port", com_port, "--fqbn", model, "ino"],
            capture_output=True, text=True, check=True
        )
        print("Arduino IDE output:\n", result.stdout)
        if result.stderr:
            print("Arduino IDE error output:\n", result.stderr)
        print("Installation complete.")
        return True
    except FileNotFoundError:
        print("Error: 'arduino-cli' command not found. Make sure Arduino CLI is installed and in your PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error during Arduino CLI execution: {e}")
        print("Arduino IDE output:\n", e.stdout)
        if e.stderr:
            print("Arduino IDE error output:\n", e.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred during installation: {e}")
        return False

# --- Main Execution ---
if __name__ == '__main__':
    # Hide the cursor in the terminal for cleaner output
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()  # Ensure the change is applied immediately

    # --- Handle Drag and Drop / Command Line Arguments ---
    # Check if a command-line argument (dragged file/folder path) is provided
    if len(sys.argv) > 1:
        FOLDER_PATH = sys.argv[1]
        print(f"Using path from drag and drop: {FOLDER_PATH}")
        # If using drag and drop, you might want to disable auto_load_script
        # as you are likely providing a new source. Uncomment the line below if needed.
        # AUTO_LOAD_SCRIPT = False
    else:
        # Use the default path from configuration if no argument is provided
        FOLDER_PATH = DEFAULT_FOLDER_PATH
        print(f"Using default folder path: {FOLDER_PATH}")


    # --- Initial Path Validation ---
    if not os.path.exists(FOLDER_PATH):
        print(f"Error: Specified folder or file '{FOLDER_PATH}' not found.")
        sys.stdout.write("\033[?25h")  # Show cursor before exiting
        sys.stdout.flush()
        sys.exit(1)  # Exit with an error code

    # --- COM Port Setup ---
    if COM_PORT == "":
        COM_PORT = auto_detect_com_port()
        if COM_PORT:
            print(f"Auto-detected COM port: {COM_PORT}")
        else:
            print("Could not auto-detect COM port. Please specify it manually in the configuration.")
            print("Available ports:")
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                print(f"- {p.device}: {p.description}")
            sys.stdout.write("\033[?25h")  # Show cursor before exiting
            sys.stdout.flush()
            sys.exit(1)  # Exit with an error code

    # --- Arduino Sketch Installation ---
    if INSTALL_ARDUINO_SKETCH:
        if not install_arduino_sketch(COM_PORT, ARDUINO_BOARD_MODEL):
            sys.stdout.write("\033[?25h")  # Show cursor before exiting
            sys.stdout.flush()
            sys.exit(1)  # Exit with an error code

    # --- File/Folder Handling and Frame Processing ---
    processed_frames = []
    # Use base name for script file to handle both folder and single file cases
    # Replace invalid characters for filenames if necessary
    script_file_name = os.path.basename(FOLDER_PATH)
    # Simple sanitization (more robust handling might be needed for complex paths)
    script_file_name = "".join([c for c in script_file_name if c.isalnum() or c in (' ', '.', '_')]).rstrip()
    if not script_file_name:
        script_file_name = "default_script" # Fallback name if sanitization results in empty string

    script_file_path = os.path.join("Scripts", f"{script_file_name}.bin")


    if AUTO_LOAD_SCRIPT:
        print(f"Attempting to load frames from script file: {script_file_path}")
        try:
            with open(script_file_path, "rb") as f:  # Open in read binary mode
                while True:
                    # Read BYTES_PER_FRAME at a time
                    frame_data = f.read(BYTES_PER_FRAME)
                    if not frame_data:
                        break  # End of file
                    if len(frame_data) == BYTES_PER_FRAME:
                        processed_frames.append(frame_data)  # Append the bytes
                    else:
                         print(f"Warning: Read incomplete frame data from {script_file_path}. Expected {BYTES_PER_FRAME} bytes, got {len(frame_data)}. Skipping.")
                         # Depending on the expected file format, you might want to raise an error here
                         break  # Stop reading on incomplete data

            if not processed_frames:
                 print(f"No frames loaded from {script_file_path}. Check file content or set AUTO_LOAD_SCRIPT = False.")
                 # Optionally fall back to processing images if auto_load fails
                 # AUTO_LOAD_SCRIPT = False
                 # print("Falling back to processing images.")
                 # continue # Go back to the start of the main loop to process images
            else:
                 print(f"Successfully loaded {len(processed_frames)} frames from {script_file_path}.")

        except FileNotFoundError:
            print(f"Script file not found: {script_file_path}. Set AUTO_LOAD_SCRIPT = False to process images.")
            sys.stdout.write("\033[?25h")  # Show cursor before exiting
            sys.stdout.flush()
            sys.exit(1)  # Exit with an error code
        except Exception as e:
            print(f"Error loading script file: {e}")
            sys.stdout.write("\033[?25h")  # Show cursor before exiting
            sys.stdout.flush()
            sys.exit(1)  # Exit with an error code

    else:  # Process images and potentially save to script file
        print("Processing images...")
        # Ensure the Scripts directory exists
        os.makedirs("Scripts", exist_ok=True)
        script_file = None
        try:
            # Open script file for writing in binary mode
            script_file = open(script_file_path, "wb")

            if os.path.isdir(FOLDER_PATH):
                # Process frames from a folder within the start and end range
                # Ensure dirF is defined and sorted correctly
                dirF = sorted([f for f in os.listdir(FOLDER_PATH) if
                               f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))],
                              # Include more image types
                              key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else float(
                                  'inf'))  # Robust sorting
                total_frames_in_folder = len(dirF)
                # Adjust effective end frame based on available files and user setting
                effective_end_frame = min(END_FRAME_INDEX, total_frames_in_folder)

                if START_FRAME_INDEX >= effective_end_frame:
                    print(
                        f"Warning: Start frame index ({START_FRAME_INDEX}) is beyond or equal to effective end frame index ({effective_end_frame}). No frames to process.")
                else:
                    for i in range(START_FRAME_INDEX, effective_end_frame):
                        try:
                            img_path = os.path.join(FOLDER_PATH, dirF[i])
                            img = Image.open(img_path)
                            # Get byte data using the updated convert function
                            byte_data = convert(img, ENABLE_PRINTOUT, BLACK_PIXEL_VALUE, WHITE_PIXEL_VALUE,
                                                COLOR_BINARIZATION_THRESHOLD)
                            if byte_data and len(byte_data) == BYTES_PER_FRAME:  # Ensure we got 64 bytes
                                frame_bytes = bytes(byte_data)
                                processed_frames.append(frame_bytes)  # Append as bytes
                                if script_file:
                                    script_file.write(frame_bytes)  # Write bytes to file
                            else:
                                print(
                                    f"Warning: Could not process frame {i} ({dirF[i]}) or received incorrect data length. Skipping.")
                        except FileNotFoundError:
                            print(
                                f"Error: Frame file not found: {os.path.join(FOLDER_PATH, dirF[i])}. Stopping processing.")
                            break  # Stop processing if a file is missing
                        except Exception as e:
                            print(f"Error processing frame {i} ({dirF[i]}): {e}. Stopping processing.")
                            break  # Stop processing on other errors

            elif os.path.isfile(FOLDER_PATH):
                # Process a single image or GIF
                try:
                    im = Image.open(FOLDER_PATH)
                    if '.gif' in FOLDER_PATH.lower():
                        # Process GIF frames within the start and end range (GIFs are 0-indexed)
                        total_gif_frames = im.n_frames if hasattr(im, 'n_frames') else 1
                        effective_end_frame = min(END_FRAME_INDEX, total_gif_frames)

                        if START_FRAME_INDEX >= effective_end_frame:
                             print(f"Warning: Start frame index ({START_FRAME_INDEX}) is beyond or equal to effective end frame index ({effective_end_frame}). No GIF frames to process.")
                        else:
                            for i, frame in enumerate(ImageSequence.Iterator(im)):
                                if i >= START_FRAME_INDEX and i < effective_end_frame:
                                    byte_data = convert(frame, ENABLE_PRINTOUT, BLACK_PIXEL_VALUE, WHITE_PIXEL_VALUE,
                                                        COLOR_BINARIZATION_THRESHOLD)
                                    if byte_data and len(byte_data) == BYTES_PER_FRAME:
                                        frame_bytes = bytes(byte_data)
                                        processed_frames.append(frame_bytes)
                                        if script_file:
                                            script_file.write(frame_bytes)
                                    else:
                                        print(
                                            f"Warning: Could not process GIF frame {i} or received incorrect data length. Skipping.")
                                elif i >= effective_end_frame:
                                    break  # Stop processing if we've passed the end frame

                    else:
                        # Process a single image (only frame 0) if within start/end range
                        if START_FRAME_INDEX == 0 and END_FRAME_INDEX >= 1:
                            byte_data = convert(im, ENABLE_PRINTOUT, BLACK_PIXEL_VALUE, WHITE_PIXEL_VALUE,
                                                COLOR_BINARIZATION_THRESHOLD)
                            if byte_data and len(byte_data) == BYTES_PER_FRAME:
                                frame_bytes = bytes(byte_data)
                                processed_frames.append(frame_bytes)
                                if script_file:
                                    script_file.write(frame_bytes)
                            else:
                                print(f"Warning: Could not process the image or received incorrect data length.")
                        elif START_FRAME_INDEX > 0:
                             print(f"Info: Single image at index 0 skipped as start is {START_FRAME_INDEX}.")


                except FileNotFoundError:
                     print(f"Error: Image file not found: {FOLDER_PATH}")
                except Exception as e:
                    print(f"Error processing image: {e}")
        finally:
            if script_file:
                script_file.close()  # Ensure the script file is closed even if errors occur
                if processed_frames:
                    print(f"Processed {len(processed_frames)} frames and saved to {script_file_path}.")
                else:
                    print(f"No frames processed. Script file {script_file_path} may be empty or not created.")


    if not processed_frames:
        print("No frames available to send. Exiting.")
        sys.stdout.write("\033[?25h")  # Show cursor before exiting
        sys.stdout.flush()
        sys.exit(1)  # Exit with an error code

    # --- Serial Connection ---
    ser = None  # Initialize ser to None
    try:
        ser = serial.Serial(COM_PORT, BAUDRATE, timeout=1)  # Add a timeout
        # Give the Arduino time to reset after opening the serial connection
        sleep(2)  # Adjust this delay if needed
    except serial.SerialException as e:
        print(f"Failed to connect to Arduino on {COM_PORT}: {e}")
        sys.stdout.write("\033[?25h")  # Show cursor before exiting
        sys.stdout.flush()
        sys.exit(1)  # Exit with an error code


    if not ser or not ser.is_open:  # Check if ser is not None and is open
        print("Failed to open serial port.")
        sys.stdout.write("\033[?25h")  # Show cursor before exiting
        sys.stdout.flush()
        sys.exit(1)  # Exit with an error code


    print(f"Serial port {COM_PORT} opened successfully at {BAUDRATE} baud.")
    print("Please wait for Arduino initialization...")
    # Wait for a signal from Arduino if needed, or a fixed delay
    sleep(3)  # Give Arduino some time to initialize

    # --- Main Loop (Sending and Idle) ---
    try:
        while True:  # Outer loop to keep the script running for looping animation or idle state
            if processed_frames and ser and ser.is_open:  # Check if ser is not None and is open
                print("\nStart sending frames (sending every {} frames)...".format(FRAMES_PER_PRINT)) # Indicate skipping
                begin_time = time()
                frame_count_sent_in_cycle = 0  # Counter for frames *actually sent* in the current cycle

                # Iterate through all processed frames, but only send based on FRAMES_PER_PRINT
                for i, frame_bytes in enumerate(processed_frames):

                    # Check if the current frame index is a multiple of FRAMES_PER_PRINT
                    if i % FRAMES_PER_PRINT == 0:
                        try:
                            # Send the BYTES_PER_FRAME of data
                            ser.write(frame_bytes)
                            # Wait for a confirmation from the Arduino ("OK\r\n")
                            # This synchronizes sending with Arduino's processing speed
                            # Use readline with a timeout to prevent infinite blocking
                            response = ""
                            try:
                               response = ser.readline().decode('utf-8').strip()
                            except serial.SerialTimeoutException:
                               print(f"\nWarning: Serial read timeout while waiting for confirmation for frame {START_FRAME_INDEX + i}. Arduino might be unresponsive.")
                               # Decide how to handle this: break, skip frame, retry?
                               # For now, break the sending loop
                               break # Exit the sending loop


                            if response == "OK":
                                # Arduino processed the frame, proceed to the next
                                # Display actual frame index being sent
                                actual_frame_index = START_FRAME_INDEX + i
                                # Use carriage return \r to overwrite the line for cleaner output
                                sys.stdout.write(f"\rSent frame: {actual_frame_index}")
                                sys.stdout.flush()  # Ensure output is displayed immediately

                                frame_count_sent_in_cycle += 1 # Increment sent frame count

                            else:
                                # Received unexpected response or timeout
                                print(
                                    f"\nWarning: Received unexpected response from Arduino for frame {START_FRAME_INDEX + i}: '{response}'")
                                # Depending on the issue, you might want to retry or skip the frame
                                # For now, we'll just print a warning and continue
                                frame_count_sent_in_cycle += 1  # Still count the frame as attempted


                        except serial.SerialTimeoutException:
                            # This specific timeout is now handled within the inner try block for readline
                            pass  # Already handled above
                        except serial.SerialException as e:
                            print(f"\nSerial error during sending frame {START_FRAME_INDEX + i}: {e}")
                            break  # Exit the sending loop on serial error
                        except Exception as e:
                            print(f"\nAn unexpected error occurred while sending frame {START_FRAME_INDEX + i}: {e}")
                            break  # Exit on other errors
                    # If i % FRAMES_PER_PRINT != 0, the frame is skipped and nothing is sent

                end_time = time()
                duration = end_time - begin_time
                print("\nSending finished.")  # Print a newline after the progress updates
                print("-" * 20)
                print(f"Total frames processed in cycle: {len(processed_frames)}") # Report total processed
                print(f"Total frames sent in this run: {frame_count_sent_in_cycle}") # Report total sent
                print(f"Time elapsed: {duration:.2f} seconds")
                # Report the Target FPS (from configuration)
                print(f"Target FPS: {TARGET_FPS}")
                # Report the Approximate Actual FPS based on frames *sent* and duration
                if duration > 0:
                     print(f"Approximate Actual FPS (sent): {round(frame_count_sent_in_cycle / duration, 2)}")
                # Report the effective FPS based on original frames and duration (if needed)
                # if duration > 0:
                #      print(f"Approximate Effective FPS (original frames): {round(len(processed_frames) / duration, 2)}")
                print("-" * 20)

                # After the sending loop finishes:
                if not LOOP_ANIMATION:
                    # If LOOP_ANIMATION is False, enter idle state
                    print("\nAnimation finished. Entering idle state. Press Enter to exit.")
                    # Wait for user input to exit the script
                    input()
                    break  # Exit the outer while True loop

                else:  # LOOP_ANIMATION is True
                     # If LOOP_ANIMATION is True, the outer while True loop will continue,
                     # restarting the sending process from the beginning of processed_frames.
                     print("\nAnimation cycle finished. Restarting...")


            else:
                 # This case should ideally not be reached if setup was successful
                 print("Error: No processed frames or serial connection is closed unexpectedly.")
                 break  # Exit the outer loop

    except KeyboardInterrupt:
        # Handle Ctrl+C interruption
        print("\nInterrupted by user. Entering idle state. Press Enter to exit.")
        # Enter idle state: wait for user input before cleanup
        input()
    except Exception as e:
        # Handle any other unexpected errors
        print(f"\nAn unexpected error occurred during animation: {e}")
        print("Entering idle state. Press Enter to exit.")
        # Enter idle state: wait for user input before cleanup
        input()

    # --- Cleanup ---
    # This part is reached when the outer loop is broken (either by finishing non-looping animation,
    # user interrupt, or an unrecoverable error).
    if ser and ser.is_open:  # Check if ser object exists and is open
        ser.close()
        print("Serial port closed.")
    else:
        print("Serial port was already closed or not opened.")

    # Show the cursor again in the terminal
    sys.stdout.write("\033[0m\033[?25h")
    sys.stdout.flush()
    sys.exit(0)  # Exit successfully
