# ============================================================
# APP.PY
# Quantum Equity Research Terminal - Main Application Interface
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gc
import time
from datetime import datetime

from data_provider import (
    get_stock_data, get_live_price, get_company_info, search_stocks,
    format_price, validate_market_data, clear_data_cache
)
from prediction_memory import (
    store_prediction, evaluate_predictions, get_prediction_adjustment, complete_prediction
)
from quantum_joint_engine import quantum_joint_forecast
from sector_lookup import get_sector_etf
from analytics import add_features, extract_inputs, validate_inputs, create_forecast_report

# Streamlit Config
st.set_page_config(
    page_title="Quantum Equity Research Terminal",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.set_option("client.showErrorDetails", False)

# Initialize Session State
DEFAULT_STATE = {
    "forecast": None,
    "forecast_settings": None,
    "last_run": "Never",
    "last_price": None,
    "prediction_id": None
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

def apply_quantum_ui():
    st.markdown("""
        <style>
        .stApp {
            background: radial-gradient(circle at 10% 10%, rgba(34,211,238,.15), transparent 45%),
                        radial-gradient(circle at 90% 90%, rgba(139,92,246,.15), transparent 45%),
                        linear-gradient(135deg, #020617, #0f172a);
        }
        h1 { color: #22d3ee !important; font-weight: 900; }
        h2, h3, h4 { color: #e0f2fe !important; font-weight: 700; }
        p { color: #cbd5e1; }
        section[data-testid="stSidebar"] { background: #020617; }
        .stButton button {
            background: linear-gradient(90deg, #06b6d4, #8b5cf6);
            color: white; border-radius: 12px; font-weight: 800; border: none;
        }
        .metric-box {
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(34, 211, 238, 0.2);
            border-radius: 14px; padding: 14px; text-align: center;
        }
        .positive { color: #34d399; font-weight: 800; }
        .negative { color: #f87171; font-weight: 800; }
        .neutral { color: #22d3ee; font-weight: 800; }
        </style>
    """, unsafe_allow_html=True)

apply_quantum_ui()

def safe_float(value, default=0.0):
    try: return float(value)
    except: return default

def format_percent(value):
    try:
        val = float(value)
        arrow = "▲" if val >= 0 else "▼"
        return f"{arrow} {val:+.2f}%"
    except: return "N/A"

def metric_card(title, value, change=None):
    extra = f'<div class="{"positive" if change >= 0 else "negative"}">{format_percent(change)}</div>' if change is not None else ""
    st.markdown(f"""
        <div class="metric-box">
            <h5 style="color: #94a3b8; margin: 0 0 6px 0; font-size: 0.9rem;">{title}</h5>
            <h3 style="margin: 0; font-size: 1.6rem; color: #f1f5f9;">{value}</h3>
            {extra}
        </div>
    """, unsafe_allow_html=True)

def render_status_badge(text, status="neutral"):
    st.markdown(f'<div class="{status}" style="display:inline-block; padding: 6px 14px; border-radius: 14px; border: 1px solid currentColor;">{text}</div>', unsafe_allow_html=True)

def quantum_loading():
    box = st.empty()
    frames = [
        "⚛️ Extracting historical joint factor distribution...",
        "⚛️ Reconstructing empirical correlation structures...",
        "⚛️ Loading statevector amplitudes into multi-register quantum circuit...",
        "⚛️ Executing Aer simulator measurement loops..."
    ]
    for frame in frames:
        box.markdown(f'<div class="metric-box"><h3>{frame}</h3></div>', unsafe_allow_html=True)
        time.sleep(0.3)
    box.empty()

def reset_forecast_state():
    for key, value in DEFAULT_STATE.items():
        st.session_state[key] = value
    gc.collect()

# Sidebar Setup
st.sidebar.title("⚛️ Controls")
search_query = st.sidebar.text_input("Search Ticker/Company", "Microsoft")
try: search_results = search_stocks(search_query)
except: search_results = []

if search_results:
    selected = st.sidebar.selectbox("Select Asset", search_results, format_func=lambda x: x.get("label", x.get("symbol", "Unknown")))
    ticker = selected.get("symbol", search_query).upper()
    company_name = selected.get("name", ticker)
else:
    ticker = search_query.upper()
    company_name = ticker

forecast_days = st.sidebar.selectbox("Forecast Horizon", [1, 2, 7, 30, 60, 90], index=3)
shots = st.sidebar.slider("Quantum Sampling Shots", 500, 3000, 1500, step=500)
run_button = st.sidebar.button("🚀 Execute Quantum Forecast")
clear_button = st.sidebar.button("🧹 Reset System")

if clear_button:
    reset_forecast_state()
    st.rerun()

# Load Caches
live_data = get_live_price(ticker) or {}
company = get_company_info(ticker) or {"name": company_name}
current_price = safe_float(live_data.get("price"))
daily_change = safe_float(live_data.get("change_percent"))

# Top Banner Dashboard
c1, c2, c3 = st.columns(3)
with c1: metric_card("Company", company.get("name", ticker))
with c2: metric_card("Live Price", format_price(current_price) if current_price else "N/A")
with c3: metric_card("Daily Change", format_percent(daily_change) if live_data else "N/A", daily_change if live_data else None)

st.caption(f"Last Price Sync: {datetime.now().strftime('%H:%M:%S')} | Target Ticker: {ticker}")

market_data = get_stock_data(ticker)
spy_data = get_stock_data("SPY")
sector_etf = get_sector_etf(ticker)
sector_data = get_stock_data(sector_etf) if sector_etf else pd.DataFrame()

if market_data.empty or "Close" not in market_data.columns:
    st.error("Historical market records unavailable.")
    st.stop()

market_data["Close"] = pd.to_numeric(market_data["Close"], errors="coerce")
market_data = market_data.replace([np.inf, -np.inf], np.nan).dropna(subset=["Close"])

with st.expander("📈 Historical Price Action Feed"):
    recent = market_data.tail(50).copy()
    recent["Return %"] = recent["Close"].pct_change() * 100
    st.dataframe(recent, use_container_width=True)

market_data_features = add_features(market_data)
quantum_inputs = extract_inputs(market_data_features)

if not validate_inputs(market_data_features, quantum_inputs):
    st.error("Feature space validation failed.")
    st.stop()

with st.expander("⚛️ Input State Representation Vector"):
    st.dataframe(pd.DataFrame({"Feature": list(quantum_inputs.keys()), "Value": list(quantum_inputs.values())}), use_container_width=True)

# Run Button trigger
if run_button:
    exec_price = safe_float(current_price) if current_price else safe_float(market_data["Close"].iloc[-1])
    try:
        quantum_loading()
        with st.spinner("Processing multi-factor register entanglement..."):
            result = quantum_joint_forecast(market_data, exec_price, days=forecast_days, shots=shots, spy_data=spy_data, sector_data=sector_data)
        
        pred_id = store_prediction(ticker, forecast_days, exec_price, result["expected_price"])
        st.session_state.forecast = result
        st.session_state.forecast_settings = [ticker, forecast_days, shots]
        st.session_state.last_run = datetime.now().strftime("%H:%M:%S")
        st.session_state.last_price = exec_price
        st.session_state.prediction_id = pred_id
        st.success("Analysis successfully finalized.")
    except Exception as err:
        st.error(f"Execution Error: {err}")
        st.stop()

forecast = st.session_state.forecast
adaptive_adjustment = get_prediction_adjustment(ticker)

if forecast:
    forecast["adaptive_adjustment"] = adaptive_adjustment
    forecast["adjusted_price"] = forecast["expected_price"] + adaptive_adjustment

with st.sidebar.expander("🧠 Model Learning Bias Feed"):
    st.write(f"Active Ticker: {ticker}")
    st.write(f"Adaptive Ticker Bias: {adaptive_adjustment:+.4f}")

# Layout Results View
if forecast is not None:
    expected_return = (forecast["expected_price"] / forecast["starting_price"] - 1) * 100
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Expected Price", format_price(forecast["expected_price"]))
    with c2: metric_card("Horizon Drift (Return)", f"{expected_return:+.2f}%", expected_return)
    with c3: metric_card("Decision Confidence", f"{forecast['confidence_score']:.1f}%")
    with c4: metric_card("State Risk Score", f"{forecast['risk_score']:.2f}")
    
    st.divider()
    meta = forecast.get("model_metadata", {})
    st.caption(f"⚙️ Simulation Details: {meta.get('total_qubits','?')} qubits ({meta.get('qubits_per_factor','?')} qubits/factor) "
               f"· Quantum State Entropy: {meta.get('quantum_entropy','N/A')} "
               f"· Entanglement Coupling Score: {meta.get('entanglement_score','N/A')}% "
               f"· Macro context: {'Included' if meta.get('macro_available') else 'Degraded (3-factor mode)'} "
               f"· Sampler: {'Classical Fallback' if meta.get('fallback_to_classical') else 'Qiskit Simulator'}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        regime = forecast.get("market_regime", "Unknown")
        render_status_badge(regime, {"Bullish": "positive", "Bearish": "negative", "Neutral": "neutral"}.get(regime, "neutral"))
    with c2: st.metric("Upside Probability (>+5%)", f"{forecast['upside_probability']:.2f}%")
    with c3: st.metric("Downside Probability (<-5%)", f"{forecast['downside_probability']:.2f}%")
    
    # Probability Distribution Plotting
    st.subheader("⚛️ Price Return Probability Density (Marginalized Statevector)")
    fig, ax = plt.subplots(figsize=(10, 3.5))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')
    ax.plot(forecast["price_grid"], forecast["probability"], color='#22d3ee', linewidth=2)
    ax.fill_between(forecast["price_grid"], forecast["probability"], color='#22d3ee', alpha=0.15)
    ax.set_xlabel("Predicted Future Price ($)", color='#cbd5e1')
    ax.set_ylabel("Measured Density", color='#cbd5e1')
    ax.tick_params(colors='#cbd5e1')
    ax.grid(True, color='#334155', linestyle='--', alpha=0.4)
    st.pyplot(fig, clear_figure=True)
    plt.close(fig)
    
    # Conditional Probabilities Breakdowns
    st.subheader("🔗 Multi-Factor Joint Conditionals")
    st.caption("Derived directly from the entangled multi-factor system state. Explores the impact of extreme register regimes on price density.")
    conds = forecast.get("conditionals", {})
    if conds:
        rows = []
        labels_map = {"volatility": "Volatility Register", "momentum": "Momentum Register", "macro": "Macro/Sector Register"}
        for factor, vals in conds.items():
            rows.append({
                "Factor Register": labels_map.get(factor, factor),
                "P(Drop > 5%) | Extreme High": f"{vals['p_drop_given_high']*100:.1f}%" if vals.get('p_drop_given_high') is not None else "N/A",
                "P(Drop > 5%) | Extreme Low": f"{vals['p_drop_given_low']*100:.1f}%" if vals.get('p_drop_given_low') is not None else "N/A",
                "Unconditional P(Drop > 5%)": f"{vals['p_drop_unconditional']*100:.1f}%"
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Conditional metrics unavailable for 3-factor mode.")
        
    # Heatmap Block
    st.subheader("🌐 Joint Distribution Heatmap (Price Return × Volatility)")
    try:
        active_factors = meta.get("active_factors", [])
        j_prob, j_shape = forecast.get("joint_probability"), forecast.get("joint_shape")
        if j_prob is not None and j_shape and "price_return" in active_factors and "volatility" in active_factors:
            j_nd = np.array(j_prob).reshape(j_shape)
            p_ax, v_ax = active_factors.index("price_return"), active_factors.index("volatility")
            other_axes = tuple(i for i in range(len(active_factors)) if i not in (p_ax, v_ax))
            heat = j_nd.sum(axis=other_axes)
            if p_ax < v_ax: heat = heat.T
            
            fig2, ax2 = plt.subplots(figsize=(8, 4.5))
            fig2.patch.set_facecolor('#0f172a')
            ax2.set_facecolor('#0f172a')
            im = ax2.imshow(heat, aspect="auto", origin="lower", cmap="plasma")
            ax2.set_xlabel("Price Return Quantile Bin", color='#cbd5e1')
            ax2.set_ylabel("Volatility Quantile Bin", color='#cbd5e1')
            ax2.tick_params(colors='#cbd5e1')
            cb = fig2.colorbar(im, ax=ax2)
            cb.ax.yaxis.set_tick_params(color='#cbd5e1')
            cb.ax.yaxis.label.set_color('#cbd5e1')
            st.pyplot(fig2, clear_figure=True)
            plt.close(fig2)
        else:
            st.info("Bivariate space map unavailable.")
    except Exception as heatmap_err:
        st.warning(f"Heatmap plotting aborted: {heatmap_err}")
        
    # Prediction Feedback Block
    st.subheader("🧠 Closed-Loop Self-Learning Adjustment Feed")
    st.caption("Feed realized results back into the adaptive memory matrix. The model calculates localized prediction biases and shifts future expectations.")
    pred_id = st.session_state.prediction_id
    if pred_id:
        actual_price_input = st.number_input("Realized (Actual) Settlement Price ($)", min_value=0.0, value=0.0, step=0.1)
        if st.button("Submit Price Target Settlement"):
            if actual_price_input > 0.0:
                complete_prediction(pred_id, actual_price_input)
                st.success("Target finalized. Updating model learning matrix.")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("Please supply a valid price target.")
    else:
        st.info("Initiate a forecast to log and complete predictions.")

    with st.expander("📄 Export Forecast"):
        report = create_forecast_report(forecast)
        st.download_button("Download Forecast CSV", report.to_csv(index=False), file_name=f"{ticker}_forecast.csv", mime="text/csv")
