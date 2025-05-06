import os
import sys
from time import sleep
from collections.abc import Iterable


from PIL import Image
from numpy.ma.extras import average

# 1 will make square lighten
BLACK = 0
WHITE = 1
COLOR_CHECK = 150


def image_to_lcd_bytes(img, printout=False, black=BLACK, white=WHITE, color_check=COLOR_CHECK):
    """
    Resizes an image to 20x16, converts it to black and white, and generates
    a list of 64 bytes for 8 LCD custom characters (5x8 pixels each).

    Args:
        img (PIL.Image.Image): The input image object.
        printout (bool): Whether to print a text representation of the image.
        black (int): Value for black pixels.
        white (int): Value for white pixels.
        color_check (int): Threshold for determining black/white pixels.

    Returns:
        list: A list of 64 integers (bytes) representing the custom character data,
              or None if an error occurs.
    """
    try:

        # Resize the image to 20x16 pixels
        img_resized = img.resize((20, 16))

        # Get pixel data
        def check(color, lim=100):
            if lim == -1:
                if isinstance(color, Iterable):
                    lim = average(color)
                    if lim < 1:
                        lim = 1
                    lim = 240/lim
                else:
                    lim = 100
            b = False
            if type(color) is int:
                return color > lim
            cl = list(map(lambda x: x if x > lim else 0, color))
            if cl.count(0) < 2:
                b = True
            if len(color) > 3 and color[3] < 10:
                b = False
            return b

        # Convert pixels to black or white based on the color_check threshold
        pixels = list(map(lambda x: white if check(x, color_check) else black, list(img_resized.getdata())))

        # The 20x16 image will be divided into 8 custom characters (5x8 each)
        # These characters are arranged in a 4x2 grid on the 20x16 image:
        # Char 0 | Char 1 | Char 2 | Char 3
        # -------|--------|--------|-------
        # Char 4 | Char 5 | Char 6 | Char 7

        if printout:
            print("\033[0J\033[H", end="")
            for i in range(16):
                for j in range(20):
                    print("\033[0K", end="", sep="")
                    print(f'\033[37;47m ' if pixels[i * 20 + j] == white else f'\033[30;40m ', end="")
                    print(f'\033[m', end='')
                print()
                if i == 15:
                    sleep(1/144)
        else:
            # Use ANSI escape codes to indicate processing without clearing the screen
            sys.stdout.write("\033[sProcessing image...\033[u")
            sys.stdout.flush() # Ensure the output is displayed immediately


        # List to hold all 64 bytes for the 8 custom characters
        all_char_bytes = []

        # Iterate through the 8 custom characters
        for char_index in range(8):
            # Determine the starting pixel coordinates for this character block
            # Each character is 5 pixels wide and 8 pixels tall
            # There are 4 characters horizontally and 2 vertically
            char_col = char_index % 4
            char_row = char_index // 4

            start_x = char_col * 5
            start_y = char_row * 8

            # Extract data for each of the 8 rows in the current character
            for row_in_char in range(8):
                byte_value = 0
                # Iterate through the 5 pixels in the current row of the character
                for col_in_char in range(5):
                    # Calculate the global pixel coordinates
                    global_x = start_x + col_in_char
                    global_y = start_y + row_in_char

                    # Get the pixel value (0 or 1)
                    pixel_value = pixels[global_y * 20 + global_x]
                    bit = pixel_value

                    # The 5 pixels occupy the lower 5 bits of the byte (bits 0-4)
                    # Bit 4 is the leftmost pixel, Bit 0 is the rightmost
                    # So, pixel at col_in_char 0 goes to bit 4, col_in_char 1 to bit 3, etc.
                    byte_value |= (bit << (4 - col_in_char))

                # Append the calculated byte value for the current row
                all_char_bytes.append(byte_value)

        # Return the list of 64 bytes
        return all_char_bytes

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def convert(image_file, printout=False, black=BLACK, white=WHITE, color_check=COLOR_CHECK):
    """
    Wrapper function to convert an image to LCD character bytes.
    """
    try:
        return image_to_lcd_bytes(image_file, printout, black, white, color_check)
    except Exception as e:
        print(f"Conversion error: {e}")
        return None

