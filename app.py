import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator

# --- STREAMLIT PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Quantum Stock Forecast & Risk Analytics",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished financial styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-left: 5px solid #1f77b4;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# --- APP HEADER ---
st.title("⚛️ Quantum Equity Research & Risk Analytics Engine")
st.markdown("""
This platform uses **Qiskit Aer Matrix Product State (MPS)** tensor network simulators to model asset price paths via **High-Qubit Quantum Monte Carlo**. 
By encoding probability amplitudes across scaled qubit registers, we evaluate projected price targets and downside tail-risk metrics.
""")

st.divider()

# --- SIDEBAR INTERACTIVE CONTROLS ---
st.sidebar.header("🛠️ Simulation Controls")

popular_tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", 
    "BRK-B", "JPM", "V", "UNH", "PG", "MA", "HD", "DIS", 
    "NFLX", "AMD", "COIN", "SPY", "QQQ", "^GSPC", "BTC-USD"
]

33 selected_ticker = st.sidebar.selectbox(
34     "Select or Type Target Asset Ticker:",
35     options=popular_tickers,
36     index=0,
37     accept_new_options=True
38 ).upper().strip()

39 # Validate ticker before running engine
40 test_df = yf.download(selected_ticker, period="1y", progress=False)
41 if test_df.empty:
42     st.sidebar.error(f"❌ '{selected_ticker}' is not a valid Yahoo Finance ticker.")
43     st.stop()

# NEW: User-controlled forecast days
forecast_days = st.sidebar.slider(
    "Forecast Time Horizon (Days):",
    min_value=1,
    max_value=30,
    value=30
)

# NEW: User-controlled qubit count
num_qubits = st.sidebar.slider(
    "Quantum Register Resolution (Qubits):",
    min_value=2,
    max_value=16,
    value=16
)

shots = st.sidebar.selectbox("Quantum Measurement Shots:", [10000, 30000, 50000], index=1)

# Optional safety warning
if num_qubits > 14 and shots > 30000:
    st.sidebar.warning("High qubit count + high shots may slow down simulation.")

run_button = st.sidebar.button("⚡ Run Quantum Analysis", type="primary", width="stretch")

# --- QUANTUM SIMULATION ENGINE ---
@st.cache_data(ttl=3600)
def run_quantum_engine(ticker, days, qubits, measurement_shots):
    df = yf.download(ticker, period="1y", progress=False)['Close']
    
    if df.empty:
        raise ValueError(f"No pricing data found for symbol '{ticker}'.")
        
    log_returns = np.log(df / df.shift(1)).dropna()
    
    S0 = float(df.iloc[-1])
    mu = float(log_returns.mean())
    sigma = float(log_returns.std())

    ann_vol = sigma * np.sqrt(252) * 100
    
    dt = days / 252
    num_states = 2**qubits
    
    min_price = S0 * np.exp((mu - 0.5 * sigma**2) * dt - 3 * sigma * np.sqrt(dt))
    max_price = S0 * np.exp((mu - 0.5 * sigma**2) * dt + 3 * sigma * np.sqrt(dt))
    price_grid = np.linspace(min_price, max_price, num_states)
    pct_grid = ((price_grid - S0) / S0) * 100
    
    drift = (mu - 0.5 * sigma**2) * dt
    scale = sigma * np.sqrt(dt)
    probs = np.exp(- (np.log(price_grid / S0) - drift)**2 / (2 * scale**2))
    probs /= np.sum(probs)
    
    qreg = QuantumRegister(qubits, 'q')
    creg = ClassicalRegister(qubits, 'c')
    qc = QuantumCircuit(qreg, creg)

    # Proper amplitude encoding of full probability distribution
    qc.initialize(np.sqrt(probs), qreg)
    qc.measure(qreg, creg)

    
    # Configure Matrix Product State (MPS) Tensor Network Backend
    backend = AerSimulator(
        method='matrix_product_state',
        matrix_product_state_truncation_threshold=1e-6
    )
    job = backend.run(qc, shots=measurement_shots)
    counts = job.result().get_counts()
    
    quantum_probs = np.zeros(num_states)
    for bitstring, count in counts.items():
        quantum_probs[int(bitstring, 2)] = count / measurement_shots
        
    expected_price = np.sum(price_grid * quantum_probs)
    expected_pct = ((expected_price - S0) / S0) * 100
    
    cdf = np.cumsum(quantum_probs)
    var_95_idx = np.searchsorted(cdf, 0.05)
    var_95_pct = pct_grid[var_95_idx]
    var_95_price = price_grid[var_95_idx]
    
    tail_probs = quantum_probs[:var_95_idx+1]
    tail_prices = price_grid[:var_95_idx+1]
    expected_tail_loss = np.sum(tail_prices * tail_probs) / np.sum(tail_probs) if np.sum(tail_probs) > 0 else var_95_price
    etl_pct = ((expected_tail_loss - S0) / S0) * 100

    prob_up_5 = np.sum(quantum_probs[pct_grid >= 5.0]) * 100
    prob_down_5 = np.sum(quantum_probs[pct_grid <= -5.0]) * 100
    prob_positive = np.sum(quantum_probs[pct_grid >= 0.0]) * 100

    return {
        'S0': S0, 'mu': mu, 'sigma': sigma, 'ann_vol': ann_vol,
        'price_grid': price_grid, 'pct_grid': pct_grid, 'quantum_probs': quantum_probs,
        'expected_price': expected_price, 'expected_pct': expected_pct,
        'var_95_pct': var_95_pct, 'var_95_price': var_95_price,
        'etl_pct': etl_pct, 'expected_tail_loss': expected_tail_loss,
        'prob_up_5': prob_up_5, 'prob_down_5': prob_down_5, 'prob_positive': prob_positive,
        'df': df, 'cdf': cdf
    }

