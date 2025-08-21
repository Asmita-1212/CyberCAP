import re
from sklearn.feature_extraction.text import TfidfVectorizer

def clean_text(text):
    text = text.lower()                              # Convert text to lowercase
    text = re.sub(r'[^a-zA-Z\s]', '', text)          # Remove numbers, symbols, punctuation
    return text

vectorizer = TfidfVectorizer(stop_words="english")   # Convert text into numeric features using TF-IDF
