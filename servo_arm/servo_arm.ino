#include <ESP32Servo.h>

// ================= SERVO OBJECTS =================
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
int srv1Angle = 90;
int srv2Angle = 140;
int srv3Angle = 180;
int srv4Angle = 0;
int srv5Angle = 90;
int srv6Angle = 10;

String incoming = "";

// ================= SPEED CONTROL =================
const int STEP_DELAY = 12;
const int STEP_SIZE = 1;

void smoothMove(Servo &srv, int &currentAngle, int targetAngle) {
  targetAngle = constrain(targetAngle, 0, 180);
  if (currentAngle == targetAngle) return;

  int step = (targetAngle > currentAngle) ? STEP_SIZE : -STEP_SIZE;
  while (currentAngle != targetAngle) {
    currentAngle += step;
    if ((step > 0 && currentAngle > targetAngle) || (step < 0 && currentAngle < targetAngle)) {
      currentAngle = targetAngle;
    }
    srv.write(currentAngle);
    delay(STEP_DELAY);
  }
}

void moveToHome() {
  smoothMove(servoBase, srv1Angle, 90);
  smoothMove(servoShoulder, srv2Angle, 140);
  smoothMove(servoElbow, srv3Angle, 180);
  smoothMove(servoWrist, srv4Angle, 0);
  smoothMove(servoWristRot, srv5Angle, 90);
  smoothMove(servoGrip, srv6Angle, 10);
}

void setAllAngles(int base, int shoulder, int elbow, int wrist, int wristRot, int grip) {
  smoothMove(servoBase, srv1Angle, base);
  smoothMove(servoShoulder, srv2Angle, shoulder);
  smoothMove(servoElbow, srv3Angle, elbow);
  smoothMove(servoWrist, srv4Angle, wrist);
  smoothMove(servoWristRot, srv5Angle, wristRot);
  smoothMove(servoGrip, srv6Angle, grip);
}

void handleVisionStyleCommand(String cmd) {
  int xIndex = cmd.indexOf("X:");
  int yIndex = cmd.indexOf(",Y:");
  int zIndex = cmd.indexOf(",Z:");

  if (xIndex >= 0 && yIndex >= 0 && zIndex >= 0) {
    int xVal = cmd.substring(xIndex + 2, yIndex).toInt();
    int yVal = cmd.substring(yIndex + 3, zIndex).toInt();
    float zVal = cmd.substring(zIndex + 3).toFloat();

    int targetShoulder, targetElbow;
    if (yVal <= 140) {
      targetShoulder = yVal;
      targetElbow = map(yVal, 0, 180, 180, 90);
    } else {
      targetShoulder = 140;
      targetElbow = srv3Angle + (yVal - 140);
      targetElbow = constrain(targetElbow, 90, 180);
    }

    smoothMove(servoBase, srv1Angle, constrain(xVal, 0, 180));
    smoothMove(servoShoulder, srv2Angle, targetShoulder);
    smoothMove(servoElbow, srv3Angle, targetElbow);

    if (zVal < 0.10) {
      smoothMove(servoGrip, srv6Angle, 90);
      Serial.println("GRIP: CLOSED");
    } else {
      smoothMove(servoGrip, srv6Angle, 10);
      Serial.println("GRIP: OPEN");
    }

    Serial.print("Base:"); Serial.print(srv1Angle);
    Serial.print(" Shoulder:"); Serial.print(srv2Angle);
    Serial.print(" Elbow:"); Serial.print(srv3Angle);
    Serial.print(" Z:"); Serial.println(zVal, 3);
    return;
  }

  if (cmd.equalsIgnoreCase("HOME")) {
    moveToHome();
    Serial.println("ARM: HOME");
    return;
  }

  if (cmd.equalsIgnoreCase("OPEN")) {
    smoothMove(servoGrip, srv6Angle, 10);
    Serial.println("GRIP: OPEN");
    return;
  }

  if (cmd.equalsIgnoreCase("CLOSE")) {
    smoothMove(servoGrip, srv6Angle, 90);
    Serial.println("GRIP: CLOSED");
    return;
  }

  if (cmd.startsWith("MOVE ")) {
    int a[6];
    int index = 0;
    String temp = cmd.substring(5);
    while (temp.length() > 0 && index < 6) {
      int space = temp.indexOf(' ');
      String value = (space >= 0) ? temp.substring(0, space) : temp;
      a[index++] = value.toInt();
      if (space < 0) break;
      temp = temp.substring(space + 1);
    }
    if (index == 6) {
      setAllAngles(a[0], a[1], a[2], a[3], a[4], a[5]);
      Serial.println("ARM: MOVE OK");
    } else {
      Serial.println("ARM: INVALID MOVE COMMAND");
    }
    return;
  }

  Serial.println("ARM: UNKNOWN COMMAND");
}

void setup() {
  Serial.begin(115200);
  servoBase.attach(srv1);
  servoShoulder.attach(srv2);
  servoElbow.attach(srv3);
  servoWrist.attach(srv4);
  servoWristRot.attach(srv5);
  servoGrip.attach(srv6);

  moveToHome();
  delay(500);
  Serial.println("ARM READY");
  Serial.println("Commands: HOME, OPEN, CLOSE, MOVE <6 angles>, or X:..,Y:..,Z:..");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      incoming.trim();
      if (incoming.length() > 0) {
        handleVisionStyleCommand(incoming);
      }
      incoming = "";
    } else {
      incoming += c;
    }
  }
}
