import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime

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
        Quantum probability forecasting engine
        </h3>


        <p style="
            font-size:20px;
            color:#b8c1d1;
        ">

        Multi-factor market analysis using
        classical market data and quantum probability simulation.

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

            Historical trends,
            volatility,
            momentum,
            and market behavior.
            """
        )


    with col2:

        st.markdown(
            """
            ### ⚛️ Quantum Engine

            Quantum state encoding,
            probability weighting,
            and simulation.
            """
        )


    with col3:

        st.markdown(
            """
            ### 🛡 Risk Analytics

            Probability ranges,
            uncertainty,
            and downside protection.
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


    "last_ticker": None,


    "quantum_features": None

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

rgba(15,23,42,0.8);


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
    "⚛️ Quantum Equity Research Terminal"
)


st.caption(
    "Quantum weighted probability forecasting with multi-factor market analysis."
)


st.divider()
# ============================================================
# SIDEBAR CONTROLS
# ============================================================


st.sidebar.title(
    "Quantum Simulation Controls"
)



# ============================================================
# STOCK SEARCH
# ============================================================


search_query = st.sidebar.text_input(
    "Search Company or Symbol",
    value="Apple"
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

    max_value=8,

    value=6

)



shots = st.sidebar.slider(

    "Quantum Shots",

    min_value=500,

    max_value=5000,

    value=2000,

    step=500

)



st.sidebar.info(

    """
    Higher qubits increase possible states.

    More shots improve probability sampling.

    """

)



run_button = st.sidebar.button(

    "Run Quantum Forecast"

)



