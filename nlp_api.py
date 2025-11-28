from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List

app = FastAPI()

# تحميل المودل
tokenizer = AutoTokenizer.from_pretrained("robot_NLP_model")
model = AutoModelForSequenceClassification.from_pretrained("robot_NLP_model")

# لو عندك mapping من رقم الintent لاسمه
intent_mapping = model.config.id2label

class TextInputList(BaseModel):
    texts: List[str]

@app.get("/")
def root():
    return {"status": "API is running!"}

@app.post("/predict")
def predict(data: TextInputList):
    predictions = []
    for text in data.texts:
        input_text = tokenizer(text, return_tensors='pt')
        with torch.no_grad():
            logits = model(**input_text).logits
        predicted_class = torch.argmax(logits, dim=1).item()
        predictions.append(intent_mapping.get(predicted_class, "unknown"))
    return {"predictions": predictions}
