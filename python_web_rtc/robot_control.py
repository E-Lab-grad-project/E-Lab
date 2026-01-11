import cv2
import numpy as np
from threading import Thread
from queue import Queue, Empty
from core.interface import frameProcessor
from media.yolo.tracking import norm_to_angle, estimate_distance

# ------------------------- ROBOT CONTROLLER -------------------------
class RobotController:
    """Handles sending servo commands to Arduino/ESP32."""
    
    def __init__(self, serial_port="COM8", baudrate=115200):
        self.ser = None
        try:
            import serial
            self.ser = serial.Serial(serial_port, baudrate, timeout=1)
            import time
            time.sleep(2)
            print("🟢 Serial connected to Arduino/ESP32")
        except Exception:
            print("⚠ WARNING: Could not open serial port")
            self.ser = None

    def send_state(self, x: int, y: int, z: float):
        grip_state = "CLOSE" if z < 0.10 else "OPEN"
        msg = f"X:{x},Y:{y},Z:{z:.2f}\n"

        print("\n" + "="*60)
        print("🤖 ROBOT COMMAND")
        print(f"Base (X)        : {x}")
        print(f"Shoulder (Y)    : {y}")
        print(f"Distance (Z)    : {z:.2f}")
        print(f"Gripper         : {grip_state}")
        print(f"Serial Message  : {msg.strip()}")
        print("="*60)

        if self.ser is None:
            print("[NO SERIAL] Skipping send")
            return

        try:
            self.ser.write(msg.encode())
        except Exception as e:
            print("❌ Serial error:", e)

    def close(self):
        if self.ser:
            self.ser.close()
            print("🔴 Serial connection closed")