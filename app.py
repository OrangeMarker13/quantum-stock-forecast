# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# PART 1/11
# ============================================================

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import gc
import time

from datetime import datetime

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


from prediction_memory import (
    store_prediction,
    evaluate_predictions,
    get_prediction_adjustment,
    complete_prediction
)



# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="Quantum Equity Research Terminal",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.set_option(
    "client.showErrorDetails",
    False
)



# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {

    "forecast": None,

    "forecast_settings": None,

    "last_run": "Never",

    "last_price": None,

    "prediction_id": None,

    "risk_score": 0,

    "confidence_score": 0,

    "market_regime": "Unknown"

}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value



# ============================================================
# FORMAT HELPERS
# ============================================================

def get_change_class(value):

    try:

        value = float(value)

        if value > 0:
            return "positive"

        if value < 0:
            return "negative"

        return "neutral"

    except:

        return "neutral"



def format_percent(value):

    try:

        value = float(value)

        arrow = "▲" if value >= 0 else "▼"

        return f"{arrow} {value:+.2f}%"

    except:

        return "N/A"



# ============================================================
# QUANTUM UI
# ============================================================

def apply_quantum_ui():

    st.markdown(
        """
        <style>

        .stApp {

            background:
            radial-gradient(
                circle at 10% 10%,
                rgba(34,211,238,.18),
                transparent 35%
            ),
            radial-gradient(
                circle at 90% 90%,
                rgba(139,92,246,.18),
                transparent 40%
            ),
            linear-gradient(
                135deg,
                #020617,
                #0f172a
            );

        }


        h1 {

            color:#22d3ee !important;

            font-weight:900;

        }


        h2,h3,h4 {

            color:#e0f2fe !important;

        }


        p {

            color:#cbd5e1;

        }


        section[data-testid="stSidebar"] {

            background:#020617;

        }


        .stButton button {

            background:
            linear-gradient(
                90deg,
                #06b6d4,
                #8b5cf6
            );

            color:white;

            border-radius:16px;

            font-weight:900;

        }


        .metric-box {

            background:
            rgba(15,23,42,.8);

            border:
            1px solid
            rgba(34,211,238,.25);

            border-radius:18px;

            padding:18px;

            text-align:center;

        }


        .positive {

            color:#22ff88;

            font-weight:900;

        }


        .negative {

            color:#ff5555;

            font-weight:900;

        }


        .neutral {

            color:#22d3ee;

            font-weight:900;

        }

        </style>
        """,
        unsafe_allow_html=True
    )


apply_quantum_ui()



# ============================================================
# DISPLAY FUNCTIONS
# ============================================================

def render_metric_card(
    title,
    value,
    change=None
):

    change_html = ""

    if change is not None:

        change_html = f"""

        <div class="{get_change_class(change)}">

        {format_percent(change)}

        </div>

        """


    st.markdown(
        f"""

        <div class="metric-box">

        <h4>{title}</h4>

        <h2>{value}</h2>

        {change_html}

        </div>

        """,
        unsafe_allow_html=True
    )



def render_status_badge(
    text,
    status="neutral"
):

    st.markdown(
        f"""

        <div class="{status}"

        style="

        display:inline-block;

        padding:8px 18px;

        border-radius:20px;

        border:1px solid currentColor;

        ">

        {text}

        </div>

        """,

        unsafe_allow_html=True
    )



# ============================================================
# LOADING ANIMATION
# ============================================================

def quantum_loading():

    box = st.empty()

    frames = [

        "⚛️ Initializing quantum states",

        "⚛️ Encoding probability space",

        "⚛️ Running simulation",

        "⚛️ Measuring results"

    ]


    for frame in frames:

        box.markdown(

            f"""

            <div class="metric-box">

            <h3>{frame}</h3>

            </div>

            """,

            unsafe_allow_html=True

        )

        time.sleep(.35)


    box.empty()



# ============================================================
# RESET
# ============================================================

def reset_forecast_state():

    for key,value in DEFAULT_STATE.items():

        st.session_state[key] = value


    gc.collect()
# ============================================================
# APP.PY
# PART 2/11
# MARKET DATA PIPELINE
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



# ============================================================
# STOCK SEARCH
# ============================================================

try:

    search_results = search_stocks(
        search_query
    )

except Exception:

    search_results = []



