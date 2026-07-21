# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 1A/6
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


# ============================================================
# PREDICTION MEMORY
# Evaluation only.
# Does NOT alter adaptive weights.
# Does NOT modify quantum probabilities.
# ============================================================

from prediction_memory import (
    evaluate_predictions,
    get_prediction_adjustment
)



# ============================================================
# SESSION STATE INITIALIZATION
# Prevents Streamlit crashes
# ============================================================

if "forecast" not in st.session_state:
    st.session_state.forecast = None

if "forecast_settings" not in st.session_state:
    st.session_state.forecast_settings = None

if "last_run" not in st.session_state:
    st.session_state.last_run = "Never"

if "last_price" not in st.session_state:
    st.session_state.last_price = None

if "risk_score" not in st.session_state:
    st.session_state.risk_score = 0

if "confidence_score" not in st.session_state:
    st.session_state.confidence_score = 0

if "market_regime" not in st.session_state:
    st.session_state.market_regime = "Unknown"



# ============================================================
# UNIVERSAL GAIN / LOSS COLOR ENGINE
# ============================================================

def color_change(value):

    try:

        value = float(value)

        if value >= 0:

            return (
                f'<span class="positive">'
                f'▲ {value:+.2f}%'
                f'</span>'
            )

        else:

            return (
                f'<span class="negative">'
                f'▼ {value:+.2f}%'
                f'</span>'
            )

    except Exception:

        return str(value)



# ============================================================
# QUANTUM TERMINAL PREMIUM UI ENGINE
# ============================================================

def apply_quantum_ui():

    st.markdown(
    """
    <style>


    /* ================================
       GLOBAL BACKGROUND
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
       TEXT
    ================================= */

    h1 {

        color:#22d3ee !important;

        font-weight:900 !important;

        letter-spacing:-1px;

        text-shadow:
        0 0 20px
        rgba(34,211,238,.55);

    }



    h2,
    h3 {

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


    """
    ,
    unsafe_allow_html=True
    )
    # ============================================================
# APP.PY PART 1B/6
# UI COMPONENT HELPERS + DISPLAY ENGINE
# ============================================================



# ============================================================
# PREMIUM CARD RENDERING FUNCTIONS
# ============================================================


def render_metric_card(
    title,
    value,
    change=None
):

    change_html = ""


    if change is not None:


        try:

            change = float(change)

        except:

            change = 0



        css = change_color(change)



        change_html = f"""

        <p class="{css}">

        {change:+.2f}%

        </p>

        """



    st.markdown(

        f"""

        <div class="metric-box">


        <h4>

        {title}

        </h4>


        <h2>

        {value}

        </h2>


        {change_html}


        </div>

        """,

        unsafe_allow_html=True

    )







# ============================================================
# STATUS BADGE ENGINE
# ============================================================


def render_status_badge(
    text,
    status="neutral"
):


    colors = {


        "positive":

        "#22ff88",


        "negative":

        "#ff5555",


        "neutral":

        "#22d3ee"

    }



    color = colors.get(

        status,

        "#22d3ee"

    )



    st.markdown(

        f"""

        <div style="

        display:inline-block;

        padding:8px 18px;

        border-radius:20px;

        background:{color}22;

        border:1px solid {color};

        color:{color};

        font-weight:900;

        box-shadow:

        0 0 20px {color}55;

        ">


        {text}


        </div>

        """,

        unsafe_allow_html=True

    )







# ============================================================
# FORECAST COLOR ENGINE
#
# Keeps forecast display consistent:
# Gain = green
# Loss = red
# ============================================================


def forecast_direction(
    current,
    predicted
):


    try:


        difference = (

            float(predicted)

            -

            float(current)

        )



    except:


        return "neutral"



    if difference > 0:


        return "positive"



    elif difference < 0:


        return "negative"



    return "neutral"







def render_forecast_change(
    current,
    predicted
):


    try:


        percent = (

            (

                float(predicted)

                -

                float(current)

            )

            /

            float(current)

        ) * 100



    except:


        percent = 0



    css = forecast_direction(

        current,

        predicted

    )



    st.markdown(

        f"""

        <span class="{css}"

        style="font-size:22px;">


        {percent:+.2f}%


        </span>

        """,

        unsafe_allow_html=True

    )







# ============================================================
# DATA COLOR FORMATTERS
#
# Used for tables and dataframe outputs
# ============================================================


def color_gain_loss(value):


    try:


        number = float(value)


    except:


        return ""



    if number > 0:


        return "color:#22ff88;font-weight:900;"


    elif number < 0:


        return "color:#ff5555;font-weight:900;"



    return "color:#cbd5e1;"








def style_dataframe(df):


    if df.empty:


        return df



    styled = df.style



    for column in df.columns:


        if (

            "return" in column.lower()

            or

            "change" in column.lower()

            or

            "%" in column

        ):


            styled = styled.map(

                color_gain_loss,

                subset=[column]

            )



    return styled








# ============================================================
# QUANTUM LOADING ANIMATION
# ============================================================


