import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import math

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
    page_title="Quantum Equity Intelligence Engine",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)



# ============================================================
# SESSION INITIALIZATION
# ============================================================

if "started" not in st.session_state:
    st.session_state.started = False


session_defaults = {

    "forecast": None,

    "forecast_settings": None,

    "last_run": None,

    "last_price": None,

    "confidence_score": None,

    "market_regime": None,

    "factor_weights": None,

    "quantum_distribution": None

}


for key, value in session_defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value



# ============================================================
# LANDING PAGE
# ============================================================

if not st.session_state.started:


    st.markdown(
        """
        <div style="
        text-align:center;
        padding:60px 20px;
        ">

        <h1 style="
        font-size:55px;
        ">
        ⚛️ Quantum Equity Intelligence Engine
        </h1>


        <h3>
        Adaptive quantum probability forecasting system
        </h3>


        <p style="
        font-size:20px;
        color:#b8c1d1;
        ">

        Multi-factor market prediction using historical behavior,
        dynamic weighting, and quantum probability simulation.

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
            ### 📈 Historical Intelligence

            Learns from:

            • Long-term trends

            • Momentum cycles

            • Volatility regimes

            • Previous market patterns
            """
        )



    with col2:

        st.markdown(
            """
            ### ⚛️ Quantum Probability

            Uses:

            • Probability amplitude encoding

            • Quantum state sampling

            • Distribution measurement

            • Uncertainty modeling
            """
        )



    with col3:

        st.markdown(
            """
            ### 🧠 Adaptive AI Factors

            Combines:

            • Technical signals

            • Macro conditions

            • Sector movement

            • Sentiment data
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

            padding:16px;

        }

        </style>
        """,
        unsafe_allow_html=True
    )



    if st.button(
        "🚀 Launch Quantum Engine",
        use_container_width=True
    ):

        st.session_state.started = True

        st.rerun()



    st.stop()



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

radial-gradient(
circle at top left,
#172554,
transparent 35%
),

radial-gradient(
circle at bottom right,
#3b0764,
transparent 35%
),

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


border:

1px solid #334155;


padding:

18px;


border-radius:

16px;


box-shadow:

0 0 20px rgba(34,211,238,0.15);

}



.status-box {

background:

rgba(15,23,42,0.85);


border-left:

5px solid #22c55e;


padding:

14px;


border-radius:

10px;

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

}



</style>

""",
unsafe_allow_html=True
)



# ============================================================
# HEADER
# ============================================================


st.title(
    "⚛️ Quantum Equity Intelligence Engine"
)


st.caption(
    "Adaptive weighted quantum probability forecasting"
)


st.divider()
# ============================================================
# SIDEBAR CONTROLS
# ============================================================


st.sidebar.title(
    "⚛️ Quantum Forecast Controls"
)



# ============================================================
# STOCK SEARCH
# ============================================================


search_query = st.sidebar.text_input(

    "Search Company or Symbol",

    value="Microsoft"

)



try:

    matches = search_stocks(
        search_query
    )


except Exception:

    matches = []



if matches:


    selected = st.sidebar.selectbox(

        "Select Asset",

        matches,

        format_func=lambda x:

        x.get(
            "label",
            x.get(
                "symbol",
                "Unknown"
            )
        )

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


    ticker = (

        search_query

        .upper()

        .strip()

    )


    company_name = ticker





# ============================================================
# FORECAST SETTINGS
# ============================================================


forecast_days = st.sidebar.selectbox(

    "Prediction Horizon",

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

    min_value=4,

    max_value=10,

    value=7

)



shots = st.sidebar.slider(

    "Quantum Measurements",

    min_value=1000,

    max_value=10000,

    value=4000,

    step=1000

)



st.sidebar.info(

"""

Quantum states:

2^qubits possible outcomes


Higher measurements reduce sampling noise.

