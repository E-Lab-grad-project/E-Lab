import os
import time


class HandRobotController:
    """Sends 6 comma-separated servo angles to the hand-mirror Arduino firmware."""

    def __init__(self, serial_port: str | None = None, baudrate: int | None = None):
        self.serial_port = serial_port or os.environ.get("HAND_MIRROR_SERIAL_PORT", "COM4")
        self.baudrate = int(baudrate or os.environ.get("HAND_MIRROR_BAUD", "9600"))
        self.ser = None
        self.connected = False

        try:
            import serial

            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1)
            time.sleep(2)
            self.connected = True
            print(f"Hand mirror serial connected on {self.serial_port} @ {self.baudrate}")
        except Exception as exc:
            print(f"Hand mirror serial not connected ({self.serial_port}): {exc}")

    def send_angles(
        self,
        base: int,
        shoulder: int,
        elbow: int,
        wrist_pitch: int,
        wrist_roll: int,
        gripper: int,
    ) -> None:
        msg = f"{base},{shoulder},{elbow},{wrist_pitch},{wrist_roll},{gripper}\n"

        if self.ser is None:
            return

        try:
            self.ser.write(msg.encode())
            self.connected = True
        except Exception as exc:
            self.connected = False
            print(f"Hand mirror serial error: {exc}")

    def close(self) -> None:
        if self.ser:
            self.ser.close()
            self.ser = None
            self.connected = False


_controller: HandRobotController | None = None


def get_hand_controller() -> HandRobotController:
    global _controller
    if _controller is None:
        _controller = HandRobotController()
    return _controller
