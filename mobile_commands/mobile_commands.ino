#include <Servo.h>

// ===============================
// Declare 6 servo objects
// ===============================
Servo servoBase;      // محور 1
Servo servoShoulder;  // محور 2
Servo servoElbow;     // محور 3
Servo servoWrist;     // محور 4
Servo servoGrip;      // محور 5 (gripper open/close)
Servo servoWristRot;  // محور 6 (rotation)

const int pinBase = 25;
const int pinShoulder = 26;
const int pinElbow = 27;
const int pinWrist = 12;
const int pinGrip = 13;
const int pinWristRot = 14;

// ===============================
// Servo positions (adjust as needed)
// ===============================
int basePos = 90;
int shoulderPos = 90;
int elbowPos = 90;
int wristPos = 90;
int gripPos = 90;
int wristRotPos = 90;

void setup() {
  Serial.begin(115200);

  // Attach servos
  servoBase.attach(pinBase);
  servoShoulder.attach(pinShoulder);
  servoElbow.attach(pinElbow);
  servoWrist.attach(pinWrist);
  servoGrip.attach(pinGrip);
  servoWristRot.attach(pinWristRot);

  // Initialize positions
  servoBase.write(basePos);
  servoShoulder.write(shoulderPos);
  servoElbow.write(elbowPos);
  servoWrist.write(wristPos);
  servoGrip.write(gripPos);
  servoWristRot.write(wristRotPos);

  Serial.println("🟢 6DOF Arm Ready");
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "MOVE_UP") {
      shoulderPos = constrain(shoulderPos - 10, 0, 180);
      servoShoulder.write(shoulderPos);
    } 
    else if (command == "MOVE_DOWN") {
      shoulderPos = constrain(shoulderPos + 10, 0, 180);
      servoShoulder.write(shoulderPos);
    } 
    else if (command == "MOVE_LEFT") {
      basePos = constrain(basePos - 10, 0, 180);
      servoBase.write(basePos);
    } 
    else if (command == "MOVE_RIGHT") {
      basePos = constrain(basePos + 10, 0, 180);
      servoBase.write(basePos);
    } 
    else if (command == "GRIP") {
      gripPos = 0;  // close
      servoGrip.write(gripPos);
    } 
    else if (command == "RELEASE") {
      gripPos = 90; // open
      servoGrip.write(gripPos);
    } 
    else {
      Serial.print("⚠️ Unknown command: ");
      Serial.println(command);
    }

    delay(500); // delay for servo movement
  }
}
