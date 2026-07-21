import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from data_provider import get_stock_data


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
This platform combines quantum probability sampling,
financial modeling, and risk analytics to estimate
future price distributions.
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
    max_value=7,
    value=5
)



shots = st.sidebar.selectbox(
    "Quantum Measurement Shots:",
    options=[
        250,
        500,
        1000
    ],
    index=1
)



if num_qubits >= 6:

    st.sidebar.warning(
        "Higher qubit settings require more processing."
    )



run_button = st.sidebar.button(
    "⚡ Run Quantum Analysis",
    type="primary",
    width="stretch"
)



# ============================================================
# MARKET DATA LOADING
# ============================================================

@st.cache_data(
    ttl=60,
    max_entries=100
)
def load_market_data(ticker):

    try:

        prices = get_stock_data(
            ticker
        )

        return prices


    except Exception:

        return pd.Series(dtype=float)



prices = load_market_data(
    selected_ticker
)



# ============================================================
# LIVE PRICE DASHBOARD
# ============================================================


price_col1, price_col2 = st.columns(2)



with price_col1:


    if not prices.empty:

        latest_price = float(
            prices.iloc[-1]
        )


        st.metric(
            "Latest Price",
            f"${latest_price:.2f}"
        )


    else:

        st.metric(
            "Latest Price",
            "Unavailable"
        )



with price_col2:


    st.metric(
        "Selected Asset",
        selected_ticker
    )



# ============================================================
# HISTORICAL DATA FUNCTION
# ============================================================

@st.cache_data(
    ttl=3600,
    max_entries=100
)
def get_historical_data(ticker):

    data = get_stock_data(
        ticker
    )
# ============================================================
# QUANTUM ENGINE
# ============================================================


@st.cache_data(
    ttl=1800,
    max_entries=50
)
def run_quantum_engine(
    ticker,
    days,
    qubits,
    measurement_shots
):


    prices = get_historical_data(
        ticker
    )



    if prices.empty:

        raise ValueError(
            f"No market data found for {ticker}. "
            "Provider failed to return prices."
        )



    returns = np.log(
        prices /
        prices.shift(1)
    ).dropna()



    if len(returns) < 20:

        raise ValueError(
            "Not enough historical price data."
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
    # PROBABILITY MODEL
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
            "Probability model failed."
        )



    distribution /= distribution_sum



    # ========================================================
    # QUANTUM SAMPLING
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


        if index < states:

            quantum_probs[index] = (

                count /
                measurement_shots

            )



    probability_sum = np.sum(
        quantum_probs
    )



    if probability_sum == 0:

        raise ValueError(
            "Quantum simulation failed."
        )



    quantum_probs /= probability_sum



    # ========================================================
    # RISK CALCULATIONS
    # ========================================================


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



    var_index = min(
        var_index,
        len(price_grid)-1
    )



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

            np.sum(
                tail_probs
            )

        )


    else:


        expected_tail_loss = (
            var_95_price
        )



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

    with st.spinner(
        "Running quantum probability simulation..."
    ):

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


st.divider()



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



    time_axis = np.arange(
        0,
        forecast_days + 1
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
        figsize=(10,4)
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
        "Quantum Probability Distribution"
    )



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



    st.markdown(
        "### Risk Metrics"
    )



    st.write(
        f"Expected Price: ${data['expected_price']:.2f}"
    )


    st.write(
        f"95% VaR: {data['var_95_pct']:.2f}%"
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
    # ============================================================
# REPORT TAB
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


        explanation = (
            "The model indicates positive expected movement "
            "with stronger upside probability."
        )



    elif (

        data["expected_pct"] < -1.5

        or

        data["prob_down_5"] > 30

    ):


        signal = "🔴 BEARISH / CAUTION"


        explanation = (
            "The model indicates increased downside risk."
        )



    else:


        signal = "🟡 NEUTRAL"


        explanation = (
            "The forecast remains balanced."
        )



    st.markdown(
        f"## {signal}"
    )



    st.info(
        explanation
    )



    risk_ratio = (

        data["prob_up_5"]

        /

        max(
            data["prob_down_5"],
            0.01
        )

    )



    st.write(
        f"""
Asset:

{selected_ticker}


Current Price:

${data['S0']:.2f}


Forecast Horizon:

{forecast_days} days


Expected Price:

${data['expected_price']:.2f}


Expected Return:

{data['expected_pct']:+.2f}%


Annualized Volatility:

{data['ann_vol']:.1f}%


Positive Return Probability:

{data['prob_positive']:.1f}%


Upside / Downside Ratio:

{risk_ratio:.2f}
"""
    )



# ============================================================
# RAW DATA TAB
# ============================================================


with tab4:


    st.subheader(
        "Quantum State Probability Matrix"
    )



    dataframe = pd.DataFrame(
        {

            "Price Outcome ($)":

                data["price_grid"],


            "Return (%)":

                data["pct_grid"],


            "Quantum Probability":

                data["quantum_probs"],


            "Cumulative Probability":

                data["cdf"]

        }
    )



    st.dataframe(
        dataframe,
        width="stretch"
    )



    st.download_button(

        label="Download Simulation CSV",

        data=dataframe.to_csv(
            index=False
        ),

        file_name=f"{selected_ticker}_quantum_forecast.csv",

        mime="text/csv"

    )



# ============================================================
# HISTORICAL PRICE
# ============================================================


st.divider()



with st.expander(
    "View Historical Price Data"
):


    historical_fig, historical_ax = plt.subplots(
        figsize=(10,3)
    )



    historical_ax.plot(
        data["prices"].index,
        data["prices"].values
    )



    historical_ax.set_title(
        f"{selected_ticker} Historical Prices"
    )



    historical_ax.set_xlabel(
        "Date"
    )



    historical_ax.set_ylabel(
        "Price ($)"
    )



    historical_ax.grid(
        True,
        alpha=0.25
    )



    st.pyplot(
        historical_fig
    )



    plt.close(
        historical_fig
    )



# ============================================================
# FOOTER
# ============================================================


st.divider()



st.caption(
    """
Quantum Stock Forecast is an educational research model.
Forecast outputs are statistical estimates and are not financial advice.
"""
)


st.divider()


    return data
