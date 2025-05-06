import math
import sys

import serial.tools.list_ports
import serial
from PIL import Image, ImageSequence
from ImageToDigit import convert
from time import sleep, time
import os

folder = "Bad Apple"    # Folder or file

COM = ""
BAUDRATE = 500000  # The higher, the faster. I've tested on UNO R3 the highest was 500000, unstable
install = False
model = "arduino:avr:uno"

FPS = 1  # Base speed is 7.5 FPS, set 1 to keep base speed
FPP = math.floor(FPS/((BAUDRATE*7.5)/500000))   # Frame advance per print, visual only speed hack
FPP = 1 if FPP < 1 else FPP
BLACK = 0
WHITE = 1
COLOR_CHECK = 240   # The higher, the less White you will see, -1 for auto
LOOP = True
printout = False

auto_load = False   # Load from pre-built Script

# File params
start = 0   # Does nothing, implant later
end = 100   # Does nothing, implant later

if os.path.isdir(folder) or os.path.isfile(folder):
    pass
else:
    print("Folder doesn't exist")
    exit()

# Folder params
if "." not in folder:
    start = 0   # This works but no error handlers
    dirF = os.listdir(f"./{folder}/")
    dirF = list(map(lambda x: str(x)+".png", sorted(map(lambda x: int(x.split(".png")[0]), dirF))))
    end = len(dirF)     # This works, just specific a number or modify from len
else:
    if not any(ext in folder for ext in ['gif', 'png', 'jpg', 'jpeg', 'bmp', 'webp']):
        exit()

if __name__ == '__main__':
    print("\033[?25l", end="")
    if COM == "":
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if "CH340" in p[1]:
                COM = p[0]

    if install:
        print("Installing Arduino...")
        os.system(f"arduino-cli compile --upload --port {COM} --fqbn {model} ino")

    ser = serial.Serial(COM, BAUDRATE)
    if not ser:
        print("Failed to connect to Arduino.")

    print("Please wait...")
    for i in range(3):
        print(3 - i)
        sleep(1)
    print("Serial port opened")

    if ser.is_open:
        if not auto_load:
            if "." not in folder:
                with open(f"Scripts/{folder}.txt", "w") as f:
                    for i in range(start, end):
                        img = Image.open(f"{folder}/{dirF[i]}")
                        a = convert(img, printout, BLACK, WHITE, COLOR_CHECK)
                        if a:
                            f.write(a)
                            f.write("\n")
                    f.close()
            else:
                im = Image.open(folder)
                with open(f"Scripts/{folder}.txt", "w") as f:
                    if '.gif' in folder:
                        for frame in ImageSequence.Iterator(im):
                            a = convert(frame, printout, BLACK, WHITE, COLOR_CHECK)
                            if a:
                                f.write(a)
                                f.write("\n")
                        f.close()
                    else:
                        a = convert(im, printout, BLACK, WHITE, COLOR_CHECK)
                        if a:
                            f.write(a)
                            f.write("\n")
                        f.close()

        while ser.is_open:
            i = 0
            print("\nStart sending...")
            with open(f"Scripts/{folder}.txt", "r") as f:
                script = f.readlines()

            if not script:
                exit()

            begin = time()

            last_point = len(script) - 1
            for line in script:
                if i % FPP == 0 or i == last_point:
                    print("Frame: ", i)
                    ser.write(bytes(line, encoding='utf-8'))
                    # sleep(1/FPS - 0.1)
                    ser.readline()
                i += 1
            length = time() - begin
            print("Frame: ", i)
            print("Frame: The End")
            print(*["-" for _ in range(12)])
            print(f"Total frames: {i + 1 - start} frames")
            print(f"Time: {length}")
            print(f"Approximate FPS: {round(i / length)}")
            if not LOOP:
                break

    ser.close()
    sys.stdout.write("\033[0m\033[?25h")
    exit()
