# Smart Retail Sales Analysis & Demand Forecasting
### Cornerstone Project · Data Analysis Essentials (DAE)
**Department of Computer Science and Engineering**

**Project Team:**
- S. Leela Venkata Krishna Reddy (25B11CS861)
- P. Surya Akhil (25B11CS717)
- K. Surya Raja Mokshagna (25B11CS453)

---

## 📌 Executive Summary
This project analyzes **18,041 retail sales transactions** from the DMart multi-year dataset (2011–2017). By leveraging statistical data analysis, exploratory data visualization, and supervised machine learning, it extracts actionable commercial insights and delivers an automated **Sales & Demand Forecasting Web Application**.

---

## 🚀 Key Project Findings & Deliverables

1. **Revenue & Profit Dynamics**:
   - Total Gross Revenue: **$4,645,683**
   - Total Net Profit: **$569,637** (Overall profit margin: ~12.26%)
   - Average Order Value (AOV): **$257.51**
   - Peak Fiscal Year: **2014** ($1,239,278 in sales, $134,874 in profit).

2. **Category & Flagship Products**:
   - **Technology** generates the largest revenue share ($1.72M) and highest profit ($254K).
   - **Office Supplies** accounts for the highest transaction frequency (62.7% of all orders).
   - Top Flagship Product: **Canon imageCLASS 2200 Advanced Copier** ($61,599 in gross sales).

3. **Regional & Customer Insights**:
   - **Central Territory** leads all regions ($1,816,492 sales, $197,342 profit).
   - **Consumer Segment** represents over 51% of overall demand.

4. **Strategic Pricing & Discount Threshold**:
   - Discounts up to **20%** maintain strong profitability ($24 to $74 average profit per item).
   - Discounts exceeding **30%** create severe operational losses (reaching -$276 to -$1,925 per order in high markdown brackets).

5. **Machine Learning Model Comparison**:
   | Model | MAE ($) | RMSE ($) | R² Score | Result |
   | :--- | :---: | :---: | :---: | :--- |
   | **Linear Regression** | 267.69 | 486.75 | 0.2092 | Baseline |
   | **Decision Tree Regressor** | 138.54 | 507.64 | 0.1399 | Overfits local branches |
   | **Random Forest Regressor** | **108.63** | **387.05** | **0.5000** | 🏆 **Best Model (Saved as `.pkl`)** |

---

## 📂 Project Structure

```
DAE/
├── DMart_Sales_Analysis_Project.ipynb   # Complete step-by-step Jupyter Notebook
├── DMart_Sales_Analysis_DAE.pptx        # Presentation Deck (24 slides)
├── DAE Project Abstract.pdf             # Project Abstract documentation
├── DMart_All_Data_2011_2017.xlsx        # Primary Sales Dataset (18,041 records)
├── train_model.py                       # Automated training & artifact generation
├── app.py                               # FastAPI backend & prediction service
├── static/
│   ├── index.html                       # Enterprise dashboard & interactive forecaster UI (Dark Theme)
│   ├── style.css                        # Midnight dark mode enterprise design system
│   └── app.js                           # Chart.js visualizations & reactive inference
├── dmart_sales_model.pkl.gz             # Trained Random Forest Regressor (compressed model)
├── scaler.pkl                           # StandardScaler for numerical features
├── model_meta.json                      # Feature list, encodings, and metrics
├── eda_summary.json                     # Precomputed KPIs and chart series
├── requirements.txt                     # Dependency specifications
├── run_app.bat                          # One-click launch script
└── train_and_run.bat                    # One-click retraining and launch script
```

---

## 💻 How to Run

### Option 1: Quick Launch (Windows)
Double-click `run_app.bat` to launch the web dashboard at `http://127.0.0.1:8000`.

### Option 2: Command Line
```powershell
# 1. Install dependencies (if not already installed)
python -m pip install -r requirements.txt

# 2. Retrain the model (optional, artifacts already included)
python train_model.py

# 3. Start the application server
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```
Open your browser and navigate to: **`http://127.0.0.1:8000`**
