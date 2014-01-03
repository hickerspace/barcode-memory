#include <Adafruit_NeoPixel.h>

#define PIN 6

Adafruit_NeoPixel strip = Adafruit_NeoPixel(50, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'
  
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    delay(10);
    
    int ledNo = Serial.read();
    int rgb[3];
    rgb[0] = Serial.read();
    rgb[1] = Serial.read();
    rgb[2] = Serial.read();
    
    // light it up
    strip.setPixelColor(ledNo, strip.Color(rgb[0], rgb[2], rgb[1]));
    strip.show();
  }
}
