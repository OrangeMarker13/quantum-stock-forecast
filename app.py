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



# ============================================================
# LOCAL MODULES
# ============================================================

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
# Prevents unnecessary recomputation
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
# UNIVERSAL COLOR ENGINE
# ============================================================


def get_change_class(value):

    try:

        value = float(value)


        if value > 0:

            return "positive"


        elif value < 0:

            return "negative"


        else:

            return "neutral"


    except Exception:

        return "neutral"







def format_percent(value):


    try:

        value = float(value)


        arrow = "▲" if value >= 0 else "▼"


        return f"{arrow} {value:+.2f}%"


    except Exception:

        return "N/A"







# ============================================================
# PREMIUM QUANTUM TERMINAL UI
# ============================================================


def apply_quantum_ui():


    st.markdown(

    """

    <style>


    /* ================================
       MAIN BACKGROUND
    ================================= */


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





    /* ================================
       HEADINGS
    ================================= */


    h1 {


        color:#22d3ee !important;


        font-weight:900 !important;


        text-shadow:

        0 0 20px rgba(34,211,238,.5);


    }





    h2,
    h3 {


        color:#e0f2fe !important;


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

        rgba(34,211,238,.25);


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


        padding:12px 20px;


        font-weight:900;


        box-shadow:

        0 0 25px rgba(34,211,238,.35);


    }





    .stButton button:hover {


        transform:translateY(-3px);


        box-shadow:

        0 0 40px rgba(139,92,246,.7);


    }





    /* ================================
       CARDS
    ================================= */


    .metric-box {


        background:

        rgba(15,23,42,.75);


        border:

        1px solid rgba(34,211,238,.25);


        border-radius:18px;


        padding:18px;


        text-align:center;


        box-shadow:

        0 0 25px rgba(34,211,238,.15);


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







# Apply UI immediately

apply_quantum_ui()




# ============================================================
# SAFE DISPLAY HELPERS
# ============================================================


def render_metric_card(

    title,

    value,

    change=None

):


    change_html = ""


    if change is not None:


        css = get_change_class(change)


        change_html = f"""

        <div class="{css}">

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

    background:rgba(255,255,255,.05);

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
# FORECAST STATE MANAGEMENT
# ============================================================


def reset_forecast_state():


    st.session_state.forecast = None

    st.session_state.forecast_settings = None

    st.session_state.last_run = "Never"

    st.session_state.last_price = None

    st.session_state.risk_score = 0

    st.session_state.confidence_score = 0

    st.session_state.market_regime = "Unknown"


# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 2/6
# CONTROLS + MARKET DATA PIPELINE
# ============================================================



# ============================================================
# SIDEBAR CONTROL PANEL
# ============================================================


st.sidebar.title(

    "⚛️ Quantum Forecast Controls"

)





search_query = st.sidebar.text_input(

    "Search Company or Symbol",

    value="Microsoft"

)





# ============================================================
# STOCK SEARCH ENGINE
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
# FORECAST PARAMETERS
# ============================================================


forecast_days = st.sidebar.selectbox(

    "Forecast Horizon",

    options=[

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

• Adaptive weights remain unchanged

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
# LIVE PRICE DATA
# ============================================================


@st.cache_data(

    ttl=60,

    max_entries=100

)

def load_live_price(symbol):


    try:


        return get_live_price(

            symbol

        )


    except Exception:


        return None







live_data = load_live_price(

    ticker

)







# ============================================================
# COMPANY INFORMATION
# ============================================================


@st.cache_data(

    ttl=3600,

    max_entries=100

)

def load_company_info(symbol):


    try:


        return get_company_info(

            symbol

        )


    except Exception:


        return {}







company = load_company_info(

    ticker

)







if not company:


    company = {


        "name":

        company_name


    }







# ============================================================
# CURRENT PRICE EXTRACTION
# ============================================================


current_price = None



if live_data:


    try:


        current_price = float(

            live_data.get(

                "price",

                0

            )

        )


    except Exception:


        current_price = None







daily_change = 0



if live_data:


    try:


        daily_change = float(

            live_data.get(

                "change_percent",

                0

            )

        )


    except Exception:


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
# HISTORICAL DATA LOADER
# ============================================================


@st.cache_data(

    ttl=900,

    max_entries=50

)

def load_market_history(symbol):


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







market_data = load_market_history(

    ticker

)







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

    subset=[

        "Close"

    ]

)







if len(market_data) < 120:


    st.warning(

        "Limited historical data. Forecast quality may decrease."

    )








# ============================================================
# BASIC MARKET CLEANUP
# ============================================================


market_data = market_data.replace(

    [

        np.inf,

        -np.inf

    ],

    np.nan

)






market_data = market_data.fillna(

    0

)







# ============================================================
# RECENT DATA DISPLAY
# ============================================================


with st.expander(

    "📈 Recent Market Data"

):


    recent = market_data.tail(50).copy()



    if "Close" in recent.columns:


        recent["Daily Return %"] = (

            recent["Close"]

            .pct_change()

            *

            100

        )



    st.dataframe(

        recent,

        width="stretch"

    )





# ============================================================
# END PART 2/6
# ============================================================
# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 3/6
# FEATURE ENGINEERING + MODEL INPUT PIPELINE
# ============================================================




# ============================================================
# EXTERNAL MARKET CONTEXT ENGINE
# ============================================================


def get_external_features(symbol):

    """
    Future expansion layer.

    Current version keeps external signals neutral.

    Possible integrations:
    - Federal Reserve rates
    - CPI inflation
    - Treasury yields
    - Sector performance
    - Earnings events
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
# DATA PREPARATION
# ============================================================


def prepare_market_features(data):


    if data is None:


        return pd.DataFrame()



    if data.empty:


        return data






    df = data.copy()



    numeric_columns = df.select_dtypes(

        include=[np.number]

    ).columns






    df[numeric_columns] = df[numeric_columns].replace(

        [

            np.inf,

            -np.inf

        ],

        np.nan

    )






    df[numeric_columns] = df[numeric_columns].fillna(

        0

    )






    return df







market_data = prepare_market_features(

    market_data

)








# ============================================================
# TECHNICAL INDICATOR ENGINE
# ============================================================


def add_technical_features(data):


    df = data.copy()






    # ----------------------------
    # Daily returns
    # ----------------------------


    df["Return"] = (

        df["Close"]

        .pct_change()

    )








    # ----------------------------
    # Moving averages
    # ----------------------------


    df["MA_7"] = (

        df["Close"]

        .rolling(

            window=7

        )

        .mean()

    )





    df["MA_30"] = (

        df["Close"]

        .rolling(

            window=30

        )

        .mean()

    )





    df["MA_90"] = (

        df["Close"]

        .rolling(

            window=90

        )

        .mean()

    )








    # ----------------------------
    # Volatility
    # ----------------------------


    df["Volatility"] = (

        df["Return"]

        .rolling(

            window=30

        )

        .std()

    )








    # ----------------------------
    # Momentum
    # ----------------------------


    df["Momentum_20"] = (

        df["Close"]

        /

        df["Close"].shift(20)

        -

        1

    )








    # ----------------------------
    # RSI calculation
    # ----------------------------


    delta = df["Close"].diff()



    gains = delta.where(

        delta > 0,

        0

    )



    losses = -delta.where(

        delta < 0,

        0

    )






    avg_gain = gains.rolling(

        14

    ).mean()





    avg_loss = losses.rolling(

        14

    ).mean()





    relative_strength = (

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

                relative_strength

            )

        )

    )








    # ----------------------------
    # Market strength indicator
    # ----------------------------


    df["Market_Strength"] = (

        df["MA_30"]

        /

        (

            df["MA_90"]

            +

            1e-9

        )

    )



    df["Market_Strength"] = (

        df["Market_Strength"]

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






    df = df.fillna(

        0

    )






    return df







market_data = add_technical_features(

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
# MODEL INPUT VALIDATION
# ============================================================


def validate_model_inputs(

    data,

    features

):


    if data.empty:


        return False






    required_columns = [

        "Close",

        "Return",

        "Volatility",

        "Momentum_20",

        "RSI"

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
# FEATURE SUMMARY DISPLAY
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

        width="stretch"

    )





# ============================================================
# END PART 3/6
# ============================================================
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






    S0 = float(

        starting_price

    )







    # ========================================================
    # HISTORICAL RETURN ENGINE
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
    # TREND ANALYSIS
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
    # ADAPTIVE WEIGHT SYSTEM
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
    # EXTERNAL MARKET SIGNALS
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







    macro_signal += (

        rate_signal

        *

        0.25

    )








    # ========================================================
    # MARKET STATE
    # ========================================================


    market_state = (

        technical_signal

        *

        technical_weight


        +

        macro_signal

        *

        macro_weight


        +

        global_signal

        *

        global_weight


        +

        sector_signal

        *

        sector_weight


        +

        sentiment_signal

        *

        sentiment_weight


        +

        earnings_signal

        *

        0.10

    )






    market_state = np.clip(

        market_state,

        -0.35,

        0.35

    )








    # ========================================================
    # DRIFT CALCULATION
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
    # MOVEMENT SAFETY LIMITS
    # ========================================================


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
    # QUANTUM PRICE STATE SPACE
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

        S0*0.02,

        S0*allowed_move

    )








    lower_bound = max(

        S0*(1-allowed_move),

        expected_price-price_range

    )






    upper_bound = min(

        S0*(1+allowed_move),

        expected_price+price_range

    )








    price_grid = np.linspace(

        lower_bound,

        upper_bound,

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








    # ========================================================
    # END PART 4/6
    # ========================================================
# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 5/6
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






    classical_probability = np.nan_to_num(

        classical_probability,

        nan=1.0,

        posinf=1.0,

        neginf=0.0

    )







    probability_total = (

        classical_probability.sum()

    )






    if probability_total <= 0:


        classical_probability = np.ones(

            states

        )


        probability_total = states







    classical_probability /= probability_total








    # ========================================================
    # QUANTUM CIRCUIT ENCODING
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








    except Exception:


        quantum_probability = None







    # ========================================================
    # SAFE QUANTUM FALLBACK
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
    # EXPECTED PRICE FROM QUANTUM DISTRIBUTION
    # ========================================================


    quantum_expected_price = (

        np.sum(

            price_grid

            *

            quantum_probability

        )

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
    # RETURN FORECAST OBJECT
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



        "model_metadata":{


            "technical_weight":

                technical_weight,


            "macro_weight":

                macro_weight,


            "global_weight":

                global_weight,


            "sector_weight":

                sector_weight,


            "sentiment_weight":

                sentiment_weight,


            "technical_signal":

                technical_signal,


            "market_state":

                market_state

        }

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

            .strftime(

                "%H:%M:%S"

            )

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
# END PART 5/6
# ============================================================
# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# Adaptive Quantum Forecast Engine
# PART 5/6
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






    classical_probability = np.nan_to_num(

        classical_probability,

        nan=1.0,

        posinf=1.0,

        neginf=0.0

    )







    probability_total = (

        classical_probability.sum()

    )






    if probability_total <= 0:


        classical_probability = np.ones(

            states

        )


        probability_total = states







    classical_probability /= probability_total








    # ========================================================
    # QUANTUM CIRCUIT ENCODING
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








    except Exception:


        quantum_probability = None







    # ========================================================
    # SAFE QUANTUM FALLBACK
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
    # EXPECTED PRICE FROM QUANTUM DISTRIBUTION
    # ========================================================


    quantum_expected_price = (

        np.sum(

            price_grid

            *

            quantum_probability

        )

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
    # RETURN FORECAST OBJECT
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



        "model_metadata":{


            "technical_weight":

                technical_weight,


            "macro_weight":

                macro_weight,


            "global_weight":

                global_weight,


            "sector_weight":

                sector_weight,


            "sentiment_weight":

                sentiment_weight,


            "technical_signal":

                technical_signal,


            "market_state":

                market_state

        }

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

            .strftime(

                "%H:%M:%S"

            )

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
# END PART 5/6
# ============================================================
