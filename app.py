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


# ============================================================
# HEADER
# ============================================================

st.title("⚛️ Quantum Equity Research & Risk Analytics Engine")

st.markdown("""
This platform models asset price distributions using Qiskit quantum
probability sampling combined with financial Monte Carlo techniques.
The system evaluates projected prices, volatility, and downside risk.
""")


st.divider()


# ============================================================
# SIDEBAR CONTROLS
# ============================================================

st.sidebar.header("🛠️ Simulation Controls")


popular_tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "BRK-B", "JPM",
    "V", "UNH", "PG", "MA", "HD",
    "DIS", "NFLX", "AMD", "COIN",
    "SPY", "QQQ", "^GSPC", "BTC-USD"
]


selected_ticker = st.sidebar.selectbox(
    "Select Asset:",
    options=popular_tickers,
    index=0,
    accept_new_options=True
).upper().strip()


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
    value=10,
    help="Higher qubits increase resolution but require more memory."
)


shots = st.sidebar.selectbox(
    "Quantum Measurement Shots:",
    options=[2000, 5000, 10000],
    index=1
)


if num_qubits >= 11:
    st.sidebar.warning(
        "High qubit settings require more computation."
    )


run_button = st.sidebar.button(
    "⚡ Run Quantum Analysis",
    type="primary",
    width="stretch"
)



# ============================================================
# STOCK DATA CACHE
# ============================================================