# Safe Execution Engine Call
try:
    data = run_quantum_engine(selected_ticker, forecast_days, num_qubits, shots)
except Exception as e:
    st.error(f"❌ **Error loading ticker '{selected_ticker}':** Please verify that the symbol is valid on Yahoo Finance (e.g., AAPL, NVDA, SPY, BTC-USD).")
    st.stop()

# --- TOP SUMMARY METRICS CARD ---
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Current Price", f"${data['S0']:.2f}")
col2.metric(f"{forecast_days}-Day Quantum Target", f"${data['expected_price']:.2f}", f"{data['expected_pct']:+.2f}%")
col3.metric("Annualized Volatility", f"{data['ann_vol']:.1f}%")
col4.metric("95% Value at Risk (VaR)", f"{data['var_95_pct']:.2f}%")
col5.metric("Win Probability (>0%)", f"{data['prob_positive']:.1f}%")

st.divider()

# --- MULTI-TAB DETAILED ANALYSIS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Forecast Trajectory", 
    "📈 Risk & Probability Distribution", 
    "📑 Executive Report & Signal", 
    "📜 Raw Simulation Data"
])

# TAB 1: TRAJECTORY FAN CHART
with tab1:
    st.subheader(f"{forecast_days}-Day Cone of Uncertainty ({selected_ticker})")
    
    time_axis = np.arange(0, forecast_days + 1)
    pcts = [0.05, 0.20, 0.35, 0.50, 0.65, 0.80, 0.95]
    vals_target = [((data['price_grid'][np.searchsorted(data['cdf'], p)] - data['S0']) / data['S0']) * 100 for p in pcts]
    time_factor = np.sqrt(time_axis / forecast_days)
    
    p5, p20, p35, p50, p65, p80, p95 = [v * time_factor for v in vals_target]
    
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.fill_between(time_axis, p35, p65, color='#1f77b4', alpha=0.6, label='High Probability Core (30%)')
    ax.fill_between(time_axis, p20, p35, color='#1f77b4', alpha=0.35)
    ax.fill_between(time_axis, p65, p80, color='#1f77b4', alpha=0.35)
    ax.fill_between(time_axis, p5,  p20, color='#1f77b4', alpha=0.15, label='Extreme Tails (5%-95%)')
    ax.fill_between(time_axis, p80, p95, color='#1f77b4', alpha=0.15)
    
    ax.plot(time_axis, p50, color='#0a385c', linewidth=2.5, label='Median Path')
    ax.axhline(0, color='red', linestyle='--', alpha=0.7)
    ax.plot(0, 0, marker='o', color='red', markersize=6)
    
    ax.set_ylabel("Projected Return (%)")
    ax.set_xlabel("Days Ahead")
    ax.grid(True, alpha=0.25)
    ax.legend(loc='upper left')
    st.pyplot(fig)

