# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 1/6
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import time
import gc


from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


from data_provider import (
    get_stock_data,
    get_live_price,
    get_company_info,
    search_stocks,
    format_price,
    validate_market_data
)


from prediction_memory import (
    evaluate_predictions,
    get_prediction_adjustment
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
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "forecast": None,
    "forecast_settings": None,
    "last_run": "Never",
    "last_price": None,
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



def format_score(value):

    try:

        return f"{float(value):.3f}"

    except:

        return "N/A"



# ============================================================
# QUANTUM TERMINAL UI
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
            #0f172a,
            #020617
        );

        color:#e5e7eb;

    }


    h1 {

        color:#22d3ee !important;
        font-weight:900 !important;

    }


    h2,h3 {

        color:#e0f2fe !important;

    }


    p {

        color:#cbd5e1;

    }


    section[data-testid="stSidebar"] {

        background:
        linear-gradient(
            180deg,
            #020617,
            #111827
        );

    }


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

        padding:12px 20px;

        font-weight:900;

    }


    .metric-box {

        background:
        rgba(15,23,42,.75);

        border:
        1px solid rgba(34,211,238,.25);

        border-radius:18px;

        padding:18px;

        text-align:center;

    }


    .positive {

        color:#22ff88 !important;
        font-weight:900;

    }


    .negative {

        color:#ff5555 !important;
        font-weight:900;

    }


    .neutral {

        color:#22d3ee !important;
        font-weight:900;

    }

    </style>
    """,

    unsafe_allow_html=True

    )


apply_quantum_ui()



# ============================================================
# DISPLAY COMPONENTS
# ============================================================

def render_metric_card(title, value, change=None):

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



def render_status_badge(text, status="neutral"):

    st.markdown(

    f"""

    <div class="{status}"

    style="

    display:inline-block;

    padding:8px 18px;

    border-radius:20px;

    border:1px solid currentColor;

    background:rgba(255,255,255,.05);

    ">

    {text}

    </div>

    """,

    unsafe_allow_html=True

    )



# ============================================================
# LOADING + RESET
# ============================================================

def quantum_loading():

    box = st.empty()

    messages = [

        "⚛️ Initializing quantum states",

        "⚛️ Encoding market probability",

        "⚛️ Running quantum simulation",

        "⚛️ Measuring probability distribution"

    ]


    for message in messages:

        box.markdown(

        f"""

        <div class="metric-box">

        <h3>{message}</h3>

        </div>

        """,

        unsafe_allow_html=True

        )

        time.sleep(.35)


    box.empty()



def reset_forecast_state():

    for key, value in DEFAULT_STATE.items():

        st.session_state[key] = value


    gc.collect()
    # ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 2/6
# CONTROLS + MARKET DATA PIPELINE
# ============================================================


# ============================================================
# SIDEBAR CONTROLS
# ============================================================

st.sidebar.title(
    "⚛️ Quantum Forecast Controls"
)


search_query = st.sidebar.text_input(
    "Search Company or Symbol",
    value="Microsoft"
)



# ============================================================
# STOCK SEARCH
# ============================================================

try:

    search_results = search_stocks(search_query)

except:

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

    ticker = search_query.upper().strip()

    company_name = ticker



# ============================================================
# FORECAST SETTINGS
# ============================================================

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

    min_value=3,

    max_value=8,

    value=6

)



shots = st.sidebar.slider(

    "Quantum Shots",

    min_value=500,

    max_value=3000,

    value=1500,

    step=500

)



st.sidebar.info(

"""
Quantum settings:

• Qubits control probability states

• Shots control sampling accuracy

• Higher values increase computation

