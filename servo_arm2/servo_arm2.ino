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

void setup() { 
  Serial.begin(115200); 
  servoBase.attach(srv1); 
  servoShoulder.attach(srv2); 
  servoElbow.attach(srv3); 
  servoWrist.attach(srv4); 
  servoWristRot.attach(srv5); 
  servoGrip.attach(srv6); 

  servoBase.write(srv1Angle); 
  servoShoulder.write(srv2Angle); 
  servoElbow.write(srv3Angle); 
  servoWrist.write(srv4Angle); 
  servoWristRot.write(srv5Angle); 
  servoGrip.write(srv6Angle); 

  delay(500); 
  Serial.println("🟢 6DOF Arm Ready (Direct Move)"); 
} 

void loop() { 
  while (Serial.available()) { 
    char c = Serial.read(); 
    if (c == '\n') { 
      incoming.trim(); 
      int xIndex = incoming.indexOf("X:"); 
      int yIndex = incoming.indexOf(",Y:"); 
      int zIndex = incoming.indexOf(",Z:"); 
      if (xIndex >= 0 && yIndex >= 0 && zIndex >= 0) { 
        int xVal = incoming.substring(xIndex + 2, yIndex).toInt(); 
        int yVal = incoming.substring(yIndex + 3, zIndex).toInt(); 
        float zVal = incoming.substring(zIndex + 3).toFloat(); 
        xVal = constrain(xVal, 0, 180); 

        // ===== SHOULDER + ELBOW CONTROL ===== 
        int targetShoulder, targetElbow; 
        if (yVal <= 140) { 
          targetShoulder = yVal; 
          targetElbow = map(yVal, 0, 180, 180, 90); 
        } else { 
          targetShoulder = 140; 
          targetElbow = srv3Angle + (yVal - 140); 
          targetElbow = constrain(targetElbow, 90, 180); 
        } 

        // ===== BASE ===== 
        servoBase.write(xVal); 
        srv1Angle = xVal; 

        // ===== SHOULDER + ELBOW ===== 
        servoShoulder.write(targetShoulder); 
        srv2Angle = targetShoulder; 
        servoElbow.write(targetElbow); 
        srv3Angle = targetElbow; 

        // ===== GRIPPER ===== 
        if (zVal < 0.10) { 
          servoShoulder.write(80); 
          srv2Angle = 80; 
          servoGrip.write(90); 
          Serial.println("✊ GRIP CLOSED"); 
        } else { 
          servoGrip.write(srv6Angle); 
          Serial.println("🖐 GRIP OPEN"); 
        } 

        // ===== DEBUG ===== 
        Serial.print("Base: "); Serial.print(srv1Angle); 
        Serial.print(" | Shoulder: "); Serial.print(srv2Angle); 
        Serial.print(" | Elbow: "); Serial.print(srv3Angle); 
        Serial.print(" | Z: "); Serial.println(zVal, 3); 
      } 
      incoming = ""; 
    } else { 
      incoming += c; 
    } 
  } 
}
