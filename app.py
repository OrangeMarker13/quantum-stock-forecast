# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 1/6
# ============================================================

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
    validate_market_data,
    clear_data_cache
)


# Prediction memory only evaluates past forecasts.
# It does NOT modify adaptive factor weights.
from prediction_memory import (
    store_prediction,
    evaluate_predictions,
    get_prediction_adjustment
)

# ============================================================
# QUANTUM TERMINAL PREMIUM UI ENGINE
# PLACE AFTER IMPORTS
# ============================================================

def apply_quantum_ui():

    st.markdown(
    """
    <style>


    /* ================================
       GLOBAL APP BACKGROUND
    ================================= */


    .stApp {

        background:

        radial-gradient(
            circle at 15% 10%,
            rgba(34,211,238,0.22),
            transparent 35%
        ),

        radial-gradient(
            circle at 85% 90%,
            rgba(139,92,246,0.20),
            transparent 40%
        ),

        linear-gradient(
            135deg,
            #020617,
            #0f172a,
            #020617
        );

        color:#e5e7eb;

    }



    /* ================================
       TYPOGRAPHY
    ================================= */


    h1 {

        color:#22d3ee !important;

        font-weight:900 !important;

        letter-spacing:-1px;

        text-shadow:

        0 0 20px

        rgba(34,211,238,.55);

    }



    h2,h3 {

        color:#e0f2fe !important;

        font-weight:800;

    }



    p {

        color:#cbd5e1;

    }




    /* ================================
       SIDEBAR
    ================================= */


    section[data-testid="stSidebar"] {


        background:

        linear-gradient(
            180deg,
            #020617,
            #111827
        );


        border-right:

        1px solid

        rgba(34,211,238,.3);


    }



    section[data-testid="stSidebar"] * {

        color:#e2e8f0;

    }




    /* ================================
       BUTTONS
    ================================= */


    .stButton button {


        background:

        linear-gradient(
            90deg,
            #06b6d4,
            #8b5cf6
        );


        color:white;


        border:none;


        border-radius:16px;


        padding:12px 18px;


        font-weight:900;


        font-size:16px;


        box-shadow:

        0 0 25px

        rgba(34,211,238,.35);


        transition:.25s ease;


    }




    .stButton button:hover {


        transform:

        translateY(-4px);


        box-shadow:

        0 0 45px

        rgba(139,92,246,.7);


    }




    /* ================================
       METRIC CARDS
    ================================= */


    div[data-testid="metric-container"] {


        background:

        linear-gradient(
            145deg,
            rgba(15,23,42,.95),
            rgba(30,41,59,.95)
        );


        border:

        1px solid

        rgba(34,211,238,.25);


        border-radius:20px;


        padding:18px;


        box-shadow:

        0 15px 40px

        rgba(0,0,0,.35);


        transition:.25s;


    }




    div[data-testid="metric-container"]:hover {


        transform:

        translateY(-5px);


        border-color:#22d3ee;


        box-shadow:

        0 0 35px

        rgba(34,211,238,.35);


    }




    /* ================================
       CUSTOM BOXES
    ================================= */


    .metric-box {


        background:

        linear-gradient(
            145deg,
            #111827,
            #1e293b
        );


        border:

        1px solid

        rgba(34,211,238,.3);


        border-radius:22px;


        padding:20px;


        text-align:center;


        box-shadow:

        0 15px 45px

        rgba(0,0,0,.4);


        transition:.25s;


    }



    .metric-box:hover {


        transform:

        translateY(-6px);


        box-shadow:

        0 0 40px

        rgba(34,211,238,.35);


    }




    /* ================================
       GAINS / LOSSES
    ================================= */


    .positive {


        color:#22ff88 !important;


        font-weight:900 !important;


        text-shadow:

        0 0 15px

        rgba(34,255,136,.55);


    }




    .negative {


        color:#ff5555 !important;


        font-weight:900 !important;


        text-shadow:

        0 0 15px

        rgba(255,85,85,.55);


    }




    /* ================================
       TABS
    ================================= */


    button[data-baseweb="tab"] {


        background:

        rgba(15,23,42,.75);


        border-radius:14px;


        margin-right:5px;


        font-weight:800;


        color:#cbd5e1;


    }



    button[data-baseweb="tab"][aria-selected="true"] {


        background:

        linear-gradient(
            90deg,
            #0891b2,
            #7c3aed
        );


        color:white;


    }




    /* ================================
       INPUTS
    ================================= */


    input {


        background:#020617 !important;


        color:white !important;


        border-radius:12px !important;


        border:

        1px solid

        rgba(34,211,238,.25) !important;


    }



    div[data-baseweb="select"] {


        border-radius:12px;

    }




    /* ================================
       TABLES
    ================================= */


    div[data-testid="stDataFrame"] {


        border-radius:18px;


        border:

        1px solid

        rgba(34,211,238,.25);


        overflow:hidden;


    }



    /* ================================
       DOWNLOAD BUTTON
    ================================= */


    .stDownloadButton button {


        background:

        linear-gradient(
            90deg,
            #10b981,
            #06b6d4
        );


        color:white;


        border-radius:14px;


        font-weight:800;


    }




    /* ================================
       DIVIDERS
    ================================= */


    hr {


        border-color:

        rgba(34,211,238,.25);


    }




    /* ================================
       ALERTS
    ================================= */


    div[data-testid="stAlert"] {


        border-radius:16px;


        border:

        1px solid

        rgba(34,211,238,.2);


    }




    /* ================================
       REMOVE STREAMLIT BRANDING
    ================================= */


    #MainMenu {

        visibility:hidden;

    }


    footer {

        visibility:hidden;

    }



    </style>
    """,
    unsafe_allow_html=True
    )


