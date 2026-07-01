import os
import urllib.request

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)

DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")


def ensure_hand_landmarker_model(path: str = DEFAULT_MODEL_PATH) -> str:
    if os.path.isfile(path):
        return path

    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"Downloading hand landmarker model to {path} ...")
    urllib.request.urlretrieve(MODEL_URL, path)
    print("Hand landmarker model ready.")
    return path
