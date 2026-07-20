import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# --- PAGE CONFIG ---
st.set_page_config(page_title="Quantum Terminal", layout="wide")
st.title("⚛️ Quantum Equity Research & Risk Analytics Engine")

# --- SIDEBAR ---
st.sidebar.header("🛠️ Simulation Controls")
# Hybrid: Predefined list + custom input
ticker_list = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "SPY", "QQQ", "BTC-USD"]
selected = st.sidebar.selectbox("Select Asset:", ticker_list)
custom = st.sidebar.text_input("Or enter custom ticker:")
ticker = custom if custom else selected
days = st.sidebar.slider("Horizon (Days):", 7, 90, 30)
qubits = st.sidebar.select_slider("Qubits (Complexity):", [4, 6, 8, 10], value=6)

# --- QUANTUM ENGINE (AerSimulator) ---
@st.cache_data(ttl=3600)
def run_quantum_engine(ticker, days, qubits):
    df = yf.Ticker(ticker).history(period="1y")
    if df.empty: return None
    
    close = df['Close'].dropna()
    log_ret = np.log(close / close.shift(1)).dropna()
    S0, mu, sigma = float(close.iloc[-1]), float(log_ret.mean()), float(log_ret.std())
    
    # Grid setup
    num_states = 2**qubits
    price_grid = np.linspace(S0 * 0.8, S0 * 1.2, num_states)
    pct_grid = ((price_grid - S0) / S0) * 100
    
    # Distributions
    probs = np.exp(- (np.log(price_grid / S0) - (mu - 0.5 * sigma**2) * (days/252))**2 / 
                   (2 * (sigma * np.sqrt(days/252))**2))
    probs /= np.sum(probs)
    
    # Qiskit Aer Simulation
    qc = QuantumCircuit(qubits)
    qc.initialize(np.sqrt(probs), range(qubits))
    qc.measure_all()
    
    sim = AerSimulator()
    job = sim.run(qc, shots=20000)
    result = job.result()
    counts = result.get_counts()
    
    quantum_probs = np.zeros(num_states)
    for bitstring, count in counts.items():
        quantum_probs[int(bitstring, 2)] = count / 20000
        
    return {'S0': S0, 'price_grid': price_grid, 'pct_grid': pct_grid, 
            'quantum_probs': quantum_probs, 'ann_vol': sigma * np.sqrt(252) * 100}

# --- DASHBOARD ---
data = run_quantum_engine(ticker, days, qubits)

if data:
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Price", f"${data['S0']:.2f}")
    c2.metric("Annual Volatility", f"{data['ann_vol']:.1f}%")
    c3.metric("Quantum States", f"{2**qubits}")

    tab1, tab2, tab3 = st.tabs(["📊 Risk Distribution", "📈 Price Projection", "📜 Raw Data"])
    
    with tab1:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(data['pct_grid'], data['quantum_probs'], width=0.5)
        ax.set_title("Quantum Risk Distribution")
        st.pyplot(fig)
        
    with tab2:
        st.line_chart(data['price_grid'])
        
    with tab3:
        st.dataframe(pd.DataFrame({'Price': data['price_grid'], 'Prob': data['quantum_probs']}), width='stretch')
else:
    st.error("Data fetch failed. Ensure the ticker is valid.")
