#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);


void setup() {
  Serial.begin(500000);
  lcd.init();
  lcd.backlight();
  lcd.home();
  lcd.clear();
}

void loop() {
  if (Serial.available() > 0) {
    String inputString = Serial.readStringUntil('\n');
    uint8_t customCharData[8];
    for (int charIndex = 0; charIndex < 8; charIndex++) {
        int startIndex = charIndex * 16;
        for (int i = 0; i < 8; i++) {
          int digit1_char = inputString[startIndex + i * 2];
          int digit2_char = inputString[(startIndex + i* 2) + 1];
          customCharData[i] = (uint8_t)(digit1_char * 10 + digit2_char - 528);
        }
        lcd.createChar(charIndex, customCharData);
      }
      lcd.setCursor(6, 0);
      for (int i = 0; i < 4; i++) {
        lcd.write(i);
      }
      lcd.setCursor(6, 1);
      for (int i = 4; i < 8; i++) {
        lcd.write(i);
      }
      Serial.println("");
    }
}
