import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import traceback

from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector

# --- PAGE CONFIG ---
st.set_page_config(page_title="Quantum Analytics", layout="wide")

st.title("⚛️ Quantum Equity Research Engine")

# --- SIDEBAR ---
selected_ticker = st.sidebar.text_input("Ticker Symbol:", "AAPL").upper().strip()
forecast_days = st.sidebar.slider("Horizon (Days):", 7, 90, 30)
num_qubits = st.sidebar.slider("Qubits:", 4, 10, 8)
shots = st.sidebar.selectbox("Shots:", [10000, 30000, 50000], index=1)

# --- ENGINE ---
@st.cache_data(ttl=3600)
def run_quantum_engine(ticker, days, qubits, measurement_shots):
    df_hist = yf.Ticker(ticker).history(period="1y")
    
    if df_hist.empty or 'Close' not in df_hist.columns:
        return None
        
    close_prices = df_hist['Close'].dropna()
    log_returns = np.log(close_prices / close_prices.shift(1)).dropna()
    
    S0 = float(close_prices.iloc[-1])
    mu = float(log_returns.mean())
    sigma = float(log_returns.std())
    
    dt = days / 252
    num_states = 2**qubits
    
    min_p = S0 * np.exp((mu - 0.5 * sigma**2) * dt - 3 * sigma * np.sqrt(dt))
    max_p = S0 * np.exp((mu - 0.5 * sigma**2) * dt + 3 * sigma * np.sqrt(dt))
    price_grid = np.linspace(min_p, max_p, num_states)
    pct_grid = ((price_grid - S0) / S0) * 100
    
    probs = np.exp(- (np.log(price_grid / S0) - (mu - 0.5 * sigma**2) * dt)**2 / (2 * (sigma * np.sqrt(dt))**2))
    probs /= np.sum(probs)
    
    # Qiskit Logic
    qc = QuantumCircuit(qubits)
    qc.initialize(np.sqrt(probs), range(qubits))
    counts = Statevector.from_instruction(qc).sample_counts(shots=measurement_shots)
    
    quantum_probs = np.zeros(num_states)
    for bitstring, count in counts.items():
        quantum_probs[int(bitstring, 2)] = count / measurement_shots
        
    return {
        'S0': S0, 'price_grid': price_grid, 'pct_grid': pct_grid, 
        'quantum_probs': quantum_probs, 'ann_vol': sigma * np.sqrt(252) * 100
    }

# --- EXECUTION ---
if st.button("Run Simulation"):
    try:
        data = run_quantum_engine(selected_ticker, forecast_days, num_qubits, shots)
        
        if data is None:
            st.error(f"Error: Could not fetch data for {selected_ticker}. Check if it's delisted.")
        else:
            st.success("Simulation Complete")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Current Price", f"${data['S0']:.2f}")
            with col2:
                st.metric("Annual Volatility", f"{data['ann_vol']:.1f}%")
                
            fig, ax = plt.subplots()
            ax.plot(data['pct_grid'], data['quantum_probs'])
            st.pyplot(fig)
            
            st.dataframe(pd.DataFrame({'Price': data['price_grid'], 'Prob': data['quantum_probs']}), width='stretch')
            
    except Exception as e:
        st.error("An unexpected error occurred.")
        with st.expander("Details"):
            st.code(traceback.format_exc())
