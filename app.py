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

# --- APP HEADER ---
st.title("⚛️ Quantum Equity Research & Risk Analytics Engine")
st.markdown("Modeling asset price paths via High-Qubit Quantum Monte Carlo.")
st.divider()

# --- SIDEBAR ---
selected_ticker = st.sidebar.text_input("Enter Asset Ticker:", value="AAPL").upper().strip()
forecast_days = 30
num_qubits = 16
shots = st.sidebar.selectbox("Quantum Measurement Shots:", [10000, 30000, 50000], index=1)

# --- QUANTUM ENGINE ---
@st.cache_data(ttl=3600)
def run_quantum_engine(ticker, days, qubits, measurement_shots):
    # Fetch data
    df_raw = yf.download(ticker, period="1y", progress=False)
    
    # Validation Check
    if df_raw.empty or 'Close' not in df_raw.columns:
        return None
    
    # Ensure 1D series
    df = df_raw['Close'].squeeze()
    log_returns = np.log(df / df.shift(1)).dropna()
    
    S0 = float(df.iloc[-1])
    mu = float(log_returns.mean())
    sigma = float(log_returns.std())
    ann_vol = sigma * np.sqrt(252) * 100
    
    dt = days / 252
    num_states = 2**qubits
    
    # Simulation Logic
    price_grid = np.linspace(S0 * 0.8, S0 * 1.2, num_states)
    pct_grid = ((price_grid - S0) / S0) * 100
    drift = (mu - 0.5 * sigma**2) * dt
    scale = sigma * np.sqrt(dt)
    
    probs = np.exp(- (np.log(price_grid / S0) - drift)**2 / (2 * scale**2))
    probs /= np.sum(probs)
    
    # Qiskit Circuit
    qc = QuantumCircuit(qubits, qubits)
    qc.h(range(qubits))
    qc.ry(2 * np.arcsin(np.sqrt(probs)), range(qubits))
    qc.measure(range(qubits), range(qubits))
    
    backend = AerSimulator(method='matrix_product_state')
    counts = backend.run(qc, shots=measurement_shots).result().get_counts()
    
    quantum_probs = np.zeros(num_states)
    for bitstring, count in counts.items():
        quantum_probs[int(bitstring, 2)] = count / measurement_shots
        
    expected_price = np.sum(price_grid * quantum_probs)
    
    return {
        'S0': S0, 'ann_vol': ann_vol, 'price_grid': price_grid, 
        'pct_grid': pct_grid, 'quantum_probs': quantum_probs, 
        'expected_price': expected_price, 'expected_pct': ((expected_price - S0) / S0) * 100
    }

# --- EXECUTION ---
data = run_quantum_engine(selected_ticker, forecast_days, num_qubits, shots)

if data:
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Price", f"${data['S0']:.2f}")
    c2.metric("Target Price", f"${data['expected_price']:.2f}", f"{data['expected_pct']:.2f}%")
    c3.metric("Annual Volatility", f"{data['ann_vol']:.1f}%")
    
    fig, ax = plt.subplots()
    ax.bar(data['pct_grid'], data['quantum_probs'])
    st.pyplot(fig)
else:
    st.error(f"❌ No data found for **{selected_ticker}**. Please check the ticker symbol (e.g., AAPL, NVDA, BTC-USD).")
