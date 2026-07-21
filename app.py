import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from data_provider import (
    get_stock_data,
    get_live_price
)



# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================


st.set_page_config(

    page_title="Quantum Stock Forecast & Risk Analytics",

    page_icon="Q",

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

    "Quantum Equity Research & Risk Analytics Engine"

)



st.markdown(

    """

This platform combines quantum probability sampling,

technical indicators, market statistics,

and risk analytics to estimate future

price distributions.

"""

)



st.divider()



# ============================================================
# SIDEBAR
# ============================================================


st.sidebar.header(

    "Simulation Controls"

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



# ============================================================
# FORECAST SETTINGS
# ============================================================


forecast_days = st.sidebar.selectbox(

    "Forecast Horizon:",

    options=[

        7,

        30,

        60,

        90

    ],

    index=1

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

    "Run Quantum Analysis",

    type="primary",

    width="stretch"

)



# ============================================================
# LIVE PRICE
# ============================================================


live_price = get_live_price(

    selected_ticker

)



price_col1, price_col2 = st.columns(2)



with price_col1:


    if live_price is not None:


        st.metric(

            "Live Price",

            f"${live_price:.2f}"

        )


    else:


        st.metric(

            "Live Price",

            "Unavailable"

        )



with price_col2:


    st.metric(

        "Selected Asset",

        selected_ticker

    )



# ============================================================
# MARKET DATA LOADER
# ============================================================


@st.cache_data(

    ttl=3600,

    max_entries=100

)

def load_market_data(

    ticker

):


    data = get_stock_data(

        ticker

    )



    if data is None:


        return pd.DataFrame()



    return data.dropna()



# ============================================================
# DATA PREVIEW
# ============================================================


market_data = load_market_data(

    selected_ticker

)



if market_data.empty:


    st.warning(

        "No market data available."

    )


    st.stop()
# ============================================================
# QUANTUM ENGINE WITH MARKET FEATURES
# ============================================================


@st.cache_data(

    ttl=1800,

    max_entries=50

)

def run_quantum_engine(

    market_data,

    days,

    qubits,

    measurement_shots

):


    data = market_data.copy()



    prices = (

        data["Close"]

        .dropna()

        .astype(float)

    )



    if prices.empty:


        raise ValueError(

            "No price history available."

        )



    if len(prices) < 50:


        raise ValueError(

            "Not enough historical data."

        )



    returns = (

        prices

        .pct_change()

        .dropna()

    )



    S0 = float(

        prices.iloc[-1]

    )



    # ========================================================
    # FEATURE EXTRACTION
    # ========================================================


    current_rsi = float(

        data["RSI"]

        .dropna()

        .iloc[-1]

    )



    current_momentum = float(

        data["Momentum"]

        .dropna()

        .iloc[-1]

    )



    current_volatility = float(

        data["Volatility"]

        .dropna()

        .iloc[-1]

    )



    current_volume_change = 0



    if "Volume_Change" in data.columns:


        volume_values = (

            data["Volume_Change"]

            .dropna()

        )


        if not volume_values.empty:


            current_volume_change = float(

                volume_values.iloc[-1]

            )



    sma20 = float(

        data["SMA20"]

        .dropna()

        .iloc[-1]

    )



    sma50 = float(

        data["SMA50"]

        .dropna()

        .iloc[-1]

    )



    # ========================================================
    # BASE STATISTICS
    # ========================================================


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



    # ========================================================
    # FEATURE BASED MARKET BIAS
    # ========================================================


    feature_bias = 0



    # Moving average trend

    if sma20 > sma50:


        feature_bias += 0.002



    else:


        feature_bias -= 0.002



    # Momentum

    feature_bias += (

        current_momentum *

        0.15

    )



    # RSI adjustment

    if current_rsi > 55:


        feature_bias += 0.001



    elif current_rsi < 45:


        feature_bias -= 0.001



    # Volume confirmation

    if current_volume_change > 0:


        feature_bias += 0.0005



    elif current_volume_change < 0:


        feature_bias -= 0.0005



    adjusted_mu = (

        mu +

        feature_bias

    )



    # ========================================================
    # PRICE DISTRIBUTION
    # ========================================================


    dt = days / 252



    states = 2 ** qubits



    drift = (

        adjusted_mu -

        0.5 *

        sigma ** 2

    ) * dt



    volatility_range = (

        2.5 *

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



    # ========================================================
    # MARKET FEATURE WEIGHTING
    # ========================================================


    feature_multiplier = (

        1 +

        feature_bias * 20

    )



    distribution = (

        distribution *

        feature_multiplier

    )



    distribution = np.maximum(

        distribution,

        0

    )



    distribution /= np.sum(

        distribution

    )



    # ========================================================
    # QUANTUM SAMPLING
    # ========================================================


    circuit = QuantumCircuit(

        qubits

    )



    circuit.initialize(

        np.sqrt(

            distribution

        ),

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



    quantum_probs /= np.sum(

        quantum_probs

    )



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



    var_95_price = price_grid[var_index]



    var_95_pct = pct_grid[var_index]
    # ============================================================
# FINISH RISK CALCULATIONS
# ============================================================


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


        "S0":

        S0,


        "mu":

        adjusted_mu,


        "sigma":

        sigma,


        "ann_vol":

        annual_volatility,


        "price_grid":

        price_grid,


        "pct_grid":

        pct_grid,


        "quantum_probs":

        quantum_probs,


        "cdf":

        cdf,


        "expected_price":

        expected_price,


        "expected_pct":

        expected_pct,


        "var_95_price":

        var_95_price,


        "var_95_pct":

        var_95_pct,


        "expected_tail_loss":

        expected_tail_loss,


        "etl_pct":

        etl_pct,


        "prob_positive":

        prob_positive,


        "prob_up_5":

        prob_up_5,


        "prob_down_5":

        prob_down_5,


        "prices":

        prices,


        "rsi":

        current_rsi,


        "momentum":

        current_momentum,


        "sma20":

        sma20,


        "sma50":

        sma50,


        "volume_change":

        current_volume_change

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

            market_data,

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



# ============================================================
# FEATURE DASHBOARD
# ============================================================


st.divider()



st.subheader(

    "Market Factors Used"

)



factor_col1, factor_col2, factor_col3, factor_col4 = st.columns(4)



factor_col1.metric(

    "RSI",

    f"{data['rsi']:.1f}"

)



factor_col2.metric(

    "20 Day Momentum",

    f"{data['momentum'] * 100:.2f}%"

)



factor_col3.metric(

    "SMA Trend",

    "Bullish"

    if data["sma20"] > data["sma50"]

    else

    "Bearish"

)



factor_col4.metric(

    "Volume Change",

    f"{data['volume_change'] * 100:.2f}%"

)



st.divider()
# ============================================================
# TABS
# ============================================================


tab1, tab2, tab3, tab4 = st.tabs(

    [

        "Forecast",

        "Risk",

        "Report",

        "Data"

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

        alpha=0.25,

        label="Extended Range"

    )



    ax.fill_between(

        time_axis,

        p5,

        p95,

        alpha=0.15,

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

        label="VaR 95%"

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



    st.subheader(

        "Risk Metrics"

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

        f"Probability of +5% Gain: {data['prob_up_5']:.1f}%"

    )


    st.write(

        f"Probability of -5% Loss: {data['prob_down_5']:.1f}%"

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


        signal = "BULLISH OUTLOOK"



    elif (

        data["expected_pct"] < -1.5

        or

        data["prob_down_5"] > 30

    ):


        signal = "BEARISH / CAUTION"



    else:


        signal = "NEUTRAL"



    st.subheader(

        signal

    )



    st.write(

        f"""

Asset: {selected_ticker}


Current Price:

${data['S0']:.2f}


Forecast:

{forecast_days} days


Expected Price:

${data['expected_price']:.2f}


Expected Return:

{data['expected_pct']:+.2f}%


Positive Probability:

{data['prob_positive']:.1f}%


RSI:

{data['rsi']:.1f}


Momentum:

{data['momentum'] * 100:.2f}%


Moving Average Trend:

{"Bullish" if data["sma20"] > data["sma50"] else "Bearish"}

"""

    )



# ============================================================
# DATA TAB
# ============================================================


with tab4:


    dataframe = pd.DataFrame(

        {

            "Price":

            data["price_grid"],


            "Return %":

            data["pct_grid"],


            "Quantum Probability":

            data["quantum_probs"],


            "CDF":

            data["cdf"]

        }

    )



    st.dataframe(

        dataframe,

        width="stretch"

    )



    st.download_button(

        "Download Forecast CSV",

        dataframe.to_csv(

            index=False

        ),

        file_name=f"{selected_ticker}_forecast.csv",

        mime="text/csv"

    )



# ============================================================
# HISTORICAL DATA
# ============================================================


st.divider()



with st.expander(

    "View Historical Price Data"

):


    fig3, ax3 = plt.subplots(

        figsize=(10,3)

    )



    ax3.plot(

        data["prices"].values

    )



    ax3.set_title(

        f"{selected_ticker} Historical Price"

    )



    ax3.set_xlabel(

        "Trading Days"

    )



    ax3.set_ylabel(

        "Price"

    )



    ax3.grid(

        True,

        alpha=0.25

    )



    st.pyplot(

        fig3

    )



    plt.close(

        fig3

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



prices = market_data["Close"]
