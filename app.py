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
        background: linear-gradient(
            135deg,
            #00ff88,
            #00cc66
        );

        color: black;

        font-size: 22px;

        font-weight: 800;

        border-radius: 16px;

        border: 2px solid #00ff88;

        padding: 16px;

        transition: all 0.3s ease;
    }


    div[data-testid="stButton"] button:hover {

        transform: scale(1.08);

        box-shadow:
        0 0 25px #00ff88,
        0 0 50px rgba(0,255,136,0.5);

    }

    </style>
    """,
    unsafe_allow_html=True
    )


    start = st.button(
        "🚀 Start Quantum Simulation",
        use_container_width=True
    )


    if start:

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


    "market_regime": None


}





for key, value in session_defaults.items():


    if key not in st.session_state:


        st.session_state[key] = value





# ============================================================
# AUTO MARKET REFRESH
# ============================================================


st_autorefresh(

    interval=15000,

    key="market_refresh"

)





# ============================================================
# TERMINAL STYLE
# ============================================================


st.markdown(
"""
<style>

.stApp {
    background:
    radial-gradient(circle at top left, #172554, transparent 35%),
    radial-gradient(circle at bottom right, #3b0764, transparent 35%),
    #050816;

    color: #f8fafc;
}


/* Sidebar */

[data-testid="stSidebar"] {

    background:
    linear-gradient(
        180deg,
        #111827,
        #020617
    );

    border-right: 1px solid #334155;
}


/* Main title */

h1 {

    color: #22d3ee !important;

    text-shadow:
    0 0 15px #22d3ee;

}


/* Headers */

h2, h3 {

    color: #e0f2fe !important;

}


/* Buttons */

.stButton > button {

    width: 100%;

    background:
    linear-gradient(
        90deg,
        #06b6d4,
        #8b5cf6
    );

    color: white;

    border-radius: 12px;

    border: none;

    font-weight: bold;

    padding: 12px;

    transition: 0.3s;

}


.stButton > button:hover {

    transform: scale(1.03);

    box-shadow:
    0 0 20px #22d3ee;

}


/* Metric cards */

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



/* Status */

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



/* Positive market movement */

.positive {

    color: #22ff88;

    font-weight: 800;

    text-shadow:
    0 0 12px rgba(34,255,136,0.8);

}



/* Negative market movement */

.negative {

    color: #ff4444;

    font-weight: 800;

    text-shadow:
    0 0 12px rgba(255,68,68,0.8);

}



/* Quantum glow cards */

.metric-box:hover {

    transform: translateY(-5px);

    box-shadow:
    0 0 25px rgba(34,211,238,0.45);

    transition: 0.3s ease;

}



/* Inputs */

input {

    background-color:

    #111827 !important;

    color:

    white !important;

}



/* Dropdown menus */

[data-baseweb="select"] {

    background-color:

    #111827;

}



/* Divider */

hr {

    border-color:

    #334155;

}


/* Dataframes */

[data-testid="stDataFrame"] {

    border-radius:

    12px;

}



/* Tabs */

button[data-baseweb="tab"] {

    color:

    #94a3b8;

}


button[data-baseweb="tab"]:hover {

    color:

    #22d3ee;

}


button[aria-selected="true"] {

    color:

    #22d3ee !important;

    border-bottom:

    2px solid #22d3ee;

}
/* Quantum action buttons */

.stButton > button {

    background: linear-gradient(
        135deg,
        #00ff88,
        #00cc66
    );

    color: black;

    font-weight: 700;

    border-radius: 12px;

    border: 1px solid #00ff88;

    padding: 0.6rem 1.2rem;

    transition: all 0.25s ease;

}


/* Hover effect */

.stButton > button:hover {

    transform: scale(1.05);

    box-shadow:
        0 0 18px #00ff88,
        0 0 35px rgba(0,255,136,0.5);

    background:
        linear-gradient(
            135deg,
            #00ffaa,
            #00ff88
        );

}


/* Sidebar buttons */

[data-testid="stSidebar"] .stButton > button {

    background:
        linear-gradient(
            135deg,
            #00ff88,
            #00b85a
        );

}


/* Warning/danger buttons later */

.danger-button {

    background:
        linear-gradient(
            135deg,
            #ff4444,
            #cc0000
        );

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


matches = search_stocks(

    search_query

)


if matches:


    selected = st.sidebar.selectbox(

        "Select Asset",

        matches,

        format_func=lambda x: x["label"]

    )


    ticker = selected["symbol"]

    company_name = selected["name"]


else:

    ticker = search_query.upper().strip()

    company_name = ticker


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

    max_value=7,

    value=5

)





shots = st.sidebar.slider(

    "Quantum Shots",

    min_value=250,

    max_value=4000,

    value=1500,

    step=250

)





if qubits >= 7 and shots > 2000:


    st.sidebar.warning(

        "Large simulation detected. Reduce shots for better stability."

    )





if qubits == 6 and shots > 3000:


    st.sidebar.warning(

        "High shot count detected."

    )





run_button = st.sidebar.button(

    "Run Quantum Analysis"

)





# ============================================================
# LIVE MARKET HEADER
# ============================================================


live_data = get_live_price(

    ticker

)



company = get_company_info(

    ticker

)



current_price = None





if live_data:


    current_price = live_data.get(

        "price"

    )





header1, header2, header3 = st.columns(3)





with header1:

    company_name = company.get(
        "name",
        ticker
    )

    st.metric(
        "Company",
        company_name
    )





with header2:


    st.metric(

        "Live Price",

        format_price(

            current_price

        )

    )





with header3:

    if live_data:

        daily_change = live_data.get(
            "change_percent",
            0
        )

        if daily_change >= 0:

            change_display = (
                f"<span class='positive'>"
                f"🟢 +{daily_change:.2f}%"
                f"</span>"
            )

        else:

            change_display = (
                f"<span class='negative'>"
                f"🔴 {daily_change:.2f}%"
                f"</span>"
            )
        else:

             change_display = "N/A"


    st.metric(

        "Daily Change",

        change_display

    )









st.caption(

    f"Last update: {datetime.datetime.now().strftime('%H:%M:%S')}"

)





# ============================================================
# LOAD HISTORICAL DATA
# ============================================================


@st.cache_data(

    ttl=900,

    max_entries=100

)

def load_market_data(symbol):


    data = get_stock_data(

        symbol

    )



    if not validate_market_data(

        data

    ):


        return pd.DataFrame()



    return data





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

        st.rerun()



    st.stop()
    # ============================================================
# QUANTUM FORECAST ENGINE
# ============================================================


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

            "Not enough historical data."

        )





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

            "Invalid return history."

        )





    S0 = float(starting_price)





    # ========================================================
    # MARKET STATISTICS
    # ========================================================


    daily_mean = float(

        returns.mean()

    )





    daily_volatility = float(

        returns.std()

    )





    if np.isnan(daily_volatility) or daily_volatility <= 0:


        daily_volatility = 0.01





    annual_volatility = (

        daily_volatility *

        np.sqrt(252)

    )





    # ========================================================
    # RECENT MARKET BEHAVIOR
    # ========================================================


    recent = returns.tail(

        90

    )





    recent_mean = float(

        recent.mean()

    )





    recent_volatility = float(

        recent.std()

    )





    if np.isnan(recent_volatility):


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





    # ========================================================
    # MARKET REGIME
    # ========================================================


    if momentum_score > 0.25:


        regime = "Bullish"



    elif momentum_score < -0.25:


        regime = "Bearish"



    else:


        regime = "Neutral"





    # ========================================================
    # ADJUSTED DRIFT
    # ========================================================


    drift = daily_mean





    # reduce unrealistic trend assumptions


    drift += (

        momentum_score *

        daily_volatility *

        0.15

    )





    # volatility drag


    drift -= (

        0.5 *

        daily_volatility ** 2

    )





    # limit extreme forecasts


    drift = np.clip(

        drift,

        -0.01,

        0.01

    )





    # ========================================================
    # PRICE DISTRIBUTION
    # ========================================================


    years = days / 252





    expected_price = S0 * np.exp(

        drift *

        days

    )





    forecast_volatility = (

        annual_volatility *

        np.sqrt(years)

    )





    # wider realistic range


    spread = (

        S0 *

        forecast_volatility *

        2.2

    )





    states = 2 ** qubits





    price_grid = np.linspace(

        max(

            expected_price - spread,

            S0 * 0.60

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
    # PROBABILITY MODEL
    # ========================================================


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





    # small market uncertainty adjustment


    uncertainty_factor = (

        1 +

        annual_volatility

    )





    probabilities = (

        probabilities /

        uncertainty_factor

    )





    probabilities = np.nan_to_num(

        probabilities

    )





    if probabilities.sum() <= 0:


        probabilities = np.ones(

            states

        )





    probabilities /= probabilities.sum()
        # ========================================================
    # QUANTUM STATE SAMPLING
    # ========================================================


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


        try:


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


            continue





    if quantum_probability.sum() <= 0:


        quantum_probability = probabilities.copy()



    else:


        quantum_probability /= quantum_probability.sum()





    # ========================================================
    # REALISTIC FORECAST ADJUSTMENTS
    # ========================================================


    raw_expected_price = np.sum(

        price_grid *

        quantum_probability

    )





    # penalize extreme confidence


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





    # ========================================================
    # CONFIDENCE SCORE
    # ========================================================


    distribution_entropy = -np.sum(

        quantum_probability *

        np.log(

            quantum_probability +

            1e-12

        )

    )





    max_entropy = np.log(

        states

    )





    confidence_score = (

        1 -

        (

            distribution_entropy /

            max_entropy

        )

    ) * 100





    confidence_score = np.clip(

        confidence_score,

        5,

        95

    )





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

        adjusted_expected_price,



        "volatility":

        annual_volatility * 100,



        "returns":

        returns,



        "market_regime":

        regime,



        "confidence_score":

        confidence_score

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


    if live_data:


        run_price = live_data.get(

            "price"

        )


    else:


        run_price = None





    if run_price is None:


        run_price = float(

            market_data["Close"]

            .iloc[-1]

        )





    try:


        if qubits >= 7 and shots > 3000:


            shots = 3000


            st.warning(

                "Shots reduced automatically for stability."

            )





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


        st.session_state.market_regime = result["market_regime"]


        st.session_state.confidence_score = result["confidence_score"]





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





neutral_probability = 100 - (

    upside_probability +

    downside_probability

)





# normalize edge cases


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

    forecast["volatility"] *

    (

        downside_probability /

        100

    )

)





st.session_state.neutral_probability = neutral_probability


st.session_state.risk_score = risk_score
# ============================================================
# DASHBOARD
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

        <h2>{format_price(forecast['starting_price'])}</h2>

        </div>

        """,

        unsafe_allow_html=True

    )





with card2:


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Quantum Target</h4>

        <h2>{format_price(expected_price)}</h2>

        <p>{expected_change:+.2f}%</p>

        </div>

        """,

        unsafe_allow_html=True

    )





