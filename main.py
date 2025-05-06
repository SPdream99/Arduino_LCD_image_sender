import sys
import serial.tools.list_ports
import serial
from PIL import Image, ImageSequence
# Import the updated convert function which returns bytes
from ImageToDigit import convert
from time import sleep, time
import os

# --- Configuration ---
folder = "Bad Apple"    # Folder containing image sequence or path to a single image/gif
COM = ""                # COM port for Arduino (leave empty to auto-detect CH340)
BAUDRATE = 500000       # Serial baud rate (must match Arduino)
install = True         # Set to True to compile and upload Arduino sketch
model = "arduino:avr:uno"   # Arduino board model

FPS = 1                 # Target FPS (adjust FPP accordingly)
# FPP is now less critical as we wait for Arduino confirmation
FPP = 1     # Frame advance per print (visual only speed hack, keep at 1)

BLACK = 0               # Value for black pixels in the generated data
WHITE = 1               # Value for white pixels in the generated data
COLOR_CHECK = 240       # Threshold for determining black/white pixels (-1 for auto)
LOOP = False             # Loop the animation
printout = False       # Print text representation of the image during conversion

auto_load = False       # Load from pre-built script file (currently not used with byte sending)

# File/Folder parameters (currently basic implementation)
start = 0
end = 100

# --- File/Folder Handling ---
if os.path.isdir(folder):
    # If it's a folder, list and sort image files
    dirF = os.listdir(f"./{folder}/")
    # Filter for png files and sort numerically
    dirF = sorted([f for f in dirF if f.endswith('.png')], key=lambda x: int(x.split(".png")[0]))
    end = len(dirF)     # Set end to the number of frames
elif os.path.isfile(folder):
    # If it's a single file, check supported extensions
    if not any(folder.lower().endswith(ext) for ext in ['.gif', 'png', 'jpg', 'jpeg', 'bmp', 'webp']):
        print("Unsupported file format.")
        exit()
    end = 1 # Only one frame for single images
else:
    print(f"Error: Folder or file '{folder}' not found.")
    exit()

