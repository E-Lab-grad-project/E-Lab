#include <ESP32Servo.h>

// ===============================
// Servo objects
// ===============================
Servo servoBase;      // محور 1
Servo servoShoulder;  // محور 2
Servo servoElbow;     // محور 3
Servo servoWrist;     // محور 4
Servo servoGrip;      // محور 5 (gripper)
Servo servoWristRot;  // محور 6 (rotation)

// ===============================
// Servo pins
// ===============================
const int srv1 = 25;
const int srv2 = 26;
const int srv3 = 27;
const int srv4 = 12;
const int srv5 = 13;
const int srv6 = 14;

// ===============================
// Startup positions
// ===============================
int srv1Angle = 90;    // Base
int srv2Angle = 140;   // Shoulder
int srv3Angle = 180;   // Elbow
int srv4Angle = 0;     // Wrist
int srv5Angle = 90;    // Grip (open)
int srv6Angle = 10;    // Wrist rotation

// ===============================
// Serial buffer
// ===============================
String incoming = "";

// ===============================
void setup() {
  Serial.begin(115200);

  // Attach servos
  servoBase.attach(srv1);
  servoShoulder.attach(srv2);
  servoElbow.attach(srv3);
  servoWrist.attach(srv4);
  servoGrip.attach(srv5);
  servoWristRot.attach(srv6);

  // Initialize positions
  servoBase.write(srv1Angle);
  servoShoulder.write(srv2Angle);
  servoElbow.write(srv3Angle);
  servoWrist.write(srv4Angle);
  servoGrip.write(srv5Angle);
  servoWristRot.write(srv6Angle);

  delay(500);

  Serial.println("🟢 6DOF Arm Ready");
  Serial.println("Commands:");
  Serial.println(" - Number (0–180) → Base servo");
  Serial.println(" - GRIP → Close gripper");
  Serial.println(" - OPEN → Open gripper");
}

// ===============================
void loop() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      incoming.trim();

      // -------- GRIP CLOSE --------
      if (incoming == "GRIP") {
        servoGrip.write(0);   // Close (adjust if needed)
        Serial.println("✊ GRIP closed");
      }

      // -------- GRIP OPEN --------
      else if (incoming == "OPEN") {
        servoGrip.write(srv5Angle); // Open position
        Serial.println("🖐 GRIP opened");
      }

      // -------- BASE SERVO --------
      else {
        int angle = incoming.toInt();
        angle = constrain(angle, 0, 180);
        srv1Angle = angle;
        servoBase.write(srv1Angle);
        Serial.print("🔄 Base moved to: ");
        Serial.println(srv1Angle);
      }

      incoming = "";
    }
    else {
      incoming += c;
    }
  }
}