# TAB 2: PROBABILITY & RISK
with tab2:
    st.subheader("Quantum Probability Density & Risk Metrics")
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.plot(data['pct_grid'], data['quantum_probs'], color='#1f77b4', linewidth=2)
        ax2.fill_between(data['pct_grid'], data['quantum_probs'], color='#1f77b4', alpha=0.3)
        ax2.axvline(data['expected_pct'], color='green', linestyle='-', label=f"Expected: {data['expected_pct']:+.2f}%")
        ax2.axvline(data['var_95_pct'], color='red', linestyle='--', label=f"95% VaR: {data['var_95_pct']:.2f}%")
        ax2.set_xlabel("Projected Price Change (%)")
        ax2.set_ylabel("Quantum Probability Mass")
        ax2.grid(True, alpha=0.25)
        ax2.legend()
        st.pyplot(fig2)
        
    with col_b:
        st.markdown("### Risk Breakdown")
        st.write(f"**Expected Price Target:** ${data['expected_price']:.2f}")
        st.write(f"**95% Value at Risk (Dollar):** -${abs((data['var_95_price'] - data['S0'])):.2f}")
        st.write(f"**Expected Tail Loss (ETL):** {data['etl_pct']:.2f}%")
        st.write(f"**Probability of Gain > +5%:** {data['prob_up_5']:.1f}%")
        st.write(f"**Probability of Loss > -5%:** {data['prob_down_5']:.1f}%")

# TAB 3: EXECUTIVE SUMMARY REPORT
with tab3:
    st.subheader(f"Automated Quantum Equity Report: {selected_ticker}")
    
    if data['expected_pct'] > 1.5 and data['prob_positive'] > 55:
        signal = "🟢 BULLISH OUTLOOK"
        signal_desc = f"The Quantum Monte Carlo register exhibits positive distribution drift, indicating favorable risk-adjusted upside potential over the {forecast_days}-day horizon."
    elif data['expected_pct'] < -1.5 or data['prob_down_5'] > 30:
        signal = "🔴 BEARISH / CAUTION"
        signal_desc = "The simulation indicates downside skew and elevated tail-risk. Investors should consider hedging exposure."
    else:
        signal = "🟡 NEUTRAL / CONSOLIDATION"
        signal_desc = "The forecast distribution remains tightly clustered around current levels with symmetric variance."

    st.markdown(f"### Overall Assessment: **{signal}**")
    st.info(signal_desc)
    
    st.markdown("#### Key Takeaways for Traders & Analysts")
    st.write(f"1. **Volatility Environment:** {selected_ticker} exhibits an annualized volatility of **{data['ann_vol']:.1f}%**. This translates to a {forecast_days}-day projected standard deviation spread of **±{data['ann_vol']/np.sqrt(12):.1f}%**.")
    st.write(f"2. **Asymmetry Ratio:** The probability of experiencing a **+5% rally ({data['prob_up_5']:.1f}%)** versus a **-5% decline ({data['prob_down_5']:.1f}%)** yields a risk-reward skew factor of **{(data['prob_up_5']/(data['prob_down_5']+1e-5)):.2f}**.")

# TAB 4: RAW DATA
with tab4:
    st.subheader("Raw Output Matrix (Quantum Bins)")
    df_raw = pd.DataFrame({
        "Price Outcome ($)": data['price_grid'],
        "Return (%)": data['pct_grid'],
        "Quantum Probability Mass": data['quantum_probs'],
        "Cumulative Probability (CDF)": data['cdf']
    })
    st.dataframe(df_raw, width="stretch")