# --- Main Execution ---
if __name__ == '__main__':
    # Hide the cursor in the terminal
    print("\033[?25l", end="")

    # Auto-detect COM port if not specified
    if COM == "":
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            # Look for common Arduino/USB-to-Serial chip descriptions
            if "Arduino" in p.description or "USB-SERIAL CH340" in p.description or "Serial" in p.description:
                COM = p.device
                print(f"Auto-detected COM port: {COM}")
                break
        if COM == "":
            print("Could not auto-detect COM port. Please specify it manually.")
            # Show available ports to help the user
            print("Available ports:")
            for p in ports:
                print(f"- {p.device}: {p.description}")
            sys.stdout.write("\033[?25h") # Show cursor before exiting
            exit()


    # Compile and upload Arduino sketch if install is True
    if install:
        print("Installing Arduino sketch...")
        # Ensure the 'ino' folder exists and contains the .ino file
        if os.path.exists("ino/ino.ino"):
             # Use subprocess to run the command and capture output
            import subprocess
            try:
                result = subprocess.run(
                    ["arduino-cli", "compile", "--upload", "--port", COM, "--fqbn", model, "ino"],
                    capture_output=True, text=True, check=True
                )
                print("Arduino IDE output:\n", result.stdout)
                if result.stderr:
                    print("Arduino IDE error output:\n", result.stderr)
                print("Installation complete.")
            except FileNotFoundError:
                print("Error: 'arduino-cli' command not found. Make sure Arduino CLI is installed and in your PATH.")
                sys.stdout.write("\033[?25h") # Show cursor before exiting
                exit()
            except subprocess.CalledProcessError as e:
                print(f"Error during Arduino CLI execution: {e}")
                print("Arduino IDE output:\n", e.stdout)
                if e.stderr:
                    print("Arduino IDE error output:\n", e.stderr)
                sys.stdout.write("\033[?25h") # Show cursor before exiting
                exit()
            except Exception as e:
                print(f"An unexpected error occurred during installation: {e}")
                sys.stdout.write("\033[?25h") # Show cursor before exiting
                exit()
        else:
            print("Error: 'ino/ino.ino' not found. Please ensure the Arduino sketch is in the correct location.")
            sys.stdout.write("\033[?25h") # Show cursor before exiting
            exit()


    # Open serial connection
    try:
        ser = serial.Serial(COM, BAUDRATE, timeout=1) # Add a timeout
        # Give the Arduino time to reset after opening the serial connection
        sleep(2)
    except serial.SerialException as e:
        print(f"Failed to connect to Arduino on {COM}: {e}")
        sys.stdout.write("\033[?25h") # Show cursor before exiting
        exit()

    if not ser.is_open:
        print("Failed to open serial port.")
        sys.stdout.write("\033[?25h") # Show cursor before exiting
        exit()


    print(f"Serial port {COM} opened successfully at {BAUDRATE} baud.")
    print("Please wait for Arduino initialization...")
    # Wait for a signal from Arduino if needed, or a fixed delay
    sleep(3) # Give Arduino some time to initialize

    # --- Image Processing and Sending ---
    processed_frames = []

    print("Processing images...")
    if "." not in folder:
        # Process frames from a folder
        for i in range(start, end):
            try:
                img = Image.open(f"{folder}/{dirF[i]}")
                # Get byte data using the updated convert function
                byte_data = convert(img, printout, BLACK, WHITE, COLOR_CHECK)
                if byte_data and len(byte_data) == 64: # Ensure we got 64 bytes
                    processed_frames.append(bytes(byte_data)) # Append as bytes
                else:
                    print(f"Warning: Could not process frame {i} or received incorrect data length.")
            except FileNotFoundError:
                print(f"Error: Frame file not found: {folder}/{dirF[i]}")
                break # Stop processing if a file is missing
            except Exception as e:
                print(f"Error processing frame {i}: {e}")
                break # Stop processing on other errors

    else:
        # Process a single image or GIF
        try:
            im = Image.open(folder)
            if '.gif' in folder.lower():
                # Process GIF frames
                for frame in ImageSequence.Iterator(im):
                    byte_data = convert(frame, printout, BLACK, WHITE, COLOR_CHECK)
                    if byte_data and len(byte_data) == 64:
                         processed_frames.append(bytes(byte_data))
                    else:
                         print(f"Warning: Could not process a GIF frame or received incorrect data length.")
            else:
                # Process a single image
                byte_data = convert(im, printout, BLACK, WHITE, COLOR_CHECK)
                if byte_data and len(byte_data) == 64:
                    processed_frames.append(bytes(byte_data))
                else:
                    print(f"Warning: Could not process the image or received incorrect data length.")
        except FileNotFoundError:
             print(f"Error: Image file not found: {folder}")
        except Exception as e:
            print(f"Error processing image: {e}")


    if not processed_frames:
        print("No frames were successfully processed. Exiting.")
        ser.close()
        sys.stdout.write("\033[?25h") # Show cursor before exiting
        exit()

    print(f"Finished processing {len(processed_frames)} frames.")

    # --- Sending Data to Arduino ---
    while ser.is_open:
        print("\nStart sending frames...")
        begin = time()
        frame_count = 0

        for frame_bytes in processed_frames:
            try:
                # Send the 64 bytes of data
                ser.write(frame_bytes)
                # Wait for a confirmation from the Arduino ("OK\r\n")
                # This synchronizes sending with Arduino's processing speed
                response = ser.readline().decode('utf-8').strip()
                if response == "OK":
                    # Arduino processed the frame, proceed to the next
                    print(f"Sent frame: {frame_count}")
                    frame_count += 1
                else:
                    # Received unexpected response or timeout
                    print(f"Warning: Received unexpected response from Arduino: '{response}'")
                    # Depending on the issue, you might want to retry or skip the frame
                    # For now, we'll just print a warning and continue
                    frame_count += 1 # Still count the frame as attempted

            except serial.SerialTimeoutException:
                print(f"Error: Serial read timeout while waiting for Arduino confirmation for frame {frame_count}.")
                # This indicates the Arduino might not be responding
                break # Exit the sending loop
            except serial.SerialException as e:
                print(f"Serial error during sending frame {frame_count}: {e}")
                break # Exit the sending loop on serial error
            except Exception as e:
                print(f"An unexpected error occurred while sending frame {frame_count}: {e}")
                break # Exit on other errors


        length = time() - begin
        print("\nSending finished.")
        print(*["-" for _ in range(20)])
        print(f"Total frames sent: {frame_count}")
        print(f"Time elapsed: {length:.2f} seconds")
        if length > 0:
             print(f"Approximate FPS: {round(frame_count / length, 2)}")
        print(*["-" for _ in range(20)])

        # If LOOP is False, break the sending loop
        if not LOOP:
            break

    # --- Cleanup ---
    ser.close()
    print("Serial port closed.")
    # Show the cursor again in the terminal
    sys.stdout.write("\033[0m\033[?25h")
    exit()