apply_quantum_ui()
# ============================================================
# APP.PY PART 2/6
# CONTROLS + LIVE DATA + MARKET LOADING
# ============================================================


# ============================================================
# SIDEBAR CONTROLS
# ============================================================

st.sidebar.title(
    "⚛️ Quantum Forecast Controls"
)


search_query = st.sidebar.text_input(
    "Search Company or Symbol",
    "Microsoft"
)



# ------------------------------------------------------------
# STOCK SEARCH
# ------------------------------------------------------------

try:

    search_results = search_stocks(
        search_query
    )

except Exception:

    search_results = []



if search_results:


    selected_asset = st.sidebar.selectbox(

        "Select Asset",

        search_results,

        format_func=lambda x:
            x.get(
                "label",
                x.get(
                    "symbol",
                    "Unknown"
                )
            )

    )


    ticker = selected_asset.get(
        "symbol",
        search_query.upper()
    )


    company_name = selected_asset.get(
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



# ------------------------------------------------------------
# FORECAST SETTINGS
# ------------------------------------------------------------

forecast_days = st.sidebar.selectbox(

    "Forecast Horizon",

    [
        1,
        2,
        7,
        30,
        60,
        90
    ],

    index=3

)



qubits = st.sidebar.slider(

    "Quantum Qubits",

    3,

    8,

    6

)



shots = st.sidebar.slider(

    "Quantum Shots",

    500,

    5000,

    2000,

    step=500

)



st.sidebar.info(
"""
Quantum simulation:

Qubits control possible market states.

Shots control probability sampling accuracy.
"""
)



run_button = st.sidebar.button(
    "🚀 Run Quantum Forecast"
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
        "price"
    )





# ============================================================
# MARKET HEADER DISPLAY
# ============================================================


info1, info2, info3 = st.columns(3)



with info1:


    st.metric(

        "Company",

        company.get(
            "name",
            company_name
        )

    )




with info2:


    st.metric(

        "Live Price",

        format_price(
            current_price
        )

    )




with info3:


    # Reliable daily change

    daily_change = 0.0


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

        daily_change = 0.0



    color_class = (

        "positive"

        if daily_change >= 0

        else

        "negative"

    )



    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Daily Change</h4>

        <h2 class="{color_class}">

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
# HISTORICAL MARKET DATA
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
        "No market data available."
    )


    if st.button(
        "Clear Cache"
    ):


        clear_data_cache()

        st.cache_data.clear()

        st.rerun()


    st.stop()





