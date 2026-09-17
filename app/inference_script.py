# Final and Corrected inference_script.py

import pandas as pd
import numpy as np
import os
import joblib
from sklearn.preprocessing import LabelEncoder

# Get the base directory (AI-Nutritionist)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Load models using correct relative path
reg_model = joblib.load(os.path.join(BASE_DIR, "models", "nutrition_regressor.pkl"))
clf_model = joblib.load(os.path.join(BASE_DIR, "models", "nutrition_classifier.pkl"))
label_encoder = joblib.load(os.path.join(BASE_DIR, "models", "label_encoder.pkl"))

# Load input data for testing (you can change this to any sample data)
model_input = pd.read_csv(os.path.join(BASE_DIR, "data", "nutrition_dataset.csv"))

# Drop target columns from input
target_columns = [
    'Recommended_Calories', 'Recommended_Protein', 
    'Recommended_Carbs', 'Recommended_Fats', 'Recommended_Meal_Plan'
]

X = model_input.drop(columns=target_columns)
X = pd.get_dummies(X)

# Ensure model_input has the same feature columns as training set
# You may need to save feature names during training if mismatches occur

# Run predictions
pred_nutrition = reg_model.predict(X)
pred_meal_plan_encoded = clf_model.predict(X)
pred_meal_plan = label_encoder.inverse_transform(pred_meal_plan_encoded)

# Format predictions
prediction_df = pd.DataFrame(pred_nutrition, columns=[
    'Predicted_Calories', 'Predicted_Protein', 'Predicted_Carbs', 'Predicted_Fats'])
prediction_df['Predicted_Meal_Plan'] = pred_meal_plan

# Save to CSV
output_path = os.path.join(BASE_DIR, "final_diet_predictions.csv")
prediction_df.to_csv(output_path, index=False)

print("✅ Inference completed. Results saved to final_diet_predictions.csv")
