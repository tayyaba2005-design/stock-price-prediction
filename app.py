from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import pickle
from flask_cors import CORS
from tensorflow.keras.models import load_model
import os

app = Flask(__name__)
CORS(app)

print("🚀 Starting backend...")

# -------------------------------
# LOAD DATASET (FINAL FIX)
# -------------------------------
try:
    if not os.path.exists("stocks_df.csv"):
        raise FileNotFoundError("stocks_df.csv not found!")

    df = pd.read_csv("stocks_df.csv")

    # Clean column names
    df.columns = df.columns.str.strip()

    print("📊 Columns found:", df.columns.tolist())

    # Auto-detect Symbol column
    if 'Symbol' not in df.columns:
        if 'Stock' in df.columns:
            df.rename(columns={'Stock': 'Symbol'}, inplace=True)
        elif 'Ticker' in df.columns:
            df.rename(columns={'Ticker': 'Symbol'}, inplace=True)
        elif 'Company' in df.columns:
            df.rename(columns={'Company': 'Symbol'}, inplace=True)
        else:
            raise Exception("❌ No Symbol/Stock/Ticker/Company column found!")

    # Check required columns
    if 'Date' not in df.columns or 'Close' not in df.columns:
        raise Exception("❌ 'Date' or 'Close' column missing!")

    # Process data
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(['Symbol', 'Date'])
    df = df.dropna()

    print("✅ Dataset loaded successfully")

except Exception as e:
    print("❌ Dataset Error:", e)
    df = pd.DataFrame()

# -------------------------------
# LOAD MODEL + SCALER
# -------------------------------
try:
    if not os.path.exists("stock_model.keras"):
        raise FileNotFoundError("Model file missing!")

    if not os.path.exists("scaler.pkl"):
        raise FileNotFoundError("Scaler file missing!")

    model = load_model("stock_model.keras")
    scaler = pickle.load(open("scaler.pkl", "rb"))

    print("✅ Model & Scaler loaded")

except Exception as e:
    print("❌ Model Error:", e)
    model = None
    scaler = None

# -------------------------------
# GET TOP COMPANIES
# -------------------------------
try:
    top_companies = df['Symbol'].value_counts().head(15).index.tolist()
except:
    top_companies = []

# -------------------------------
# ROUTES
# -------------------------------

@app.route('/')
def home():
    return "Backend is running!"

@app.route('/companies', methods=['GET'])
def companies():
    if not top_companies:
        return jsonify({"error": "No companies available"})
    return jsonify(top_companies)

@app.route('/get_prices', methods=['POST'])
def get_prices():
    try:
        company = request.json['company']

        data = df[df['Symbol'] == company].tail(30)

        if len(data) < 30:
            return jsonify({"error": "Not enough data"})

        return jsonify(data['Close'].tolist())

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if model is None or scaler is None:
            return jsonify({"error": "Model not loaded"})

        prices = request.json['prices']

        if len(prices) != 30:
            return jsonify({"error": "Need exactly 30 prices"})

        prices = np.array(prices).reshape(-1, 1)
        prices = scaler.transform(prices)
        prices = prices.reshape(1, 30, 1)

        prediction = model.predict(prices)
        prediction = scaler.inverse_transform(prediction)

        return jsonify({"predicted_price": float(prediction[0][0])})

    except Exception as e:
        return jsonify({"error": str(e)})

# -------------------------------
# RUN SERVER
# -------------------------------
if __name__ == "__main__":
    print("🔥 Starting Flask server...")
    app.run(debug=True, port=5000)