def quantum_loading():

    placeholder = st.empty()


    frames = [

        "⚛️ Initializing quantum states",

        "⚛️ Encoding market probabilities",

        "⚛️ Running quantum simulation",

        "⚛️ Measuring probability distribution"

    ]



    for frame in frames:


        placeholder.markdown(

            f"""

            <div class="metric-box">


            <h3>

            {frame}

            </h3>


            </div>

            """,

            unsafe_allow_html=True

        )





    placeholder.empty()







# ============================================================
# MARKET HEADER COMPONENT
# ============================================================


def render_market_header(

    company,

    ticker,

    price,

    daily_change

):


    col1,col2,col3 = st.columns(3)



    with col1:


        render_metric_card(

            "Company",

            company

        )



    with col2:


        render_metric_card(

            "Live Price",

            price

        )



    with col3:


        render_metric_card(

            "Daily Change",

            f"{daily_change:+.2f}%",

            daily_change

        )








# ============================================================
# SAFE SESSION STATE ACCESS
# ============================================================


def get_forecast_state():


    return st.session_state.get(

        "forecast",

        None

    )






def reset_forecast_state():


    st.session_state.forecast = None


    st.session_state.forecast_settings = None


    st.session_state.last_run = "Never"


    st.session_state.last_price = None


    st.session_state.risk_score = None


    st.session_state.confidence_score = None


    st.session_state.market_regime = None







# ============================================================
# FINAL UI INITIALIZATION
# ============================================================


st.markdown(

"""

<style>


.stMarkdown {


    color:#e5e7eb;

}



[data-testid="stExpander"] {


    border-radius:18px;


    border:1px solid rgba(34,211,238,.25);


}



</style>

""",

unsafe_allow_html=True

)
# ============================================================
# APP.PY PART 2/6
# CONTROLS + LIVE DATA + MARKET LOADING
# ============================================================


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================


if "forecast" not in st.session_state:
    st.session_state.forecast = None


if "forecast_settings" not in st.session_state:
    st.session_state.forecast_settings = None


if "last_run" not in st.session_state:
    st.session_state.last_run = "Never"


if "last_price" not in st.session_state:
    st.session_state.last_price = None


if "risk_score" not in st.session_state:
    st.session_state.risk_score = None


if "confidence_score" not in st.session_state:
    st.session_state.confidence_score = None


if "market_regime" not in st.session_state:
    st.session_state.market_regime = "Unknown"





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





