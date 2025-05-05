import os
import sys
from time import sleep

from PIL import Image

# 1 will make square lighten
BLACK = 0
WHITE = 1
COLOR_CHECK = 150


def image_to_lcd_decimal_string(img, printout=False, black=BLACK, white=WHITE, color_check=COLOR_CHECK):
    """
    Resizes an image to 20x16, converts it to black and white, and generates
    a single string of concatenated decimal values for 8 LCD custom characters
    (5x8 pixels each).

    Args:
        image_path (str): The path to the input image file.

    Returns:
        str: A string containing the concatenated decimal values of the 64 bytes,
             or None if an error occurs.
    """
    try:

        # Resize the image to 20x16 pixels
        img_resized = img.resize((20, 16))

        # Get pixel data
        def check(color, lim=100):
            b = False
            if type(color) is int:
                return color > lim
            cl = list(map(lambda x: x if x > lim else 0, color))
            if cl.count(0) < 2:
                b = True
            if len(color) > 3 and color[3] < 10:
                b = False
            return b

        # print(list(img_resized.getdata()))
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
            print("\033[sProcessing image...\033[u", end="")

        decimal_string = ""

        # Iterate through the 8 custom characters
        for char_index in range(8):
            char_data = []  # List to hold 8 bytes for the current character

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

                    # Get the pixel value (0 or 255)
                    # We need to map 0 (black) to 1 and 255 (white) to 0
                    # for the LCD custom character data
                    pixel_value = pixels[global_y * 20 + global_x]
                    bit = pixel_value

                    # The 5 pixels occupy the lower 5 bits of the byte (bits 0-4)
                    # Bit 4 is the leftmost pixel, Bit 0 is the rightmost
                    # So, pixel at col_in_char 0 goes to bit 4, col_in_char 1 to bit 3, etc.
                    byte_value |= (bit << (4 - col_in_char))

                char_data.append(byte_value)

            # Convert the 8 bytes for the character to decimal strings and concatenate
            for byte_value in char_data:
                if byte_value < 10:
                    byte_value = "0" + str(byte_value)
                decimal_string += str(byte_value)  # Convert integer to decimal string and append

        return decimal_string

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def convert(image_file, printout=False, black=BLACK, white=WHITE, color_check=COLOR_CHECK):
    try:
        return image_to_lcd_decimal_string(image_file, printout, black, white, color_check)
    except:
        return
