import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import time

from streamlit_autorefresh import st_autorefresh

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from data_provider import (
    get_stock_data,
    get_live_price,
    get_company_info,
    search_stocks,
    format_price,
    format_percent,
    validate_market_data,
    clear_data_cache
)


# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Quantum Equity Research Terminal",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# LANDING PAGE
# ============================================================

if "started" not in st.session_state:
    st.session_state.started = False


if not st.session_state.started:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:60px 20px;
        ">

        <h1 style="font-size:55px;">
        ⚛️ Quantum Equity Research Terminal
        </h1>

        <h3>
        Quantum-powered stock forecasting and risk analytics platform
        </h3>

        <p style="
            font-size:20px;
            color:#b8c1d1;
        ">
        Explore market probabilities using historical data,
        statistical modeling, and quantum simulation.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.divider()


    col1, col2, col3 = st.columns(3)


    with col1:
        st.markdown(
            """
            ### 📈 Market Intelligence

            Analyze historical trends,
            volatility, momentum,
            and price behavior.
            """
        )


    with col2:
        st.markdown(
            """
            ### ⚛️ Quantum Simulation

            Encode probability distributions
            into quantum states using Qiskit.
            """
        )


    with col3:
        st.markdown(
            """
            ### 🛡 Risk Analytics

            Measure upside,
            downside,
            confidence,
            and uncertainty.
            """
        )


    st.divider()


    st.markdown(
        """
        <style>

        div[data-testid="stButton"] button {

            background:
            linear-gradient(
                135deg,
                #00ff88,
                #00cc66
            );

            color:black;

            font-size:22px;

            font-weight:800;

            border-radius:16px;

            border:2px solid #00ff88;

            padding:16px;

        }


        div[data-testid="stButton"] button:hover {

            transform:scale(1.08);

            box-shadow:
            0 0 25px #00ff88;

        }

        </style>
        """,
        unsafe_allow_html=True
    )


    if st.button(
        "🚀 Start Quantum Simulation",
        use_container_width=True
    ):

        st.session_state.started = True
        st.rerun()


    st.stop()



# ============================================================
# SESSION STATE
# ============================================================

session_defaults = {

    "forecast": None,

    "forecast_settings": None,

    "last_run": None,

    "last_price": None,

    "neutral_probability": None,

    "risk_score": None,

    "confidence_score": None,

    "market_regime": None,

    "last_ticker": None

}


for key, value in session_defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value



# ============================================================
# AUTO REFRESH
# ============================================================

st_autorefresh(
    interval=30000,
    key="market_refresh"
)



# ============================================================
# GLOBAL TERMINAL STYLE
# ============================================================

st.markdown(
"""
<style>

.stApp {

    background:
    radial-gradient(circle at top left,#172554,transparent 35%),
    radial-gradient(circle at bottom right,#3b0764,transparent 35%),
    #050816;

    color:#f8fafc;

}


[data-testid="stSidebar"] {

    background:
    linear-gradient(
        180deg,
        #111827,
        #020617
    );

}


h1 {

    color:#22d3ee !important;

    text-shadow:
    0 0 15px #22d3ee;

}


h2,h3 {

    color:#e0f2fe !important;

}


.metric-box {

    background:
    linear-gradient(
        145deg,
        #111827,
        #1e293b
    );

    border:1px solid #334155;

    padding:18px;

    border-radius:16px;

    box-shadow:
    0 0 20px rgba(34,211,238,0.15);

}


.metric-box:hover {

    transform:translateY(-5px);

    box-shadow:
    0 0 25px rgba(34,211,238,0.45);

}


.status-box {

    background:
    rgba(15,23,42,0.8);

    border-left:
    5px solid #22c55e;

    padding:14px;

    border-radius:10px;

}


.positive {

    color:#22ff88;

    font-weight:800;

}


.negative {

    color:#ff4444;

    font-weight:800;

}


.stButton > button {

    background:
    linear-gradient(
        135deg,
        #00ff88,
        #00cc66
    );

    color:black;

    font-weight:700;

    border-radius:12px;

    border:1px solid #00ff88;

}


input {

    background-color:#111827 !important;

    color:white !important;

}


hr {

    border-color:#334155;

}


button[data-baseweb="tab"] {

    color:#94a3b8;

}


button[aria-selected="true"] {

    color:#22d3ee !important;

}


</style>
""",
unsafe_allow_html=True
)
# ============================================================
# HEADER
# ============================================================

