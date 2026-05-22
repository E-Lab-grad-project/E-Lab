import asyncio
import websockets
import json
import time

# ===============================
# Action functions
# ===============================
def move_down(): 
    print("⬇️ move_down")
def move_up():
    print("⬆️ move_up")
def move_left(): 
    print("⬅️ move_left")
def move_right(): 
    print("➡️ move_right")
def grip(): 
    print("✊ grip")
def release(): 
    print("🖐️ release")

# Map command names to functions
COMMANDS_MAP = {
    "move_down": move_down,
    "move_up": move_up,
    "move_left": move_left,
    "move_right": move_right,
    "grip": grip,
    "release": release
}

# Delay بين كل أمر والثاني (ثواني)
DELAY_BETWEEN_COMMANDS = 1.0

# ===============================
# Execute commands sequentially
# ===============================
def execute_commands(commands, delay_between=DELAY_BETWEEN_COMMANDS):
    for cmd in commands:
        func = COMMANDS_MAP.get(cmd)
        if not func:
            print(f"❌ Unknown command: {cmd}")
            continue
        func()
        time.sleep(delay_between)

# ===============================
# WebSocket listener
# ===============================
async def listen():
    # غير هذا الـ IP ليكون IP الكمبيوتر اللي عليه FastAPI
    url = "ws://192.168.1.30:8000/ws"

    while True:
        try:
            async with websockets.connect(url) as websocket:
                print("🟢 Connected to WebSocket server")

                while True:
                    data = await websocket.recv()
                    payload = json.loads(data)
                    commands = payload.get("texts", [])
                    if commands:
                        print("📥 Commands received:", commands)
                        execute_commands(commands)

        except (websockets.exceptions.ConnectionClosedError, 
                websockets.exceptions.InvalidStatusCode) as e:
            print(f"⚠️ Connection lost. Retrying in 3s... ({e})")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"🔥 Unexpected error: {e}")
            await asyncio.sleep(3)

# ===============================
# Main
# ===============================
if __name__ == "__main__":
    asyncio.run(listen())