# ============================================================
# LIVE MARKET DATA
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
# MARKET HEADER
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

        "Live Price",

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



    if daily_change >= 0:


        st.markdown(

            f"""

            <div class="metric-box">

            <h4>Daily Change</h4>

            <h2 class="positive">

            🟢 +{daily_change:.2f}%

            </h2>

            </div>

            """,

            unsafe_allow_html=True

        )


    else:


        st.markdown(

            f"""

            <div class="metric-box">

            <h4>Daily Change</h4>

            <h2 class="negative">

            🔴 {daily_change:.2f}%

            </h2>

            </div>

            """,

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
# MARKET DATA CLEANING
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

        f"Missing columns: {missing_columns}"

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



if len(market_data) < 120:


    st.error(

        "Need at least 120 trading days."

    )


    st.stop()



# ============================================================
# FUTURE DATA PROVIDER CONNECTION POINT
# ============================================================


def get_external_features():

    """
    Future connection point.

    data_provider.py will eventually return:

    - S&P 500 movement
    - sector performance
    - VIX
    - interest rates
    - inflation
    - news sentiment
    - earnings data
    - macro indicators

    """

    return {}



external_features = get_external_features()



st.session_state.quantum_features = external_features
# ============================================================
# QUANTUM MULTI-FACTOR FORECAST ENGINE
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



    if len(prices) < 120:

        raise ValueError(

            "Insufficient historical data."

        )



    S0 = float(starting_price)



    # ========================================================
    # HISTORICAL RETURN ANALYSIS
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



    daily_volatility = float(

        returns.std()

    )



    if daily_volatility <= 0:

        daily_volatility = 0.01



    annual_volatility = (

        daily_volatility *

        np.sqrt(252)

    )



    # ========================================================
    # MULTIPLE TIMEFRAME TREND ANALYSIS
    # ========================================================


    trend_7 = (

        prices.iloc[-1]

        /

        prices.iloc[-7]

        - 1

    )



    trend_30 = (

        prices.iloc[-1]

        /

        prices.iloc[-30]

        - 1

    )



    trend_90 = (

        prices.iloc[-1]

        /

        prices.iloc[-90]

        - 1

    )



    trend_180 = (

        prices.iloc[-1]

        /

        prices.iloc[-180]

        - 1

    )



    momentum_score = (

        trend_7 * 0.15

        +

        trend_30 * 0.30

        +

        trend_90 * 0.35

        +

        trend_180 * 0.20

    )



    momentum_score = np.clip(

        momentum_score,

        -0.25,

        0.25

    )



    # ========================================================
    # VOLATILITY REGIME
    # ========================================================


    recent_volatility = float(

        returns.tail(30).std()

    )



    volatility_ratio = (

        recent_volatility /

        daily_volatility

    )



    volatility_penalty = np.clip(

        volatility_ratio - 1,

        0,

        1

    )



    # ========================================================
    # EXTERNAL DATA WEIGHTING
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



    global_market_score = external_features.get(

        "global_market_score",

        0

    )



    # ========================================================
    # WEIGHTED MARKET STATE MODEL
    # ========================================================


    market_state = (

        momentum_score * 0.35

        +

        macro_score * 0.15

        +

        sector_score * 0.15

        +

        sentiment_score * 0.15

        +

        global_market_score * 0.20

    )



    market_state = np.clip(

        market_state,

        -0.5,

        0.5

    )



    # ========================================================
    # REALISTIC DRIFT MODEL
    # ========================================================


    historical_drift = (

        returns.mean()

    )



    drift = (

        historical_drift * 0.45

        +

        market_state * 0.35

        -

        volatility_penalty * 0.20

    )



    # HARD LIMITS PREVENT CRAZY FORECASTS

    drift = np.clip(

        drift,

        -0.003,

        0.003

    )



    # ========================================================
    # PRICE DISTRIBUTION
    # ========================================================


    days_factor = np.sqrt(

        days / 252

    )



    expected_move = (

        drift *

        days

    )



    max_expected_move = 0.35



    expected_move = np.clip(

        expected_move,

        -max_expected_move,

        max_expected_move

    )



    expected_price = (

        S0 *

        np.exp(

            expected_move

        )

    )



    forecast_range = (

        S0 *

        annual_volatility *

        days_factor *

        2

    )



    forecast_range = np.clip(

        forecast_range,

        S0 * 0.05,

        S0 * 0.45

    )



    states = 2 ** qubits



    price_grid = np.linspace(

        max(

            S0 * 0.55,

            expected_price - forecast_range

        ),

        expected_price + forecast_range,

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
    # PROBABILITY MODEL
    # ========================================================


    expected_return = (

        expected_price /

        S0

        - 1

    )



    sigma = (

        annual_volatility *

        days_factor

    )



    if sigma <= 0:

        sigma = 0.05



    z = (

        (

            return_grid / 100

            -

            expected_return

        )

        /

        sigma

    )



    classical_probability = np.exp(

        -0.5 *

        z ** 2

    )



    # ========================================================
    # QUANTUM ENCODING
    # ========================================================


    classical_probability = (

        classical_probability /

        classical_probability.sum()

    )



    quantum_probability = None



    try:


        circuit = QuantumCircuit(

            qubits

        )


        amplitudes = np.sqrt(

            classical_probability

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



    if (

        quantum_probability is None

        or

        quantum_probability.sum() == 0

    ):


        quantum_probability = classical_probability



    else:


        quantum_probability /= quantum_probability.sum()



    # ========================================================
    # FINAL QUANTUM EXPECTATION
    # ========================================================


    quantum_expected_price = np.sum(

        price_grid *

        quantum_probability

    )



    # ========================================================
    # CONFIDENCE
    # ========================================================


    entropy = -np.sum(

        quantum_probability *

        np.log(

            quantum_probability +

            1e-12

        )

    )



    confidence = (

        1 -

        entropy /

        np.log(states)

    ) * 100



    confidence = np.clip(

        confidence,

        10,

        90

    )



    if momentum_score > 0.03:

        regime = "Bullish"


    elif momentum_score < -0.03:

        regime = "Bearish"


    else:

        regime = "Neutral"



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


        "market_state":

        market_state

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



    # ========================================================
    # EXTERNAL MARKET SIGNALS
    # FUTURE CONNECTION POINT FOR DATA_PROVIDER.PY
    # ========================================================


    external_features = {


        # Overall economy conditions

        "macro_score":

        0,



        # Industry performance

        "sector_score":

        0,



        # News / market sentiment

        "sentiment_score":

        0,



        # S&P 500 / global market movement

        "global_market_score":

        0

    }



    try:


        with st.spinner(

            "Running quantum multi-factor probability simulation..."

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



        st.session_state.market_regime = (

            result["market_regime"]

        )



        st.session_state.confidence_score = (

            result["confidence_score"]

        )



        st.success(

            "Quantum multi-factor analysis completed."

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
# QUANTUM PROBABILITY MARKET DASHBOARD
# ============================================================


st.divider()



st.subheader(

    "Quantum Probability Market Dashboard"

)



card1, card2, card3, card4 = st.columns(4)



with card1:


    st.markdown(

        f"""

        <div class="metric-box">


        <h4>Current Price</h4>


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


    predicted_change = (

        (

            forecast["expected_price"]

            -

            forecast["starting_price"]

        )

        /

        forecast["starting_price"]

    ) * 100



    color = (

        "positive"

        if predicted_change >= 0

        else "negative"

    )



    st.markdown(

        f"""

        <div class="metric-box">


        <h4>Quantum Expected Value</h4>


        <h2>

        {format_price(

            forecast["expected_price"]

        )}

        </h2>


        <p class="{color}">

        {predicted_change:+.2f}%

        </p>


        </div>

        """,

        unsafe_allow_html=True

    )





with card3:


    upside_probability = np.sum(

        forecast["probability"]

        [

            forecast["return_grid"] > 5

        ]

    ) * 100



    downside_probability = np.sum(

        forecast["probability"]

        [

            forecast["return_grid"] < -5

        ]

    ) * 100



    st.markdown(

        f"""

        <div class="metric-box">


        <h4>Upside Probability</h4>


        <h2>

        {upside_probability:.1f}%

        </h2>


        <p>

        Probability of >5% gain

        </p>


        </div>

        """,

        unsafe_allow_html=True

    )





with card4:


    st.markdown(

        f"""

        <div class="metric-box">


        <h4>Quantum Confidence</h4>


        <h2>

        {forecast["confidence_score"]:.1f}%

        </h2>


        <p>

        {forecast["market_regime"]}

        Market State

        </p>


        </div>

        """,

        unsafe_allow_html=True

    )





# ============================================================
# RISK SCENARIOS
# ============================================================


risk1, risk2, risk3 = st.columns(3)



neutral_probability = (

    100

    -

    upside_probability

    -

    downside_probability

)



neutral_probability = np.clip(

    neutral_probability,

    0,

    100

)



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