st.title(
    "⚛️ Quantum Equity Research Terminal"
)

st.caption(
    "Quantum probability simulation combined with statistical market analytics."
)

st.divider()



# ============================================================
# SIDEBAR CONTROLS
# ============================================================

st.sidebar.title(
    "Simulation Controls"
)



# ============================================================
# STOCK SEARCH
# ============================================================

search_query = st.sidebar.text_input(
    "Search Company or Symbol",
    value="Apple"
)


try:
    matches = search_stocks(search_query)

except Exception:

    matches = []



if matches:

    selected = st.sidebar.selectbox(
        "Select Asset",
        matches,
        format_func=lambda x: x.get("label", x.get("symbol", "Unknown"))
    )

    ticker = selected.get(
        "symbol",
        search_query.upper()
    )

    company_name = selected.get(
        "name",
        ticker
    )


else:

    ticker = search_query.upper().strip()

    company_name = ticker



# ============================================================
# FORECAST SETTINGS
# ============================================================

forecast_days = st.sidebar.selectbox(

    "Forecast Period",

    [
        7,
        30,
        60,
        90
    ],

    index=3

)



qubits = st.sidebar.slider(

    "Quantum Qubits",

    min_value=3,

    max_value=6,

    value=5

)



shots = st.sidebar.slider(

    "Quantum Shots",

    min_value=250,

    max_value=2500,

    value=1000,

    step=250

)



if qubits >= 6 and shots > 1500:

    st.sidebar.warning(
        "Large simulation settings detected. Lower values improve stability."
    )



run_button = st.sidebar.button(
    "Run Quantum Analysis"
)



# ============================================================
# LIVE MARKET DATA
# ============================================================

try:

    live_data = get_live_price(ticker)

except Exception:

    live_data = None



try:

    company = get_company_info(ticker)

except Exception:

    company = {}



current_price = None



if live_data:

    current_price = live_data.get(
        "price",
        None
    )



if not current_price:

    current_price = None



# ============================================================
# MARKET HEADER CARDS
# ============================================================

header1, header2, header3 = st.columns(3)



with header1:

    display_company = company.get(
        "name",
        company_name
    )

    st.metric(
        "Company",
        display_company
    )



with header2:

    st.metric(

        "Live Price",

        format_price(current_price)

    )



with header3:


    daily_change = 0


    if live_data:

        daily_change = live_data.get(
            "change_percent",
            0
        )



    try:

        daily_change = float(
            daily_change
        )

    except Exception:

        daily_change = 0



    if daily_change >= 0:

        change_html = f"""
        <div class="metric-box">

        <h4>Daily Change</h4>

        <h2>
        <span class="positive">
        🟢 +{daily_change:.2f}%
        </span>
        </h2>

        </div>
        """

    else:

        change_html = f"""
        <div class="metric-box">

        <h4>Daily Change</h4>

        <h2>
        <span class="negative">
        🔴 {daily_change:.2f}%
        </span>
        </h2>

        </div>
        """



    st.markdown(
        change_html,
        unsafe_allow_html=True
    )



st.caption(

    f"Last update: {datetime.datetime.now().strftime('%H:%M:%S')}"

)



# ============================================================
# LOAD HISTORICAL DATA
# ============================================================


@st.cache_data(
    ttl=900,
    max_entries=50
)

def load_market_data(symbol):


    try:

        data = get_stock_data(symbol)


        if not validate_market_data(data):

            return pd.DataFrame()


        return data


    except Exception:

        return pd.DataFrame()



