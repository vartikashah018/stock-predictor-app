import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
import streamlit as st
from io import BytesIO

def fetch_usd_to_inr():
    try:
        fx_data = yf.Ticker("USDINR=X").history(period="1d")
        rate = fx_data["Close"].iloc[-1]
        return rate
    except:
        st.error("❌ Failed to fetch USD to INR exchange rate.")
        return None

def predict_stock(ticker, years):
    df = yf.Ticker(ticker).history(period=f"{years}y")
    if df.empty:
        st.error("❌ Invalid ticker or no data found. Try a different one.")
        return

    # Fetch USD to INR conversion rate
    exchange_rate = fetch_usd_to_inr()
    if exchange_rate is None:
        return

    # Scale and prepare data
    data = df['Close'].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)

    train_size = int(len(scaled_data) * 0.8)
    train_data = scaled_data[:train_size]

    X_train, y_train = [], []
    for i in range(60, len(train_data)):
        X_train.append(train_data[i - 60:i])
        y_train.append(train_data[i])
    X_train, y_train = np.array(X_train), np.array(y_train)

    # LSTM model
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(LSTM(50))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, y_train, epochs=5, batch_size=64, verbose=0)

    # Prepare test data
    test_data = scaled_data[train_size - 60:]
    X_test = []
    for i in range(60, len(test_data)):
        X_test.append(test_data[i - 60:i])
    X_test = np.array(X_test)

    predictions = model.predict(X_test)
    predictions = scaler.inverse_transform(predictions)
    actual = data[train_size:]

    # Convert both to INR
    actual_inr = actual * exchange_rate
    predictions_inr = predictions * exchange_rate

    # Plot results
    st.subheader("📊 Actual vs Predicted Closing Prices (INR)")
    fig, ax = plt.subplots()
    ax.plot(actual_inr, label="Actual Price (INR)", linewidth=2)
    ax.plot(predictions_inr, label="Predicted Price (INR)", linewidth=2)
    ax.set_xlabel("Time")
    ax.set_ylabel("Price (₹ INR)")
    ax.legend()

    st.pyplot(fig)

    # Downloadable plot
    buf = BytesIO()
    fig.savefig(buf, format="png")
    st.download_button("📥 Download Plot as PNG", buf.getvalue(), file_name="stock_prediction_inr.png", mime="image/png")
        # Buy/Sell Suggestion
    last_actual_price = actual_inr[-1][0]
    last_predicted_price = predictions_inr[-1][0]
    
    st.subheader("💡 Suggestion")

    if last_predicted_price > last_actual_price * 1.02:
        st.success(f"📈 Suggestion: BUY\n\nPredicted price ₹{last_predicted_price:.2f} is **higher** than current ₹{last_actual_price:.2f}.")
    elif last_predicted_price < last_actual_price * 0.98:
        st.error(f"📉 Suggestion: SELL\n\nPredicted price ₹{last_predicted_price:.2f} is **lower** than current ₹{last_actual_price:.2f}.")
    else:
        st.info(f"📊 Suggestion: HOLD\n\nPredicted price ₹{last_predicted_price:.2f} is **close** to current ₹{last_actual_price:.2f}.")