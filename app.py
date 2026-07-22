# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# PART 1/6
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
    validate_market_data,
    clear_data_cache
)

from prediction_memory import (
    evaluate_predictions,
    get_prediction_adjustment
)


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
        return (
            "positive"
            if value > 0
            else "negative"
            if value < 0
            else "neutral"
        )
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
# PREMIUM QUANTUM UI
# ============================================================

def apply_quantum_ui():

    st.markdown(
        """
        <style>

        .stApp {
            background:
            radial-gradient(
                circle at 10% 10%,
                rgba(34,211,238,0.18),
                transparent 35%
            ),
            radial-gradient(
                circle at 90% 90%,
                rgba(139,92,246,0.18),
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
            text-shadow:0 0 20px rgba(34,211,238,.5);
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

            border-right:
            1px solid
            rgba(34,211,238,.25);
        }


        section[data-testid="stSidebar"] * {
            color:#e2e8f0;
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
            1px solid
            rgba(34,211,238,.25);

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
# DISPLAY HELPERS
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
# QUANTUM LOADING
# ============================================================

def quantum_loading():

    placeholder = st.empty()

    frames = [
        "⚛️ Initializing quantum states",
        "⚛️ Encoding market probability",
        "⚛️ Running quantum simulation",
        "⚛️ Measuring probability distribution"
    ]


    for frame in frames:

        placeholder.markdown(
            f"""
            <div class="metric-box">

            <h3>{frame}</h3>

            </div>
            """,
            unsafe_allow_html=True
        )

        time.sleep(0.5)


    placeholder.empty()



# ============================================================
# RESET STATE
# ============================================================

def reset_forecast_state():

    for key, value in DEFAULT_STATE.items():
        st.session_state[key] = value
# ============================================================
# CONTROLS + MARKET DATA PIPELINE
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
except:
    search_results = []


if search_results:

    selected_asset = st.sidebar.selectbox(
        "Select Asset",
        search_results,
        format_func=lambda x: x.get(
            "label",
            x.get("symbol","Unknown")
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
Quantum settings:

• Qubits control probability states
• Shots control sampling accuracy
• Higher values increase computation
• Adaptive weights remain active
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
    gc.collect()
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
# COMPANY CACHE
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
# CURRENT MARKET VALUES
# ============================================================

current_price = None
daily_change = 0


if live_data:

    try:
        current_price = float(
            live_data.get("price",0)
        )
    except:
        pass


    try:
        daily_change = float(
            live_data.get(
                "change_percent",
                0
            )
        )
    except:
        pass



# ============================================================
# MARKET HEADER
# ============================================================

col1,col2,col3 = st.columns(3)


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
# HISTORICAL DATA CACHE
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



market_data = (
    market_data
    .replace(
        [np.inf,-np.inf],
        np.nan
    )
    .fillna(0)
)



# ============================================================
# RECENT MARKET DATA
# ============================================================

with st.expander(
    "📈 Recent Market Data"
):

    recent = market_data.tail(50).copy()

    recent["Daily Return %"] = (
        recent["Close"]
        .pct_change()
        *100
    )

    st.dataframe(
        recent,
        width="stretch"
    )
# ============================================================
# FEATURE ENGINEERING + MODEL INPUT PIPELINE
# ============================================================


# ============================================================
# EXTERNAL MARKET FEATURES
# ============================================================

def get_external_features(symbol):

    return {
        "macro_score":0.0,
        "sector_score":0.0,
        "sentiment_score":0.0,
        "global_market_score":0.0,
        "earnings_score":0.0,
        "rate_score":0.0
    }


external_features = get_external_features(ticker)



# ============================================================
# DATA CLEANUP
# ============================================================

def prepare_market_features(data):

    if data is None or data.empty:
        return pd.DataFrame()

    df = data.copy()

    cols = df.select_dtypes(
        include=[np.number]
    ).columns

    df[cols] = (
        df[cols]
        .replace(
            [np.inf,-np.inf],
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


    df["Return"] = (
        df["Close"]
        .pct_change()
    )


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


    df["Volatility"] = (
        df["Return"]
        .rolling(30)
        .std()
    )


    df["Momentum_20"] = (
        df["Close"]
        /
        df["Close"].shift(20)
        -1
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


    rs = avg_gain / (
        avg_loss + 1e-9
    )


    df["RSI"] = (
        100 -
        (
            100 /
            (1 + rs)
        )
    )


    # Market strength

    df["Market_Strength"] = (
        df["MA_30"]
        /
        (df["MA_90"] + 1e-9)
        *50
    )


    df["Market_Strength"] = np.clip(
        df["Market_Strength"],
        0,
        100
    )


    return (
        df
        .replace(
            [np.inf,-np.inf],
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

    row = data.iloc[-1]

    return {
        "price":float(row["Close"]),
        "volatility":float(row["Volatility"]),
        "momentum":float(row["Momentum_20"]),
        "market_strength":float(row["Market_Strength"]),
        "rsi":float(row["RSI"])
    }



quantum_inputs = extract_quantum_inputs(
    market_data
)



# ============================================================
# INPUT VALIDATION
# ============================================================

def validate_model_inputs(data, features):

    required = [
        "Close",
        "Return",
        "Volatility",
        "Momentum_20",
        "RSI"
    ]

    inputs = [
        "price",
        "volatility",
        "momentum",
        "market_strength",
        "rsi"
    ]


    return (
        not data.empty
        and all(x in data.columns for x in required)
        and all(x in features for x in inputs)
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
# QUANTUM INPUT DISPLAY
# ============================================================

with st.expander(
    "⚛️ Quantum Input State"
):

    feature_display = pd.DataFrame(
        {
            "Feature":list(
                quantum_inputs.keys()
            ),

            "Value":list(
                quantum_inputs.values()
            )
        }
    )


    st.dataframe(
        feature_display,
        width="stretch"
    )
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
    # RETURNS + VOLATILITY
    # ========================================================

    returns = (
        prices
        .pct_change()
        .replace(
            [np.inf,-np.inf],
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

    def trend(window):

        if len(prices) <= window:
            return 0

        return (
            prices.iloc[-1]
            /
            prices.iloc[-window]
            -1
        )


    trend_signal = (
        trend(7)*.10
        +
        trend(30)*.30
        +
        trend(90)*.40
        +
        trend(180)*.20
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
        recent_vol / daily_volatility,
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


    total = sum(
        weights.values()
    )


    weights = {
        k:
        v / total
        for k,v in weights.items()
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
        technical_signal * weights["technical"]
        +
        macro * weights["macro"]
        +
        global_market * weights["global"]
        +
        sector * weights["sector"]
        +
        sentiment * weights["sentiment"]
        +
        earnings * .10
    )


    market_state = np.clip(
        market_state,
        -.35,
        .35
    )



    # ========================================================
    # DRIFT MODEL
    # ========================================================

    historical_return = float(
        returns.mean()
    )


    drift = (
        historical_return*.60
        +
        market_state*.40
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
    # MOVEMENT LIMITS
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
        np.exp(expected_return)
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
            max(days,1)/252
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
# ============================================================
# QUANTUM SAMPLING + FORECAST OUTPUT
# ============================================================


    # ========================================================
    # CLASSICAL PROBABILITY DISTRIBUTION
    # ========================================================

    target_return = (
        expected_price / S0
        - 1
    )


    uncertainty = (
        annual_volatility
        *
        np.sqrt(
            max(days,1) / 252
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


    classical_probability = np.exp(
        -.5 * z**2
    )


    classical_probability = np.nan_to_num(
        classical_probability,
        nan=1,
        posinf=1,
        neginf=0
    )


    total = classical_probability.sum()


    if total <= 0:

        classical_probability = np.ones(
            states
        )

        total = states


    classical_probability /= total



    # ========================================================
    # QUANTUM CIRCUIT
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


        for state,count in counts.items():

            index = int(
                state,
                2
            )

            if index < states:

                quantum_probability[index] = (
                    count / shots
                )


    except:

        quantum_probability = None



    # ========================================================
    # SAFE FALLBACK
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
    # PROBABILITY ZONES
    # ========================================================

    upside_probability = (
        quantum_probability[
            return_grid > 5
        ].sum()
        *
        100
    )


    downside_probability = (
        quantum_probability[
            return_grid < -5
        ].sum()
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
        entropy / np.log(states)
    ) * 100


    volatility_score = np.clip(
        100 - annual_volatility * 100,
        10,
        90
    )


    confidence_score = (
        entropy_score * .50
        +
        volatility_score * .30
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

        market_regime = "Bullish"

    elif market_state < -.08:

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
        downside_probability
        /
        100
    )



    # ========================================================
    # CLEAN METADATA
    # ========================================================

    metadata = {

        "weights": {
            k:
            round(v * 100,2)
            for k,v in weights.items()
        },

        "technical_signal":
            round(float(technical_signal),3),

        "market_state":
            round(float(market_state),3)
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
            metadata
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
        st.session_state.last_run = datetime.datetime.now().strftime("%H:%M:%S")
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
# FORECAST DISPLAY + ANALYTICS DASHBOARD
# ============================================================


forecast = st.session_state.forecast



if forecast:


    # ========================================================
    # SUMMARY METRICS
    # ========================================================

    st.title(
        "⚛️ Quantum Equity Research Terminal"
    )


    col1,col2,col3,col4 = st.columns(4)


    with col1:

        render_metric_card(
            "Expected Price",
            format_price(
                forecast["expected_price"]
            )
        )


    with col2:

        change = (
            forecast["expected_price"]
            /
            forecast["starting_price"]
            -
            1
        ) * 100


        render_metric_card(
            "Expected Return",
            f"{change:+.2f}%",
            change
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



    st.divider()



    # ========================================================
    # MARKET REGIME
    # ========================================================

    col1,col2,col3 = st.columns(3)


    with col1:

        render_status_badge(
            forecast["market_regime"],
            get_change_class(
                forecast["market_state"]
            )
        )


    with col2:

        st.metric(
            "Upside Probability",
            f"{forecast['upside_probability']:.2f}%"
        )


    with col3:

        st.metric(
            "Downside Probability",
            f"{forecast['downside_probability']:.2f}%"
        )



    # ========================================================
    # PRICE DISTRIBUTION GRAPH
    # ========================================================

    st.subheader(
        "Quantum Probability Distribution"
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



    # ========================================================
    # RETURN DISTRIBUTION
    # ========================================================

    st.subheader(
        "Return Probability"
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


    st.pyplot(
        fig,
        clear_figure=True
    )



    # ========================================================
    # QUANTUM DECISION TRACE
    # ========================================================

    with st.expander(
        "⚛️ Quantum Decision Trace"
    ):

        metadata = forecast[
            "model_metadata"
        ]


        weights = metadata[
            "weights"
        ]


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
                    weights["technical"],
                    weights["macro"],
                    weights["global"],
                    weights["sector"],
                    weights["sentiment"]
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


        st.subheader(
            "Signal Influence"
        )


        st.dataframe(
            weight_table,
            hide_index=True,
            width="stretch"
        )


        c1,c2 = st.columns(2)


        with c1:

            st.metric(
                "Technical Signal",
                f"{metadata['technical_signal']:.3f}"
            )


        with c2:

            st.metric(
                "Market State",
                f"{metadata['market_state']:.3f}"
            )



    # ========================================================
    # MODEL MEMORY
    # ========================================================

    with st.expander(
        "🧠 Prediction Memory"
    ):

        try:

            evaluation = evaluate_predictions()

            adjustment = get_prediction_adjustment()


            st.write(
                "Historical Evaluation"
            )

            st.json(
                evaluation
            )


            st.write(
                "Adaptive Adjustment"
            )

            st.metric(
                "Adjustment",
                f"{adjustment:.3f}"
            )


        except:

            st.info(
                "No prediction history available."
            )



    # ========================================================
    # RUN DETAILS
    # ========================================================

    with st.expander(
        "⚙️ Forecast Details"
    ):

        details = pd.DataFrame(
            {
                "Parameter":[
                    "Asset",
                    "Forecast Days",
                    "Qubits",
                    "Shots",
                    "Last Run"
                ],

                "Value":[
                    ticker,
                    forecast_days,
                    qubits,
                    shots,
                    st.session_state.last_run
                ]
            }
        )


        st.dataframe(
            details,
            hide_index=True,
            width="stretch"
        )



else:


    st.title(
        "⚛️ Quantum Equity Research Terminal"
    )


    st.info(
        "Run a quantum forecast from the sidebar."
    )
