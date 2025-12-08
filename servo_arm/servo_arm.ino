#include <ESP32Servo.h>  // مكتبة متوافقة مع ESP32

Servo myServo;

String incoming = "";
int angle = 90;  // مركز السيرفو

void setup() {
  Serial.begin(9600);
  myServo.attach(5);   // دبوس الإشارة على ESP32 (GPIO 5 مثال)
  myServo.write(angle);
  delay(500);
}

void loop() {
  // قراءة أي بيانات واردة من Python
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      int receivedAngle = incoming.toInt();
      receivedAngle = constrain(receivedAngle, 0, 180);
      angle = receivedAngle;
      myServo.write(angle);

      // Debug
      Serial.print("Servo moved to: ");
      Serial.println(angle);

      incoming = "";
    }
    else {
      incoming += c;
    }
  }
}
