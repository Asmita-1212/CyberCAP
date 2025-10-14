from joblib import load
import os

model_path = os.path.join("ml", "model.pkl")
model = load(model_path)

def classify_complaint(text):
    return model.predict([text])[0]
