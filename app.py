import traceback
import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

# --- QISKIT CORE IMPORTS (Pure Python Backend - No Aer Build Crashes) ---
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Statevector

# --- STREAMLIT PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Quantum Stock Forecast & Risk Analytics",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
This platform constructs **Qiskit Quantum Circuits** to encode asset price probabilities via **Quantum Statevector Amplitude Encoding** and **Quantum Measurement Sampling**.
""")

st.divider()

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🛠️ Simulation Controls")

popular_tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", 
    "BRK-B", "JPM", "V", "UNH", "PG", "MA", "HD", "DIS", 
    "NFLX", "AMD", "COIN", "SPY", "QQQ", "^GSPC", "BTC-USD"
]

selected_ticker = st.sidebar.selectbox(
    "Select or Type Target Asset Ticker:",
    options=popular_tickers,
    index=0,
    accept_new_options=True
).upper().strip()

forecast_days = st.sidebar.slider("Forecast Time Horizon (Days):", min_value=7, max_value=90, value=30)

# Capped safely at 10 qubits for pure-python quantum statevector calculation
num_qubits = st.sidebar.select_slider(
    "Quantum Register Resolution (Qubits):", 
    options=[4, 6, 8, 10], 
    value=8,
    help="Determines the length of the quantum register (2^N states)."
)

shots = st.sidebar.selectbox("Quantum Measurement Shots:", [10000, 30000, 50000], index=1)

# --- QUANTUM SIMULATION ENGINE (QISKIT STATEVECTOR) ---
@st.cache_data(ttl=3600)
def run_quantum_engine(ticker, days, qubits, measurement_shots):
    # 1. Fetch Price Data
    ticker_data = yf.Ticker(ticker)
    df_hist = ticker_data.history(period="1y")
    
    if df_hist.empty or 'Close' not in df_hist.columns:
        raise ValueError(f"No pricing data found for symbol '{ticker}'. Verify ticker on Yahoo Finance.")
        
    close_prices = df_hist['Close'].dropna()
    if len(close_prices) < 30:
        raise ValueError(f"Insufficient historical data for symbol '{ticker}'.")

    log_returns = np.log(close_prices / close_prices.shift(1)).dropna()
    
    S0 = float(close_prices.iloc[-1])
    mu = float(log_returns.mean())
    sigma = float(log_returns.std())
    ann_vol = sigma * np.sqrt(252) * 100
    
    dt = days / 252
    num_states = 2**qubits
    
    # 2. Price Grid & Target Amplitude Setup
    min_price = S0 * np.exp((mu - 0.5 * sigma**2) * dt - 3 * sigma * np.sqrt(dt))
    max_price = S0 * np.exp((mu - 0.5 * sigma**2) * dt + 3 * sigma * np.sqrt(dt))
    price_grid = np.linspace(min_price, max_price, num_states)
    pct_grid = ((price_grid - S0) / S0) * 100
    
    drift = (mu - 0.5 * sigma**2) * dt
    scale = sigma * np.sqrt(dt)
    if scale == 0:
        scale = 1e-6
        
    probs = np.exp(- (np.log(price_grid / S0) - drift)**2 / (2 * scale**2))
    probs /= np.sum(probs)
    amplitudes = np.sqrt(probs)
    amplitudes /= np.linalg.norm(amplitudes) # Normalize quantum state

    # 3. Construct Qiskit Quantum Circuit
    qreg = QuantumRegister(qubits, 'q')
    qc = QuantumCircuit(qreg)
    
    # Initialize quantum register with amplitude distribution
    qc.initialize(amplitudes, qreg)
    
    # Evolve & Measure Quantum Statevector
    statevector = Statevector.from_instruction(qc)
    measurement_dict = statevector.sample_counts(shots=measurement_shots)
    
    quantum_probs = np.zeros(num_states)
    for bitstring, count in measurement_dict.items():
        state_index = int(bitstring, 2)
        if state_index < num_states:
            quantum_probs[state_index] = count / measurement_shots
            
    # Normalize probabilities
    if np.sum(quantum_probs) > 0:
        quantum_probs /= np.sum(quantum_probs)
    else:
        quantum_probs = probs

    # 4. Compute Financial Metrics
    expected_price = np.sum(price_grid * quantum_probs)
    expected_pct = ((expected_price - S0) / S0) * 100
    
    cdf = np.cumsum(quantum_probs)
    var_95_idx = np.searchsorted(cdf, 0.05)
    var_95_idx = min(var_95_idx, len(pct_grid) - 1)
    
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
        'df': close_prices, 'cdf': cdf, 'qubits': qubits
    }

# Safe Execution Engine Call with Debug Catching
try:
    with st.spinner(f"Running Qiskit Quantum Circuit Simulation for {selected_ticker}..."):
        data = run_quantum_engine(selected_ticker, forecast_days, num_qubits, shots)
except Exception as e:
    st.error(f"❌ **Simulation Error:** {str(e)}")
    with st.expander("🔍 Click to view technical error traceback"):
        st.code(traceback.format_exc())
    st.stop()

# --- SUMMARY METRICS ---
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Current Price", f"${data['S0']:.2f}")
col2.metric(f"{forecast_days}-Day Target", f"${data['expected_price']:.2f}", f"{data['expected_pct']:+.2f}%")
col3.metric("Annualized Volatility", f"{data['ann_vol']:.1f}%")
col4.metric("95% Value at Risk", f"{data['var_95_pct']:.2f}%")
col5.metric("Win Probability", f"{data['prob_positive']:.1f}%")

st.divider()

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Forecast Trajectory", "📈 Quantum Probability Density", "📑 Executive Summary"])

with tab1:
    st.subheader(f"{forecast_days}-Day Quantum Cone of Uncertainty ({selected_ticker})")
    time_axis = np.arange(0, forecast_days + 1)
    pcts = [0.05, 0.20, 0.35, 0.50, 0.65, 0.80, 0.95]
    vals_target = [((data['price_grid'][min(np.searchsorted(data['cdf'], p), len(data['price_grid'])-1)] - data['S0']) / data['S0']) * 100 for p in pcts]
    time_factor = np.sqrt(time_axis / forecast_days)
    
    p5, p20, p35, p50, p65, p80, p95 = [v * time_factor for v in vals_target]
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(time_axis, p35, p65, color='#1f77b4', alpha=0.6, label='Core Range (30%)')
    ax.fill_between(time_axis, p5, p95, color='#1f77b4', alpha=0.15, label='Tail Range (90%)')
    ax.plot(time_axis, p50, color='#0a385c', linewidth=2, label='Median Target')
    ax.axhline(0, color='red', linestyle='--', alpha=0.7)
    ax.set_ylabel("Projected Return (%)")
    ax.set_xlabel("Days Ahead")
    ax.grid(True, alpha=0.2)
    ax.legend(loc='upper left')
    st.pyplot(fig)

with tab2:
    st.subheader(f"Qiskit Circuit Output ({data['qubits']} Qubits = {2**data['qubits']} Discrete States)")
    fig2, ax2 = plt.subplots(figsize=(8, 3.5))
    ax2.plot(data['pct_grid'], data['quantum_probs'], color='#1f77b4', linewidth=2)
    ax2.fill_between(data['pct_grid'], data['quantum_probs'], color='#1f77b4', alpha=0.3)
    ax2.axvline(data['expected_pct'], color='green', linestyle='-', label=f"Expected Target: {data['expected_pct']:+.2f}%")
    ax2.axvline(data['var_95_pct'], color='red', linestyle='--', label=f"95% VaR: {data['var_95_pct']:.2f}%")
    ax2.set_xlabel("Return (%)")
    ax2.set_ylabel("Quantum Probability Mass")
    ax2.grid(True, alpha=0.2)
    ax2.legend()
    st.pyplot(fig2)

with tab3:
    st.markdown(f"### Qiskit Analysis for **{selected_ticker}**")
    st.write(f"- **Expected Return:** {data['expected_pct']:+.2f}%")
    st.write(f"- **Annualized Volatility:** {data['ann_vol']:.1f}%")
    st.write(f"- **95% Value-at-Risk:** {data['var_95_pct']:.2f}%")
    st.write(f"- **Probability of Upside (>0%):** {data['prob_positive']:.1f}%")