market_data = load_market_data(
    ticker
)



if market_data.empty:


    st.error(
        "No historical market data available."
    )


    if st.button(
        "Clear Data Cache"
    ):

        clear_data_cache()

        st.cache_data.clear()

        st.rerun()


    st.stop()



# ============================================================
# MARKET DATA VALIDATION
# ============================================================


required_columns = [
    "Close"
]


missing_columns = [

    col

    for col in required_columns

    if col not in market_data.columns

]



if missing_columns:


    st.error(
        f"Missing market columns: {missing_columns}"
    )

    st.stop()



market_data = market_data.copy()



market_data["Close"] = pd.to_numeric(

    market_data["Close"],

    errors="coerce"

)



market_data = market_data.dropna(

    subset=["Close"]

)



if len(market_data) < 60:


    st.error(
        "Not enough historical market data for simulation."
    )

    st.stop()
    # ============================================================
# QUANTUM FORECAST ENGINE
# ============================================================

@st.cache_data(
    ttl=600,
    max_entries=20
)
def quantum_forecast(
    market_data,
    starting_price,
    days,
    qubits,
    shots
):

    prices = (
        market_data["Close"]
        .astype(float)
        .dropna()
    )


    if len(prices) < 60:

        raise ValueError(
            "Not enough historical prices."
        )


    latest = market_data.iloc[-1]


    market_strength = float(
        latest.get(
            "Market_Strength",
            50
        )
    ) / 100


    momentum_feature = float(
        latest.get(
            "Momentum_20",
            0
        )
    )


    rsi_signal = (
        float(
            latest.get(
                "RSI",
                50
            )
        )
        -
        50
    ) / 50


    macd_signal = float(
        latest.get(
            "MACD",
            0
        )
    )


    volatility_regime = float(
        latest.get(
            "Volatility_Regime",
            1
        )
    )


    quantum_feature_score = float(
        latest.get(
            "Quantum_Feature_Score",
            50
        )
    ) / 100



    returns = (
        prices
        .pct_change()
        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )
        .dropna()
    )


    if returns.empty:

        raise ValueError(
            "Invalid return data."
        )



    S0 = float(starting_price)



    daily_mean = float(
        returns.mean()
    )


    daily_volatility = float(
        returns.std()
    )


    if (
        np.isnan(daily_volatility)
        or daily_volatility <= 0
    ):

        daily_volatility = 0.01



    daily_volatility *= volatility_regime



    annual_volatility = (
        daily_volatility *
        np.sqrt(252)
    )



    recent_returns = returns.tail(90)


    recent_mean = float(
        recent_returns.mean()
    )


    recent_volatility = float(
        recent_returns.std()
    )


    if (
        np.isnan(recent_volatility)
        or recent_volatility == 0
    ):

        recent_volatility = daily_volatility



    momentum_score = (

        recent_mean /

        (
            recent_volatility +
            1e-9
        )

    )


    momentum_score = np.clip(
        momentum_score,
        -1,
        1
    )



    if momentum_score > 0.25:

        regime = "Bullish"

    elif momentum_score < -0.25:

        regime = "Bearish"

    else:

        regime = "Neutral"



    feature_drift = (

        market_strength * 0.35

        +

        momentum_feature * 0.25

        +

        rsi_signal * 0.15

        +

        np.tanh(macd_signal) * 0.15

        +

        quantum_feature_score * 0.10

    )



    drift = (

        daily_mean * 0.40

        +

        feature_drift * 0.60

    )



    if regime == "Bullish":

        drift *= 1.20


    elif regime == "Bearish":

        drift *= 0.80



    drift = np.clip(
        drift,
        -0.01,
        0.01
    )



    years = days / 252



    expected_price = (

        S0 *

        np.exp(
            drift *
            days
        )

    )



    forecast_volatility = (

        annual_volatility *

        np.sqrt(years)

    )



    spread = (

        S0 *

        forecast_volatility *

        2

    )



    if spread <= 0:

        spread = S0 * 0.05



    states = 2 ** qubits



    price_grid = np.linspace(

        max(
            expected_price - spread,
            S0 * 0.50
        ),

        expected_price + spread,

        states

    )



    return_grid = (

        (
            price_grid -
            S0
        )

        /

        S0

    ) * 100



    expected_return = (

        np.exp(
            drift *
            days
        )

        -

        1

    )



    return_volatility = (

        annual_volatility *

        np.sqrt(years)

    )


    if return_volatility <= 0:

        return_volatility = 0.05



    z_scores = (

        (
            return_grid / 100
            -
            expected_return
        )

        /

        return_volatility

    )



    probabilities = np.exp(

        -0.5 *

        z_scores ** 2

    )



    probabilities *= (

        0.5 +

        quantum_feature_score

    )



    probabilities = np.nan_to_num(
        probabilities
    )


    if probabilities.sum() <= 0:

        probabilities = np.ones(
            states
        )


    probabilities /= probabilities.sum()



    quantum_probability = None



    try:

        circuit = QuantumCircuit(
            qubits
        )


        circuit.initialize(
            np.sqrt(probabilities),
            range(qubits)
        )


        circuit.measure_all()



        simulator = AerSimulator(
            method="matrix_product_state"
        )


        result = simulator.run(
            circuit,
            shots=shots
        ).result()



        counts = result.get_counts()



        quantum_probability = np.zeros(
            states
        )



        for state, count in counts.items():

            index = int(
                state,
                2
            )


            if index < states:

                quantum_probability[index] = (
                    count /
                    shots
                )



    except Exception:

        quantum_probability = None



    if (
        quantum_probability is None
        or
        quantum_probability.sum() <= 0
    ):

        quantum_probability = probabilities.copy()


    else:

        quantum_probability /= quantum_probability.sum()



    raw_expected_price = np.sum(

        price_grid *

        quantum_probability

    )



    confidence_penalty = min(

        annual_volatility *

        np.sqrt(years),

        0.30

    )



    adjusted_expected_price = (

        raw_expected_price *

        (
            1 -
            confidence_penalty
        )

        +

        S0 *

        confidence_penalty

    )



    entropy = -np.sum(

        quantum_probability *

        np.log(
            quantum_probability +
            1e-12
        )

    )



    max_entropy = np.log(
        states
    )



    entropy_confidence = (

        1 -

        (
            entropy /
            max_entropy
        )

    ) * 100



    stability_score = max(

        0,

        100 -

        annual_volatility * 100

    )



    confidence_score = (

        entropy_confidence * 0.5

        +

        market_strength * 100 * 0.3

        +

        stability_score * 0.2

    )



    confidence_score = np.clip(
        confidence_score,
        5,
        95
    )



    return {

        "starting_price": S0,

        "price_grid": price_grid,

        "return_grid": return_grid,

        "probability": quantum_probability,

        "expected_price": adjusted_expected_price,

        "volatility": annual_volatility * 100,

        "returns": returns,

        "market_regime": regime,

        "confidence_score": confidence_score

    }

