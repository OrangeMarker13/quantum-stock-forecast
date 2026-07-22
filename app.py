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
# STREAMLIT CONFIG
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
# DISPLAY HELPERS
# ============================================================

def get_change_class(value):
    try:
        value = float(value)
        return "positive" if value > 0 else "negative" if value < 0 else "neutral"
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
# QUANTUM TERMINAL UI
# ============================================================

def apply_quantum_ui():
    st.markdown("""
    <style>

    .stApp {
        background:
        radial-gradient(circle at 10% 10%, rgba(34,211,238,.18), transparent 35%),
        radial-gradient(circle at 90% 90%, rgba(139,92,246,.18), transparent 40%),
        linear-gradient(135deg,#020617,#0f172a,#020617);
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
        background:linear-gradient(180deg,#020617,#111827);
        border-right:1px solid rgba(34,211,238,.25);
    }

    section[data-testid="stSidebar"] * {
        color:#e2e8f0;
    }

    .stButton button {
        background:linear-gradient(90deg,#06b6d4,#8b5cf6);
        color:white;
        border:none;
        border-radius:16px;
        padding:12px 20px;
        font-weight:900;
    }

    .metric-box {
        background:rgba(15,23,42,.75);
        border:1px solid rgba(34,211,238,.25);
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
    """, unsafe_allow_html=True)


apply_quantum_ui()


# ============================================================
# UI COMPONENTS
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
        "⚛️ Measuring distribution"
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

    gc.collect()\
# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 2/6
# MARKET DATA PIPELINE + CONTROLS
# ============================================================


# ============================================================
# SIDEBAR CONTROLS
# ============================================================

st.sidebar.title("⚛️ Quantum Forecast Controls")


search_query = st.sidebar.text_input(
    "Search Company or Symbol",
    value="Microsoft"
)


# ============================================================
# STOCK SEARCH
# ============================================================

try:
    search_results = search_stocks(search_query)
except Exception:
    search_results = []


