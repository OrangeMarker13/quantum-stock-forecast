import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import traceback
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

# --- PAGE CONFIG ---
st.set_page_config(page_title="Quantum Analytics", layout="wide")

st.title("⚛️ Quantum Equity Research & Risk Analytics Engine")

# --- SIDEBAR ---
st.sidebar.header("🛠️ Simulation Controls")
popular_tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "SPY", "QQQ"]
selected_ticker = st.sidebar.selectbox("Select Asset:", options=popular_tickers, index=0)
forecast_days = st.sidebar.slider("Horizon (Days):", 7, 90, 30)
num_qubits = st.sidebar.select_slider("Resolution (Qubits):", options=[4, 6, 8], value=6)
shots = st.sidebar.selectbox("Measurement Shots:", [10000, 30000, 50000], index=1)

# --- ENGINE ---
@st.cache_data(ttl=3600)
def run_quantum_engine(ticker, days, qubits, measurement_shots):
    df = yf.Ticker(ticker).history(period="1y")
    if df.empty: return None
    
    close = df['Close'].dropna()
    log_ret = np.log(close / close.shift(1)).dropna()
    S0, mu, sigma = float(close.iloc[-1]), float(log_ret.mean()), float(log_ret.std())
    
    dt = days / 252
    num_states = 2**qubits
    price_grid = np.linspace(S0 * 0.8, S0 * 1.2, num_states)
    pct_grid = ((price_grid - S0) / S0) * 100
    
    # Probability distribution
    probs = np.exp(- (np.log(price_grid / S0) - (mu - 0.5 * sigma**2) * dt)**2 / (2 * (sigma * np.sqrt(dt))**2))
    probs /= np.sum(probs)
    
    # Quantum Simulation
    qc = QuantumCircuit(qubits)
    qc.initialize(np.sqrt(probs), range(qubits))
    counts = Statevector.from_instruction(qc).sample_counts(shots=measurement_shots)
    
    quantum_probs = np.zeros(num_states)
    for bitstring, count in counts.items():
        quantum_probs[int(bitstring, 2)] = count / measurement_shots
        
    return {'S0': S0, 'price_grid': price_grid, 'pct_grid': pct_grid, 
            'quantum_probs': quantum_probs, 'ann_vol': sigma * np.sqrt(252) * 100}

# --- UI EXECUTION ---
data = run_quantum_engine(selected_ticker, forecast_days, num_qubits, shots)

if data:
    # Metric Row
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Price", f"${data['S0']:.2f}")
    c2.metric("Annual Volatility", f"{data['ann_vol']:.1f}%")
    c3.metric("Resolution", f"{2**num_qubits} States")

    # Tabs
    t1, t2 = st.tabs(["📊 Probability Density", "📑 Raw Data"])
    with t1:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.fill_between(data['pct_grid'], data['quantum_probs'], alpha=0.5)
        ax.set_title(f"Quantum Outcome Distribution for {selected_ticker}")
        st.pyplot(fig)
    with t2:
        st.dataframe(pd.DataFrame({'Price': data['price_grid'], 'Prob': data['quantum_probs']}), width='stretch')
else:
    st.error("Could not retrieve data.")
