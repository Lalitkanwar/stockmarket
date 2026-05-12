# Nexus Finance | AI-Powered Stock Market Dashboard

![Nexus Finance Cover](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white) ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![Machine Learning](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)

Nexus Finance is a comprehensive, production-ready fintech application built with Python and Streamlit. It provides real-time market data, interactive charting, AI-driven trend predictions, and a robust simulated portfolio management system.

## 🌟 Key Features

*   **Real-Time Data Engine:** Live stock quotes and historical data powered by `yfinance`, optimized with Streamlit caching.
*   **AI Trend Predictions:** Utilizes a Scikit-Learn Logistic Regression model trained on technical indicators (RSI & MACD) to forecast market trends.
*   **Portfolio Management:** Simulate trades, track cost-basis, and monitor real-time Profit/Loss (P/L) securely within your browser's session state.
*   **Asset Allocation:** Interactive Plotly donut charts to visualize portfolio diversity.
*   **Market News:** Seamless integration with financial news APIs to deliver the latest breaking headlines.
*   **Modern Fintech UI:** Responsive dark-mode aesthetics modeled after professional trading terminals.

## 🛠️ Installation & Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nexus-finance.git
   cd nexus-finance
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 🚀 Deployment (Streamlit Cloud)

This app is ready for one-click deployment on Streamlit Community Cloud:
1. Push this repository to your GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io/).
3. Click **New App**, connect your GitHub, and select the `app.py` file.
4. Click **Deploy!**

## 📚 Technologies Used
*   **Frontend:** Streamlit, Custom CSS
*   **Data & Finance:** pandas, numpy, yfinance, ta (Technical Analysis)
*   **Machine Learning:** scikit-learn
*   **Visualization:** Plotly (Graph Objects & Express)

## 📄 License
This project is for educational and portfolio purposes. Not intended for actual financial advice or trading.