with card3:


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Upside Probability</h4>

        <h2>{upside_probability:.1f}%</h2>

        <p>Above +5% move</p>

        </div>

        """,

        unsafe_allow_html=True

    )





with card4:


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Confidence</h4>

        <h2>{forecast['confidence_score']:.1f}%</h2>

        <p>{forecast['market_regime']} Market</p>

        </div>

        """,

        unsafe_allow_html=True

    )





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

        Aer MPS

        <br>

        {qubits} Qubits | {shots} Shots

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
# OVERVIEW
# ============================================================


with tab1:


    st.subheader(

        "Historical Statistics"

    )


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
# FORECAST TAB
# ============================================================


with tab2:


    st.subheader(

        f"{ticker} {forecast_days}-Day Forecast"

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

        "Return (%)"

    )


    ax.set_ylabel(

        "Probability"

    )


    ax.grid(

        True,

        alpha=0.25

    )


    st.pyplot(

        fig

    )


    plt.close(

        fig

    )





# ============================================================
# RISK ANALYTICS
# ============================================================


with tab3:


    st.subheader(

        "Risk Distribution"

    )


    probabilities = forecast["probability"]

    returns_grid = forecast["return_grid"]



    fig, ax = plt.subplots(

        figsize=(10,4)

    )


    ax.fill_between(

        returns_grid,

        probabilities,

        alpha=0.25

    )


    ax.plot(

        returns_grid,

        probabilities,

        linewidth=2

    )



    ax.grid(

        True,

        alpha=0.25

    )



    st.pyplot(

        fig

    )


    plt.close(

        fig

    )


    st.metric(

        "Risk Score",

        f"{risk_score:.2f}"

    )





