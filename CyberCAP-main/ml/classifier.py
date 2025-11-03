# classifier.py
import os
import re
import joblib
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer



# Define base directory
BASE_DIR = os.path.dirname(__file__)

# ✅ Correct model paths
category_model_path = os.path.join(BASE_DIR, "category_model.pkl")
priority_model_path = os.path.join(BASE_DIR, "priority_model.pkl")

# ✅ Load both models
category_model = joblib.load(category_model_path)
priority_model = joblib.load(priority_model_path)

# Text preprocessing setup
stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

def clean_text(text):
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    tokens = nltk.word_tokenize(text)
    tokens = [lemmatizer.lemmatize(w) for w in tokens if w not in stop_words]
    return " ".join(tokens)

# Function to classify a complaint
def classify_complaint(description: str, category_model, priority_model):
    if not category_model or not priority_model:
        raise ValueError("Models not loaded properly.")

    cleaned = clean_text(description)
    category = category_model.predict([cleaned])[0]
    priority = priority_model.predict([cleaned])[0]

    return {"category": category, "priority": priority}