"""

)



run_button = st.sidebar.button(

    "🚀 Run Quantum Forecast"

)





# ============================================================
# LIVE MARKET INFORMATION
# ============================================================


try:

    live_data = get_live_price(
        ticker
    )


except Exception:

    live_data = None



try:

    company = get_company_info(
        ticker
    )


except Exception:

    company = {}



current_price = None



if live_data:


    current_price = live_data.get(

        "price",

        None

    )





# ============================================================
# MARKET HEADER CARDS
# ============================================================


header1, header2, header3 = st.columns(3)



with header1:


    st.metric(

        "Company",

        company.get(

            "name",

            company_name

        )

    )



with header2:


    st.metric(

        "Current Price",

        format_price(
            current_price
        )

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



    change_color = (

        "positive"

        if daily_change >= 0

        else "negative"

    )



    change_symbol = (

        "🟢"

        if daily_change >= 0

        else "🔴"

    )



    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Daily Movement</h4>

        <h2 class="{change_color}">

        {change_symbol}

        {daily_change:+.2f}%

        </h2>

        </div>

        """,

        unsafe_allow_html=True

    )



st.caption(

f"Last market update: {datetime.datetime.now().strftime('%H:%M:%S')}"

)





# ============================================================
# HISTORICAL DATA LOADER
# ============================================================


@st.cache_data(

    ttl=900,

    max_entries=50

)

def load_market_data(symbol):


    try:


        data = get_stock_data(
            symbol
        )



        if not validate_market_data(
            data
        ):

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
# DATA CLEANING
# ============================================================


