import os
import sys
from time import sleep
# No longer need Iterable import with the new mean calculation
# from collections.abc import Iterable

from PIL import Image

# No longer need ImageStat for this approach
# from PIL import ImageStat

# --- Constants ---
# Pixel values for black and white in the output byte data
BLACK = 0
WHITE = 1

# Default threshold for binarization. Use -1 for automatic calculation.
DEFAULT_COLOR_CHECK = -1

# Dimensions of the target LCD area in pixels
LCD_WIDTH_PX = 20
LCD_HEIGHT_PX = 16

# Dimensions of a single custom character in pixels
CHAR_WIDTH_PX = 5
CHAR_HEIGHT_PX = 8

# Number of custom characters needed horizontally and vertically
CHARS_HORIZONTAL = LCD_WIDTH_PX // CHAR_WIDTH_PX  # Should be 4
CHARS_VERTICAL = LCD_HEIGHT_PX // CHAR_HEIGHT_PX  # Should be 2

# Total number of custom characters
TOTAL_CHARS = CHARS_HORIZONTAL * CHARS_VERTICAL  # Should be 8

# Total number of bytes required for all custom characters (8 bytes per character)
TOTAL_BYTES_PER_FRAME = TOTAL_CHARS * CHAR_HEIGHT_PX  # Should be 64


# --- Helper Function ---
def calculate_mean_grayscale(pixels):
    """
    Calculates the mean intensity of a list of grayscale pixel values.

    Args:
        pixels (list): A list of integer grayscale pixel values (0-255).

    Returns:
        int: The calculated mean intensity, or 128 if the list is empty.
    """
    if not pixels:
        return 128  # Default to a mid-range threshold if no pixels
    return int(sum(pixels) / len(pixels))


# --- Main Conversion Function ---
def image_to_lcd_bytes(img, printout=False, black=BLACK, white=WHITE, color_check=DEFAULT_COLOR_CHECK):
    """
    Resizes an image to the target LCD dimensions (20x16), converts it to
    black and white using a threshold, and generates a list of 64 bytes
    for 8 LCD custom characters (5x8 pixels each).

    Args:
        img (PIL.Image.Image): The input image object.
        printout (bool): Whether to print a text representation of the image
                         to the console.
        black (int): Value for black pixels in the output byte data (0 or 1).
        white (int): Value for white pixels in the output byte data (0 or 1).
        color_check (int): Threshold for determining black/white pixels (0-255).
                           Use -1 for automatic threshold calculation based on
                           the mean intensity of the resized grayscale image.

    Returns:
        list: A list of 64 integers (bytes) representing the custom character data,
              or None if an error occurs during processing.
    """
    try:
        # Resize the image to the target LCD dimensions
        img_resized = img.resize((LCD_WIDTH_PX, LCD_HEIGHT_PX))

        # Convert image to grayscale for consistent thresholding
        img_gray = img_resized.convert('L')

        # Get pixel data from the grayscale image
        pixels_gray = list(img_gray.getdata())

        # Determine the threshold for binarization
        threshold = color_check
        if threshold == -1:
            # Calculate the mean pixel intensity manually for auto mode
            threshold = calculate_mean_grayscale(pixels_gray)
            # print(f"Auto-calculated threshold: {threshold}") # Optional: print calculated threshold

        # Convert grayscale pixels to black or white based on the threshold
        # Pixels >= threshold become white, pixels < threshold become black
        pixels_binary = [white if p >= threshold else black for p in pixels_gray]

        # --- Console Printout (Optional) ---
        if printout:
            # Use ANSI escape codes for clearing and positioning cursor
            sys.stdout.write("\033[0J\033[H")  # Clear screen and move cursor to home
            for y in range(LCD_HEIGHT_PX):
                sys.stdout.write("\033[0K")  # Clear line from cursor to end
                for x in range(LCD_WIDTH_PX):
                    # Use ANSI escape codes for colored output
                    pixel_index = y * LCD_WIDTH_PX + x
                    color_code = f'\033[37;47m ' if pixels_binary[pixel_index] == white else f'\033[30;40m '
                    sys.stdout.write(color_code)
                    sys.stdout.write(f'\033[m')  # Reset colors
                sys.stdout.write('\n')  # Move to the next line
                if y == LCD_HEIGHT_PX - 1:
                    sleep(1 / 144)  # Small delay for visualization (adjust if needed)
            sys.stdout.flush()  # Ensure output is displayed

        # --- Generate LCD Custom Character Bytes ---
        # List to hold all 64 bytes for the 8 custom characters
        all_char_bytes = []

        # Iterate through the 8 custom characters
        for char_index in range(TOTAL_CHARS):
            # Determine the starting pixel coordinates for this character block
            char_col = char_index % CHARS_HORIZONTAL
            char_row = char_index // CHARS_HORIZONTAL

            start_x = char_col * CHAR_WIDTH_PX
            start_y = char_row * CHAR_HEIGHT_PX

            # Extract data for each of the 8 rows in the current character
            for row_in_char in range(CHAR_HEIGHT_PX):
                byte_value = 0
                # Iterate through the 5 pixels in the current row of the character
                for col_in_char in range(CHAR_WIDTH_PX):
                    # Calculate the global pixel coordinates
                    global_x = start_x + col_in_char
                    global_y = start_y + row_in_char

                    # Get the pixel value (0 or 1) from the binary pixel list
                    pixel_index = global_y * LCD_WIDTH_PX + global_x
                    bit = pixels_binary[pixel_index]  # The pixel value (0 or 1) is directly the bit value

                    # The 5 pixels occupy the lower 5 bits of the byte (bits 0-4)
                    # Bit 4 is the leftmost pixel, Bit 0 is the rightmost
                    # So, pixel at col_in_char 0 goes to bit 4, col_in_char 1 to bit 3, etc.
                    byte_value |= (bit << (CHAR_WIDTH_PX - 1 - col_in_char))

                # Append the calculated byte value for the current row
                all_char_bytes.append(byte_value)

        # Ensure we generated the correct number of bytes
        if len(all_char_bytes) != TOTAL_BYTES_PER_FRAME:
            print(
                f"Warning: Generated incorrect number of bytes: {len(all_char_bytes)}. Expected {TOTAL_BYTES_PER_FRAME}.")
            return None

        # Return the list of 64 bytes
        return all_char_bytes

    except Exception as e:
        print(f"An error occurred during image processing: {e}")
        return None


# --- Wrapper Function ---
def convert(image_file, printout=False, black=BLACK, white=WHITE, color_check=DEFAULT_COLOR_CHECK):
    """
    Wrapper function to convert an image to LCD character bytes.
    Handles potential errors during the conversion process.
    """
    return image_to_lcd_bytes(image_file, printout, black, white, color_check)
