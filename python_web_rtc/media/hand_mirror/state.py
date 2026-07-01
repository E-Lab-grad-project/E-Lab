from dataclasses import dataclass, field


SERVO_LABELS = ["Base", "Shoulder", "Elbow", "Wrist Pitch", "Wrist Roll", "Gripper"]


@dataclass
class HandMirrorState:
    mirroring_enabled: bool = False
    hand_detected: bool = False
    serial_connected: bool = False
    last_angles: list[int] = field(default_factory=lambda: [90, 90, 90, 90, 90, 90])

    def to_dict(self) -> dict:
        return {
            "mirroring": self.mirroring_enabled,
            "handDetected": self.hand_detected,
            "serialConnected": self.serial_connected,
            "angles": dict(zip(SERVO_LABELS, self.last_angles)),
            "anglesList": self.last_angles,
        }


hand_mirror_state = HandMirrorState()