if "Close" not in market_data.columns:


    st.error(

        "Market data missing Close prices."

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





if len(market_data) < 252:


    st.warning(

        "Less than one year of trading history. Accuracy may decrease."

    )





# ============================================================
# EXTERNAL FEATURE CONNECTION
# DATA_PROVIDER.PY WILL FILL THESE VALUES
# ============================================================


def get_external_features():


    """

    Future data_provider.py integration.

    Expected outputs:

    macro_score
    sector_score
    sentiment_score
    global_market_score
    earnings_score
    valuation_score
    analyst_score
    news_score
    interest_rate_score
    inflation_score
    vix_score


    Each value:

    -1 = negative

     0 = neutral

    +1 = positive


    """


    return {


        "macro_score":0,


        "sector_score":0,


        "sentiment_score":0,


        "global_market_score":0,


        "earnings_score":0,


        "valuation_score":0,


        "analyst_score":0,


        "news_score":0,


        "interest_rate_score":0,


        "inflation_score":0,


        "vix_score":0


    }



external_features = get_external_features()



st.session_state.factor_weights = external_features
# ============================================================
# ADAPTIVE WEIGHT CALCULATOR
# ============================================================


def calculate_dynamic_weights(

    volatility,

    momentum,

    market_conditions

):


    """
    Calculates changing factor importance.

    The model does not assume every factor
    matters equally all the time.

    """



    volatility_pressure = np.clip(

        volatility * 5,

        0,

        1

    )



    momentum_strength = np.clip(

        abs(momentum) * 5,

        0,

        1

    )



    macro_strength = np.clip(

        abs(

            market_conditions.get(

                "macro_score",

                0

            )

        ),

        0,

        1

    )



    weights = {


        "technical":

        0.35 + (

            momentum_strength * 0.15

        ),



        "volatility":

        0.15 + (

            volatility_pressure * 0.20

        ),



        "macro":

        0.15 + (

            macro_strength * 0.20

        ),



        "sector":

        0.10,



        "sentiment":

        0.10,



        "fundamentals":

        0.15

    }



    total = sum(

        weights.values()

    )



    for key in weights:

        weights[key] /= total



    return weights





# ============================================================
# QUANTUM MULTI FACTOR FORECAST ENGINE
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


    shots,


    external_features


):


    prices = (

        market_data["Close"]

        .astype(float)

        .dropna()

    )



    S0 = float(

        starting_price

    )



    if len(prices) < 120:


        raise ValueError(

            "Insufficient market history."

        )





    # ========================================================
    # RETURN ENGINE
    # ========================================================


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



    daily_volatility = returns.std()



    if daily_volatility <= 0:

        daily_volatility = 0.01



    annual_volatility = (

        daily_volatility *

        np.sqrt(252)

    )





    # ========================================================
    # MULTI WINDOW TREND MODEL
    # ========================================================


    windows = {


        "short":

        7,


        "medium":

        30,


        "long":

        90,


        "macro":

        180

    }



    trends = {}



    for name, window in windows.items():


        if len(prices) > window:


            trends[name] = (

                prices.iloc[-1]

                /

                prices.iloc[-window]

                - 1

            )


        else:


            trends[name] = 0





    technical_score = (

        trends["short"] * 0.15

        +

        trends["medium"] * 0.35

        +

        trends["long"] * 0.35

        +

        trends["macro"] * 0.15

    )



    technical_score = np.clip(

        technical_score,

        -0.5,

        0.5

    )





    # ========================================================
    # MARKET CONDITIONS
    # ========================================================


    macro_score = external_features.get(

        "macro_score",

        0

    )



    sector_score = external_features.get(

        "sector_score",

        0

    )



    sentiment_score = external_features.get(

        "sentiment_score",

        0

    )



    earnings_score = external_features.get(

        "earnings_score",

        0

    )



    valuation_score = external_features.get(

        "valuation_score",

        0

    )





    fundamentals_score = (

        earnings_score * 0.6

        +

        valuation_score * 0.4

    )





    # ========================================================
    # DYNAMIC WEIGHTS
    # ========================================================


    weights = calculate_dynamic_weights(

        annual_volatility,

        technical_score,

        external_features

    )



    factor_state = (


        technical_score *

        weights["technical"]


        +


        annual_volatility *

        -1 *

        weights["volatility"]



        +


        macro_score *

        weights["macro"]



        +


        sector_score *

        weights["sector"]



        +


        sentiment_score *

        weights["sentiment"]



        +


        fundamentals_score *

        weights["fundamentals"]

    )





    factor_state = np.clip(

        factor_state,

        -0.30,

        0.30

    )





    # ========================================================
    # REALISTIC DRIFT MODEL
    # ========================================================


    historical_return = returns.mean()



    drift = (

        historical_return * 0.35

        +

        factor_state * 0.65

    )



    # Prevent unrealistic forecasts

    drift = np.clip(

        drift,

        -0.0025,

        0.0025

    )





    expected_return = (


        np.exp(

            drift *

            days

        )

        -1

    )



    # Maximum movement based on volatility

    volatility_limit = (

        annual_volatility *

        np.sqrt(

            days / 252

        )

    )



    expected_return = np.clip(

        expected_return,

        -volatility_limit,

        volatility_limit

    )



    expected_price = (

        S0 *

        (

            1 +

            expected_return

        )

    )





    # ========================================================
    # PRICE STATE GRID
    # ========================================================


    states = 2 ** qubits



    spread = (

        S0 *

        volatility_limit *

        2

    )



    spread = np.clip(

        spread,

        S0 * 0.05,

        S0 * 0.40

    )



    price_grid = np.linspace(

        max(

            S0 * 0.60,

            expected_price - spread

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





    # ========================================================
    # PROBABILITY AMPLITUDE CREATION
    # ========================================================


    sigma = max(

        volatility_limit,

        0.05

    )



    z = (

        (

            return_grid / 100

            -

            expected_return

        )

        /

        sigma

    )



    probability = np.exp(

        -0.5 *

        z ** 2

    )



    probability *= (

        1 +

        factor_state

    )



    probability = np.maximum(

        probability,

        0

    )



    probability /= probability.sum()
    # ========================================================
    # QUANTUM STATE ENCODING
    # ========================================================


    quantum_probability = None


    try:


        circuit = QuantumCircuit(

            qubits

        )


        amplitudes = np.sqrt(

            probability

        )


        circuit.initialize(

            amplitudes,

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





    # ========================================================
    # FALLBACK IF QUANTUM SAMPLING FAILS
    # ========================================================


    if (

        quantum_probability is None

        or

        quantum_probability.sum() == 0

    ):


        quantum_probability = probability.copy()



    else:


        quantum_probability /= (

            quantum_probability.sum()

        )





    # ========================================================
    # QUANTUM EXPECTED PRICE
    # ========================================================


    quantum_expected_price = np.sum(

        price_grid *

        quantum_probability

    )





    # ========================================================
    # PROBABILITY CALIBRATION
    # ========================================================


    upside_probability = np.sum(

        quantum_probability[

            return_grid > 5

        ]

    )



    downside_probability = np.sum(

        quantum_probability[

            return_grid < -5

        ]

    )



    neutral_probability = (

        1

        -

        upside_probability

        -

        downside_probability

    )



    # ========================================================
    # CONFIDENCE ENGINE
    # ========================================================


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

        entropy /

        max_entropy

    )



    volatility_confidence = 1 - np.clip(

        annual_volatility,

        0,

        1

    )



    trend_confidence = abs(

        technical_score

    )



    confidence = (

        entropy_confidence * 0.45

        +

        volatility_confidence * 0.30

        +

        trend_confidence * 0.25

    ) * 100



    confidence = np.clip(

        confidence,

        15,

        90

    )





    # ========================================================
    # MARKET REGIME
    # ========================================================


    if technical_score > 0.04:


        regime = "Bullish"



    elif technical_score < -0.04:


        regime = "Bearish"



    else:


        regime = "Neutral"





    # ========================================================
    # FINAL RETURN OBJECT
    # ========================================================


    return {


        "starting_price":

        S0,


        "price_grid":

        price_grid,


        "return_grid":

        return_grid,


        "probability":

        quantum_probability,


        "expected_price":

        quantum_expected_price,


        "volatility":

        annual_volatility * 100,


        "returns":

        returns,


        "market_regime":

        regime,


        "confidence_score":

        confidence,


        "factor_weights":

        weights,


        "factor_state":

        factor_state,


        "upside_probability":

        upside_probability * 100,


        "downside_probability":

        downside_probability * 100,


        "neutral_probability":

        neutral_probability * 100

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

            market_data["Close"].iloc[-1]

        )



    try:



        with st.spinner(

            "Running adaptive quantum probability engine..."

        ):



            result = quantum_forecast(

                market_data,

                run_price,

                forecast_days,

                qubits,

                shots,

                external_features

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



        st.session_state.confidence_score = (

            result["confidence_score"]

        )


        st.session_state.market_regime = (

            result["market_regime"]

        )


        st.success(

            "Quantum multi-factor forecast completed."

        )



    except Exception as error:


        st.error(

            f"Quantum engine failed: {error}"

        )


        st.stop()
        # ============================================================
# FORECAST VALIDATION
# ============================================================


if st.session_state.forecast is None:


    st.info(

        "Select settings and run the quantum forecast."

    )


    st.stop()



forecast = st.session_state.forecast



if st.session_state.forecast_settings != settings:


    st.warning(

        "Settings changed. Run analysis again."

    )





# ============================================================
# DASHBOARD CALCULATIONS
# ============================================================


expected_price = forecast["expected_price"]



price_change = (

    (

        expected_price -

        forecast["starting_price"]

    )

    /

    forecast["starting_price"]

) * 100



upside_probability = forecast[

    "upside_probability"

]



downside_probability = forecast[

    "downside_probability"

]



neutral_probability = forecast[

    "neutral_probability"

]





# ============================================================
# MAIN QUANTUM DASHBOARD
# ============================================================


st.divider()



st.subheader(

    "⚛️ Quantum Probability Dashboard"

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


    color = (

        "positive"

        if price_change >= 0

        else "negative"

    )


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Quantum Expected Value</h4>

        <h2>

        {format_price(expected_price)}

        </h2>

        <p class="{color}">

        {price_change:+.2f}%

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

        Probability of +5% movement

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

        {forecast["market_regime"]}

        Regime

        </p>

        </div>

        """,

        unsafe_allow_html=True

    )





# ============================================================
# SCENARIO PROBABILITIES
# ============================================================


st.divider()



st.subheader(

    "Market Scenario Distribution"

)



risk1, risk2, risk3 = st.columns(3)



with risk1:

    st.metric(

        "Bull Scenario",

        f"{upside_probability:.1f}%"

    )



with risk2:

    st.metric(

        "Neutral Scenario",

        f"{neutral_probability:.1f}%"

    )



with risk3:

    st.metric(

        "Bear Scenario",

        f"{downside_probability:.1f}%"

    )





# ============================================================
# ADAPTIVE WEIGHTS DISPLAY
# ============================================================


st.divider()



st.subheader(

    "Dynamic Factor Importance"

)



weights = forecast["factor_weights"]



weight_df = pd.DataFrame(

    {

        "Factor":

        list(weights.keys()),


        "Current Weight (%)":

        [

            value * 100

            for value in weights.values()

        ]

    }

)



weight_df = weight_df.sort_values(

    "Current Weight (%)",

    ascending=False

)



st.dataframe(

    weight_df,

    use_container_width=True,

    hide_index=True

)





# ============================================================
# QUANTUM DISTRIBUTION GRAPH
# ============================================================


st.divider()



st.subheader(

    "Quantum State Probability Distribution"

)



fig, ax = plt.subplots(

    figsize=(10,4)

)



ax.plot(

    forecast["return_grid"],

    forecast["probability"],

    linewidth=2

)



ax.fill_between(

    forecast["return_grid"],

    forecast["probability"],

    alpha=0.25

)



ax.set_xlabel(

    "Possible Return (%)"

)



ax.set_ylabel(

    "Probability"

)



ax.set_title(

    "Measured Quantum Outcome Distribution"

)



ax.grid(

    alpha=0.25

)



st.pyplot(

    fig,

    use_container_width=True

)



plt.close(fig)





# ============================================================
# ANALYTICS TABS
# ============================================================


tab1, tab2, tab3, tab4 = st.tabs(

    [

        "Overview",

        "Risk Analytics",

        "Quantum Model",

        "Raw Data"

    ]

)





# ============================================================
# OVERVIEW TAB
# ============================================================


with tab1:


    returns = forecast["returns"]



    c1, c2, c3, c4 = st.columns(4)



    with c1:

        st.metric(

            "Average Daily Return",

            f"{returns.mean()*100:.3f}%"

        )



    with c2:

        st.metric(

            "Daily Volatility",

            f"{returns.std()*100:.3f}%"

        )



    with c3:

        st.metric(

            "Best Day",

            f"{returns.max()*100:.2f}%"

        )



    with c4:

        st.metric(

            "Worst Day",

            f"{returns.min()*100:.2f}%"

        )





# ============================================================
# RISK TAB
# ============================================================


with tab2:


    st.metric(

        "Annual Volatility",

        f"{forecast['volatility']:.2f}%"

    )


    risk_score = (

        forecast["volatility"]

        *

        (

            downside_probability /

            100

        )

    )


    st.metric(

        "Risk Score",

        f"{risk_score:.2f}"

    )





# ============================================================
# QUANTUM MODEL TAB
# ============================================================


with tab3:


    st.write(

        """

        Forecast pipeline:


        Historical prices

        ↓

        Multi timeframe trend extraction

        ↓

        Adaptive factor weighting

        ↓

        Probability amplitude encoding

        ↓

        Quantum state measurement

        ↓

        Outcome probability distribution


        """

    )



    st.metric(

        "Quantum States",

        2 ** qubits

    )



    st.metric(

        "Qubits",

        qubits

    )



    st.metric(

        "Measurements",

        shots

    )





# ============================================================
# RAW DATA TAB
# ============================================================


with tab4:


    raw = pd.DataFrame(

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

        raw,

        use_container_width=True

    )





# ============================================================
# EXPORT RESULTS
# ============================================================


st.divider()



st.subheader(

    "Export Quantum Forecast"

)



export = pd.DataFrame(

    {

        "Price":

        forecast["price_grid"],


        "Return":

        forecast["return_grid"],


        "Probability":

        forecast["probability"]

    }

)



csv = export.to_csv(

    index=False

)



st.download_button(

    "Download Forecast CSV",

    csv,

    file_name=f"{ticker}_quantum_forecast.csv",

    mime="text/csv"

)





# ============================================================
# FOOTER
# ============================================================


st.divider()



st.caption(

f"""

⚛️ Quantum Equity Intelligence Engine


Asset:

{ticker}


Forecast:

{forecast_days} days


Quantum Backend:

Qiskit Aer Matrix Product State


Quantum States:

{2 ** qubits}


Last Simulation:

{st.session_state.last_run}


Model output represents probability estimates, not guaranteed returns.

"""

)