if search_results:

    selected = st.sidebar.selectbox(
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


    ticker = selected.get(
        "symbol",
        search_query
    ).upper()


    company_name = selected.get(
        "name",
        ticker
    )


else:

    ticker = search_query.strip().upper()

    company_name = ticker



# ============================================================
# FORECAST SETTINGS
# ============================================================

forecast_days = st.sidebar.selectbox(
    "Forecast Horizon",
    [1,2,7,30,60,90],
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
    3000,
    1500,
    step=500
)



st.sidebar.info(
    """
Quantum parameters:

• Qubits define probability states
• Shots increase sampling accuracy
• Adaptive memory adjusts future predictions
"""
)



run_button = st.sidebar.button(
    "🚀 Run Quantum Forecast"
)


clear_button = st.sidebar.button(
    "🧹 Clear"
)



if clear_button:

    reset_state()

    st.rerun()



# ============================================================
# LIVE PRICE CACHE
# ============================================================

@st.cache_data(
    ttl=60,
    max_entries=100
)
def cached_price(symbol):

    try:

        return get_live_price(symbol)

    except Exception:

        return {}



live_data = cached_price(
    ticker
)



# ============================================================
# COMPANY CACHE
# ============================================================

@st.cache_data(
    ttl=3600,
    max_entries=100
)
def cached_company(symbol):

    try:

        return get_company_info(symbol)

    except Exception:

        return {}



company = cached_company(
    ticker
)


if not company:

    company = {
        "name":company_name
    }



# ============================================================
# CURRENT PRICE
# ============================================================

current_price = None

daily_change = 0



if live_data:

    current_price = safe_float(
        live_data.get(
            "price"
        )
    )


    daily_change = safe_float(
        live_data.get(
            "change_percent"
        )
    )



# ============================================================
# HEADER METRICS
# ============================================================

c1,c2,c3 = st.columns(3)



with c1:

    metric_card(
        "Company",
        company.get(
            "name",
            ticker
        )
    )



with c2:

    metric_card(
        "Live Price",
        format_price(
            current_price
        )
    )



with c3:

    metric_card(
        "Daily Change",
        percent_text(
            daily_change
        ),
        daily_change
    )



st.caption(
    f"""
Last update:
{datetime.datetime.now().strftime('%H:%M:%S')}
|
Ticker:
{ticker}
"""
)



# ============================================================
# HISTORICAL DATA CACHE
# ============================================================

@st.cache_data(
    ttl=900,
    max_entries=50
)
def cached_history(symbol):

    try:

        data = get_stock_data(
            symbol
        )


        if data is None:
            return pd.DataFrame()


        if not validate_market_data(
            data
        ):

            return pd.DataFrame()


        return data.copy()


    except Exception:

        return pd.DataFrame()



market_data = cached_history(
    ticker
)



# ============================================================
# MARKET DATA VALIDATION
# ============================================================

if market_data.empty:

    st.error(
        "No historical market data available."
    )

    st.stop()



if "Close" not in market_data.columns:

    st.error(
        "Missing Close price column."
    )

    st.stop()



market_data["Close"] = pd.to_numeric(
    market_data["Close"],
    errors="coerce"
)



market_data = (
    market_data
    .replace(
        [
            np.inf,
            -np.inf
        ],
        np.nan
    )
    .dropna(
        subset=[
            "Close"
        ]
    )
)



if len(market_data) < 120:

    st.warning(
        "Limited historical data detected."
    )



# ============================================================
# RECENT DATA VIEW
# ============================================================

with st.expander(
    "📈 Recent Market Data"
):

    recent = market_data.tail(
        50
    ).copy()


    recent["Return %"] = (
        recent["Close"]
        .pct_change()
        *
        100
    )


    st.dataframe(
        recent,
        use_container_width=True
    )
# ============================================================
# APP.PY
# PART 3/11
# FEATURE ENGINEERING + MODEL INPUTS
# ============================================================


# ============================================================
# EXTERNAL FEATURES
# ============================================================

def get_external_features(symbol):

    # Placeholder system.
    # Replace values with APIs for:
    # macro data, news sentiment,
    # sector movement, earnings, rates.

    return {

        "macro_score":0.0,

        "sector_score":0.0,

        "sentiment_score":0.0,

        "global_market_score":0.0,

        "earnings_score":0.0,

        "rate_score":0.0

    }



external_features = get_external_features(
    ticker
)



# ============================================================
# CLEAN DATA
# ============================================================

def clean_market_data(data):

    df = data.copy()


    numeric_columns = df.select_dtypes(
        include=np.number
    ).columns


    df[numeric_columns] = (
        df[numeric_columns]
        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )
        .fillna(0)
    )


    return df



market_data = clean_market_data(
    market_data
)



# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def add_features(data):

    df = data.copy()


    # Returns

    df["Return"] = (
        df["Close"]
        .pct_change()
        .fillna(0)
    )



    # Moving averages

    df["MA_7"] = (
        df["Close"]
        .rolling(7)
        .mean()
    )


    df["MA_30"] = (
        df["Close"]
        .rolling(30)
        .mean()
    )


    df["MA_90"] = (
        df["Close"]
        .rolling(90)
        .mean()
    )



    # Volatility

    df["Volatility"] = (
        df["Return"]
        .rolling(30)
        .std()
    )



    # Momentum

    df["Momentum_20"] = (
        df["Close"]
        /
        df["Close"].shift(20)
        -
        1
    )



    # RSI

    delta = df["Close"].diff()


    gains = delta.clip(
        lower=0
    )


    losses = -delta.clip(
        upper=0
    )


    avg_gain = (
        gains
        .rolling(14)
        .mean()
    )


    avg_loss = (
        losses
        .rolling(14)
        .mean()
    )


    rs = (
        avg_gain
        /
        (avg_loss + 1e-9)
    )


    df["RSI"] = (
        100
        -
        (
            100
            /
            (1 + rs)
        )
    )



    # Market strength

    df["Market_Strength"] = (
        df["MA_30"]
        /
        (df["MA_90"] + 1e-9)
        *
        50
    )


    df["Market_Strength"] = np.clip(
        df["Market_Strength"],
        0,
        100
    )



    return (
        df
        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )
        .fillna(0)
    )



market_data = add_features(
    market_data
)



# ============================================================
# QUANTUM INPUT EXTRACTION
# ============================================================

def extract_inputs(data):

    row = data.iloc[-1]


    return {

        "price":
            float(row["Close"]),

        "volatility":
            float(row["Volatility"]),

        "momentum":
            float(row["Momentum_20"]),

        "market_strength":
            float(row["Market_Strength"]),

        "rsi":
            float(row["RSI"])

    }



quantum_inputs = extract_inputs(
    market_data
)



# ============================================================
# MODEL VALIDATION
# ============================================================

def validate_inputs(
    data,
    inputs
):

    required_columns = [

        "Close",

        "Return",

        "Volatility",

        "Momentum_20",

        "RSI"

    ]


    required_inputs = [

        "price",

        "volatility",

        "momentum",

        "market_strength",

        "rsi"

    ]


    return (

        not data.empty

        and

        all(
            x in data.columns
            for x in required_columns
        )

        and

        all(
            x in inputs
            for x in required_inputs
        )

    )



if not validate_inputs(
    market_data,
    quantum_inputs
):

    st.error(
        "Model input validation failed."
    )

    st.stop()



# ============================================================
# INPUT DISPLAY
# ============================================================

with st.expander(
    "⚛️ Quantum Input State"
):

    input_table = pd.DataFrame(
        {

            "Feature":
                list(
                    quantum_inputs.keys()
                ),

            "Value":
                list(
                    quantum_inputs.values()
                )

        }
    )


    st.dataframe(
        input_table,
        use_container_width=True
    )