@st.cache_data(
    ttl=3600,
    max_entries=20
)
def get_stock_data(ticker):

    data = yf.download(
        ticker,
        period="1y",
        progress=False
    )

    if data.empty:
        raise ValueError("No stock data found.")

    close_prices = data["Close"]

    if isinstance(close_prices, pd.DataFrame):
        close_prices = close_prices.iloc[:, 0]

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

    df = get_stock_data(ticker)


    log_returns = np.log(
        df / df.shift(1)
    ).dropna()


    S0 = float(df.iloc[-1])


    mu = float(
        log_returns.mean()
    )


    sigma = float(
        log_returns.std()
    )


    if sigma == 0:
        sigma = 1e-9


    annual_volatility = (
        sigma *
        np.sqrt(252) *
        100
    )


    dt = days / 252


    number_of_states = 2 ** qubits


    # --------------------------------------------------------
    # Create possible future prices
    # --------------------------------------------------------

    expected_move = (
        mu -
        0.5 *
        sigma ** 2
    ) * dt


    price_range = (
        3 *
        sigma *
        np.sqrt(dt)
    )


    min_price = (
        S0 *
        np.exp(
            expected_move -
            price_range
        )
    )


    max_price = (
        S0 *
        np.exp(
            expected_move +
            price_range
        )
    )


    price_grid = np.linspace(
        min_price,
        max_price,
        number_of_states
    )


    pct_grid = (
        (price_grid - S0)
        /
        S0
    ) * 100



    # --------------------------------------------------------
    # Build probability distribution
    # --------------------------------------------------------

    distribution = np.exp(
        -(
            (
                np.log(price_grid / S0)
                -
                expected_move
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


    distribution /= np.sum(
        distribution
    )


    # --------------------------------------------------------
    # Quantum Sampling Circuit
    # --------------------------------------------------------

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
        number_of_states
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


    # Normalize after sampling

    quantum_probs /= np.sum(
        quantum_probs
    )


    # --------------------------------------------------------
    # Risk calculations
    # --------------------------------------------------------

    expected_price = np.sum(
        price_grid *
        quantum_probs
    )


    expected_return = (
        (expected_price - S0)
        /
        S0
    ) * 100



    cumulative_probability = np.cumsum(
        quantum_probs
    )


    var_index = np.searchsorted(
        cumulative_probability,
        0.05
    )


    var_price = price_grid[
        var_index
    ]


    var_percent = pct_grid[
        var_index
    ]



    tail_probability = quantum_probs[
        :var_index + 1
    ]


    tail_prices = price_grid[
        :var_index + 1
    ]


    expected_tail_loss = (
        np.sum(
            tail_prices *
            tail_probability
        )
        /
        np.sum(tail_probability)
    )


    etl_percent = (
        (expected_tail_loss - S0)
        /
        S0
    ) * 100



    probability_gain = np.sum(
        quantum_probs[
            pct_grid >= 0
        ]
    ) * 100



    probability_up_5 = np.sum(
        quantum_probs[
            pct_grid >= 5
        ]
    ) * 100



    probability_down_5 = np.sum(
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

        "cdf": cumulative_probability,

        "expected_price": expected_price,

        "expected_pct": expected_return,

        "var_95_price": var_price,

        "var_95_pct": var_percent,

        "expected_tail_loss": expected_tail_loss,

        "etl_pct": etl_percent,

        "prob_positive": probability_gain,

        "prob_up_5": probability_up_5,

        "prob_down_5": probability_down_5,

        "df": df
    }



# ============================================================
# RUN ENGINE ONLY AFTER BUTTON PRESS
# ============================================================

if not run_button:

    st.info(
        "Select an asset and press Run Quantum Analysis."
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
        f"Unable to run analysis: {error}"
    )

    # ============================================================
# TOP SUMMARY METRICS
# ============================================================

col1, col2, col3, col4, col5 = st.columns(5)


col1.metric(
    "Current Price",
    f"${data['S0']:.2f}"
)


col2.metric(
    f"{forecast_days}-Day Quantum Target",
    f"${data['expected_price']:.2f}",
    f"{data['expected_pct']:+.2f}%"
)


col3.metric(
    "Annualized Volatility",
    f"{data['ann_vol']:.1f}%"
)


col4.metric(
    "95% Value at Risk",
    f"{data['var_95_pct']:.2f}%"
)


col5.metric(
    "Probability of Gain",
    f"{data['prob_positive']:.1f}%"
)


st.divider()



# ============================================================
# ANALYSIS TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Forecast Trajectory",
        "📈 Risk & Probability",
        "📑 Executive Report",
        "📜 Raw Simulation Data"
    ]
)



# ============================================================
# TAB 1: FORECAST TRAJECTORY
# ============================================================

with tab1:

    st.subheader(
        f"{forecast_days}-Day Forecast Cone: {selected_ticker}"
    )


    time_axis = np.arange(
        0,
        forecast_days + 1
    )


    percentiles = [
        0.05,
        0.20,
        0.35,
        0.50,
        0.65,
        0.80,
        0.95
    ]


    percentile_values = []


    for p in percentiles:

        index = np.searchsorted(
            data["cdf"],
            p
        )

        percentile_values.append(
            data["pct_grid"][index]
        )



    time_factor = np.sqrt(
        time_axis /
        forecast_days
    )


    p5, p20, p35, p50, p65, p80, p95 = [
        value * time_factor
        for value in percentile_values
    ]



    fig, ax = plt.subplots(
        figsize=(10, 4.5)
    )


    ax.fill_between(
        time_axis,
        p35,
        p65,
        alpha=0.5,
        label="High Probability Zone"
    )


    ax.fill_between(
        time_axis,
        p20,
        p35,
        alpha=0.3
    )


    ax.fill_between(
        time_axis,
        p65,
        p80,
        alpha=0.3
    )


    ax.fill_between(
        time_axis,
        p5,
        p20,
        alpha=0.15,
        label="Extreme Tail Risk"
    )


    ax.fill_between(
        time_axis,
        p80,
        p95,
        alpha=0.15
    )


    ax.plot(
        time_axis,
        p50,
        linewidth=2.5,
        label="Median Forecast"
    )


    ax.axhline(
        0,
        linestyle="--",
        alpha=0.7
    )


    ax.set_xlabel(
        "Days Ahead"
    )


    ax.set_ylabel(
        "Projected Return (%)"
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
# TAB 2: RISK DISTRIBUTION
# ============================================================

with tab2:

    st.subheader(
        "Quantum Probability Density & Risk Metrics"
    )


    chart_col, metrics_col = st.columns(
        [2, 1]
    )



    with chart_col:

        fig2, ax2 = plt.subplots(
            figsize=(8, 4)
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
            label=f"Expected: {data['expected_pct']:+.2f}%"
        )


        ax2.axvline(
            data["var_95_pct"],
            linestyle="--",
            label=f"VaR: {data['var_95_pct']:.2f}%"
        )


        ax2.set_xlabel(
            "Projected Return (%)"
        )


        ax2.set_ylabel(
            "Probability"
        )


        ax2.grid(
            True,
            alpha=0.25
        )


        ax2.legend()


        st.pyplot(
            fig2
        )


        plt.close(
            fig2
        )



    with metrics_col:

        st.markdown(
            "### Risk Breakdown"
        )


        st.write(
            f"Expected Price Target: ${data['expected_price']:.2f}"
        )


        st.write(
            f"95% VaR Price: ${data['var_95_price']:.2f}"
        )


        st.write(
            f"Expected Tail Loss: {data['etl_pct']:.2f}%"
        )


        st.write(
            f"Probability of +5% Gain: {data['prob_up_5']:.1f}%"
        )


        st.write(
            f"Probability of -5% Loss: {data['prob_down_5']:.1f}%"
        )



# ============================================================
# TAB 3: EXECUTIVE REPORT
# ============================================================

with tab3:

    st.subheader(
        f"Quantum Equity Report: {selected_ticker}"
    )


    if (
        data["expected_pct"] > 1.5
        and
        data["prob_positive"] > 55
    ):

        signal = "🟢 BULLISH OUTLOOK"

        description = (
            "The probability distribution shows "
            "positive expected movement with favorable "
            "upside probability."
        )


    elif (
        data["expected_pct"] < -1.5
        or
        data["prob_down_5"] > 30
    ):

        signal = "🔴 BEARISH / CAUTION"

        description = (
            "The model shows increased downside "
            "risk and negative distribution pressure."
        )


    else:

        signal = "🟡 NEUTRAL"

        description = (
            "The forecast remains close to current "
            "levels with balanced uncertainty."
        )



    st.markdown(
        f"## {signal}"
    )


    st.info(
        description
    )


    st.markdown(
        "### Key Takeaways"
    )


    st.write(
        f"""
1. Volatility:
{selected_ticker} shows annualized volatility of
{data['ann_vol']:.1f}%.


2. Risk Reward:
The model estimates a
{data['prob_up_5']:.1f}% chance of a gain above 5%
and a
{data['prob_down_5']:.1f}% chance of a loss below -5%.


3. Expected Movement:
The quantum distribution predicts a
{data['expected_pct']:+.2f}% expected return
over {forecast_days} days.
"""
    )



# ============================================================
# TAB 4: RAW DATA TABLE
# ============================================================

with tab4:

    st.subheader(
        "Quantum State Probability Matrix"
    )


    raw_data = pd.DataFrame(
        {
            "Price Outcome ($)": data["price_grid"],

            "Return (%)": data["pct_grid"],

            "Quantum Probability": data["quantum_probs"],

            "Cumulative Probability": data["cdf"]
        }
    )


    st.dataframe(
        raw_data,
        width="stretch"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Quantum simulation model for research and educational purposes. "
    "Outputs represent statistical projections and are not financial advice."
)
    st.stop()
