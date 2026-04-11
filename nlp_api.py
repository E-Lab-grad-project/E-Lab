from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List, Optional
import serial
import time

# ===============================
# FastAPI setup
# ===============================
app = FastAPI()

# ===============================
# Serial setup (Arduino)
# ===============================
try:
    ser = serial.Serial("COM8", 115200, timeout=1)
    time.sleep(2)
    SERIAL_CONNECTED = True
    print("🟢 Serial connected to Arduino")
except Exception as e:
    ser = None
    SERIAL_CONNECTED = False
    print(f"⚠️ Serial not connected: {e}")

def send_command(command: str):
    """
    Send command to Arduino if connected, else print it (mock).
    """
    if SERIAL_CONNECTED and ser:
        try:
            ser.write(f"{command}\n".encode())
            print(f"📤 Sent command: {command}")
        except Exception as e:
            print(f"❌ Error sending command {command}: {e}")
    else:
        print(f"💡 [Mock] Command: {command}")
    time.sleep(0.2)

# ===============================
# Servo functions (existing commands)
# ===============================
def move_down():  send_command("MOVE_DOWN")
def move_up():    send_command("MOVE_UP")
def move_left():  send_command("MOVE_LEFT")
def move_right(): send_command("MOVE_RIGHT")
def move_forward(): send_command("MOVE_FORWARD")
def move_backward(): send_command("MOVE_BACKWARD")
def grip():       send_command("GRIP")
def release():    send_command("RELEASE")

COMMANDS_MAP = {
    "move_down": move_down,
    "move_up": move_up,
    "move_left": move_left,
    "move_right": move_right,
    "move_forward": move_forward,
    "move_backward": move_backward,
    "grip": grip,
    "release": release
}

# ===============================
# NLP model
# ===============================
tokenizer = AutoTokenizer.from_pretrained("robot_intent_model")
model = AutoModelForSequenceClassification.from_pretrained("robot_intent_model")
intent_mapping = model.config.id2label

# ===============================
# Request schemas
# ===============================
class TextInputList(BaseModel):
    texts: List[str]

class ServoUpdate(BaseModel):
    armId: int
    servoIndex: int
    degree: int  # degree from slider

class PredictRequest(BaseModel):
    texts: List[str]
    servoUpdates: Optional[List[ServoUpdate]] = []

# ===============================
# Internal state
# ===============================
# Keep track of last servo angles
srv_angles = {}  # key: (armId, servoIndex), value: degree

# ===============================
# Root endpoint
# ===============================
@app.get("/")
def root():
    return {"status": "API is running!"}

# ===============================
# Predict + execute endpoint
# ===============================
@app.post("/predict")
def predict(data: PredictRequest):
    predictions = []

    # 1️⃣ NLP commands
    for text in data.texts:
        input_text = tokenizer(text, return_tensors='pt')
        with torch.no_grad():
            logits = model(**input_text).logits
        predicted_class = torch.argmax(logits, dim=1).item()
        command = intent_mapping.get(predicted_class, "unknown")
        predictions.append(command)

        # Execute command on arm (or mock)
        func = COMMANDS_MAP.get(command)
        if func:
            func()
        else:
            print(f"⚠️ Unknown command: {command}")

    # 2️⃣ Servo updates from Flutter sliders
    for update in data.servoUpdates:
        arm = update.armId
        srv = update.servoIndex
        degree = update.degree

        # Format: "ARM{arm}_SRV{srv} {degree}"
        send_command(f"ARM{arm}_SRV{srv} {degree}")

        # Store for internal reference
        srv_angles[(arm, srv)] = degree

    return {
        "predictions": predictions,
        "servoAngles": {f"arm{arm}_srv{srv}": deg for (arm, srv), deg in srv_angles.items()}
    }