st.sidebar.markdown(

"""

### Quantum Simulation

Qubits determine possible market states.

Shots determine sampling resolution.

Adaptive weights remain unchanged.

Prediction memory only evaluates previous forecasts.

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





if not company:


    company = {

        "name": company_name

    }






current_price = None



if live_data:


    current_price = live_data.get(

        "price",

        None

    )






# ============================================================
# MARKET HEADER
# ============================================================


if current_price is not None:


    daily_change = live_data.get(

        "change_percent",

        0

    )


else:


    daily_change = 0





try:

    daily_change = float(

        daily_change

    )


except Exception:


    daily_change = 0






render_market_header(

    company.get(

        "name",

        company_name

    ),

    ticker,

    format_price(

        current_price

    ),

    daily_change

)





st.caption(

    f"Last market update: {datetime.datetime.now().strftime('%H:%M:%S')}"

)






# ============================================================
# HISTORICAL DATA LOADING
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
# DATA VALIDATION
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
# DAILY PERFORMANCE COLORS
# ============================================================


market_data["Daily Return %"] = (

    market_data["Close"]

    .pct_change()

    *

    100

)





styled_market = style_dataframe(

    market_data.tail(50)

)





with st.expander(

    "📈 Recent Market Data"

):


    st.dataframe(

        styled_market,

        width="stretch"

    )
    # ============================================================
# APP.PY PART 3/6
# EXTERNAL DATA + FEATURE PIPELINE
# ============================================================


# ============================================================
# EXTERNAL MARKET FEATURE ENGINE
# ============================================================


def get_external_features(symbol):

    """
    External market context layer.

    IMPORTANT:
    These values do not modify adaptive weights.

    They only provide additional market context.

    Prediction memory:
    - evaluates previous forecasts
    - does not update this engine
    - does not create bias

    Future integrations:
    - Federal Reserve data
    - CPI
    - Treasury yields
    - Sector ETFs
    - Earnings reports
    - News sentiment
    """


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
# PREDICTION MEMORY CALIBRATION
# ============================================================


def apply_prediction_calibration(

    base_prediction,

    symbol,

    horizon

):

    """
    Historical error correction only.

    Does NOT:
    - change factor weights
    - change quantum probabilities
    - change market signals

    It only measures previous forecast error.
    """


    try:


        adjustment = get_prediction_adjustment(

            symbol,

            horizon

        )


        adjustment = float(

            adjustment

        )


        # Prevent historical memory from
        # overpowering current market data


        adjustment = np.clip(

            adjustment,

            -0.05,

            0.05

        )



        calibrated_prediction = (

            base_prediction

            *

            (

                1

                +

                adjustment

            )

        )


        return calibrated_prediction



    except Exception:


        return base_prediction






# ============================================================
# MARKET FEATURE PREPARATION
# ============================================================


def prepare_market_features(data):


    if data is None:


        return pd.DataFrame()



    if data.empty:


        return data



    prepared = data.copy()





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
# TECHNICAL FEATURE CALCULATIONS
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






    # RSI approximation


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

        (

            avg_loss

            +

            1e-9

        )

    )



    df["RSI"] = (

        100

        -

        (

            100

            /

            (

                1

                +

                rs

            )

        )

    )






    # Market strength score


    df["Market_Strength"] = (

        (

            df["MA_30"]

            /

            df["MA_90"]

        )

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



    df = df.fillna(0)



    return df






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
# MODEL INPUT VALIDATION
# ============================================================


def validate_model_inputs(

    data,

    features

):


    if data.empty:


        return False





    if "Close" not in data.columns:


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

            "Insufficient historical data."

        )





    S0 = float(

        starting_price

    )





    # ========================================================
    # HISTORICAL RETURNS
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
    # TECHNICAL TREND ENGINE
    # ========================================================


    def safe_trend(window):


        if len(prices) <= window:


            return 0.0



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
    # ADAPTIVE WEIGHT SYSTEM
    #
    # IMPORTANT:
    # Prediction memory does not modify these.
    # External features do not modify these.
    # No hidden feedback loop.
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





    macro += (

        rates

        *

        0.25

    )







    # ========================================================
    # COMBINED MARKET STATE
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





    expected_return = (

        drift

        *

        days

    )






    # ========================================================
    # HORIZON SAFETY LIMITS
    # ========================================================


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
    # QUANTUM STATE SPACE
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
# PROBABILITY ENGINE + QUANTUM SAMPLING + FORECAST OUTPUT
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
    #
    # Measures signal agreement.
    #
    # Does not modify adaptive weights.
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






    probability_sum = (

        classical_probability.sum()

    )





    if probability_sum <= 0:


        classical_probability = np.ones(

            states

        )


        probability_sum = states





    classical_probability /= probability_sum







    # ========================================================
    # QUANTUM STATE ENCODING
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
    # EXPECTED QUANTUM PRICE
    # ========================================================


    quantum_expected_price = np.sum(

        price_grid

        *

        quantum_probability

    )







    # ========================================================
    # UPSIDE / DOWNSIDE / NEUTRAL PROBABILITY
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

        entropy

        /

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
    # MARKET REGIME CLASSIFICATION
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
    # FINAL FORECAST OBJECT
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

            annual_vol * 100,



        "returns":

            returns,



        "market_regime":

            regime,



        "confidence_score":

            confidence_score,



        "market_state":

            market_state,



        "risk_score":

            risk_score,



        "upside_probability":

            upside_probability,



        "downside_probability":

            downside_probability,



        "neutral_probability":

            neutral_probability,



        "model_metadata": {


            "technical_signal":

                technical_signal,


            "market_state":

                market_state,


            "technical_weight":

                technical_weight,


            "macro_weight":

                macro_weight,


            "global_weight":

                global_weight,


            "sector_weight":

                sector_weight,


            "sentiment_weight":

                sentiment_weight


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


        quantum_loading()



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

            .strftime(

                "%H:%M:%S"

            )

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

            "Quantum analysis completed successfully."

        )





    except Exception as error:


        st.error(

            f"Forecast failed: {error}"

        )


        st.stop()
        # ============================================================
# APP.PY PART 5/6
# PROBABILITY ENGINE + QUANTUM SAMPLING + FORECAST OUTPUT
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
    #
    # Measures signal agreement.
    #
    # Does not modify adaptive weights.
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






    probability_sum = (

        classical_probability.sum()

    )





    if probability_sum <= 0:


        classical_probability = np.ones(

            states

        )


        probability_sum = states





    classical_probability /= probability_sum







    # ========================================================
    # QUANTUM STATE ENCODING
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
    # EXPECTED QUANTUM PRICE
    # ========================================================


    quantum_expected_price = np.sum(

        price_grid

        *

        quantum_probability

    )







    # ========================================================
    # UPSIDE / DOWNSIDE / NEUTRAL PROBABILITY
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

        entropy

        /

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
    # MARKET REGIME CLASSIFICATION
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
    # FINAL FORECAST OBJECT
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

               annual_vol * 100,



          "returns":

             returns,



          "market_regime":

               regime,



          "confidence_score":

             confidence_score,



         "market_state":

               market_state,



          "risk_score":

               risk_score,



          "upside_probability":

              upside_probability,



         "downside_probability":

              downside_probability,



         "neutral_probability":

              neutral_probability,
    


         "model_metadata": {


            "technical_signal":

                 technical_signal,


              "market_state":

                 market_state,
    

             "technical_weight":

               technical_weight,


             "macro_weight":

                macro_weight,


             "global_weight":

                global_weight,

             "sector_weight":

                  sector_weight,


             "sentiment_weight":

                  sentiment_weight
    

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


        quantum_loading()



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

            .strftime(

                "%H:%M:%S"

            )

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

            "Quantum analysis completed successfully."

        )





    except Exception as error:


        st.error(

            f"Forecast failed: {error}"

        )


        st.stop()
