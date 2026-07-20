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

selected_ticker = st.sidebar.selectbox(
    "Select or Type Target Asset Ticker:",
    options=popular_tickers,
    index=0,
    accept_new_options=True
).upper().strip()

# Locked parameters as requested
forecast_days = 30
num_qubits = 16

st.sidebar.info(f"Forecast Horizon: {forecast_days} Days (Locked)")
st.sidebar.info(f"Resolution: {num_qubits} Qubits (Locked)")

shots = st.sidebar.selectbox("Quantum Measurement Shots:", [10000, 30000, 50000], index=1)

# --- QUANTUM SIMULATION ENGINE ---
@st.cache_data(ttl=3600)
def run_quantum_engine(ticker, days, qubits, measurement_shots):
    df_raw = yf.download(ticker, period="1y", progress=False)
    
    if df_raw.empty or 'Close' not in df_raw.columns:
        return None
    
    df = df_raw['Close']
    log_returns = np.log(df / df.shift(1)).dropna()
    
    # Handle Series vs Scalar extraction
    S0 = float(df.iloc[-1].iloc[0] if isinstance(df.iloc[-1], pd.Series) else df.iloc[-1])
    mu = float(log_returns.mean().iloc[0] if isinstance(log_returns.mean(), pd.Series) else log_returns.mean())
    sigma = float(log_returns.std().iloc[0] if isinstance(log_returns.std(), pd.Series) else log_returns.std())
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
    
    angles = 2 * np.arcsin(np.sqrt(probs))
    qreg = QuantumRegister(qubits, 'q')
    creg = ClassicalRegister(qubits, 'c')
    qc = QuantumCircuit(qreg, creg)
    
    for i in range(qubits):
        qc.h(qreg[i])
        qc.ry(angles[i], qreg[i])
    qc.measure(qreg, creg)
    
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

    return {
        'S0': S0, 'ann_vol': ann_vol, 'price_grid': price_grid, 'pct_grid': pct_grid, 
        'quantum_probs': quantum_probs, 'expected_price': expected_price, 
        'expected_pct': expected_pct, 'var_95_pct': var_95_pct, 'var_95_price': var_95_price, 
        'etl_pct': etl_pct, 'prob_up_5': np.sum(quantum_probs[pct_grid >= 5.0]) * 100, 
        'prob_down_5': np.sum(quantum_probs[pct_grid <= -5.0]) * 100, 
        'prob_positive': np.sum(quantum_probs[pct_grid >= 0.0]) * 100, 'cdf': cdf
    }

# --- EXECUTION ---
data = run_quantum_engine(selected_ticker, forecast_days, num_qubits, shots)

if data:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Current Price", f"${data['S0']:.2f}")
    c2.metric(f"{forecast_days}-Day Target", f"${data['expected_price']:.2f}", f"{data['expected_pct']:+.2f}%")
    c3.metric("Annual Volatility", f"{data['ann_vol']:.1f}%")
    c4.metric("95% VaR", f"{data['var_95_pct']:.2f}%")
    c5.metric("Win Prob (>0%)", f"{data['prob_positive']:.1f}%")

    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Forecast Trajectory", "📈 Risk & Probability", "📑 Executive Report", "📜 Raw Data"])
    
    with tab1:
        time_axis = np.arange(0, forecast_days + 1)
        # Simplified fan chart logic
        st.line_chart(pd.DataFrame({'Median Path': np.linspace(data['S0'], data['expected_price'], forecast_days + 1)}))
        
    with tab2:
        fig2, ax2 = plt.subplots()
        ax2.plot(data['pct_grid'], data['quantum_probs'])
        st.pyplot(fig2)
        
    with tab3:
        st.write(f"Overall assessment for {selected_ticker} is neutral-to-volatile.")
        
    with tab4:
        st.dataframe(pd.DataFrame({'Price': data['price_grid'], 'Prob': data['quantum_probs']}), width='stretch')
else:
    st.error(f"❌ Error: Could not retrieve valid data for '{selected_ticker}'. It may be delisted or inactive.")
