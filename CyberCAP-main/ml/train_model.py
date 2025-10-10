import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
import joblib
from preprocessing import clean_text, vectorizer

# Load dataset
df = pd.read_csv("../data/cyber_complaints.csv")   # Read complaints dataset
df['text'] = df['text'].apply(clean_text)          # Clean each complaint text

# Features & Labels
X = vectorizer.fit_transform(df['text'])           # Convert cleaned text → numeric features
y = df['category']                                 # Complaint category is the target

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train model
model = MultinomialNB()                            # Use Naive Bayes classifier
model.fit(X_train, y_train)                        # Train model on training data

# Save model
joblib.dump(model, "../models/complaint_classifier.pkl")   # Save trained model
joblib.dump(vectorizer, "../models/vectorizer.pkl")        # Save vectorizer