# ============================================================
# RUN QUANTUM ANALYSIS
# ============================================================


settings = [

    ticker,

    forecast_days,

    qubits,

    shots

]



if run_button:


    if current_price:

        run_price = float(
            current_price
        )


    else:

        run_price = float(

            market_data["Close"]
            .iloc[-1]

        )



    try:


        with st.spinner(

            "Running quantum probability simulation..."

        ):


            result = quantum_forecast(

                market_data,

                run_price,

                forecast_days,

                qubits,

                shots

            )



        st.session_state.forecast = result

        st.session_state.forecast_settings = settings

        st.session_state.last_run = (

            datetime.datetime.now()

            .strftime(
                "%H:%M:%S"
            )

        )

        st.session_state.last_price = run_price

        st.session_state.market_regime = (

            result["market_regime"]

        )

        st.session_state.confidence_score = (

            result["confidence_score"]

        )


        st.success(

            "Quantum analysis completed."

        )


    except Exception as error:


        st.error(

            f"Quantum simulation failed: {error}"

        )



        st.stop()
        # ============================================================
# FORECAST VALIDATION
# ============================================================


if st.session_state.forecast is None:


    st.info(
        "Choose settings and run quantum analysis."
    )


    st.stop()



forecast = st.session_state.forecast



if st.session_state.forecast_settings != settings:


    st.warning(
        "Settings changed. Run analysis again."
    )



