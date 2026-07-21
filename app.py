import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Quantum Stock Forecast & Risk Analytics",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown(
    """
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
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "⚛️ Quantum Equity Research & Risk Analytics Engine"
)

st.markdown(
    """
This platform uses Qiskit quantum probability sampling with
financial modeling techniques to estimate price distributions,
volatility, and downside risk.
"""
)

st.divider()



# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "🛠️ Simulation Controls"
)


popular_tickers = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "BRK-B",
    "JPM",
    "V",
    "UNH",
    "PG",
    "MA",
    "HD",
    "DIS",
    "NFLX",
    "AMD",
    "COIN",
    "SPY",
    "QQQ",
    "^GSPC",
    "BTC-USD"
]


selected_ticker = st.sidebar.selectbox(
    "Select Asset:",
    options=popular_tickers,
    index=0,
    accept_new_options=True
)


selected_ticker = (
    selected_ticker
    .upper()
    .strip()
)



forecast_days = st.sidebar.slider(
    "Forecast Time Horizon (Days):",
    min_value=1,
    max_value=30,
    value=30
)



num_qubits = st.sidebar.slider(
    "Quantum Register Resolution:",
    min_value=3,
    max_value=12,
    value=10
)



shots = st.sidebar.selectbox(
    "Quantum Measurement Shots:",
    options=[
        2000,
        5000,
        10000
    ],
    index=1
)



if num_qubits >= 11:

    st.sidebar.warning(
        "High qubit settings require more memory."
    )



run_button = st.sidebar.button(
    "⚡ Run Quantum Analysis",
    type="primary",
    width="stretch"
)



# ============================================================
# STOCK DATA LOADING
# ============================================================

@st.cache_data(
    ttl=600,
    max_entries=50
)
def get_stock_data(ticker):

    try:

        data = yf.download(
            ticker,
            period="1y",
            progress=False,
            auto_adjust=True
        )


    except Exception:

        return pd.Series(dtype=float)



    if data.empty:

        return pd.Series(dtype=float)



    if "Close" not in data:

        return pd.Series(dtype=float)



    close_prices = data["Close"]



    if isinstance(
        close_prices,
        pd.DataFrame
    ):

        close_prices = (
            close_prices
            .iloc[:, 0]
        )



    close_prices = (
        close_prices
        .dropna()
        .astype(float)
    )



    return close_prices




# ============================================================
# QUANTUM ENGINE
# ============================================================

@st.cache_data(
    ttl=1800,
    max_entries=20
)
def run_quantum_engine(
    ticker,
    days,
    qubits,
    measurement_shots
):


    prices = get_stock_data(
        ticker
    )



    if prices.empty:

        raise ValueError(
            f"No price data found for {ticker}"
        )



    returns = np.log(
        prices /
        prices.shift(1)
    ).dropna()



    if len(returns) < 20:

        raise ValueError(
            "Not enough market history."
        )



    S0 = float(
        prices.iloc[-1]
    )



    mu = float(
        returns.mean()
    )


    sigma = float(
        returns.std()
    )



    if sigma <= 0:

        sigma = 1e-9



    annual_volatility = (
        sigma *
        np.sqrt(252) *
        100
    )



    dt = days / 252



    states = 2 ** qubits



    drift = (
        mu -
        0.5 *
        sigma ** 2
    ) * dt



    volatility_range = (
        3 *
        sigma *
        np.sqrt(dt)
    )



    min_price = (
        S0 *
        np.exp(
            drift -
            volatility_range
        )
    )


    max_price = (
        S0 *
        np.exp(
            drift +
            volatility_range
        )
    )



    price_grid = np.linspace(
        min_price,
        max_price,
        states
    )



    pct_grid = (
        (
            price_grid -
            S0
        )
        /
        S0
    ) * 100



    # ========================================================
    # Probability Distribution
    # ========================================================


    distribution = np.exp(
        -(
            (
                np.log(
                    price_grid /
                    S0
                )
                -
                drift
            )
            ** 2
        )
        /
        (
            2 *
            sigma ** 2 *
            dt
        )
    )



    distribution_sum = np.sum(
        distribution
    )


    if distribution_sum == 0:

        raise ValueError(
            "Probability calculation failed."
        )



    distribution /= distribution_sum



    if len(distribution) != states:

        raise ValueError(
            "Quantum state size mismatch."
        )



    # ========================================================
    # Quantum Sampling
    # ========================================================


    circuit = QuantumCircuit(
        qubits
    )



    circuit.initialize(
        np.sqrt(distribution),
        range(qubits)
    )


    circuit.measure_all()



    backend = AerSimulator(
        method="matrix_product_state"
    )



    result = backend.run(
        circuit,
        shots=measurement_shots
    ).result()



    counts = result.get_counts()



    quantum_probs = np.zeros(
        states
    )



    for state, count in counts.items():

        index = int(
            state,
            2
        )

        quantum_probs[index] = (
            count /
            measurement_shots
        )



    quantum_probs /= np.sum(
        quantum_probs
    )

# ============================================================
# RISK CALCULATIONS
# ============================================================


    expected_price = np.sum(
        price_grid *
        quantum_probs
    )


    expected_pct = (
        (
            expected_price -
            S0
        )
        /
        S0
    ) * 100



    cdf = np.cumsum(
        quantum_probs
    )



    var_index = np.searchsorted(
        cdf,
        0.05
    )


    if var_index >= len(price_grid):

        var_index = len(price_grid) - 1



    var_95_price = (
        price_grid[var_index]
    )


    var_95_pct = (
        pct_grid[var_index]
    )



    tail_prices = (
        price_grid[
            :var_index + 1
        ]
    )


    tail_probs = (
        quantum_probs[
            :var_index + 1
        ]
    )



    if np.sum(tail_probs) > 0:

        expected_tail_loss = (
            np.sum(
                tail_prices *
                tail_probs
            )
            /
            np.sum(tail_probs)
        )

    else:

        expected_tail_loss = var_95_price



    etl_pct = (
        (
            expected_tail_loss -
            S0
        )
        /
        S0
    ) * 100



    prob_positive = np.sum(
        quantum_probs[
            pct_grid >= 0
        ]
    ) * 100



    prob_up_5 = np.sum(
        quantum_probs[
            pct_grid >= 5
        ]
    ) * 100



    prob_down_5 = np.sum(
        quantum_probs[
            pct_grid <= -5
        ]
    ) * 100



    return {

        "S0": S0,

        "mu": mu,

        "sigma": sigma,

        "ann_vol": annual_volatility,

        "price_grid": price_grid,

        "pct_grid": pct_grid,

        "quantum_probs": quantum_probs,

        "cdf": cdf,

        "expected_price": expected_price,

        "expected_pct": expected_pct,

        "var_95_price": var_95_price,

        "var_95_pct": var_95_pct,

        "expected_tail_loss": expected_tail_loss,

        "etl_pct": etl_pct,

        "prob_positive": prob_positive,

        "prob_up_5": prob_up_5,

        "prob_down_5": prob_down_5,

        "prices": prices
    }



# ============================================================
# RUN ANALYSIS
# ============================================================


if not run_button:

    st.info(
        "Choose an asset and press Run Quantum Analysis."
    )

    st.stop()



try:

    data = run_quantum_engine(
        selected_ticker,
        forecast_days,
        num_qubits,
        shots
    )


except Exception as error:

    st.error(
        f"Analysis failed: {error}"
    )

    st.stop()



# ============================================================
# SUMMARY METRICS
# ============================================================


col1, col2, col3, col4, col5 = st.columns(5)



col1.metric(
    "Current Price",
    f"${data['S0']:.2f}"
)



col2.metric(
    "Forecast Target",
    f"${data['expected_price']:.2f}",
    f"{data['expected_pct']:+.2f}%"
)



col3.metric(
    "Annual Volatility",
    f"{data['ann_vol']:.1f}%"
)



col4.metric(
    "95% VaR",
    f"{data['var_95_pct']:.2f}%"
)



col5.metric(
    "Gain Probability",
    f"{data['prob_positive']:.1f}%"
)



st.divider()



# ============================================================
# TABS
# ============================================================


tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Forecast",
        "📈 Risk",
        "📑 Report",
        "📜 Data"
    ]
)



# ============================================================
# FORECAST TAB
# ============================================================


with tab1:

    st.subheader(
        f"{selected_ticker} {forecast_days}-Day Forecast"
    )



    time_axis = np.arange(
        0,
        forecast_days + 1
    )



    percentile_levels = [
        0.05,
        0.20,
        0.35,
        0.50,
        0.65,
        0.80,
        0.95
    ]



    percentile_returns = []



    for level in percentile_levels:

        index = np.searchsorted(
            data["cdf"],
            level
        )

        index = min(
            index,
            len(data["pct_grid"]) - 1
        )

        percentile_returns.append(
            data["pct_grid"][index]
        )



    time_factor = np.sqrt(
        time_axis /
        forecast_days
    )



    paths = [
        value * time_factor
        for value in percentile_returns
    ]


    p5, p20, p35, p50, p65, p80, p95 = paths



    fig, ax = plt.subplots(
        figsize=(10, 4)
    )


    ax.fill_between(
        time_axis,
        p35,
        p65,
        alpha=0.5,
        label="Core Range"
    )


    ax.fill_between(
        time_axis,
        p20,
        p80,
        alpha=0.2,
        label="Extended Range"
    )


    ax.fill_between(
        time_axis,
        p5,
        p95,
        alpha=0.1,
        label="Tail Risk"
    )


    ax.plot(
        time_axis,
        p50,
        linewidth=2,
        label="Median"
    )


    ax.axhline(
        0,
        linestyle="--"
    )


    ax.set_xlabel(
        "Days"
    )


    ax.set_ylabel(
        "Return (%)"
    )


    ax.grid(
        True,
        alpha=0.25
    )


    ax.legend()



    st.pyplot(
        fig
    )


    plt.close(
        fig
    )



# ============================================================
# RISK TAB
# ============================================================


with tab2:

    st.subheader(
        "Probability Distribution"
    )


    left, right = st.columns(
        [2,1]
    )



    with left:

        fig2, ax2 = plt.subplots(
            figsize=(8,4)
        )


        ax2.plot(
            data["pct_grid"],
            data["quantum_probs"],
            linewidth=2
        )


        ax2.fill_between(
            data["pct_grid"],
            data["quantum_probs"],
            alpha=0.25
        )


        ax2.axvline(
            data["expected_pct"],
            linestyle="-",
            label="Expected"
        )


        ax2.axvline(
            data["var_95_pct"],
            linestyle="--",
            label="VaR"
        )


        ax2.set_xlabel(
            "Return (%)"
        )


        ax2.set_ylabel(
            "Probability"
        )


        ax2.legend()


        ax2.grid(
            True,
            alpha=0.25
        )


        st.pyplot(
            fig2
        )


        plt.close(
            fig2
        )



    with right:

        st.markdown(
            "### Risk Metrics"
        )


        st.write(
            f"Expected Price: ${data['expected_price']:.2f}"
        )


        st.write(
            f"VaR 95%: {data['var_95_pct']:.2f}%"
        )


        st.write(
            f"Expected Tail Loss: {data['etl_pct']:.2f}%"
        )


        st.write(
            f"+5% Gain Probability: {data['prob_up_5']:.1f}%"
        )


        st.write(
            f"-5% Loss Probability: {data['prob_down_5']:.1f}%"
        )

    # Results continue in Part 2
