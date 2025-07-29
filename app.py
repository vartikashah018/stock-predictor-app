import streamlit as st
from auth import validate_login, add_user, create_users_table
from predict import predict_stock
import yfinance as yf

# ----------------------- Config & Setup -----------------------
st.set_page_config(page_title="📈 Stock Price Predictor", layout="wide")
st.title("📉 Stock Price Predictor (INR)")
create_users_table()  # Ensure DB table exists

# ----------------------- Session State Init -----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ----------------------- Sidebar: Login/Signup -----------------------
st.sidebar.title("🔐 Login / Signup")

if not st.session_state.logged_in:
    login_tab, signup_tab = st.sidebar.tabs(["Login", "Signup"])

    with login_tab:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("🔓 Login", key="login_button"):
            if validate_login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"✅ Welcome back, {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

    with signup_tab:
        new_user = st.text_input("Choose a username", key="signup_user")
        new_pass = st.text_input("Choose a password", type="password", key="signup_pass")
        if st.button("📝 Signup", key="signup_button"):
            if add_user(new_user, new_pass):
                st.success("✅ Account created! Please log in.")
            else:
                st.warning("⚠️ Username already exists. Try another.")

# ----------------------- Logged-In User Interface -----------------------
if st.session_state.logged_in:
    st.sidebar.success(f"👤 Logged in as: {st.session_state.username}")
    if st.sidebar.button("🚪 Logout", key="logout_button"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()

    # Navigation
    nav_choice = st.sidebar.selectbox("📚 Navigate", ["🔮 Predict", "👤 Profile", "⚙️ Settings"], key="nav_choice")

    # Ticker helper data
    nifty_tickers = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS",
        "ITC.NS", "ICICIBANK.NS", "WIPRO.NS", "POWERGRID.NS", "TATAMOTORS.NS"
    ]

    @st.cache_data(ttl=600)
    def get_sorted_tickers(tickers, sort_order="asc"):
        try:
            data = yf.download(tickers, period="1d", group_by='ticker', threads=True, progress=False)
            ticker_prices = {}
            for ticker in tickers:
                try:
                    last_price = data[ticker]['Close'].iloc[-1]
                    ticker_prices[ticker] = round(last_price, 2)
                except Exception:
                    continue
            sorted_tickers = sorted(ticker_prices.items(), key=lambda x: x[1], reverse=(sort_order == "desc"))
            return sorted_tickers
        except Exception as e:
            st.error(f"Error fetching ticker prices: {e}")
            return []

    with st.expander("💡 Need help picking a stock?"):
        sort_choice = st.radio("Sort by price:", ["Cheapest First", "Costliest First"], horizontal=True)
        order = "asc" if sort_choice == "Cheapest First" else "desc"
        sorted_tickers = get_sorted_tickers(nifty_tickers, order)
        st.markdown("### 📈 Ticker Suggestions:")
        for ticker, price in sorted_tickers:
            st.markdown(f"- `{ticker}` → ₹{price}")

    # ----------------- Predict Page -----------------
    if nav_choice == "🔮 Predict":
        st.subheader("🔍 Predict Stock Closing Price")
        st.markdown("Enter the stock ticker and number of years to predict future price (converted to ₹ INR).")

        ticker = st.text_input("Enter stock ticker (e.g. AAPL, TSLA, INFY.NS)", value="AAPL", key="predict_ticker")
        years = st.slider("Select number of years of historical data", 1, 10, 5, key="predict_years")

        # Suggestions based on input
        if ticker.strip().upper() == "AAPL":
            st.info("💡 Apple Inc. (AAPL) is one of the most traded US stocks.")
        elif ticker.strip().upper() == "TSLA":
            st.info("💡 Tesla, Inc. (TSLA) is a highly volatile stock – expect unpredictable predictions.")
        elif ticker.strip().upper().endswith(".NS"):
            st.info("💡 You've entered a NSE India ticker – converted prediction will be in INR.")
        else:
            st.info("💡 Enter a valid ticker (e.g. 'MSFT', 'GOOG', or 'RELIANCE.NS').")

        if st.button("🔮 Predict", key="predict_button"):
            predict_stock(ticker, years)

    # ----------------- Profile Page -----------------
    elif nav_choice == "👤 Profile":
        st.subheader("👤 Your Profile")
        st.markdown(f"**Username:** `{st.session_state.username}`")
        st.markdown("📅 More profile features coming soon (edit details, saved predictions, etc).")

    # ----------------- Settings Page -----------------
    elif nav_choice == "⚙️ Settings":
        st.subheader("⚙️ App Settings")
        st.markdown("🌙 **Dark mode** is enabled by default.")
        st.markdown("📂 Additional configurations will be added here.")