# ============================================================
# QUANTUM MODEL
# ============================================================


with tab4:


    st.subheader(

        "Quantum Simulation Architecture"

    )


    st.write(

        """

Historical prices are transformed into a probability distribution.

The distribution is encoded into a quantum state.

Aer MPS sampling estimates possible future market states.

The model provides probabilities, not guaranteed predictions.

"""

    )


    st.code(

        """

Historical Data

↓

Return Analysis

↓

Market Regime Detection

↓

Probability Encoding

↓

Quantum State Sampling

↓

Risk Forecast

""",

        language="text"

    )





# ============================================================
# RAW DATA
# ============================================================


with tab5:


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

        width="stretch"

    )





# ============================================================
# HISTORICAL CHART
# ============================================================


st.divider()


with st.expander(

    "Historical Market Data"

):


    fig, ax = plt.subplots(

        figsize=(10,4)

    )


    ax.plot(

        market_data["Close"],

        linewidth=2

    )


    ax.set_title(

        f"{ticker} Historical Price"

    )


    ax.grid(

        True,

        alpha=0.25

    )


    st.pyplot(

        fig

    )


    plt.close(

        fig

    )





# ============================================================
# FOOTER
# ============================================================


st.divider()


st.caption(

f"""

Quantum Equity Research Terminal


Asset:

{ticker}


Simulation:

Qiskit Aer Matrix Product State


Last Analysis:

{st.session_state.last_run}


This model provides statistical research estimates.

It is not financial advice.

"""

)
