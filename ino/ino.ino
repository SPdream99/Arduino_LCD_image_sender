#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

// Buffer to hold incoming custom character data (8 chars * 8 bytes/char = 64 bytes)
uint8_t customCharDataBuffer[64];
int bufferIndex = 0;
bool dataReady = false;

void setup() {
  // Start serial communication at a high baud rate (ensure this is stable for your board)
  Serial.begin(500000);
  // Initialize the LCD
  lcd.init();
  // Turn on the backlight
  lcd.backlight();
  // Move cursor to home position
  lcd.home();
  // Clear the display
  lcd.clear();
}

void loop() {
  // Read incoming bytes from the serial buffer
  while (Serial.available() > 0) {
    // Check if the buffer has space
    if (bufferIndex < 64) {
      // Read a byte and store it in the buffer
      customCharDataBuffer[bufferIndex] = Serial.read();
      bufferIndex++;
    }
    // If the buffer is full (received 64 bytes)
    if (bufferIndex == 64) {
      // Set the dataReady flag to true
      dataReady = true;
      // Reset the buffer index for the next frame
      bufferIndex = 0;
      // Exit the while loop as a full frame is received
      break;
    }
  }

  // If a full frame of data is received
  if (dataReady) {
    // Reset the dataReady flag
    dataReady = false;

    // Update custom characters using the data from the buffer
    for (int charIndex = 0; charIndex < 8; charIndex++) {
      // Create a temporary array for the current character's data
      uint8_t currentCharData[8];
      // Copy 8 bytes from the main buffer for the current character
      for (int i = 0; i < 8; i++) {
        currentCharData[i] = customCharDataBuffer[charIndex * 8 + i];
      }
      // Create the custom character on the LCD
      lcd.createChar(charIndex, currentCharData);
    }

    // Display the custom characters on the LCD
    // Set cursor to the first position for the display area
    lcd.setCursor(6, 0);
    // Write the first 4 custom characters (index 0-3)
    for (int i = 0; i < 4; i++) {
      lcd.write(i);
    }
    // Set cursor to the second row for the display area
    lcd.setCursor(6, 1);
    // Write the next 4 custom characters (index 4-7)
    for (int i = 4; i < 8; i++) {
      lcd.write(i);
    }

    // Optionally send a confirmation back to the Python script
    // This helps the Python script know when the Arduino is ready for the next frame
    Serial.println("OK");
  }
}