# ============================================================
# DATA CLEANING
# ============================================================


market_data = market_data.copy()



if "Close" not in market_data.columns:


    st.error(
        "Missing closing price data."
    )


    st.stop()




market_data["Close"] = pd.to_numeric(

    market_data["Close"],

    errors="coerce"

)



market_data = market_data.dropna(

    subset=[
        "Close"
    ]

)




if len(market_data) < 120:


    st.error(

        "Insufficient historical data. Need at least 120 trading days."

    )


    st.stop()
    # ============================================================
# APP.PY PART 3/6
# EXTERNAL DATA + FEATURE PIPELINE
# ============================================================


# ============================================================
# EXTERNAL MARKET FEATURE ENGINE
# ============================================================

def get_external_features(symbol):

    """
    External factors layer.

    These values represent additional market information.
    They are independent from adaptive weight calculation.

    Future integrations:
    - Federal Reserve rates
    - CPI/inflation
    - Sector ETFs
    - Market indices
    - Earnings data
    - News sentiment APIs
    """


    return {


        # Macroeconomic environment

        "macro_score": 0.0,


        # Industry performance

        "sector_score": 0.0,


        # News/social sentiment

        "sentiment_score": 0.0,


        # Global market movement

        "global_market_score": 0.0,


        # Earnings impact

        "earnings_score": 0.0,


        # Interest rate environment

        "rate_score": 0.0


    }





external_features = get_external_features(
    ticker
)





# ============================================================
# PREDICTION MEMORY STATUS
# ============================================================


def apply_prediction_calibration(
    base_prediction,
    symbol,
    horizon
):

    """
    Applies historical forecast calibration.

    This DOES NOT:
    - change factor weights
    - change market signals
    - change quantum probability

    It only corrects systematic
    prediction error.
    """


    try:


        adjustment = get_prediction_adjustment(

            symbol,

            horizon

        )


        adjustment = float(
            adjustment
        )


        # Safety limit prevents bias

        adjustment = np.clip(

            adjustment,

            -0.05,

            0.05

        )



        return (

            base_prediction

            *

            (1 + adjustment)

        )



    except Exception:


        return base_prediction






# ============================================================
# MARKET DATA PREPARATION
# ============================================================


def prepare_market_features(data):


    if data is None:

        return pd.DataFrame()



    if data.empty:

        return data



    prepared = data.copy()



    # Ensure numerical stability


    numeric_columns = prepared.select_dtypes(

        include=[
            np.number
        ]

    ).columns



    prepared[numeric_columns] = prepared[

        numeric_columns

    ].replace(

        [
            np.inf,

            -np.inf

        ],

        np.nan

    )



    prepared[numeric_columns] = prepared[

        numeric_columns

    ].fillna(0)



    return prepared





market_data = prepare_market_features(
    market_data
)





# ============================================================
# QUANTUM FEATURE EXTRACTION
# ============================================================


def extract_quantum_inputs(data):


    if data.empty:

        return {}



    latest = data.iloc[-1]



    return {


        "price":

        float(

            latest.get(

                "Close",

                0

            )

        ),



        "volatility":

        float(

            latest.get(

                "Volatility",

                0

            )

        ),



        "momentum":

        float(

            latest.get(

                "Momentum_20",

                0

            )

        ),



        "market_strength":

        float(

            latest.get(

                "Market_Strength",

                50

            )

        ),



        "rsi":

        float(

            latest.get(

                "RSI",

                50

            )

        )

    }





quantum_inputs = extract_quantum_inputs(
    market_data
)





# ============================================================
# MODEL VALIDATION
# ============================================================