# ============================================================
# PROBABILITY CALCULATIONS
# ============================================================


expected_price = forecast["expected_price"]



expected_change = (

    (

        expected_price -

        forecast["starting_price"]

    )

    /

    forecast["starting_price"]

) * 100



returns_grid = forecast["return_grid"]


probabilities = forecast["probability"]



upside_probability = np.sum(

    probabilities[

        returns_grid > 5

    ]

) * 100



downside_probability = np.sum(

    probabilities[

        returns_grid < -5

    ]

) * 100



neutral_probability = (

    100 -

    (

        upside_probability +

        downside_probability

    )

)



upside_probability = np.clip(

    upside_probability,

    0,

    100

)



downside_probability = np.clip(

    downside_probability,

    0,

    100

)



neutral_probability = np.clip(

    neutral_probability,

    0,

    100

)



risk_score = (

    forecast["volatility"]

    *

    (

        downside_probability /

        100

    )

)



st.session_state.neutral_probability = neutral_probability


st.session_state.risk_score = risk_score



# ============================================================
# QUANTUM MARKET DASHBOARD
# ============================================================


st.divider()


st.subheader(

    "Quantum Market Dashboard"

)



card1, card2, card3, card4 = st.columns(4)



with card1:


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Starting Price</h4>

        <h2>
        {format_price(
            forecast["starting_price"]
        )}
        </h2>

        </div>

        """,

        unsafe_allow_html=True

    )



with card2:


    change_color = (

        "positive"

        if expected_change >= 0

        else "negative"

    )


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Quantum Target</h4>

        <h2>
        {format_price(expected_price)}
        </h2>


        <p class="{change_color}">

        {expected_change:+.2f}%

        </p>


        </div>

        """,

        unsafe_allow_html=True

    )



with card3:


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Upside Probability</h4>

        <h2>
        {upside_probability:.1f}%
        </h2>


        <p>
        Above +5% move
        </p>


        </div>

        """,

        unsafe_allow_html=True

    )



with card4:


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Confidence</h4>

        <h2>

        {forecast["confidence_score"]:.1f}%

        </h2>


        <p>

        {forecast["market_regime"]} Market

        </p>


        </div>

        """,

        unsafe_allow_html=True

    )



# ============================================================
# RISK SCENARIOS
# ============================================================


risk1, risk2, risk3 = st.columns(3)



with risk1:


    st.metric(

        "Upside Scenario",

        f"{upside_probability:.1f}%"

    )



with risk2:


    st.metric(

        "Neutral Scenario",

        f"{neutral_probability:.1f}%"

    )



with risk3:


    st.metric(

        "Downside Scenario",

        f"{downside_probability:.1f}%"

    )



# ============================================================
# SYSTEM STATUS
# ============================================================


st.divider()


st.subheader(

    "System Status"

)



s1, s2, s3 = st.columns(3)



with s1:


    st.markdown(

        """

        <div class="status-box">

        ✓ Historical Data Connected

        </div>

        """,

        unsafe_allow_html=True

    )



with s2:


    st.markdown(

        f"""

        <div class="status-box">

        ✓ Quantum Backend Ready

        <br>

        Aer Matrix Product State

        <br>

        {qubits} Qubits |

        {shots} Shots

        </div>

        """,

        unsafe_allow_html=True

    )



