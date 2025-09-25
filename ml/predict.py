import joblib
from preprocessing import clean_text

# Load model & vectorizer
model = joblib.load("../models/complaint_classifier.pkl")
vectorizer = joblib.load("../models/vectorizer.pkl")

def classify_complaint(text):
    text_clean = clean_text(text)                        # Clean new complaint
    X = vectorizer.transform([text_clean])               # Convert to numeric
    prediction = model.predict(X)[0]                     # Predict category

    # Assign priority
    priority = "High" if prediction in ["Fraud", "Harassment"] else "Medium"
    return prediction, priority