def validate_model_inputs(
    data,
    features
):


    if data.empty:

        return False



    required_columns = [

        "Close",

    ]



    for column in required_columns:


        if column not in data.columns:

            return False



    required_features = [

        "price",

        "volatility",

        "momentum",

        "market_strength",

        "rsi"

    ]



    for feature in required_features:


        if feature not in features:

            return False



    return True





model_ready = validate_model_inputs(

    market_data,

    quantum_inputs

)





if not model_ready:


    st.error(
        "Model input validation failed."
    )


    st.stop()
    # ============================================================
# APP.PY PART 4/6
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
            "Insufficient historical data"
        )



    S0 = float(
        starting_price
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



    daily_vol = float(
        returns.std()
    )



    if daily_vol <= 0:

        daily_vol = 0.01



    annual_vol = (

        daily_vol

        *

        np.sqrt(252)

    )





    # ========================================================
    # TREND SIGNAL ENGINE
    # ========================================================


    def safe_trend(window):


        if len(prices) <= window:

            return 0



        return (

            prices.iloc[-1]

            /

            prices.iloc[-window]

            -

            1

        )




    trend_7 = safe_trend(7)

    trend_30 = safe_trend(30)

    trend_90 = safe_trend(90)

    trend_180 = safe_trend(180)





    technical_signal = (

        trend_7 * 0.10

        +

        trend_30 * 0.30

        +

        trend_90 * 0.40

        +

        trend_180 * 0.20

    )



    technical_signal = np.clip(

        technical_signal,

        -0.20,

        0.20

    )





    # ========================================================
    # VOLATILITY REGIME
    # ========================================================


    recent_vol = float(

        returns

        .tail(30)

        .std()

    )



    volatility_ratio = (

        recent_vol

        /

        daily_vol

    )



    volatility_ratio = np.clip(

        volatility_ratio,

        0.5,

        3

    )





    # ========================================================
    # ADAPTIVE WEIGHTS
    #
    # ISOLATED FROM MEMORY SYSTEM
    # ========================================================


    technical_weight = (

        0.45

        /

        volatility_ratio

    )


    macro_weight = (

        0.15

        *

        volatility_ratio

    )


    global_weight = (

        0.15

        *

        volatility_ratio

    )


    sector_weight = 0.15


    sentiment_weight = 0.10




    total_weight = (

        technical_weight

        +

        macro_weight

        +

        global_weight

        +

        sector_weight

        +

        sentiment_weight

    )



    technical_weight /= total_weight

    macro_weight /= total_weight

    global_weight /= total_weight

    sector_weight /= total_weight

    sentiment_weight /= total_weight





    # ========================================================
    # EXTERNAL SIGNALS
    # ========================================================


    macro = external_features.get(
        "macro_score",
        0
    )


    sector = external_features.get(
        "sector_score",
        0
    )


    sentiment = external_features.get(
        "sentiment_score",
        0
    )


    global_market = external_features.get(
        "global_market_score",
        0
    )


    earnings = external_features.get(
        "earnings_score",
        0
    )


    rates = external_features.get(
        "rate_score",
        0
    )



    macro += rates * 0.25





    # ========================================================
    # MARKET STATE
    # ========================================================


    market_state = (

        technical_signal
        *
        technical_weight

        +

        macro
        *
        macro_weight

        +

        global_market
        *
        global_weight

        +

        sector
        *
        sector_weight

        +

        sentiment
        *
        sentiment_weight

        +

        earnings
        *
        0.10

    )



    market_state = np.clip(

        market_state,

        -0.35,

        0.35

    )





    # ========================================================
    # DRIFT MODEL
    # ========================================================


    historical_return = float(

        returns.mean()

    )



    drift = (

        historical_return * 0.60

        +

        market_state * 0.40

    )



    drift = np.clip(

        drift,

        -0.0015,

        0.0015

    )





    expected_return = drift * days





    allowed_moves = {


        1: 0.03,

        2: 0.05,

        7: 0.10,

        30: 0.18,

        60: 0.25,

        90: 0.35

    }



    allowed_move = allowed_moves.get(

        days,

        0.35

    )



    expected_return = np.clip(

        expected_return,

        -allowed_move,

        allowed_move

    )





    expected_price = (

        S0

        *

        np.exp(

            expected_return

        )

    )





    # ========================================================
    # QUANTUM PRICE STATES
    # ========================================================


    states = 2 ** qubits



    price_range = (

        S0

        *

        annual_vol

        *

        np.sqrt(

            max(days,1)

            /

            252

        )

        *

        1.5

    )



    price_range = np.clip(

        price_range,

        S0 * 0.02,

        S0 * allowed_move

    )



    lower = max(

        S0*(1-allowed_move),

        expected_price-price_range

    )



    upper = min(

        S0*(1+allowed_move),

        expected_price+price_range

    )



    price_grid = np.linspace(

        lower,

        upper,

        states

    )



    return_grid = (

        (

            price_grid

            -

            S0

        )

        /

        S0

    ) * 100
    # ============================================================
# APP.PY PART 5/6
# PROBABILITY ENGINE + RESULTS
# ============================================================



    # ========================================================
    # CLASSICAL PROBABILITY DISTRIBUTION
    # ========================================================


    target_return = (

        expected_price

        /

        S0

        -

        1

    )



    uncertainty = (

        annual_vol

        *

        np.sqrt(

            max(days,1)

            /

            252

        )

    )



    uncertainty = np.clip(

        uncertainty,

        0.02,

        allowed_move

    )



    z_score = (

        (

            return_grid / 100

            -

            target_return

        )

        /

        uncertainty

    )



    classical_probability = np.exp(

        -0.5 *

        z_score ** 2

    )





    # ========================================================
    # FACTOR ALIGNMENT
    # ========================================================


    factor_alignment = np.mean(

        [

            abs(technical_signal),

            abs(macro),

            abs(global_market),

            abs(sector),

            abs(sentiment)

        ]

    )



    factor_alignment = np.clip(

        factor_alignment,

        0,

        1

    )



    classical_probability *= (

        0.85

        +

        factor_alignment * 0.15

    )





    classical_probability = np.nan_to_num(

        classical_probability,

        nan=1.0

    )



    probability_sum = classical_probability.sum()



    if probability_sum <= 0:


        classical_probability = np.ones(

            states

        )


        probability_sum = states



    classical_probability /= probability_sum





    # ========================================================
    # QUANTUM SAMPLING
    # ========================================================


    quantum_probability = None



    try:


        circuit = QuantumCircuit(

            qubits

        )



        amplitudes = np.sqrt(

            classical_probability

        )



        amplitudes /= np.linalg.norm(

            amplitudes

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

                    count

                    /

                    shots

                )





    except Exception:


        quantum_probability = None





    # ========================================================
    # SAFE FALLBACK
    # ========================================================


    if (

        quantum_probability is None

        or

        quantum_probability.sum() <= 0

    ):


        quantum_probability = (

            classical_probability.copy()

        )


    else:


        quantum_probability /= (

            quantum_probability.sum()

        )





    # ========================================================
    # EXPECTED PRICE
    # ========================================================


    quantum_expected_price = np.sum(

        price_grid

        *

        quantum_probability

    )





    # ========================================================
    # SCENARIO PROBABILITIES
    # ========================================================


    upside_probability = (

        np.sum(

            quantum_probability[

                return_grid > 5

            ]

        )

        *

        100

    )



    downside_probability = (

        np.sum(

            quantum_probability[

                return_grid < -5

            ]

        )

        *

        100

    )



    neutral_probability = (

        100

        -

        upside_probability

        -

        downside_probability

    )



    upside_probability = np.clip(

        upside_probability,

        0,

        95

    )



    downside_probability = np.clip(

        downside_probability,

        0,

        95

    )



    neutral_probability = np.clip(

        neutral_probability,

        5,

        95

    )





    # ========================================================
    # CONFIDENCE MODEL
    # ========================================================


    entropy = -np.sum(

        quantum_probability

        *

        np.log(

            quantum_probability + 1e-12

        )

    )



    entropy_score = (

        1

        -

        entropy /

        np.log(states)

    ) * 100



    volatility_score = (

        100

        -

        annual_vol * 100

    )



    volatility_score = np.clip(

        volatility_score,

        10,

        90

    )



    confidence_score = (

        entropy_score * 0.50

        +

        volatility_score * 0.30

        +

        factor_alignment * 100 * 0.20

    )



    confidence_score = np.clip(

        confidence_score,

        10,

        95

    )





    # ========================================================
    # MARKET REGIME
    # ========================================================


    if market_state > 0.08:


        regime = "Bullish"



    elif market_state < -0.08:


        regime = "Bearish"



    else:


        regime = "Neutral"





    # ========================================================
    # RISK SCORE
    # ========================================================


    risk_score = (

        annual_vol * 100

        *

        (

            downside_probability

            /

            100

        )

    )





    # ========================================================
    # RETURN MODEL OUTPUT
    # ========================================================


    return {

        "starting_price": S0,

        "price_grid": price_grid,

        "return_grid": return_grid,

        "probability": quantum_probability,

        "expected_price": quantum_expected_price,

        "volatility": annual_vol * 100,

        "returns": returns,

        "market_regime": regime,

        "confidence_score": confidence_score,

        "market_state": market_state,

        "risk_score": risk_score,


        "upside_probability": upside_probability,

        "downside_probability": downside_probability,

        "neutral_probability": neutral_probability,


        "model_metadata": {

            "technical_signal": technical_signal,

            "market_state": market_state

        }

    }



# ============================================================
# FORECAST EXECUTION
# ============================================================


settings = [

    ticker,

    forecast_days,

    qubits,

    shots

]



if run_button:


    run_price = (

        float(current_price)

        if current_price

        else

        float(

            market_data["Close"].iloc[-1]

        )

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

                shots,

                external_features

            )



        st.session_state.forecast = result


        st.session_state.forecast_settings = settings


        st.session_state.last_run = (

            datetime.datetime.now()

            .strftime("%H:%M:%S")

        )


        st.session_state.last_price = run_price


        st.session_state.risk_score = (

            result["risk_score"]

        )


        st.session_state.confidence_score = (

            result["confidence_score"]

        )


        st.session_state.market_regime = (

            result["market_regime"]

        )


        st.success(

            "Quantum analysis completed."

        )



    except Exception as error:


        st.error(

            f"Forecast failed: {error}"

        )


        st.stop()
    # ============================================================
# APP.PY PART 6/6
# DASHBOARD + EXPORT + PREDICTION MEMORY
# ============================================================


# ============================================================
# VALIDATION
# ============================================================


if st.session_state.forecast is None:


    st.info(
        "Select settings and run a forecast."
    )


    st.stop()



forecast = st.session_state.forecast



if st.session_state.forecast_settings != settings:


    st.warning(
        "Settings changed. Run forecast again."
    )





# ============================================================
# PREDICTION MEMORY RECORDING
# ============================================================


def save_prediction_record(
    ticker,
    forecast,
    horizon
):


    """
    Stores forecast for future residual analysis.

    This does not affect current predictions.

    It is only used to measure:
    predicted vs actual error.
    """


    try:


        from prediction_memory import save_prediction



        save_prediction(

            ticker,

            horizon,

            forecast["starting_price"],

            forecast["expected_price"]

        )



    except Exception:


        pass





save_prediction_record(

    ticker,

    forecast,

    forecast_days

)





# ============================================================
# DASHBOARD
# ============================================================


st.divider()


st.subheader(
    "⚛️ Quantum Probability Dashboard"
)



expected_price = forecast["expected_price"]



price_change = (

    (

        expected_price

        -

        forecast["starting_price"]

    )

    /

    forecast["starting_price"]

) * 100





c1,c2,c3,c4 = st.columns(4)



with c1:


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





with c2:


    cls = (

        "positive"

        if price_change >= 0

        else

        "negative"

    )



    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Expected Price</h4>

        <h2>

        {format_price(expected_price)}

        </h2>


        <p class="{cls}">

        {price_change:+.2f}%

        </p>

        </div>

        """,

        unsafe_allow_html=True

    )





with c3:


    st.metric(

        "Upside Probability",

        f"{forecast['upside_probability']:.1f}%"

    )





with c4:


    st.metric(

        "Confidence",

        f"{forecast['confidence_score']:.1f}%"

    )



st.caption(

    f"""

    Regime: {forecast['market_regime']}

    |

    Last Simulation:

    {st.session_state.last_run}

    """

)





# ============================================================
# SCENARIOS
# ============================================================


st.divider()



s1,s2,s3 = st.columns(3)



with s1:

    st.metric(

        "Bull Scenario",

        f"{forecast['upside_probability']:.1f}%"

    )



with s2:

    st.metric(

        "Neutral Scenario",

        f"{forecast['neutral_probability']:.1f}%"

    )



with s3:

    st.metric(

        "Bear Scenario",

        f"{forecast['downside_probability']:.1f}%"

    )





# ============================================================
# ANALYTICS TABS
# ============================================================


tab1,tab2,tab3,tab4 = st.tabs(

    [

        "Overview",

        "Forecast",

        "Risk",

        "Quantum"

    ]

)





with tab1:


    st.subheader(

        "Market Statistics"

    )


    returns = forecast["returns"]



    a,b,c,d = st.columns(4)



    a.metric(

        "Average Daily Return",

        f"{returns.mean()*100:.3f}%"

    )



    b.metric(

        "Daily Volatility",

        f"{returns.std()*100:.3f}%"

    )



    c.metric(

        "Best Day",

        f"{returns.max()*100:.2f}%"

    )



    d.metric(

        "Worst Day",

        f"{returns.min()*100:.2f}%"

    )







with tab2:


    fig,ax = plt.subplots(

        figsize=(10,4)

    )


    ax.plot(

        forecast["return_grid"],

        forecast["probability"]

    )


    ax.set_xlabel(

        "Return (%)"

    )


    ax.set_ylabel(

        "Probability"

    )


    ax.set_title(

        "Quantum Probability Distribution"

    )


    ax.grid(

        alpha=0.3

    )


    st.pyplot(

        fig,

        width="stretch"

    )


    plt.close(fig)







with tab3:


    st.metric(

        "Risk Score",

        f"{forecast['risk_score']:.2f}"

    )



    st.metric(

        "Annual Volatility",

        f"{forecast['volatility']:.2f}%"

    )







with tab4:


    st.write(

"""
Historical Market Data

↓

Feature Extraction

↓

Adaptive Probability Model

↓

Quantum State Encoding

↓

Qiskit Aer MPS Sampling

↓

Probability Forecast
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

        "Shots",

        shots

    )





# ============================================================
# EXPORT
# ============================================================


st.divider()



export = pd.DataFrame(

    {

        "Future Price":

            forecast["price_grid"],


        "Return %":

            forecast["return_grid"],


        "Probability":

            forecast["probability"]

    }

)




st.download_button(

    "Download Forecast CSV",

    export.to_csv(index=False),

    file_name=f"{ticker}_forecast.csv",

    mime="text/csv",

    width="stretch"

)





# ============================================================
# FOOTER
# ============================================================


st.divider()



st.caption(

f"""

⚛️ Quantum Equity Research Terminal


Ticker: {ticker}


Quantum States: {2 ** qubits}


Qubits: {qubits}


Last Simulation: {st.session_state.last_run}


Probability model only. Not financial advice.

"""

)