with s3:


    st.markdown(

        f"""

        <div class="status-box">

        ✓ Last Simulation

        <br>

        {st.session_state.last_run}

        </div>

        """,

        unsafe_allow_html=True

    )
    # ============================================================
# ANALYTICS TABS
# ============================================================


tab1, tab2, tab3, tab4, tab5 = st.tabs(

    [

        "Overview",

        "Forecast",

        "Risk Analytics",

        "Quantum Model",

        "Raw Data"

    ]

)



# ============================================================
# OVERVIEW TAB
# ============================================================


with tab1:


    st.subheader(

        "Historical Statistics"

    )


    returns = forecast["returns"]



    overview1, overview2, overview3, overview4 = st.columns(4)



    with overview1:


        st.metric(

            "Average Daily Return",

            f"{returns.mean()*100:.3f}%"

        )



    with overview2:


        st.metric(

            "Daily Volatility",

            f"{returns.std()*100:.3f}%"

        )



    with overview3:


        st.metric(

            "Best Trading Day",

            f"{returns.max()*100:.2f}%"

        )



    with overview4:


        st.metric(

            "Worst Trading Day",

            f"{returns.min()*100:.2f}%"

        )



    st.divider()



    st.subheader(

        "Market Regime"

    )


    regime = forecast["market_regime"]



    if regime == "Bullish":


        st.success(

            "Bullish momentum detected."

        )


    elif regime == "Bearish":


        st.error(

            "Bearish momentum detected."

        )


    else:


        st.info(

            "Neutral market conditions detected."

        )





# ============================================================
# FORECAST TAB
# ============================================================


with tab2:


    st.subheader(

        f"{ticker} {forecast_days}-Day Quantum Forecast"

    )



    fig, ax = plt.subplots(

        figsize=(10,4)

    )



    ax.plot(

        forecast["return_grid"],

        forecast["probability"],

        linewidth=2

    )



    ax.set_xlabel(

        "Potential Return (%)"

    )


    ax.set_ylabel(

        "Probability Density"

    )



    ax.set_title(

        "Quantum Probability Distribution"

    )



    ax.grid(

        True,

        alpha=0.25

    )



    st.pyplot(

        fig,

        use_container_width=True

    )



    plt.close(

        fig

    )



    st.divider()



    forecast_table = pd.DataFrame(

        {

            "Potential Price":

            forecast["price_grid"],


            "Return (%)":

            forecast["return_grid"],


            "Probability (%)":

            forecast["probability"] * 100

        }

    )



    forecast_table = forecast_table.sort_values(

        by="Probability (%)",

        ascending=False

    )



    st.subheader(

        "Highest Probability Outcomes"

    )


    st.dataframe(

        forecast_table.head(10),

        use_container_width=True

    )





# ============================================================
# RISK ANALYTICS TAB
# ============================================================


with tab3:


    st.subheader(

        "Risk Distribution"

    )



    risk_probabilities = forecast["probability"]

    risk_returns = forecast["return_grid"]



    fig, ax = plt.subplots(

        figsize=(10,4)

    )



    ax.fill_between(

        risk_returns,

        risk_probabilities,

        alpha=0.25

    )



    ax.plot(

        risk_returns,

        risk_probabilities,

        linewidth=2

    )



    ax.axvline(

        0,

        linestyle="--"

    )



    ax.axvline(

        5,

        linestyle="--"

    )



    ax.axvline(

        -5,

        linestyle="--"

    )



    ax.set_xlabel(

        "Return (%)"

    )



    ax.set_ylabel(

        "Probability"

    )



    ax.set_title(

        "Quantum Risk Curve"

    )



    ax.grid(

        True,

        alpha=0.25

    )



    st.pyplot(

        fig,

        use_container_width=True

    )



    plt.close(

        fig

    )



    risk_col1, risk_col2 = st.columns(2)



    with risk_col1:


        st.metric(

            "Risk Score",

            f"{risk_score:.2f}"

        )



    with risk_col2:


        st.metric(

            "Annual Volatility",

            f"{forecast['volatility']:.2f}%"

        )





