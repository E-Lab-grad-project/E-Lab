from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List
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
    ser = serial.Serial("COM3", 115200, timeout=1)
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
    time.sleep(0.5)

# ===============================
# Servo functions
# ===============================
def move_down():  send_command("MOVE_DOWN")
def move_up():    send_command("MOVE_UP")
def move_left():  send_command("MOVE_LEFT")
def move_right(): send_command("MOVE_RIGHT")
def grip():       send_command("GRIP")
def release():    send_command("RELEASE")

COMMANDS_MAP = {
    "move_down": move_down,
    "move_up": move_up,
    "move_left": move_left,
    "move_right": move_right,
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
# Request schema
# ===============================
class TextInputList(BaseModel):
    texts: List[str]

# ===============================
# Root
# ===============================
@app.get("/")
def root():
    return {"status": "API is running!"}

# ===============================
# Predict + execute endpoint
# ===============================
@app.post("/predict")
def predict(data: TextInputList):
    predictions = []

    for text in data.texts:
        # NLP prediction
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

    return {"predictions": predictions}
