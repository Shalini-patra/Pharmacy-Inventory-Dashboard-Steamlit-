# 💊 Pharmacy Smart Inventory Monitoring System

> An end-to-end Inventory Intelligence Platform that helps pharmacies reduce stock-outs, minimize medicine expiry, automate reorder decisions, and transform raw transaction data into actionable business insights.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-NeonDB-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![GitHub Actions](https://img.shields.io/badge/Automation-GitHub_Actions-success)

---

<a href="https://pharmo.streamlit.app/">
  <img src="https://img.shields.io/badge/%F0%9F%9A%80%20Go to%20Live Streamlit%20App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" width="400">
</a>


---

# 📌 Project Overview

Managing pharmacy inventory is much more than tracking stock quantities. Every medicine has different demand patterns, expiry periods, supplier lead times, and business value.

Traditional pharmacy billing software records sales and inventory but often lacks the analytical capabilities required to answer questions like:

- Which medicines should be reordered today?
- Which products are approaching expiry?
- How much inventory should be maintained?
- Which medicines generate the highest revenue?
- Which products have seasonal demand?
- Which customers are the most valuable?

This project addresses those challenges by combining **Data Engineering, Inventory Analytics, Demand Forecasting, Automation, and Business Intelligence** into a single platform.

---

# 🎯 Business Objectives

The project was designed to help pharmacies:

- Prevent stock-outs
- Reduce medicine expiry losses
- Optimize inventory levels
- Automate reorder decisions
- Improve inventory visibility
- Support data-driven business decisions
- Reduce manual inventory monitoring

---

# 🏗️ Solution Architecture

```text
                    Historical Data Generator
                             │
                             ▼
               Generate Pharmacy Master Dataset
                             │
                             ▼
            Incremental Transaction Generator
                             │
                             ▼
                 Generate Daily Transactions
                             │
                             ▼
                 Incremental ETL Pipeline
                             │
      ┌──────────────────────┼──────────────────────┐
      ▼                      ▼                      ▼
 Data Cleaning        Feature Engineering   Statistical Analysis
      │                      │                      │
      └──────────────────────┼──────────────────────┘
                             ▼
                    Business Calculations
                             │
        ├── Demand Forecasting
        ├── Safety Stock
        ├── Reorder Point
        ├── Suggested Reorder Quantity
        ├── ABC Analysis
        ├── Bundle Analysis
        └── Inventory Health Metrics
                             │
                             ▼
                  PostgreSQL (NeonDB)
                             │
                             ▼
                 Streamlit Dashboard
                             │
          ┌──────────────────┴──────────────────┐
          ▼                                     ▼
 Manual Reorder Email                 Automated Reorder Email
```

---

# 🚀 Features

## 📊 Executive Overview

- Revenue & Profit KPIs
- Sales Trends
- Top & Bottom Moving Medicines
- Customer Metrics
- Sales Activity Heatmap

---

## 📦 Reorder Management

- Intelligent Reorder Classification
- Safety Stock Monitoring
- Reorder Point Calculation
- Suggested Reorder Quantity
- Shelf-life Aging Matrix
- Automated Reorder Email
- CSV Export

---

## 💰 Transactions & Revenue

- Revenue Analysis
- Profit Analysis
- Transaction Trends
- Financial KPIs

---

## 💊 Drugs Inventory

- Drug Search
- Inventory Summary
- Category Analysis
- Treemap Visualization
- Stock Update Form
- Restock Recording

---

## 👥 Customer Analytics

- Customer KPIs
- Regular Customer Analysis
- Transaction History
- Customer Summary

---

## 📈 ABC Analysis

- Revenue Contribution
- ABC Classification
- Drug-Level Analysis
- Revenue Share Visualization

---

## 🛒 Bundle Analysis

- Frequently Bought Together Medicines
- Bundle Frequency Analysis
- Cross-selling Opportunities

---

## ⚙️ Settings

- System Health
- Forecast Configuration
- Alert Configuration
- Database Status
- System Logs

---

# ⚙️ ETL Pipeline

The automated ETL pipeline performs:

- Data Extraction
- Data Validation
- Data Cleaning
- Feature Engineering
- Statistical Analysis
- Seasonal Demand Detection
- Demand Forecasting
- Safety Stock Calculation
- Reorder Point Calculation
- Suggested Reorder Quantity Calculation
- Inventory Snapshot Generation
- ABC Classification
- Analytics Table Updates

---

# 📈 Business Impact

Designed to help pharmacies achieve:

| Metric | Impact |
|---------|--------|
| Potential Inventory Loss Reduction | ~20% |
| Manual Reorder Monitoring Reduction | ~85% |
| Inventory Review Time Saved | ~8–10 Hours / Week |
| Inventory Visibility | Real-time |
| Reorder Alerts | Automated |

---

# 🌐 Real-World Deployment

The current project uses **realistic synthetic data** to simulate pharmacy operations.

In a production environment, the synthetic data generator can be replaced with **live transaction data from existing Pharmacy Billing/POS software**.

Rather than replacing the pharmacy's billing application, this platform is designed to function as an **Inventory Intelligence Layer** by integrating through:

- REST APIs
- Database Integration
- Scheduled Data Synchronization
- CSV/API Connectors (where APIs are unavailable)

This approach allows pharmacies to continue using their existing billing software while gaining advanced analytics, forecasting, reorder optimization, and executive dashboards.

---

# 🛠️ Technology Stack

### Programming

- Python

### Database

- PostgreSQL (NeonDB)

### Dashboard

- Streamlit

### Data Processing

- Pandas
- NumPy

### Visualization

- Plotly

### Database Connectivity

- psycopg2

### Automation

- GitHub Actions

### Notifications

- SMTP Email

### Version Control

- GitHub

---

# 📚 Key Techniques

- Incremental ETL
- Feature Engineering
- Time-Series Analysis
- Demand Forecasting
- Seasonal Detection
- Inventory Optimization
- Safety Stock Calculation
- Reorder Point Optimization
- ABC Analysis
- Bundle Analysis
- Data Visualization
- Email Automation

---

# 📂 Project Structure

```text
📦 Pharmacy Smart Inventory System
│
├── Historical Data Generator
├── Incremental Transaction Generator
├── Incremental ETL Pipeline
├── PostgreSQL Database
├── Streamlit Dashboard
│   ├── Executive Overview
│   ├── Reorder Management
│   ├── Transactions & Revenue
│   ├── Drugs Inventory
│   ├── Customer Analytics
│   ├── ABC Analysis
│   ├── Bundle Analysis
│   └── Settings
│
├── Email Notification Module
├── Automation (GitHub Actions)
└── Documentation
```

---

# 📸 Dashboard Preview

> *(Add dashboard screenshots here)*

- Executive Overview
- Reorder Management
- Drugs Inventory
- Transactions & Revenue
- Customer Analytics
- ABC Analysis
- Bundle Analysis

---

# 🚀 Future Enhancements

- POS/Billing Software Integration
- Real-Time API Synchronization
- Barcode Scanner Integration
- Purchase Order Generation
- Supplier Management
- Mobile Dashboard
- Role-Based Authentication
- AI-powered Procurement Recommendations

---

# 👨‍💻 Author

**T Shalini Patra**

If you found this project interesting or have suggestions for improvement, feel free to connect or share your feedback.

---

## ⭐ If you like this project, consider giving it a Star!