"""

)



run_button = st.sidebar.button(
    "🚀 Run Quantum Forecast"
)



clear_button = st.sidebar.button(
    "🧹 Clear Forecast"
)



if clear_button:

    reset_forecast_state()

    st.rerun()



# ============================================================
# LIVE PRICE CACHE
# ============================================================

@st.cache_data(
    ttl=60,
    max_entries=100
)

def load_live_price(symbol):

    try:

        return get_live_price(symbol)

    except:

        return None



live_data = load_live_price(ticker)



# ============================================================
# COMPANY INFORMATION CACHE
# ============================================================

@st.cache_data(
    ttl=3600,
    max_entries=100
)

def load_company_info(symbol):

    try:

        return get_company_info(symbol)

    except:

        return {}



company = load_company_info(ticker)



if not company:

    company = {
        "name": company_name
    }



# ============================================================
# CURRENT PRICE
# ============================================================

current_price = None


daily_change = 0



if live_data:

    try:

        current_price = float(
            live_data.get(
                "price",
                0
            )
        )


    except:

        current_price = None



    try:

        daily_change = float(
            live_data.get(
                "change_percent",
                0
            )
        )


    except:

        daily_change = 0



# ============================================================
# MARKET HEADER
# ============================================================

col1, col2, col3 = st.columns(3)



with col1:

    render_metric_card(

        "Company",

        company.get(
            "name",
            company_name
        )

    )



with col2:

    render_metric_card(

        "Live Price",

        format_price(
            current_price
        )

    )



with col3:

    render_metric_card(

        "Daily Change",

        format_percent(
            daily_change
        ),

        daily_change

    )



st.caption(

    f"""

    Market update:
    {datetime.datetime.now().strftime('%H:%M:%S')}

    |

    Asset:
    {ticker}

    """

)



# ============================================================
# HISTORICAL MARKET DATA
# ============================================================

@st.cache_data(

    ttl=900,

    max_entries=50

)

def load_market_history(symbol):

    try:

        data = get_stock_data(symbol)


        if data is None:

            return pd.DataFrame()



        if not validate_market_data(data):

            return pd.DataFrame()



        return data.copy()


    except:

        return pd.DataFrame()



market_data = load_market_history(ticker)



# ============================================================
# DATA VALIDATION
# ============================================================

if market_data.empty:

    st.error(
        "No historical market data found."
    )

    st.stop()



if "Close" not in market_data.columns:

    st.error(
        "Market data missing Close price."
    )

    st.stop()



market_data["Close"] = pd.to_numeric(

    market_data["Close"],

    errors="coerce"

)



market_data = market_data.dropna(
    subset=["Close"]
)



if len(market_data) < 120:

    st.warning(
        "Limited historical data. Forecast quality may decrease."
    )



market_data = market_data.replace(

    [
        np.inf,
        -np.inf
    ],

    np.nan

)



market_data = market_data.fillna(0)



# ============================================================
# RECENT DATA DISPLAY
# ============================================================

with st.expander(
    "📈 Recent Market Data"
):

    recent = market_data.tail(50).copy()


    recent["Daily Return %"] = (

        recent["Close"]

        .pct_change()

        * 100

    )


    st.dataframe(

        recent,

        use_container_width=True

    )
    # ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 3/6
# FEATURE ENGINEERING + MODEL INPUT PIPELINE
# ============================================================


# ============================================================
# EXTERNAL MARKET FEATURES
# ============================================================

def get_external_features(symbol):

    return {

        "macro_score": 0.0,

        "sector_score": 0.0,

        "sentiment_score": 0.0,

        "global_market_score": 0.0,

        "earnings_score": 0.0,

        "rate_score": 0.0

    }



external_features = get_external_features(
    ticker
)



# ============================================================
# MARKET DATA CLEANUP
# ============================================================

def prepare_market_features(data):

    if data is None or data.empty:

        return pd.DataFrame()


    df = data.copy()


    numeric_columns = df.select_dtypes(
        include=[np.number]
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



market_data = prepare_market_features(
    market_data
)



# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def add_technical_features(data):

    df = data.copy()



    # Returns

    df["Return"] = (

        df["Close"]

        .pct_change()

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


    gains = delta.where(
        delta > 0,
        0
    )


    losses = -delta.where(
        delta < 0,
        0
    )


    avg_gain = gains.rolling(14).mean()

    avg_loss = losses.rolling(14).mean()


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



    df = df.replace(

        [
            np.inf,
            -np.inf
        ],

        np.nan

    )



    return df.fillna(0)



market_data = add_technical_features(
    market_data
)



# ============================================================
# QUANTUM INPUT EXTRACTION
# ============================================================

def extract_quantum_inputs(data):

    latest = data.iloc[-1]


    return {

        "price":

        float(
            latest["Close"]
        ),


        "volatility":

        float(
            latest["Volatility"]
        ),


        "momentum":

        float(
            latest["Momentum_20"]
        ),


        "market_strength":

        float(
            latest["Market_Strength"]
        ),


        "rsi":

        float(
            latest["RSI"]
        )

    }



quantum_inputs = extract_quantum_inputs(
    market_data
)



# ============================================================
# INPUT VALIDATION
# ============================================================

def validate_model_inputs(data, features):

    required_columns = [

        "Close",

        "Return",

        "Volatility",

        "Momentum_20",

        "RSI"

    ]


    required_features = [

        "price",

        "volatility",

        "momentum",

        "market_strength",

        "rsi"

    ]



    if data.empty:

        return False



    for column in required_columns:

        if column not in data:

            return False



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
# QUANTUM INPUT DISPLAY
# ============================================================

with st.expander(
    "⚛️ Quantum Input State"
):

    feature_display = pd.DataFrame(

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

        feature_display,

        use_container_width=True

    )
    # ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 4/6
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
            "Not enough historical data."
        )



    S0 = float(
        starting_price
    )



    # ========================================================
    # RETURN + VOLATILITY ENGINE
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
    # TREND MODEL
    # ========================================================

    def calculate_trend(window):

        if len(prices) <= window:

            return 0.0


        return (

            prices.iloc[-1]

            /

            prices.iloc[-window]

            -

            1

        )



    trend_7 = calculate_trend(7)

    trend_30 = calculate_trend(30)

    trend_90 = calculate_trend(90)

    trend_180 = calculate_trend(180)



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

    recent_volatility = float(

        returns

        .tail(30)

        .std()

    )



    volatility_ratio = (

        recent_volatility

        /

        daily_volatility

    )



    volatility_ratio = np.clip(

        volatility_ratio,

        0.5,

        3

    )



    # ========================================================
    # ADAPTIVE WEIGHTS
    # ========================================================

    weights = {

        "technical":

        0.45 / volatility_ratio,


        "macro":

        0.15 * volatility_ratio,


        "global":

        0.15 * volatility_ratio,


        "sector":

        0.15,


        "sentiment":

        0.10

    }



    total_weight = sum(
        weights.values()
    )


    for key in weights:

        weights[key] /= total_weight



    # ========================================================
    # EXTERNAL SIGNALS
    # ========================================================

    macro_signal = external_features.get(
        "macro_score",
        0
    )


    sector_signal = external_features.get(
        "sector_score",
        0
    )


    sentiment_signal = external_features.get(
        "sentiment_score",
        0
    )


    global_signal = external_features.get(
        "global_market_score",
        0
    )


    earnings_signal = external_features.get(
        "earnings_score",
        0
    )


    rate_signal = external_features.get(
        "rate_score",
        0
    )


    macro_signal += rate_signal * 0.25



    # ========================================================
    # MARKET STATE
    # ========================================================

    market_state = (

        technical_signal

        *

        weights["technical"]


        +

        macro_signal

        *

        weights["macro"]


        +

        global_signal

        *

        weights["global"]


        +

        sector_signal

        *

        weights["sector"]


        +

        sentiment_signal

        *

        weights["sentiment"]


        +

        earnings_signal * 0.10

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



    movement_limits = {

        1:0.03,

        2:0.05,

        7:0.10,

        30:0.18,

        60:0.25,

        90:0.35

    }



    allowed_move = movement_limits.get(

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
    # QUANTUM STATE GRID
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

        S0 * 0.02,

        S0 * allowed_move

    )



    lower_bound = max(

        S0 * (1 - allowed_move),

        expected_price - price_range

    )



    upper_bound = min(

        S0 * (1 + allowed_move),

        expected_price + price_range

    )



    price_grid = np.linspace(

        lower_bound,

        upper_bound,

        states

    )



    return_grid = (

        (

            price_grid - S0

        )

        /

        S0

    ) * 100
    # ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 5/6
# QUANTUM SAMPLING + FORECAST OUTPUT
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

        annual_volatility

        *

        np.sqrt(

            max(days, 1)

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

        -0.5

        *

        z_score ** 2

    )



    classical_probability = np.nan_to_num(

        classical_probability,

        nan=1.0,

        posinf=1.0,

        neginf=0.0

    )



    probability_total = classical_probability.sum()



    if probability_total <= 0:

        classical_probability = np.ones(states)

        probability_total = states



    classical_probability /= probability_total



    # ========================================================
    # QUANTUM CIRCUIT SIMULATION
    # ========================================================

    quantum_probability = None


    try:

        amplitudes = np.sqrt(
            classical_probability
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



    except:

        quantum_probability = None



    # ========================================================
    # QUANTUM FALLBACK
    # ========================================================

    if (

        quantum_probability is None

        or

        quantum_probability.sum() == 0

    ):

        quantum_probability = (

            classical_probability.copy()

        )


    else:

        quantum_probability /= quantum_probability.sum()



    # ========================================================
    # EXPECTED PRICE
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



    volatility_score = (

        100

        -

        annual_volatility * 100

    )



    volatility_score = np.clip(

        volatility_score,

        10,

        90

    )



    signal_strength = abs(
        market_state
    )



    confidence_score = (

        entropy_score * 0.50

        +

        volatility_score * 0.30

        +

        signal_strength * 100 * 0.20

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

        market_regime = "Bullish"


    elif market_state < -0.08:

        market_regime = "Bearish"


    else:

        market_regime = "Neutral"



    # ========================================================
    # RISK SCORE
    # ========================================================

    risk_score = (

        annual_volatility

        *

        100

        *

        (

            downside_probability

            /

            100

        )

    )



    # ========================================================
    # CLEAN METADATA
    # ========================================================

    model_metadata = {

        "weights": {

            key:

            round(

                value * 100,

                2

            )

            for key, value in weights.items()

        },


        "technical_signal":

        round(

            technical_signal,

            3

        ),


        "market_state":

        round(

            market_state,

            3

        )

    }



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

        classical_probability,


        "volatility":

        annual_volatility * 100,


        "returns":

        returns,


        "market_regime":

        market_regime,


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

        model_metadata

    }



# ============================================================
# FORECAST EXECUTION CONTROLLER
# ============================================================

settings = [

    ticker,

    forecast_days,

    qubits,

    shots

]



if run_button:


    execution_price = (

        float(current_price)

        if current_price

        else

        float(

            market_data["Close"].iloc[-1]

        )

    )



    try:

        quantum_loading()


        with st.spinner(

            "Running quantum probability simulation..."

        ):


            forecast_result = quantum_forecast(

                market_data,

                execution_price,

                forecast_days,

                qubits,

                shots,

                external_features

            )



        st.session_state.forecast = forecast_result

        st.session_state.forecast_settings = settings

        st.session_state.last_run = (

            datetime.datetime.now()

            .strftime("%H:%M:%S")

        )


        st.session_state.last_price = execution_price


        st.session_state.risk_score = (

            forecast_result["risk_score"]

        )


        st.session_state.confidence_score = (

            forecast_result["confidence_score"]

        )


        st.session_state.market_regime = (

            forecast_result["market_regime"]

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
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 6/6
# FORECAST DISPLAY + ANALYTICS
# ============================================================


# ============================================================
# LOAD FORECAST
# ============================================================

forecast = st.session_state.forecast



if forecast is not None:


    expected_price = forecast["expected_price"]

    starting_price = forecast["starting_price"]


    expected_change = (

        (

            expected_price

            /

            starting_price

            -

            1

        )

        *

        100

    )



    # ========================================================
    # SUMMARY METRICS
    # ========================================================

    st.subheader(
        "⚛️ Quantum Forecast Summary"
    )



    col1, col2, col3, col4 = st.columns(4)



    with col1:

        render_metric_card(

            "Expected Price",

            f"${expected_price:.2f}"

        )



    with col2:

        render_metric_card(

            "Expected Return",

            f"{expected_change:+.2f}%",

            expected_change

        )



    with col3:

        render_metric_card(

            "Confidence",

            f"{forecast['confidence_score']:.2f}%"

        )



    with col4:

        render_metric_card(

            "Risk Score",

            f"{forecast['risk_score']:.2f}"

        )



    # ========================================================
    # MARKET REGIME
    # ========================================================

    st.subheader(
        "Market Regime"
    )


    regime = forecast["market_regime"]



    render_status_badge(

        regime,

        get_change_class(

            forecast["market_state"]

        )

    )



    st.caption(

        f"""

        Last Run:

        {st.session_state.last_run}

        |

        Starting Price:

        ${starting_price:.2f}

        """

    )



    # ========================================================
    # PROBABILITY BREAKDOWN
    # ========================================================

    st.subheader(
        "Quantum Probability Distribution"
    )


    prob_col1, prob_col2, prob_col3 = st.columns(3)



    with prob_col1:

        render_metric_card(

            "Upside Probability",

            f"{forecast['upside_probability']:.2f}%"

        )



    with prob_col2:

        render_metric_card(

            "Neutral Probability",

            f"{forecast['neutral_probability']:.2f}%"

        )



    with prob_col3:

        render_metric_card(

            "Downside Probability",

            f"{forecast['downside_probability']:.2f}%"

        )



    # ========================================================
    # PRICE DISTRIBUTION CHART
    # ========================================================

    st.subheader(
        "Forecast Probability Curve"
    )


    fig, ax = plt.subplots(

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

        "Quantum Sampled Price Distribution"

    )


    st.pyplot(fig)



    # ========================================================
    # FORECAST TABLE
    # ========================================================

    st.subheader(
        "Forecast States"
    )


    forecast_table = pd.DataFrame(

        {

            "Price":

            forecast["price_grid"],


            "Return %":

            forecast["return_grid"],


            "Probability %":

            forecast["probability"] * 100

        }

    )



    forecast_table["Price"] = (

        forecast_table["Price"]

        .round(2)

    )



    forecast_table["Return %"] = (

        forecast_table["Return %"]

        .round(2)

    )



    forecast_table["Probability %"] = (

        forecast_table["Probability %"]

        .round(2)

    )



    st.dataframe(

        forecast_table,

        use_container_width=True

    )



    # ========================================================
    # QUANTUM DECISION TRACE
    # ========================================================

    with st.expander(

        "⚛️ Quantum Decision Trace"

    ):


        metadata = forecast["model_metadata"]



        st.subheader(

            "Signal Influence"

        )



        weight_table = pd.DataFrame(

            {

                "Signal":

                [

                    "Technical",

                    "Macro",

                    "Global",

                    "Sector",

                    "Sentiment"

                ],



                "Weight":

                [

                    metadata["weights"]["technical"],

                    metadata["weights"]["macro"],

                    metadata["weights"]["global"],

                    metadata["weights"]["sector"],

                    metadata["weights"]["sentiment"]

                ]

            }

        )



        weight_table["Weight"] = (

            weight_table["Weight"]

            .map(

                lambda x:

                f"{x:.2f}%"

            )

        )



        st.dataframe(

            weight_table,

            hide_index=True,

            use_container_width=True

        )



        col1, col2 = st.columns(2)



        with col1:

            st.metric(

                "Technical Signal",

                f"{metadata['technical_signal']:.3f}"

            )



        with col2:

            st.metric(

                "Market State",

                f"{metadata['market_state']:.3f}"

            )



    # ========================================================
    # MODEL HISTORY
    # ========================================================

    st.subheader(

        "Prediction Memory"

    )



    evaluation = evaluate_predictions()



    if evaluation:


        history = pd.DataFrame(

            evaluation

        )


        st.dataframe(

            history,

            use_container_width=True

        )


else:


    st.info(

        "Run a quantum forecast to generate analysis."

    )