# ============================================================
# APP.PY
# PART 4/11
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
            "Insufficient market history."
        )


    S0 = float(
        starting_price
    )



    # ========================================================
    # RETURNS + VOLATILITY
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
        daily_volatility
        *
        np.sqrt(252)
    )



    # ========================================================
    # TREND SIGNAL
    # ========================================================

    def trend(window):

        if len(prices) <= window:

            return 0


        return (
            prices.iloc[-1]
            /
            prices.iloc[-window]
            -
            1
        )



    trend_signal = (

        trend(7) * .10

        +

        trend(30) * .30

        +

        trend(90) * .40

        +

        trend(180) * .20

    )


    technical_signal = np.clip(
        trend_signal,
        -.20,
        .20
    )



    # ========================================================
    # VOLATILITY REGIME
    # ========================================================

    recent_vol = float(
        returns.tail(30).std()
    )


    volatility_ratio = np.clip(

        recent_vol
        /
        daily_volatility,

        .5,

        3

    )



    # ========================================================
    # ADAPTIVE WEIGHTS
    # ========================================================

    weights = {

        "technical":
            .45 / volatility_ratio,

        "macro":
            .15 * volatility_ratio,

        "global":
            .15 * volatility_ratio,

        "sector":
            .15,

        "sentiment":
            .10

    }



    total_weight = sum(
        weights.values()
    )


    weights = {

        key:
        value / total_weight

        for key,value
        in weights.items()

    }



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


    rate = external_features.get(
        "rate_score",
        0
    )


    macro += rate * .25



    # ========================================================
    # MARKET STATE
    # ========================================================

    market_state = (

        technical_signal
        *
        weights["technical"]

        +

        macro
        *
        weights["macro"]

        +

        global_market
        *
        weights["global"]

        +

        sector
        *
        weights["sector"]

        +

        sentiment
        *
        weights["sentiment"]

        +

        earnings
        *
        .10

    )


    market_state = np.clip(
        market_state,
        -.35,
        .35
    )



    # ========================================================
    # EXPECTED DRIFT
    # ========================================================

    historical_return = float(
        returns.mean()
    )


    drift = (

        historical_return
        *
        .60

        +

        market_state
        *
        .40

    )


    drift = np.clip(
        drift,
        -.0015,
        .0015
    )


    expected_return = (
        drift
        *
        days
    )



    # ========================================================
    # PRICE MOVEMENT LIMITS
    # ========================================================

    limits = {

        1:.03,

        2:.05,

        7:.10,

        30:.18,

        60:.25,

        90:.35

    }


    allowed_move = limits.get(
        days,
        .35
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
    # QUANTUM PRICE GRID
    # ========================================================

    states = 2 ** qubits


    price_range = (

        S0

        *

        annual_volatility

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

        S0*.02,

        S0*allowed_move

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

        (price_grid-S0)

        /

        S0

        *

        100

    )



    # Continue in Part 5
# ============================================================
# APP.PY
# PART 5/11
# QUANTUM SAMPLING + FORECAST OUTPUT
# ============================================================



    # ========================================================
    # CLASSICAL PROBABILITY MODEL
    # ========================================================

    target_return = (
        expected_price
        /
        S0
        -
        1
    )


    uncertainty = (

        annual_volatility

        *

        np.sqrt(
            max(days,1)
            /
            252
        )

    )


    uncertainty = np.clip(
        uncertainty,
        .02,
        allowed_move
    )



    z = (

        (
            return_grid / 100
            -
            target_return
        )

        /

        uncertainty

    )


    probability = np.exp(
        -.5 * z**2
    )


    probability = np.nan_to_num(
        probability,
        nan=1,
        posinf=1,
        neginf=0
    )


    total_probability = (
        probability.sum()
    )


    if total_probability <= 0:

        probability = np.ones(
            states
        )

        total_probability = states



    probability /= total_probability



    # ========================================================
    # QUANTUM CIRCUIT SIMULATION
    # ========================================================

    quantum_probability = None


    try:

        amplitudes = np.sqrt(
            probability
        )


        amplitudes /= np.linalg.norm(
            amplitudes
        )


        circuit = QuantumCircuit(
            qubits
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



        for state,count in counts.items():

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
    # FALLBACK SAFETY
    # ========================================================

    if (

        quantum_probability is None

        or

        quantum_probability.sum() == 0

    ):

        quantum_probability = (
            probability.copy()
        )


    else:

        quantum_probability /= (
            quantum_probability.sum()
        )



    # ========================================================
    # EXPECTED QUANTUM PRICE
    # ========================================================

    quantum_expected_price = np.sum(

        price_grid

        *

        quantum_probability

    )



    # ========================================================
    # PROBABILITY ZONES
    # ========================================================

    upside_probability = (

        quantum_probability[
            return_grid > 5
        ]
        .sum()

        *

        100

    )


    downside_probability = (

        quantum_probability[
            return_grid < -5
        ]
        .sum()

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
    # CONFIDENCE SCORE
    # ========================================================

    entropy = -np.sum(

        quantum_probability

        *

        np.log(
            quantum_probability
            +
            1e-12
        )

    )


    entropy_score = (

        1

        -

        entropy
        /
        np.log(states)

    ) * 100



    volatility_score = np.clip(

        100
        -
        annual_volatility * 100,

        10,

        90

    )



    confidence_score = (

        entropy_score
        *
        .50

        +

        volatility_score
        *
        .30

        +

        abs(market_state)
        *
        100
        *
        .20

    )



    confidence_score = np.clip(

        confidence_score,

        10,

        95

    )



    # ========================================================
    # MARKET REGIME
    # ========================================================

    if market_state > .08:

        regime = "Bullish"


    elif market_state < -.08:

        regime = "Bearish"


    else:

        regime = "Neutral"



    # ========================================================
    # RISK SCORE
    # ========================================================

    risk_score = (

        annual_volatility

        *

        100

        *

        downside_probability

        /

        100

    )



    # ========================================================
    # MODEL TRACE DATA
    # ========================================================

    metadata = {

        "weights":

        {

            key:

            round(
                value * 100,
                2
            )

            for key,value
            in weights.items()

        },


        "technical_signal":

        round(
            float(
                technical_signal
            ),
            4
        ),


        "market_state":

        round(
            float(
                market_state
            ),
            4
        )

    }



    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    return {

        "starting_price":
            S0,


        "expected_price":
            quantum_expected_price,


        "price_grid":
            price_grid,


        "return_grid":
            return_grid,


        "probability":
            quantum_probability,


        "classical_probability":
            probability,


        "volatility":
            annual_volatility * 100,


        "returns":
            returns,


        "market_regime":
            regime,


        "confidence_score":
            confidence_score,


        "risk_score":
            risk_score,


        "market_state":
            market_state,


        "upside_probability":
            upside_probability,


        "downside_probability":
            downside_probability,


        "neutral_probability":
            neutral_probability,


        "model_metadata":
            metadata

    }
# ============================================================
# APP.PY
# PART 6/11
# FORECAST EXECUTION + ADAPTIVE MEMORY
# ============================================================



# ============================================================
# FORECAST SETTINGS
# ============================================================

forecast_settings = [

    ticker,

    forecast_days,

    qubits,

    shots

]



# ============================================================
# RUN FORECAST
# ============================================================

if run_button:


    execution_price = (

        safe_float(
            current_price
        )

        if current_price

        else

        safe_float(
            market_data["Close"].iloc[-1]
        )

    )



    try:


        quantum_loading()



        with st.spinner(
            "Running quantum probability simulation..."
        ):


            result = quantum_forecast(

                market_data,

                execution_price,

                forecast_days,

                qubits,

                shots,

                external_features

            )



        # ====================================================
        # SAVE PREDICTION MEMORY
        # ====================================================

        prediction_id = store_prediction(

            ticker,

            forecast_days,

            execution_price,

            result["expected_price"]

        )



        # ====================================================
        # SESSION STORAGE
        # ====================================================

        st.session_state.forecast = result


        st.session_state.settings = (
            forecast_settings
        )


        st.session_state.last_run = (
            datetime.datetime.now()
            .strftime(
                "%H:%M:%S"
            )
        )


        st.session_state.last_price = (
            execution_price
        )


        st.session_state.prediction_id = (
            prediction_id
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
# LOAD FORECAST
# ============================================================

forecast = (
    st.session_state.forecast
)



# ============================================================
# MEMORY ADJUSTMENT
# ============================================================

try:

    adaptive_adjustment = (
        get_prediction_adjustment()
    )

except Exception:

    adaptive_adjustment = 0



# ============================================================
# APPLY LEARNING CORRECTION
# ============================================================

if forecast is not None:


    forecast["adaptive_adjustment"] = (
        adaptive_adjustment
    )


    forecast["adjusted_price"] = (

        forecast["expected_price"]

        +

        adaptive_adjustment

    )



# ============================================================
# PREDICTION EVALUATION STATUS
# ============================================================

with st.sidebar.expander(
    "🧠 Model Learning Status"
):


    try:

        history = evaluate_predictions()


        st.write(
            f"Stored Predictions: {len(history)}"
        )


        st.write(
            f"Adaptive Bias: {adaptive_adjustment:.4f}"
        )


    except Exception:


        st.write(
            "Memory system initializing..."
        )



# ============================================================
# GARBAGE COLLECTION
# ============================================================

if len(gc.get_objects()) > 500000:

    gc.collect()
# ============================================================
# APP.PY
# PART 7/11
# FORECAST DASHBOARD
# ============================================================



# ============================================================
# MAIN HEADER
# ============================================================

st.title(
    "⚛️ Quantum Equity Research Terminal"
)



if forecast is None:


    st.info(
        "Run a quantum forecast from the sidebar."
    )


    st.stop()



# ============================================================
# SUMMARY METRICS
# ============================================================

col1,col2,col3,col4 = st.columns(4)



with col1:

    metric_card(

        "Expected Price",

        format_price(

            forecast["expected_price"]

        )

    )



with col2:


    expected_return = (

        forecast["expected_price"]

        /

        forecast["starting_price"]

        -

        1

    ) * 100



    metric_card(

        "Expected Return",

        f"{expected_return:+.2f}%",

        expected_return

    )



with col3:


    metric_card(

        "Confidence",

        f"{forecast['confidence_score']:.1f}%"

    )



with col4:


    metric_card(

        "Risk Score",

        f"{forecast['risk_score']:.2f}"

    )



st.divider()



# ============================================================
# MARKET REGIME
# ============================================================

c1,c2,c3 = st.columns(3)



with c1:


    regime = forecast["market_regime"]


    if regime == "Bullish":

        status = "positive"


    elif regime == "Bearish":

        status = "negative"


    else:

        status = "neutral"



    st.markdown(

        f"""
        <div class="card">

        <h3 class="{status}">

        {regime}

        </h3>

        </div>
        """,

        unsafe_allow_html=True

    )



with c2:


    st.metric(

        "Upside Probability",

        f"{forecast['upside_probability']:.2f}%"

    )



with c3:


    st.metric(

        "Downside Probability",

        f"{forecast['downside_probability']:.2f}%"

    )



# ============================================================
# QUANTUM DISTRIBUTION GRAPH
# ============================================================

st.subheader(
    "⚛️ Quantum Price Probability"
)



fig,ax = plt.subplots(
    figsize=(10,4)
)


ax.plot(

    forecast["price_grid"],

    forecast["probability"]

)


ax.set_xlabel(
    "Future Price"
)


ax.set_ylabel(
    "Probability"
)


ax.set_title(
    "Quantum State Distribution"
)



st.pyplot(
    fig,
    clear_figure=True
)



# ============================================================
# RETURN DISTRIBUTION
# ============================================================

st.subheader(
    "📈 Return Probability"
)



fig,ax = plt.subplots(
    figsize=(10,4)
)


ax.plot(

    forecast["return_grid"],

    forecast["probability"]

)



ax.set_xlabel(
    "Return %"
)


ax.set_ylabel(
    "Probability"
)



ax.set_title(
    "Future Return Distribution"
)



st.pyplot(
    fig,
    clear_figure=True
)



# ============================================================
# KEY MODEL OUTPUTS
# ============================================================

with st.expander(
    "⚛️ Forecast Summary"
):


    summary = pd.DataFrame(

        {

            "Metric":[

                "Ticker",

                "Forecast Horizon",

                "Starting Price",

                "Expected Price",

                "Volatility",

                "Market Regime",

                "Confidence",

                "Risk Score"

            ],


            "Value":[

                ticker,

                f"{forecast_days} days",

                format_price(
                    forecast["starting_price"]
                ),

                format_price(
                    forecast["expected_price"]
                ),

                f"{forecast['volatility']:.2f}%",

                forecast["market_regime"],

                f"{forecast['confidence_score']:.2f}%",

                f"{forecast['risk_score']:.2f}"

            ]

        }

    )


    st.dataframe(

        summary,

        hide_index=True,

        use_container_width=True

    )
# ============================================================
# APP.PY
# PART 8/11
# QUANTUM DECISION TRACE + MODEL MEMORY
# ============================================================



# ============================================================
# QUANTUM DECISION TRACE
# ============================================================

with st.expander(
    "⚛️ Quantum Decision Trace"
):


    metadata = forecast.get(
        "model_metadata",
        {}
    )


    weights = metadata.get(
        "weights",
        {}
    )



    st.subheader(
        "Signal Influence"
    )



    if weights:


        weight_table = pd.DataFrame(

            {

                "Signal":[

                    "Technical",

                    "Macro",

                    "Global",

                    "Sector",

                    "Sentiment"

                ],


                "Weight":[

                    weights.get(
                        "technical",
                        0
                    ),

                    weights.get(
                        "macro",
                        0
                    ),

                    weights.get(
                        "global",
                        0
                    ),

                    weights.get(
                        "sector",
                        0
                    ),

                    weights.get(
                        "sentiment",
                        0
                    )

                ]

            }

        )


        weight_table["Weight"] = (

            weight_table["Weight"]

            .apply(

                lambda x:

                f"{x:.2f}%"

            )

        )


        st.dataframe(

            weight_table,

            hide_index=True,

            use_container_width=True

        )



    c1,c2 = st.columns(2)



    with c1:


        st.metric(

            "Technical Signal",

            f"{metadata.get('technical_signal',0):.4f}"

        )



    with c2:


        st.metric(

            "Market State",

            f"{metadata.get('market_state',0):.4f}"

        )



# ============================================================
# MODEL MEMORY DASHBOARD
# ============================================================

with st.expander(
    "🧠 Prediction Memory System"
):


    try:


        history = evaluate_predictions()



        adjustment = (
            get_prediction_adjustment()
        )



        st.metric(

            "Adaptive Price Adjustment",

            f"{adjustment:.4f}"

        )



        if history:


            memory_df = pd.DataFrame(
                history
            )


            st.write(
                "Prediction History"
            )


            st.dataframe(

                memory_df,

                use_container_width=True

            )


        else:


            st.info(
                "No completed predictions yet."
            )



    except Exception as error:


        st.warning(

            f"Memory unavailable: {error}"

        )



# ============================================================
# LEARNING EXPLANATION
# ============================================================

with st.expander(
    "🧬 Adaptive Learning Framework"
):


    st.markdown(
        """
The model improves through prediction feedback.

Workflow:

1. Forecast generated.
2. Prediction stored in memory.
3. Future market price is compared.
4. Prediction error is calculated.
5. Bias adjustment updates future forecasts.

Current learning components:

• Historical prediction error tracking
• Average directional bias correction
• Forecast accuracy monitoring
• Adaptive adjustment value
"""
    )



# ============================================================
# FORECAST IDENTIFIER
# ============================================================

if st.session_state.prediction_id:


    st.caption(

        f"""
Prediction ID:
{st.session_state.prediction_id}
"""

    )
# ============================================================
# APP.PY
# PART 9/11
# FINAL ANALYTICS + PREDICTION FEEDBACK LOOP
# ============================================================


# ============================================================
# SAFE VALUE HELPERS
# ============================================================

def safe_float(value, default=0):

    try:

        if value is None:
            return default

        return float(value)

    except Exception:

        return default



def metric_card(
    title,
    value,
    change=None
):

    render_metric_card(
        title,
        value,
        change
    )



def percent_text(value):

    return format_percent(
        value
    )



# ============================================================
# COMPLETE OLD PREDICTION
# ============================================================

with st.expander(
    "📊 Prediction Accuracy Feedback"
):


    prediction_id = (
        st.session_state.prediction_id
    )


    if prediction_id:


        st.write(
            "Enter the actual market price after the forecast period."
        )


        actual_price = st.number_input(

            "Actual Price",

            min_value=0.0,

            value=0.0

        )


        if st.button(
            "Submit Prediction Result"
        ):


            if actual_price > 0:


                completed = complete_prediction(

                    prediction_id,

                    actual_price

                )


                if completed:

                    st.success(
                        "Prediction evaluated and memory updated."
                    )


                else:

                    st.error(
                        "Prediction ID not found."
                    )


            else:

                st.warning(
                    "Enter a valid price."
                )


    else:


        st.info(
            "Run a forecast before submitting results."
        )



# ============================================================
# ACCURACY METRICS
# ============================================================

with st.expander(
    "📈 Model Performance"
):


    try:

        history = evaluate_predictions()


        if history:


            df = pd.DataFrame(
                history
            )


            completed = df[
                df["actual_price"].notna()
            ]


            if not completed.empty:


                completed["error_percent"] = (

                    abs(

                        completed["actual_price"]

                        -

                        completed["predicted_price"]

                    )

                    /

                    completed["predicted_price"]

                    *

                    100

                )



                accuracy = max(

                    0,

                    100 -
                    completed["error_percent"].mean()

                )


                col1,col2,col3 = st.columns(3)



                with col1:

                    st.metric(

                        "Predictions",

                        len(completed)

                    )



                with col2:

                    st.metric(

                        "Accuracy",

                        f"{accuracy:.2f}%"

                    )



                with col3:

                    st.metric(

                        "Average Error",

                        f"{completed['error_percent'].mean():.2f}%"

                    )


            else:

                st.info(
                    "Waiting for completed predictions."
                )


        else:

            st.info(
                "No memory data available."
            )


    except Exception as error:


        st.warning(
            f"Performance unavailable: {error}"
        )



# ============================================================
# RESOURCE CLEANUP
# ============================================================

plt.close(
    "all"
)


gc.collect()
# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# PART 10/11
# FORECAST DASHBOARD
# ============================================================


forecast = st.session_state.forecast


st.title(
    "⚛️ Quantum Equity Research Terminal"
)



if forecast is None:

    st.info(
        "Run a quantum forecast from the sidebar."
    )

    st.stop()



# ============================================================
# SUMMARY METRICS
# ============================================================


expected_return = (

    forecast["expected_price"]

    /

    forecast["starting_price"]

    -

    1

) * 100



c1,c2,c3,c4 = st.columns(4)



with c1:

    metric_card(
        "Expected Price",
        format_price(
            forecast["expected_price"]
        )
    )



with c2:

    metric_card(
        "Expected Return",
        f"{expected_return:+.2f}%",
        expected_return
    )



with c3:

    metric_card(
        "Confidence",
        f"{forecast['confidence_score']:.1f}%"
    )



with c4:

    metric_card(
        "Risk Score",
        f"{forecast['risk_score']:.2f}"
    )



st.divider()



# ============================================================
# MARKET STATE
# ============================================================


c1,c2,c3 = st.columns(3)



with c1:

    regime = forecast["market_regime"]


    status = {

        "Bullish":"positive",

        "Bearish":"negative",

        "Neutral":"neutral"

    }.get(
        regime,
        "neutral"
    )


    render_status_badge(
        regime,
        status
    )



with c2:

    st.metric(

        "Upside Probability",

        f"{forecast['upside_probability']:.2f}%"

    )



with c3:

    st.metric(

        "Downside Probability",

        f"{forecast['downside_probability']:.2f}%"

    )



# ============================================================
# QUANTUM PRICE DISTRIBUTION
# ============================================================


st.subheader(
    "⚛️ Quantum Price Probability"
)



fig,ax = plt.subplots(
    figsize=(10,4)
)


ax.plot(

    forecast["price_grid"],

    forecast["probability"]

)


ax.set_xlabel(
    "Future Price"
)


ax.set_ylabel(
    "Probability"
)


ax.set_title(
    "Quantum State Distribution"
)


st.pyplot(
    fig,
    clear_figure=True
)



plt.close(
    fig
)



# ============================================================
# RETURN DISTRIBUTION
# ============================================================


st.subheader(
    "📈 Return Probability"
)



fig,ax = plt.subplots(
    figsize=(10,4)
)


ax.plot(

    forecast["return_grid"],

    forecast["probability"]

)



ax.set_xlabel(
    "Return %"
)


ax.set_ylabel(
    "Probability"
)



ax.set_title(
    "Future Return Distribution"
)



st.pyplot(
    fig,
    clear_figure=True
)



plt.close(
    fig
)



# ============================================================
# FORECAST SUMMARY TABLE
# ============================================================


with st.expander(
    "📊 Forecast Summary"
):


    summary = pd.DataFrame(

        {

            "Metric":[

                "Ticker",

                "Forecast Horizon",

                "Starting Price",

                "Expected Price",

                "Volatility",

                "Market Regime",

                "Confidence",

                "Risk Score"

            ],


            "Value":[

                ticker,

                f"{forecast_days} days",

                format_price(
                    forecast["starting_price"]
                ),

                format_price(
                    forecast["expected_price"]
                ),

                f"{forecast['volatility']:.2f}%",

                forecast["market_regime"],

                f"{forecast['confidence_score']:.2f}%",

                f"{forecast['risk_score']:.2f}"

            ]

        }

    )


    st.dataframe(

        summary,

        hide_index=True,

        use_container_width=True

    )
# ============================================================
# APP.PY
# PART 11/11
# FINAL CLEANUP + EXPORT + FOOTER
# ============================================================


# ============================================================
# FORECAST EXPORT
# ============================================================

def create_forecast_report(data):

    if not data:

        return pd.DataFrame()


    report = {

        "Starting Price":
            data.get(
                "starting_price",
                0
            ),


        "Expected Price":
            data.get(
                "expected_price",
                0
            ),


        "Volatility":
            data.get(
                "volatility",
                0
            ),


        "Confidence":
            data.get(
                "confidence_score",
                0
            ),


        "Risk Score":
            data.get(
                "risk_score",
                0
            ),


        "Market Regime":
            data.get(
                "market_regime",
                "Unknown"
            ),


        "Upside Probability":
            data.get(
                "upside_probability",
                0
            ),


        "Downside Probability":
            data.get(
                "downside_probability",
                0
            )

    }


    return pd.DataFrame(
        {
            "Metric":
                list(report.keys()),

            "Value":
                list(report.values())

        }
    )



# ============================================================
# REPORT DOWNLOAD
# ============================================================

if st.session_state.forecast:


    with st.expander(
        "📄 Export Forecast Report"
    ):


        report = create_forecast_report(
            st.session_state.forecast
        )


        csv = report.to_csv(
            index=False
        )


        st.download_button(

            "Download Forecast CSV",

            csv,

            file_name=f"{ticker}_quantum_forecast.csv",

            mime="text/csv"

        )



# ============================================================
# CACHE MANAGEMENT
# ============================================================

with st.sidebar.expander(
    "🧹 System Maintenance"
):


    if st.button(
        "Clear Data Cache"
    ):

        try:

            clear_data_cache()

            st.cache_data.clear()

            gc.collect()

            st.success(
                "Cache cleared."
            )


        except Exception as error:

            st.error(
                f"Cache clear failed: {error}"
            )



# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(
    """
⚛️ Quantum Equity Research Terminal

Hybrid forecasting system combining:
• Market statistics
• Technical indicators
• Probability modeling
• Quantum circuit sampling
• Adaptive prediction memory

Built for research and experimentation.
"""
)



# ============================================================
# FINAL MEMORY RELEASE
# ============================================================

del temporary if "temporary" in locals() else None


gc.collect()