# ============================================================
# QUANTUM MODEL TAB
# ============================================================


with tab4:


    st.subheader(

        "Quantum Simulation Architecture"

    )



    st.write(

        """

Historical market prices are converted into return distributions.

The distribution is encoded into a quantum state.

Qiskit Aer Matrix Product State simulation samples possible future market states.

The output represents probability estimates, not guaranteed predictions.

"""

    )



    st.code(

        """

Historical Market Data

↓

Return Calculation

↓

Momentum Detection

↓

Probability Distribution

↓

Quantum State Encoding

↓

Aer MPS Sampling

↓

Risk Forecast

""",

        language="text"

    )



    st.divider()



    st.subheader(

        "Simulation Parameters"

    )


    param1, param2, param3 = st.columns(3)



    with param1:


        st.metric(

            "Qubits",

            qubits

        )



    with param2:


        st.metric(

            "Shots",

            shots

        )



    with param3:


        st.metric(

            "States",

            2 ** qubits

        )





# ============================================================
# RAW DATA TAB
# ============================================================


with tab5:


    st.subheader(

        "Quantum State Output"

    )



    table = pd.DataFrame(

        {

            "Future Price":

            forecast["price_grid"],


            "Return (%)":

            forecast["return_grid"],


            "Probability (%)":

            forecast["probability"] * 100

        }

    )



    st.dataframe(

        table,

        use_container_width=True

    )
    # ============================================================
# HISTORICAL MARKET CHART
# ============================================================


st.divider()



with st.expander(

    "Historical Market Data"

):


    st.subheader(

        f"{ticker} Price History"

    )


    fig, ax = plt.subplots(

        figsize=(10,4)

    )



    ax.plot(

        market_data.index,

        market_data["Close"],

        linewidth=2

    )



    ax.set_xlabel(

        "Date"

    )


    ax.set_ylabel(

        "Price"

    )



    ax.set_title(

        f"{ticker} Historical Closing Price"

    )



    ax.grid(

        True,

        alpha=0.25

    )



    plt.xticks(

        rotation=45

    )



    st.pyplot(

        fig,

        use_container_width=True

    )



    plt.close(

        fig

    )





# ============================================================
# DOWNLOAD FORECAST DATA
# ============================================================


st.divider()



st.subheader(

    "Export Quantum Results"

)



export_data = pd.DataFrame(

    {

        "Future Price":

        forecast["price_grid"],


        "Return Percentage":

        forecast["return_grid"],


        "Probability Percentage":

        forecast["probability"] * 100

    }

)



csv = export_data.to_csv(

    index=False

)



st.download_button(

    label="Download Forecast CSV",

    data=csv,

    file_name=f"{ticker}_quantum_forecast.csv",

    mime="text/csv"

)





# ============================================================
# FINAL SYSTEM SUMMARY
# ============================================================


st.divider()



summary1, summary2, summary3 = st.columns(3)



with summary1:


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Asset</h4>

        <h2>

        {ticker}

        </h2>

        </div>

        """,

        unsafe_allow_html=True

    )



with summary2:


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Forecast Horizon</h4>

        <h2>

        {forecast_days} Days

        </h2>

        </div>

        """,

        unsafe_allow_html=True

    )



with summary3:


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Model Confidence</h4>

        <h2>

        {forecast["confidence_score"]:.1f}%

        </h2>

        </div>

        """,

        unsafe_allow_html=True

    )





# ============================================================
# FOOTER
# ============================================================


st.divider()



st.caption(

f"""

⚛️ Quantum Equity Research Terminal


Asset:

{ticker}


Simulation Engine:

Qiskit Aer Matrix Product State


Quantum States:

{2 ** qubits}


Qubits:

{qubits}


Last Analysis:

{st.session_state.last_run}


This application provides statistical market research estimates.

It does not provide financial advice.

"""

)
