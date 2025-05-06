#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Initialize the LCD object with the I2C address (0x27), 16 columns, and 2 rows
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Buffer to hold incoming custom character data (8 chars * 8 bytes/char = 64 bytes)
uint8_t customCharDataBuffer[64];
int bufferIndex = 0; // Index to track the current position in the buffer
bool dataReady = false; // Flag to indicate when a full frame of data is received
bool firstFrameReceived = false; // Flag to track if the first frame has been received

void setup() {
  // Start serial communication at a high baud rate.
  // Ensure this baud rate is supported and stable for your specific Arduino board.
  Serial.begin(500000);

  // Initialize the LCD
  lcd.init();
  // Turn on the backlight
  lcd.backlight();
  // Move cursor to the home position (0,0)
  lcd.home();
  // Clear the display
  lcd.clear();

  // Display initial status messages while waiting for data
  lcd.setCursor(0, 0);
  lcd.print("System Ready");
  lcd.setCursor(0, 1);
  lcd.print("Waiting for data...");
}

void loop() {
  // Read incoming bytes from the serial buffer
  // This loop reads all currently available bytes from the serial port
  while (Serial.available() > 0) {
    // Check if the buffer has space to prevent overflow (buffer size is 64 bytes)
    if (bufferIndex < 64) {
      // Read a single byte from the serial buffer and store it
      customCharDataBuffer[bufferIndex] = Serial.read();
      bufferIndex++; // Move to the next position in the buffer
    }

    // If the buffer is full (meaning a complete frame of 64 bytes is received)
    if (bufferIndex == 64) {
      // Set the dataReady flag to true to signal that a frame is ready for processing
      dataReady = true;
      // Reset the buffer index to 0 for the next incoming frame
      bufferIndex = 0;
      // Exit the while loop as a full frame is received and ready
      break;
    }
  }

  // If a full frame of data is received and the dataReady flag is true
  if (dataReady) {
    // Reset the dataReady flag immediately as we are about to process the frame
    dataReady = false;

    // If this is the first frame being received, clear the initial messages
    if (!firstFrameReceived) {
      lcd.clear(); // Clearing the LCD takes some time via I2C
      firstFrameReceived = true; // Set the flag so this only happens once
    }

    // Update custom characters using the data from the buffer
    // There are 8 custom characters (index 0 to 7)
    for (int charIndex = 0; charIndex < 8; charIndex++) {
      // Create a temporary array to hold the 8 bytes for the current character
      uint8_t currentCharData[8];
      // Copy 8 bytes from the main buffer for the current character's definition
      // The data for charIndex starts at customCharDataBuffer[charIndex * 8]
      for (int i = 0; i < 8; i++) {
        currentCharData[i] = customCharDataBuffer[charIndex * 8 + i];
      }
      // Create or update the custom character in the LCD's CGRAM
      // This is a key part that involves I2C communication and takes time.
      lcd.createChar(charIndex, currentCharData);
    }

    // Display the custom characters on the LCD
    // Set cursor to the starting position for the display area (column 6, row 0)
    lcd.setCursor(6, 0);
    // Write the first 4 custom characters (index 0, 1, 2, 3) on the first row
    for (int i = 0; i < 4; i++) {
      lcd.write(i); // Writing a custom character by its index (0-7)
    }
    // Set cursor to the starting position for the second row (column 6, row 1)
    lcd.setCursor(6, 1);
    // Write the next 4 custom characters (index 4, 5, 6, 7) on the second row
    for (int i = 4; i < 8; i++) {
      lcd.write(i); // Writing a custom character by its index (0-7)
    }

    // Send a confirmation back to the Python script.
    // This signal tells the Python script that the Arduino has finished processing
    // and displaying the current frame and is ready for the next one.
    // This is important for synchronization. Removing this would likely cause issues.
    Serial.println("OK");
  }

  // If dataReady is false and no new data arrived in this loop iteration,
  // the loop finishes quickly and the Arduino waits for the next serial data.
  // No explicit delay is added here to keep the loop responsive to incoming serial data.
}
