import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def build_and_train():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    excel_candidates = [
        os.path.join(project_dir, "DMart_All_Data_2011_2017.xlsx"),
        r"C:\Users\surya\OneDrive\Desktop\DAE\DMart_All_Data_2011_2017.xlsx",
        r"C:\Users\surya\DMart_All_Data_2011_2017.xlsx",
        r"C:\Users\surya\Downloads\DMart_All_Data_2011_2017.xlsx"
    ]
    excel_path = None
    for p in excel_candidates:
        if os.path.exists(p):
            excel_path = p
            break
            
    if not excel_path:
        raise FileNotFoundError("Cannot find DMart_All_Data_2011_2017.xlsx")
            
    print(f"Loading data from: {excel_path} ...")
    df = pd.read_excel(excel_path, sheet_name="All Data")
    print(f"Initial shape: {df.shape}")

    # Step 4: Data Cleaning (as per notebook)
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    if "Ship Date" in df.columns:
        df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")

    if "Segment" in df.columns:
        seg_mode = df["Segment"].mode()
        df["Segment"] = df["Segment"].fillna(seg_mode[0] if len(seg_mode) > 0 else "Consumer")

    if "Region" in df.columns:
        reg_mode = df["Region"].mode()
        df["Region"] = df["Region"].fillna(reg_mode[0] if len(reg_mode) > 0 else "Central")

    if "Sales" in df.columns:
        df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce")
        df["Sales"] = df["Sales"].fillna(df["Sales"].median())

    if "Profit" in df.columns:
        df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce")
        df["Profit"] = df["Profit"].fillna(df["Profit"].median())

    if "Quantity" in df.columns:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
        df["Quantity"] = df["Quantity"].fillna(df["Quantity"].median()).astype(int)

    if "Discount" in df.columns:
        df["Discount"] = pd.to_numeric(df["Discount"], errors="coerce")
        df["Discount"] = df["Discount"].fillna(df["Discount"].median())

    # Step 5: Feature Engineering
    raw_df = df.copy() # keep clean copy for EDA aggregates

    drop_id_cols = ["Row ID", "Order ID", "Customer ID", "Product ID"]
    df = df.drop(columns=[c for c in drop_id_cols if c in df.columns], errors="ignore")

    df["Order_Year"] = df["Order Date"].dt.year
    df["Order_Month"] = df["Order Date"].dt.month
    df["Order_Day"] = df["Order Date"].dt.day
    df["Order_Quarter"] = df["Order Date"].dt.quarter

    if "Ship Date" in df.columns:
        df["Shipping_Days"] = (df["Ship Date"] - df["Order Date"]).dt.days
        df["Shipping_Days"] = df["Shipping_Days"].fillna(0).astype(int)
    else:
        df["Shipping_Days"] = 0

    df["Discount_Amount"] = df["Sales"] * df["Discount"]
    df["Profit_Margin"] = (df["Profit"] / df["Sales"].replace(0, pd.NA)) * 100
    df["Profit_Margin"] = df["Profit_Margin"].fillna(0)
    df["Has_Discount"] = df["Discount"] > 0

    def sales_category(s):
        if s <= 100:
            return "Low"
        elif s <= 500:
            return "Medium"
        else:
            return "High"

    df["Sales_Category"] = df["Sales"].apply(sales_category)

    # Compute & Save EDA summary metrics for fast dashboard loading
    print("Computing EDA metrics...")
    raw_df["Order_Year"] = raw_df["Order Date"].dt.year
    raw_df["Order_Month"] = raw_df["Order Date"].dt.month
    
    total_sales = float(raw_df["Sales"].sum())
    total_profit = float(raw_df["Profit"].sum())
    avg_sales = float(raw_df["Sales"].mean())
    total_orders = int(len(raw_df))
    profit_margin_overall = round((total_profit / total_sales) * 100, 2) if total_sales > 0 else 0

    # Sales and Profit by Year
    yearly_grp = raw_df.groupby("Order_Year").agg({"Sales": "sum", "Profit": "sum", "Order Date": "count"}).reset_index()
    yearly_grp.columns = ["Year", "Sales", "Profit", "Orders"]
    yearly_grp = yearly_grp.sort_values("Year")
    yearly_data = yearly_grp.to_dict(orient="records")

    # Sales by Category
    cat_grp = raw_df.groupby("Category").agg({"Sales": "sum", "Profit": "sum", "Quantity": "sum"}).reset_index()
    category_data = cat_grp.to_dict(orient="records")

    # Sales by Sub-Category
    subcat_grp = raw_df.groupby("Sub-Category").agg({"Sales": "sum", "Profit": "sum", "Quantity": "sum"}).reset_index()
    subcat_grp = subcat_grp.sort_values("Sales", ascending=False)
    subcategory_data = subcat_grp.to_dict(orient="records")

    # Sales & Profit by Region
    reg_grp = raw_df.groupby("Region").agg({"Sales": "sum", "Profit": "sum"}).reset_index()
    reg_grp = reg_grp.sort_values("Sales", ascending=False)
    region_data = reg_grp.to_dict(orient="records")

    # Sales by Segment
    seg_grp = raw_df.groupby("Segment").agg({"Sales": "sum", "Profit": "sum"}).reset_index()
    segment_data = seg_grp.to_dict(orient="records")

    # Top 10 Products by Sales
    if "Product Name" in raw_df.columns:
        top_prod = raw_df.groupby("Product Name")["Sales"].sum().reset_index().sort_values("Sales", ascending=False).head(10)
        top_products = top_prod.to_dict(orient="records")
    else:
        top_products = []

    # Discount vs Profit
    disc_grp = raw_df.groupby("Discount")["Profit"].mean().round(2).reset_index()
    disc_grp = disc_grp.sort_values("Discount")
    discount_data = disc_grp.to_dict(orient="records")

    # Region vs Category Crosstab
    crosstab_reg_cat = pd.crosstab(raw_df["Region"], raw_df["Category"], values=raw_df["Sales"], aggfunc="sum").round(2).fillna(0).to_dict()

    eda_summary = {
        "kpis": {
            "total_sales": round(total_sales, 2),
            "total_profit": round(total_profit, 2),
            "avg_sales": round(avg_sales, 2),
            "total_orders": total_orders,
            "profit_margin": profit_margin_overall,
            "most_common_qty": int(raw_df["Quantity"].mode()[0]) if len(raw_df["Quantity"].mode()) > 0 else 3
        },
        "yearly": yearly_data,
        "category": category_data,
        "subcategory": subcategory_data,
        "region": region_data,
        "segment": segment_data,
        "top_products": top_products,
        "discount_impact": discount_data,
        "region_category_matrix": crosstab_reg_cat
    }

    with open(os.path.join(project_dir, "eda_summary.json"), "w", encoding="utf-8") as f:
        json.dump(eda_summary, f, indent=2)
    print("Saved eda_summary.json")

    # Step 7: Data Preprocessing for ML
    print("Preprocessing for Machine Learning...")
    categorical_columns = [
        "Ship Mode",
        "Segment",
        "Country",
        "City",
        "State",
        "Region",
        "Category",
        "Sub-Category",
        "Sales_Category"
    ]
    categorical_columns = [c for c in categorical_columns if c in df.columns]

    label_encoders = {}
    for column in categorical_columns:
        le = LabelEncoder()
        df[column] = le.fit_transform(df[column].astype(str))
        label_encoders[column] = {
            "classes": [str(c) for c in le.classes_],
            "mapping": {str(cls_): int(idx) for idx, cls_ in enumerate(le.classes_)}
        }

    # Drop non-feature and target-leak columns (matching notebook Cell 146)
    df = df.drop(
        columns=["Order Date", "Ship Date", "Product Name", "Customer Name", "Source", "Feedback?", "Profit", "Discount_Amount", "Profit_Margin"],
        errors="ignore"
    )

    df = df.replace([float("inf"), float("-inf")], pd.NA)
    df = df.fillna(0)

    # Scaling
    scale_columns = [
        "Quantity",
        "Discount",
        "Order_Month",
        "Order_Day",
        "Order_Quarter",
        "Shipping_Days"
    ]
    scale_columns = [c for c in scale_columns if c in df.columns]

    scaler = StandardScaler()
    df[scale_columns] = scaler.fit_transform(df[scale_columns])

    # Step 8: Splitting
    X = df.drop("Sales", axis=1)
    y = df["Sales"]
    feature_names = list(X.columns)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"X_train shape: {X_train.shape}, X_test shape: {X_test.shape}")

    # Step 9: Training Models
    print("Training Linear Regression...")
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    y_pred_lr = lr_model.predict(X_test)
    mae_lr = mean_absolute_error(y_test, y_pred_lr)
    rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr))
    r2_lr = r2_score(y_test, y_pred_lr)

    print("Training Decision Tree Regressor...")
    dt_model = DecisionTreeRegressor(random_state=42)
    dt_model.fit(X_train, y_train)
    y_pred_dt = dt_model.predict(X_test)
    mae_dt = mean_absolute_error(y_test, y_pred_dt)
    rmse_dt = np.sqrt(mean_squared_error(y_test, y_pred_dt))
    r2_dt = r2_score(y_test, y_pred_dt)

    print("Training Random Forest Regressor (Best Model)...")
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)
    mae_rf = mean_absolute_error(y_test, y_pred_rf)
    rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf))
    r2_rf = r2_score(y_test, y_pred_rf)

    metrics = {
        "Linear Regression": {"MAE": round(float(mae_lr), 2), "RMSE": round(float(rmse_lr), 2), "R2": round(float(r2_lr), 4)},
        "Decision Tree": {"MAE": round(float(mae_dt), 2), "RMSE": round(float(rmse_dt), 2), "R2": round(float(r2_dt), 4)},
        "Random Forest": {"MAE": round(float(mae_rf), 2), "RMSE": round(float(rmse_rf), 2), "R2": round(float(r2_rf), 4)}
    }
    print("Model Evaluation Results:")
    for m_name, m_vals in metrics.items():
        print(f"  {m_name}: MAE={m_vals['MAE']}, RMSE={m_vals['RMSE']}, R2={m_vals['R2']}")

    # Step 11: Save Artifacts
    model_path = os.path.join(project_dir, "dmart_sales_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(rf_model, f)
    print(f"Saved best model: {model_path}")

    model_gz_path = os.path.join(project_dir, "dmart_sales_model.pkl.gz")
    import gzip
    with gzip.open(model_gz_path, "wb") as f:
        pickle.dump(rf_model, f)
    print(f"Saved compressed model: {model_gz_path}")

    scaler_path = os.path.join(project_dir, "scaler.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    with open(os.path.join(project_dir, "model_meta.json"), "w", encoding="utf-8") as f:
        json.dump({
            "features": feature_names,
            "scale_columns": scale_columns,
            "categorical_columns": categorical_columns,
            "label_encoders": label_encoders,
            "metrics": metrics,
            "best_model": "Random Forest Regressor"
        }, f, indent=2)

    print("Saved scaler.pkl and model_meta.json")
    print("Build and training completed successfully!")

if __name__ == "__main__":
    build_and_train()
