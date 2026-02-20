# ⚡ EV Infrastructure Optimization - India

A data-driven framework to optimize Electric Vehicle (EV) charging infrastructure deployment in India using **Demand Forecasting**, **Geospatial Clustering**, and **Grid Load Optimization**.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📖 Project Overview

As EV adoption accelerates in India, strategic placement of charging stations is critical to minimize range anxiety and grid impact. This project uses a **Hybrid Data Approach** (Real + Synthetic) to model and optimize this infrastructure.

### Key Objectives
1.  **Demand Forecasting:** Predict state-wise EV sales using ARIMA/XGBoost.
2.  **Strategic Placement:** Identify "White Space" gaps using DBSCAN & K-Means clustering.
3.  **Grid Impact Analysis:** Optimize charging schedules to flatten peak load curves using Linear Programming.
4.  **Financial Viability:** Calculate ROI, NPV, and carbon credits with FAME-II subsidy integration.

---

## 🛠️ Features & Methodology

### 1. Hybrid Data Pipeline
- Automatically integrates **Real-world data** (if available) with **Synthetic data** to ensure robust execution.
- **Sources**: Kaggle (Vahan Dashboard), OpenChargeMap, and statistical synthetic generation.

### 2. Machine Learning Models
- **Forecasting**: Time-series forecasting for 2W, 3W, and 4W vehicle categories.
- **Clustering**: Geospatial analysis to group existing demand and find service gaps.

### 3. Interactive Dashboard
- Built with **Streamlit** to visualize all insights in real-time.
- Features interactive maps, load profile charts, and financial calculators.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/your-username/ev-infrastructure-optimization.git
    cd ev-infrastructure-optimization
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Data Pipeline**
    This command processes data, runs all ML models, and generates results.
    ```bash
    python main.py --process --all
    ```

4.  **Launch the Dashboard**
    ```bash
    streamlit run app.py
    ```

---

## 📊 Project Structure

```bash
EV_PROJECT/
├── app.py                  # 🖥️ Streamlit Dashboard
├── main.py                 # ⚙️ Master Pipeline Runner
├── requirements.txt        # 📦 Dependencies
├── data/
│   ├── raw/                # Raw Input Data (Real + Synthetic)
│   └── processed/          # Cleaned & Featured Data
├── src/
│   ├── data/               # Data Ingestion & Cleaning
│   ├── features/           # Feature Engineering
│   └── models/             # ML & Optimization Models
└── results/                # 📈 Generated Plots & Reports
```

---

## 📈 Results Summary

- **Forecasting**: Achieved high accuracy in predicting EV adoption trends across top Indian states.
- **Optimization**: Reduced projected peak grid load by shifting charging sessions to off-peak hours based on optimized schedules.
- **Financials**: Validated the economic viability of DC Fast Chargers in high-traffic urban clusters under FAME-II schemes.

---

## 🤝 Contributing

Contributions are welcome! Please fork this repository and submit a pull request for any enhancements.

---

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
