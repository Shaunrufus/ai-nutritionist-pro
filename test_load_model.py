import os
import joblib

model_path = os.path.join("models", "nutrition_model.pkl")
print("Loading model from:", model_path)

model = joblib.load(model_path)

print("✅ Model loaded successfully!")
