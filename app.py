import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

# --- PAGE CONFIG ---
st.set_page_config(page_title="Quantum Equity Analytics", layout="wide")
st.title("⚛️ Quantum Equity Research & Risk Analytics Engine")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🛠️ Simulation Controls")

# Searchable Ticker Input
ticker_input = st.sidebar.text_input("Enter Ticker (e.g., AAPL, NVDA, BTC-USD):", "AAPL").upper().strip()
forecast_days = st.sidebar.slider("Forecast Horizon (Days):", 7, 90, 30)
num_qubits = st.sidebar.select_slider("Resolution (Qubits):", options=[4, 6, 8], value=6)
shots = st.sidebar.selectbox("Measurement Shots:", [10000, 30000, 50000], index=1)

# --- QUANTUM ENGINE ---
@st.cache_data(ttl=3600)
def run_quantum_engine(ticker, days, qubits, shots):
    df = yf.Ticker(ticker).history(period="1y")
    if df.empty: return None
    
    close = df['Close'].dropna()
    log_ret = np.log(close / close.shift(1)).dropna()
    S0, mu, sigma = float(close.iloc[-1]), float(log_ret.mean()), float(log_ret.std())
    
    dt = days / 252
    num_states = 2**qubits
    
    # Pricing Grid
    min_p = S0 * np.exp((mu - 0.5 * sigma**2) * dt - 3 * sigma * np.sqrt(dt))
    max_p = S0 * np.exp((mu - 0.5 * sigma**2) * dt + 3 * sigma * np.sqrt(dt))
    price_grid = np.linspace(min_p, max_p, num_states)
    pct_grid = ((price_grid - S0) / S0) * 100
    
    # Probability Amplitude Initialization
    probs = np.exp(- (np.log(price_grid / S0) - (mu - 0.5 * sigma**2) * dt)**2 / (2 * (sigma * np.sqrt(dt))**2))
    probs /= np.sum(probs)
    
    # Quantum Circuit Simulation
    qc = QuantumCircuit(qubits)
    qc.initialize(np.sqrt(probs), range(qubits))
    counts = Statevector.from_instruction(qc).sample_counts(shots=shots)
    
    quantum_probs = np.zeros(num_states)
    for bitstring, count in counts.items():
        quantum_probs[int(bitstring, 2)] = count / shots
        
    return {
        'S0': S0, 'price_grid': price_grid, 'pct_grid': pct_grid, 
        'quantum_probs': quantum_probs, 'ann_vol': sigma * np.sqrt(252) * 100,
        'expected_pct': np.sum(pct_grid * quantum_probs)
    }

# --- MAIN DASHBOARD ---
data = run_quantum_engine(ticker_input, forecast_days, num_qubits, shots)

if data:
    # Top Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Price", f"${data['S0']:.2f}")
    c2.metric("Target Return", f"{data['expected_pct']:.2f}%")
    c3.metric("Annual Volatility", f"{data['ann_vol']:.1f}%")
    c4.metric("States Simulated", f"{2**num_qubits}")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Forecast Trajectory", "📈 Risk Distribution", "📜 Raw Data"])
    
    with tab1:
        st.subheader(f"Projected Outcome Cone ({ticker_input})")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(data['pct_grid'], data['quantum_probs'], color='#1f77b4', lw=2)
        ax.fill_between(data['pct_grid'], data['quantum_probs'], alpha=0.3)
        ax.set_xlabel("Return (%)")
        st.pyplot(fig)
        
    with tab2:
        st.write("### Statistical Assessment")
        st.info("The quantum register suggests the distribution above based on current market volatility and drift.")
        
    with tab3:
        st.subheader("Raw Probability Matrix")
        df_raw = pd.DataFrame({'Price ($)': data['price_grid'], 'Return (%)': data['pct_grid'], 'Probability': data['quantum_probs']})
        st.dataframe(df_raw, width='stretch')
else:
    st.error(f"Could not find data for {ticker_input}. Please check the symbol.")