if search_results:

    selected_asset = st.sidebar.selectbox(
        "Select Asset",
        search_results,
        format_func=lambda x: x.get(
            "label",
            x.get("symbol", "Unknown")
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
    [1, 2, 7, 30, 60, 90],
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
Quantum settings:

• Qubits control probability states
• Shots control sampling size
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
# CACHED MARKET DATA
# ============================================================

@st.cache_data(
    ttl=60,
    max_entries=100
)
def load_live_price(symbol):

    try:
        return get_live_price(symbol)
    except Exception:
        return None



@st.cache_data(
    ttl=3600,
    max_entries=100
)
def load_company_info(symbol):

    try:
        return get_company_info(symbol)
    except Exception:
        return {}



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

    except Exception:

        return pd.DataFrame()



# ============================================================
# LOAD DATA
# ============================================================

live_data = load_live_price(ticker)

company = load_company_info(ticker)

market_data = load_market_history(ticker)



if not company:
    company = {
        "name": company_name
    }



# ============================================================
# PRICE EXTRACTION
# ============================================================

def extract_value(data, key, default=0):

    try:
        return float(data.get(key, default))
    except Exception:
        return default



current_price = (
    extract_value(live_data, "price")
    if live_data
    else None
)


daily_change = (
    extract_value(live_data, "change_percent")
    if live_data
    else 0
)



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
        format_price(current_price)
    )


with col3:

    render_metric_card(
        "Daily Change",
        format_percent(daily_change),
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
# MARKET DATA VALIDATION
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


market_data = (
    market_data
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
    .dropna(
        subset=["Close"]
    )
)


if len(market_data) < 120:

    st.warning(
        "Limited historical data. Forecast quality may decrease."
    )



# ============================================================
# RECENT DATA VIEW
# ============================================================

with st.expander("📈 Recent Market Data"):

    recent = market_data.tail(50).copy()

    recent["Daily Return %"] = (
        recent["Close"]
        .pct_change()
        * 100
    )

    st.dataframe(
        recent,
        width="stretch"
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


external_features = get_external_features(ticker)



# ============================================================
# DATA CLEANING
# ============================================================

def prepare_market_features(data):

    if data is None or data.empty:
        return pd.DataFrame()

    df = data.copy()

    numeric = df.select_dtypes(
        include=np.number
    ).columns

    df[numeric] = (
        df[numeric]
        .replace(
            [np.inf, -np.inf],
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

    for window in [7, 30, 90]:

        df[f"MA_{window}"] = (
            df["Close"]
            .rolling(window)
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

    gain = delta.where(
        delta > 0,
        0
    )

    loss = -delta.where(
        delta < 0,
        0
    )


    avg_gain = (
        gain
        .rolling(14)
        .mean()
    )

    avg_loss = (
        loss
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
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )



market_data = add_technical_features(
    market_data
)



# ============================================================
# QUANTUM INPUT EXTRACTION
# ============================================================

def extract_quantum_inputs(data):

    if data.empty:
        return {}

    latest = data.iloc[-1]

    return {
        "price": float(
            latest["Close"]
        ),

        "volatility": float(
            latest["Volatility"]
        ),

        "momentum": float(
            latest["Momentum_20"]
        ),

        "market_strength": float(
            latest["Market_Strength"]
        ),

        "rsi": float(
            latest["RSI"]
        )
    }



quantum_inputs = extract_quantum_inputs(
    market_data
)



# ============================================================
# MODEL VALIDATION
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


    return (
        not data.empty
        and all(
            col in data.columns
            for col in required_columns
        )
        and all(
            item in features
            for item in required_features
        )
    )



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
# FEATURE DISPLAY
# ============================================================

with st.expander(
    "⚛️ Quantum Input State"
):

    feature_display = pd.DataFrame(
        {
            "Feature": list(
                quantum_inputs.keys()
            ),

            "Value": list(
                quantum_inputs.values()
            )
        }
    )


    st.dataframe(
        feature_display,
        width="stretch"
    )
# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 4/6
# QUANTUM FORECAST ENGINE
# ============================================================


# ============================================================
# QUANTUM FORECAST MODEL
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


    S0 = float(starting_price)


    # ========================================================
    # HISTORICAL RETURNS
    # ========================================================

    returns = (
        prices
        .pct_change()
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .dropna()
    )


    daily_volatility = max(
        float(returns.std()),
        0.01
    )


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


    technical_signal = np.clip(
        (
            trend(7) * .10
            +
            trend(30) * .30
            +
            trend(90) * .40
            +
            trend(180) * .20
        ),
        -.20,
        .20
    )


    # ========================================================
    # VOLATILITY REGIME
    # ========================================================

    recent_volatility = (
        returns
        .tail(30)
        .std()
    )


    volatility_ratio = np.clip(
        recent_volatility / daily_volatility,
        .5,
        3
    )


    # ========================================================
    # ADAPTIVE WEIGHTS
    # ========================================================

    weights = {
        "technical": .45 / volatility_ratio,
        "macro": .15 * volatility_ratio,
        "global": .15 * volatility_ratio,
        "sector": .15,
        "sentiment": .10
    }


    total = sum(
        weights.values()
    )


    weights = {
        key: value / total
        for key, value in weights.items()
    }



    # ========================================================
    # EXTERNAL SIGNALS
    # ========================================================

    macro = external_features.get(
        "macro_score",
        0
    )

    macro += (
        external_features.get(
            "rate_score",
            0
        )
        *
        .25
    )


    market_state = (

        technical_signal
        *
        weights["technical"]

        +

        macro
        *
        weights["macro"]

        +

        external_features.get(
            "global_market_score",
            0
        )
        *
        weights["global"]

        +

        external_features.get(
            "sector_score",
            0
        )
        *
        weights["sector"]

        +

        external_features.get(
            "sentiment_score",
            0
        )
        *
        weights["sentiment"]

        +

        external_features.get(
            "earnings_score",
            0
        )
        *
        .10
    )


    market_state = np.clip(
        market_state,
        -.35,
        .35
    )


    # ========================================================
    # EXPECTED RETURN
    # ========================================================

    drift = (
        float(returns.mean())
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


    expected_return = np.clip(
        drift * days,
        -.35,
        .35
    )


    expected_price = (
        S0
        *
        np.exp(expected_return)
    )


    # ========================================================
    # PRICE STATE SPACE
    # ========================================================

    states = 2 ** qubits


    movement_limits = {
        1: .03,
        2: .05,
        7: .10,
        30: .18,
        60: .25,
        90: .35
    }


    allowed_move = movement_limits.get(
        days,
        .35
    )


    price_range = np.clip(
        (
            S0
            *
            annual_volatility
            *
            np.sqrt(
                max(days, 1) / 252
            )
            *
            1.5
        ),
        S0 * .02,
        S0 * allowed_move
    )


    lower = max(
        S0 * (1 - allowed_move),
        expected_price - price_range
    )


    upper = min(
        S0 * (1 + allowed_move),
        expected_price + price_range
    )


    price_grid = np.linspace(
        lower,
        upper,
        states
    )


    return_grid = (
        (
            price_grid - S0
        )
        /
        S0
        *
        100
    )


    # ========================================================
    # CLASSICAL DISTRIBUTION
    # ========================================================

    uncertainty = np.clip(
        annual_volatility
        *
        np.sqrt(
            max(days,1) / 252
        ),
        .02,
        allowed_move
    )


    z = (
        (
            return_grid / 100
            -
            expected_return
        )
        /
        uncertainty
    )


    probability = np.exp(
        -.5 * z ** 2
    )


    probability = np.nan_to_num(
        probability,
        nan=1
    )


    probability /= probability.sum()


    # ========================================================
    # END PART 4/6
    # ========================================================
# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 5/6
# QUANTUM SAMPLING + FORECAST EXECUTION
# ============================================================


    # ========================================================
    # QUANTUM CIRCUIT SAMPLING
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


        for state, count in counts.items():

            index = int(
                state,
                2
            )

            if index < states:

                quantum_probability[index] = (
                    count / shots
                )


    except Exception:

        quantum_probability = None



    # ========================================================
    # FALLBACK
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
    # FORECAST METRICS
    # ========================================================

    quantum_expected_price = np.sum(
        price_grid
        *
        quantum_probability
    )


    upside = (
        np.sum(
            quantum_probability[
                return_grid > 5
            ]
        )
        *
        100
    )


    downside = (
        np.sum(
            quantum_probability[
                return_grid < -5
            ]
        )
        *
        100
    )


    neutral = (
        100
        -
        upside
        -
        downside
    )


    upside = np.clip(
        upside,
        0,
        95
    )

    downside = np.clip(
        downside,
        0,
        95
    )

    neutral = np.clip(
        neutral,
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


    volatility_score = np.clip(
        100 - annual_volatility * 100,
        10,
        90
    )


    confidence_score = np.clip(
        (
            entropy_score * .50
            +
            volatility_score * .30
            +
            abs(market_state)
            *
            100
            *
            .20
        ),
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



    risk_score = (
        annual_volatility
        *
        100
        *
        downside
        /
        100
    )



    # ========================================================
    # RETURN FORECAST OBJECT
    # ========================================================

    return {

        "starting_price": S0,

        "expected_price": quantum_expected_price,

        "price_grid": price_grid,

        "return_grid": return_grid,

        "probability": quantum_probability,

        "classical_probability": probability,

        "volatility": annual_volatility * 100,

        "returns": returns,

        "market_regime": regime,

        "confidence_score": confidence_score,

        "risk_score": risk_score,

        "market_state": market_state,

        "upside_probability": upside,

        "downside_probability": downside,

        "neutral_probability": neutral,

        "model_metadata": {
            "weights": weights,
            "technical_signal": technical_signal,
            "market_state": market_state
        }
    }



# ============================================================
# FORECAST CONTROLLER
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
        else float(
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


        st.session_state.forecast = result
        st.session_state.forecast_settings = settings
        st.session_state.last_run = (
            datetime.datetime.now()
            .strftime("%H:%M:%S")
        )

        st.session_state.last_price = execution_price
        st.session_state.risk_score = result["risk_score"]
        st.session_state.confidence_score = result["confidence_score"]
        st.session_state.market_regime = result["market_regime"]


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
# DASHBOARD OUTPUT + VISUALIZATION
# ============================================================


# ============================================================
# FORECAST DISPLAY
# ============================================================

forecast = st.session_state.forecast


if forecast is None:

    st.info(
        "Run a quantum forecast to generate analysis."
    )

else:


    # ========================================================
    # SUMMARY METRICS
    # ========================================================

    st.subheader(
        "⚛️ Quantum Forecast Summary"
    )


    current = forecast["starting_price"]

    predicted = forecast["expected_price"]


    predicted_change = (
        (predicted / current) - 1
    ) * 100


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        render_metric_card(
            "Expected Price",
            format_price(predicted)
        )


    with col2:

        render_metric_card(
            "Expected Change",
            format_percent(predicted_change),
            predicted_change
        )


    with col3:

        render_metric_card(
            "Confidence",
            f"{forecast['confidence_score']:.1f}%"
        )


    with col4:

        render_metric_card(
            "Risk Score",
            f"{forecast['risk_score']:.2f}"
        )



    # ========================================================
    # MARKET REGIME
    # ========================================================

    st.divider()


    regime = forecast["market_regime"]


    regime_status = (
        "positive"
        if regime == "Bullish"
        else
        "negative"
        if regime == "Bearish"
        else
        "neutral"
    )


    render_status_badge(
        f"Market Regime: {regime}",
        regime_status
    )



    # ========================================================
    # PROBABILITY DISTRIBUTION
    # ========================================================

    st.subheader(
        "Quantum Probability Distribution"
    )


    fig, ax = plt.subplots(
        figsize=(10,4)
    )


    ax.plot(
        forecast["price_grid"],
        forecast["probability"]
    )


    ax.set_xlabel(
        "Price"
    )

    ax.set_ylabel(
        "Probability"
    )


    ax.set_title(
        "Quantum State Price Distribution"
    )


    st.pyplot(
        fig
    )

    plt.close(fig)



    # ========================================================
    # PROBABILITY ZONES
    # ========================================================

    col1, col2, col3 = st.columns(3)


    with col1:

        render_metric_card(
            "Upside Probability",
            f"{forecast['upside_probability']:.1f}%"
        )


    with col2:

        render_metric_card(
            "Neutral Probability",
            f"{forecast['neutral_probability']:.1f}%"
        )


    with col3:

        render_metric_card(
            "Downside Probability",
            f"{forecast['downside_probability']:.1f}%"
        )



    # ========================================================
    # MODEL DETAILS
    # ========================================================

    with st.expander(
        "⚛️ Quantum Model Metadata"
    ):

        with st.expander(
    "⚛️ Quantum Decision Trace"
):

    metadata = forecast["model_metadata"]

    weights = metadata["weights"]

    weight_table = pd.DataFrame(
        {
            "Signal": [
                "Technical",
                "Macro",
                "Global",
                "Sector",
                "Sentiment"
            ],

            "Weight": [
                weights["technical"],
                weights["macro"],
                weights["global"],
                weights["sector"],
                weights["sentiment"]
            ]
        }
    )

    weight_table["Weight"] = (
        weight_table["Weight"] * 100
    ).round(2).astype(str) + "%"


    st.subheader(
        "Signal Influence"
    )

    st.dataframe(
        weight_table,
        hide_index=True,
        width="stretch"
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
    # PRICE RANGE TABLE
    # ========================================================

    with st.expander(
        "📊 Forecast State Table"
    ):


        forecast_table = pd.DataFrame(
            {
                "Price":
                    forecast["price_grid"],

                "Return %":
                    forecast["return_grid"],

                "Probability":
                    forecast["probability"]
            }
        )


        st.dataframe(
            forecast_table,
            width="stretch"
        )



    # ========================================================
    # RUN INFORMATION
    # ========================================================

    st.caption(
        f"""
        Last Run:
        {st.session_state.last_run}

        |
        
        Asset:
        {ticker}

        |

        Horizon:
        {forecast_days} days

        |

        Qubits:
        {qubits}

        |

        Shots:
        {shots}
        """
    )



# ============================================================
# CLEAN MEMORY
# ============================================================

gc.collect()
