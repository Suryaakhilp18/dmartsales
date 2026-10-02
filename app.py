import os
import json
import pickle
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(
    title="DMart Retail Operations & Demand Forecasting Portal",
    description="Avenue Supermarts Limited - Official Retail Sales Analytics & Demand Forecasting Suite",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load artifacts
model = None
scaler = None
model_meta = None
eda_summary = None

def load_artifacts():
    global model, scaler, model_meta, eda_summary
    model_path = os.path.join(BASE_DIR, "dmart_sales_model.pkl")
    model_gz_path = os.path.join(BASE_DIR, "dmart_sales_model.pkl.gz")
    scaler_path = os.path.join(BASE_DIR, "scaler.pkl")
    meta_path = os.path.join(BASE_DIR, "model_meta.json")
    eda_path = os.path.join(BASE_DIR, "eda_summary.json")

    if os.path.exists(model_gz_path):
        import gzip
        with gzip.open(model_gz_path, "rb") as f:
            model = pickle.load(f)
    elif os.path.exists(model_path):
        with open(model_path, "rb") as f:
            model = pickle.load(f)

    if os.path.exists(scaler_path):
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)

    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            model_meta = json.load(f)

    if os.path.exists(eda_path):
        with open(eda_path, "r", encoding="utf-8") as f:
            eda_summary = json.load(f)

load_artifacts()

class PredictionRequest(BaseModel):
    category: str
    sub_category: str
    segment: str
    region: str
    ship_mode: str
    quantity: int = 3
    discount: float = 0.0
    shipping_days: int = 3
    order_month: int = 6
    order_day: int = 15
    order_year: int = 2017
    country: Optional[str] = "United States"
    city: Optional[str] = "New York City"
    state: Optional[str] = "New York"

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None,
        "eda_loaded": eda_summary is not None
    }

@app.get("/api/analytics")
def get_analytics():
    if not eda_summary:
        load_artifacts()
    if not eda_summary:
        raise HTTPException(status_code=500, detail="EDA summary not generated yet. Run train_model.py first.")
    data = dict(eda_summary)
    if model_meta:
        data["model_metrics"] = model_meta.get("metrics", {})
        data["best_model"] = model_meta.get("best_model", "Random Forest Regressor")
    return data

@app.get("/api/model-info")
def get_model_info():
    if not model_meta:
        load_artifacts()
    if not model_meta:
        raise HTTPException(status_code=500, detail="Model metadata not found.")
    return model_meta

@app.post("/api/predict")
def predict_sales(req: PredictionRequest):
    if not model or not scaler or not model_meta:
        load_artifacts()
    if not model or not scaler or not model_meta:
        raise HTTPException(status_code=500, detail="Model or Scaler not loaded.")

    try:
        encoders = model_meta.get("label_encoders", {})
        feature_names = model_meta.get("features", [])
        scale_cols = model_meta.get("scale_columns", [])

        # Quarter from month
        order_quarter = (req.order_month - 1) // 3 + 1
        has_discount = req.discount > 0

        # Construct single-row dict
        input_data = {
            "Ship Mode": req.ship_mode,
            "Segment": req.segment,
            "Country": req.country or "United States",
            "City": req.city or "New York City",
            "State": req.state or "New York",
            "Region": req.region,
            "Category": req.category,
            "Sub-Category": req.sub_category,
            "Sales_Category": "Medium", # initial placeholder encoded
            "Quantity": req.quantity,
            "Discount": req.discount,
            "Order_Year": req.order_year,
            "Order_Month": req.order_month,
            "Order_Day": req.order_day,
            "Order_Quarter": order_quarter,
            "Shipping_Days": req.shipping_days,
            "Has_Discount": has_discount
        }

        # Encode categorical
        for cat_col in encoders:
            mapping = encoders[cat_col].get("mapping", {})
            val_str = str(input_data.get(cat_col, ""))
            input_data[cat_col] = mapping.get(val_str, 0)

        df_in = pd.DataFrame([input_data])

        # Ensure all training features are present
        for col in feature_names:
            if col not in df_in.columns:
                df_in[col] = 0

        df_in = df_in[feature_names]

        # Scale numerical columns
        df_in[scale_cols] = scaler.transform(df_in[scale_cols])

        # Predict
        pred = model.predict(df_in)
        predicted_sales = max(0.0, float(pred[0]))

        # Calculate estimated profit & margin based on historical category averages
        cat_margins = {
            "Technology": 0.147,
            "Office Supplies": 0.160,
            "Furniture": 0.049
        }
        base_margin = cat_margins.get(req.category, 0.12)
        # Higher discounts cut into profit margin
        discount_penalty = req.discount * 1.4
        estimated_margin_pct = max(-40.0, min(45.0, (base_margin - discount_penalty) * 100))
        estimated_profit = round(predicted_sales * (estimated_margin_pct / 100.0), 2)

        # Demand classification
        if predicted_sales < 100:
            demand_tier = "Standard Velocity"
            inventory_advice = "Maintain minimum threshold stock (10-15 units)."
        elif predicted_sales < 500:
            demand_tier = "Moderate Demand"
            inventory_advice = "Stock optimal buffer (25-40 units) for steady weekly clearance."
        else:
            demand_tier = "High-Volume / Enterprise Demand"
            inventory_advice = "Priority replenishment required. Allocate high-velocity warehouse bay."

        return {
            "predicted_sales": round(predicted_sales, 2),
            "estimated_profit": estimated_profit,
            "estimated_margin_pct": round(estimated_margin_pct, 1),
            "demand_tier": demand_tier,
            "inventory_advice": inventory_advice,
            "model_used": "RandomForestRegressor (100 Trees · Scikit-Learn Pipeline)"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount static folder (supports both /static/* and root /*)
static_dir = os.path.join(BASE_DIR, "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static_dir")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
