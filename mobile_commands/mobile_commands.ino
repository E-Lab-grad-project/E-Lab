#include <ESP32Servo.h> 

// ===============================
// Declare 6 servo objects
// ===============================
Servo servoBase;
Servo servoShoulder;
Servo servoElbow;
Servo servoWrist;
Servo servoWristRot;
Servo servoGrip;

// ================= PINS =================
const int srv1 = 25;
const int srv2 = 26;
const int srv3 = 27;
const int srv4 = 14;
const int srv5 = 12;
const int srv6 = 13;

// ================= START POSITIONS =================
int srv1Angle = 90;   // Base
int srv2Angle = 140;  // Shoulder
int srv3Angle = 180;  // Elbow
int srv4Angle = 0;    // Wrist
int srv5Angle = 90;   // Wrist rotation
int srv6Angle = 10;   // Gripper

void setup() {
  Serial.begin(115200);

  // Attach servos
  servoBase.attach(srv1);
  servoShoulder.attach(srv2);
  servoElbow.attach(srv3);
  servoWrist.attach(srv4);
  servoWristRot.attach(srv5);
  servoGrip.attach(srv6);

  // Move to start position
  servoBase.write(srv1Angle);
  servoShoulder.write(srv2Angle);
  servoElbow.write(srv3Angle);
  servoWrist.write(srv4Angle);
  servoWristRot.write(srv5Angle);
  servoGrip.write(srv6Angle);

  Serial.println("🟢 6DOF Arm Ready");
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "MOVE_UP") {
      srv2Angle = constrain(srv2Angle - 30, 0, 180);
      servoShoulder.write(srv2Angle);
    }
    else if (command == "MOVE_DOWN") {
      srv2Angle = constrain(srv2Angle + 30, 0, 180);
      servoShoulder.write(srv2Angle);
    }
    else if (command == "MOVE_LEFT") {
      srv1Angle = constrain(srv1Angle - 30, 0, 180);
      servoBase.write(srv1Angle);
    }
    else if (command == "MOVE_RIGHT") {
      srv1Angle = constrain(srv1Angle + 30, 0, 180);
      servoBase.write(srv1Angle);
    }
    else if (command == "GRIP") {
      srv6Angle = 0;   // close
      servoGrip.write(srv6Angle);
    }
    else if (command == "RELEASE") {
      srv6Angle = 90;  // open
      servoGrip.write(srv6Angle);
    }
    else {
      Serial.print("⚠️ Unknown command: ");
      Serial.println(command);
    }

    delay(500); // allow servo movement
  }
}
