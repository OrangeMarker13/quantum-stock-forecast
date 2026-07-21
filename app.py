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
        Adaptive Quantum Market Probability Engine
        </h3>

        <p style="
        font-size:20px;
        color:#b8c1d1;
        ">

        Multi-factor forecasting using historical behavior,
        adaptive weights, market variables, and quantum probability sampling.

        </p>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.divider()


    c1, c2, c3 = st.columns(3)


    with c1:
        st.markdown(
            """
            ### 📈 Market Intelligence

            Momentum,
            volatility,
            trends,
            and historical behavior.
            """
        )


    with c2:
        st.markdown(
            """
            ### ⚛️ Quantum Simulation

            Probability distributions encoded into
            quantum states and sampled.
            """
        )


    with c3:
        st.markdown(
            """
            ### 🛡 Risk Analytics

            Scenario probabilities,
            confidence,
            and downside control.
            """
        )


    st.divider()


    if st.button(
        "🚀 Start Quantum Simulation",
        width="stretch"
    ):

        st.session_state.started = True
        st.rerun()


    st.stop()



# ============================================================
# SESSION STATE
# ============================================================

defaults = {

    "forecast": None,

    "forecast_settings": None,

    "last_run": None,

    "last_price": None,

    "risk_score": None,

    "confidence_score": None,

    "market_regime": None,

    "quantum_features": None

}


for key, value in defaults.items():

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
# STYLE
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

}


h1 {

color:#22d3ee !important;

}


.metric-box {

background:
linear-gradient(
145deg,
#111827,
#1e293b
);

border:1px solid #334155;

padding:18px;

border-radius:16px;

}


.positive {

color:#22ff88;

font-weight:800;

}


.negative {

color:#ff5555;

font-weight:800;

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
    "Adaptive weighted quantum probability forecasting."
)


st.divider()
# ============================================================
# SIDEBAR CONTROLS
# ============================================================

st.sidebar.title("⚛️ Quantum Forecast Controls")


search_query = st.sidebar.text_input(
    "Search Company or Symbol",
    "Microsoft"
)


try:
    matches = search_stocks(search_query)
except Exception:
    matches = []


if matches:

    selected = st.sidebar.selectbox(
        "Select Asset",
        matches,
        format_func=lambda x: x.get(
            "label",
            x.get("symbol", "Unknown")
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

    ticker = search_query.upper().strip()
    company_name = ticker



forecast_days = st.sidebar.selectbox(
    "Forecast Horizon",
    [7,30,60,90],
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
Quantum sampling:
Higher qubits = more market states.
Higher shots = smoother probability sampling.
"""
)


run_button = st.sidebar.button(
    "🚀 Run Quantum Forecast"
)



# ============================================================
# LIVE DATA
# ============================================================

try:
    live_data = get_live_price(ticker)
except Exception:
    live_data = None


try:
    company = get_company_info(ticker)
except Exception:
    company = {}


current_price = None

if live_data:
    current_price = live_data.get("price")



h1,h2,h3 = st.columns(3)


with h1:

    st.metric(
        "Company",
        company.get(
            "name",
            company_name
        )
    )


with h2:

    st.metric(
        "Live Price",
        format_price(current_price)
    )


with h3:

    change = 0

    if live_data:
        change = live_data.get(
            "change_percent",
            0
        )

    try:
        change=float(change)
    except:
        change=0

    cls="positive" if change>=0 else "negative"

    st.markdown(
        f"""
        <div class="metric-box">
        <h4>Daily Change</h4>
        <h2 class="{cls}">
        {change:+.2f}%
        </h2>
        </div>
        """,
        unsafe_allow_html=True
    )


st.caption(
    f"Last update {datetime.datetime.now().strftime('%H:%M:%S')}"
)



# ============================================================
# HISTORICAL DATA
# ============================================================

@st.cache_data(
    ttl=900,
    max_entries=50
)
def load_market_data(symbol):

    try:

        data=get_stock_data(symbol)

        if not validate_market_data(data):
            return pd.DataFrame()

        return data

    except Exception:

        return pd.DataFrame()



market_data=load_market_data(ticker)


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



if "Close" not in market_data.columns:

    st.error(
        "Missing Close price data."
    )

    st.stop()



market_data=market_data.copy()


market_data["Close"]=pd.to_numeric(
    market_data["Close"],
    errors="coerce"
)


market_data.dropna(
    subset=["Close"],
    inplace=True
)


if len(market_data)<120:

    st.error(
        "Need at least 120 trading days."
    )

    st.stop()



# ============================================================
# EXTERNAL DATA CONNECTION
# ============================================================

def get_external_features():

    return {

        "macro_score":0,
        "sector_score":0,
        "sentiment_score":0,
        "global_market_score":0,
        "earnings_score":0,
        "rate_score":0

    }


external_features=get_external_features()

st.session_state.quantum_features=external_features
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
        raise ValueError("Insufficient historical data")


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


    daily_vol = float(
        returns.std()
    )


    if daily_vol <= 0:
        daily_vol = 0.01


    annual_vol = daily_vol * np.sqrt(252)


    # ========================================================
    # TREND SIGNALS
    # ========================================================

    trend_7 = prices.iloc[-1] / prices.iloc[-7] - 1
    trend_30 = prices.iloc[-1] / prices.iloc[-30] - 1
    trend_90 = prices.iloc[-1] / prices.iloc[-90] - 1
    trend_180 = prices.iloc[-1] / prices.iloc[-180] - 1


    technical_signal = (
        trend_7 * 0.10 +
        trend_30 * 0.30 +
        trend_90 * 0.40 +
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
        returns.tail(30).std()
    )


    volatility_ratio = recent_vol / daily_vol


    volatility_ratio = np.clip(
        volatility_ratio,
        0.5,
        3
    )


    # ========================================================
    # ADAPTIVE WEIGHTS
    # ========================================================

    # calm market = technical signals stronger
    # volatile market = macro factors stronger

    technical_weight = 0.45 / volatility_ratio

    macro_weight = 0.15 * volatility_ratio

    global_weight = 0.15 * volatility_ratio

    sector_weight = 0.15

    sentiment_weight = 0.10


    total = (
        technical_weight +
        macro_weight +
        global_weight +
        sector_weight +
        sentiment_weight
    )


    technical_weight /= total
    macro_weight /= total
    global_weight /= total
    sector_weight /= total
    sentiment_weight /= total



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

        technical_signal * technical_weight +

        macro * macro_weight +

        global_market * global_weight +

        sector * sector_weight +

        sentiment * sentiment_weight +

        earnings * 0.10

    )


    market_state = np.clip(
        market_state,
        -0.35,
        0.35
    )



    # ========================================================
    # REALISTIC DRIFT MODEL
    # ========================================================

    historical_return = float(
        returns.mean()
    )


    # reduce overreaction to bad periods

    drift = (

        historical_return * 0.35 +

        market_state * 0.25 +

        (historical_return * 0.40)

    )


    # stocks usually do not have massive expected
    # daily movement without extreme conditions

    drift = np.clip(
        drift,
        -0.0015,
        0.0015
    )



    # ========================================================
    # EXPECTED RETURN
    # ========================================================

    expected_return = drift * days


    # realistic long horizon limits

    max_moves = {

        7:0.10,

        30:0.18,

        60:0.25,

        90:0.35

    }


    allowed_move = max_moves.get(
        days,
        0.35
    )


    expected_return = np.clip(
        expected_return,
        -allowed_move,
        allowed_move
    )


    expected_price = (
        S0 *
        np.exp(expected_return)
    )



    # ========================================================
    # PRICE STATE GRID
    # ========================================================

    states = 2 ** qubits


    volatility_range = (

        S0 *
        annual_vol *
        np.sqrt(days/252) *
        1.5

    )


    volatility_range = np.clip(
        volatility_range,
        S0*0.04,
        S0*allowed_move
    )


    lower_bound = max(
        S0*(1-allowed_move),
        expected_price-volatility_range
    )


    upper_bound = min(
        S0*(1+allowed_move),
        expected_price+volatility_range
    )


    price_grid=np.linspace(
        lower_bound,
        upper_bound,
        states
    )


    return_grid=(

        (price_grid-S0)
        /
        S0

    )*100
    # ============================================================
# PROBABILITY DISTRIBUTION
# ============================================================

    target_return = (
        expected_price / S0 - 1
    )


    uncertainty = (
        annual_vol *
        np.sqrt(days / 252)
    )


    uncertainty = np.clip(
        uncertainty,
        0.04,
        allowed_move
    )


    z = (
        (return_grid / 100 - target_return)
        /
        uncertainty
    )


    classical_probability = np.exp(
        -0.5 * z**2
    )



    # ========================================================
    # MARKET CONFIDENCE ADJUSTMENT
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
        0.85 +
        factor_alignment * 0.15
    )


    classical_probability = np.nan_to_num(
        classical_probability
    )


    if classical_probability.sum() <= 0:

        classical_probability = np.ones(
            states
        )


    classical_probability /= (
        classical_probability.sum()
    )



# ============================================================
# QUANTUM SAMPLING
# ============================================================

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
                    count / shots
                )


    except Exception:

        quantum_probability = None



# ============================================================
# QUANTUM FALLBACK
# ============================================================

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



# ============================================================
# EXPECTED VALUE
# ============================================================

    quantum_expected_price = np.sum(
        price_grid *
        quantum_probability
    )



# ============================================================
# SCENARIO PROBABILITIES
# ============================================================

    upside_probability = np.sum(
        quantum_probability[
            return_grid > 5
        ]
    ) * 100


    downside_probability = np.sum(
        quantum_probability[
            return_grid < -5
        ]
    ) * 100



    neutral_probability = (
        100
        -
        upside_probability
        -
        downside_probability
    )


    # keep scenarios realistic

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



# ============================================================
# CONFIDENCE SCORE
# ============================================================

    entropy = -np.sum(
        quantum_probability *
        np.log(
            quantum_probability + 1e-12
        )
    )


    entropy_score = (
        1 -
        entropy / np.log(states)
    ) * 100


    volatility_score = (
        100 -
        annual_vol * 100
    )


    volatility_score = np.clip(
        volatility_score,
        10,
        90
    )


    confidence_score = (

        entropy_score * 0.50 +

        volatility_score * 0.30 +

        factor_alignment * 100 * 0.20

    )


    confidence_score = np.clip(
        confidence_score,
        10,
        95
    )



# ============================================================
# MARKET REGIME
# ============================================================

    if market_state > 0.08:

        regime = "Bullish"

    elif market_state < -0.08:

        regime = "Bearish"

    else:

        regime = "Neutral"



# ============================================================
# RISK SCORE
# ============================================================

    risk_score = (

        annual_vol * 100 *

        (downside_probability / 100)

    )


# ============================================================
# RETURN RESULTS
# ============================================================

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

        "adaptive_weights": {

            "technical": technical_weight,

            "macro": macro_weight,

            "global": global_weight,

            "sector": sector_weight,

            "sentiment": sentiment_weight

        }

    }
    # ============================================================
# RUN FORECAST
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
        else float(market_data["Close"].iloc[-1])
    )


    try:

        with st.spinner(
            "Running adaptive quantum probability simulation..."
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
        st.session_state.last_run = datetime.datetime.now().strftime(
            "%H:%M:%S"
        )

        st.session_state.last_price = run_price
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
# DASHBOARD
# ============================================================

st.divider()

st.subheader(
    "⚛️ Quantum Probability Dashboard"
)


expected_price = forecast["expected_price"]


price_change = (

    (
        expected_price -
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
        {format_price(forecast["starting_price"])}
        </h2>
        </div>
        """,
        unsafe_allow_html=True
    )


with c2:

    cls = (
        "positive"
        if price_change >= 0
        else "negative"
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

    st.markdown(
        f"""
        <div class="metric-box">
        <h4>Upside Probability</h4>
        <h2>
        {forecast["upside_probability"]:.1f}%
        </h2>
        <p>
        Probability above +5%
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )


with c4:

    st.markdown(
        f"""
        <div class="metric-box">
        <h4>Confidence</h4>
        <h2>
        {forecast["confidence_score"]:.1f}%
        </h2>
        <p>
        {forecast["market_regime"]}
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )



# ============================================================
# SCENARIOS
# ============================================================

st.divider()


s1,s2,s3 = st.columns(3)


with s1:

    st.metric(
        "Bull Scenario",
        f'{forecast["upside_probability"]:.1f}%'
    )


with s2:

    st.metric(
        "Neutral Scenario",
        f'{forecast["neutral_probability"]:.1f}%'
    )


with s3:

    st.metric(
        "Bear Scenario",
        f'{forecast["downside_probability"]:.1f}%'
    )



# ============================================================
# ANALYTICS TABS
# ============================================================

tab1,tab2,tab3,tab4,tab5 = st.tabs(
    [
        "Overview",
        "Forecast",
        "Risk",
        "Quantum Model",
        "Raw Data"
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


    st.write(
        "Adaptive Weights"
    )

    st.json(
        forecast["adaptive_weights"]
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

    ax.grid(alpha=0.3)

    st.pyplot(
        fig,
        width="stretch"
    )

    plt.close(fig)



with tab3:

    st.metric(
        "Risk Score",
        f'{forecast["risk_score"]:.2f}'
    )

    st.metric(
        "Annual Volatility",
        f'{forecast["volatility"]:.2f}%'
    )



with tab4:

    st.write(
"""
Historical Data

↓

Adaptive Factor Weighting

↓

Probability Distribution

↓

Quantum State Encoding

↓

Qiskit Aer MPS Sampling

↓

Probability Weighted Forecast
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



with tab5:

    table = pd.DataFrame(
        {
            "Price":forecast["price_grid"],
            "Return %":forecast["return_grid"],
            "Probability %":forecast["probability"]*100
        }
    )


    st.dataframe(
        table,
        width="stretch"
    )



# ============================================================
# EXPORT
# ============================================================

st.divider()


export = pd.DataFrame(
    {
        "Future Price":forecast["price_grid"],
        "Return %":forecast["return_grid"],
        "Probability":forecast["probability"]
    }
)


st.download_button(
    "Download Quantum Forecast CSV",
    export.to_csv(index=False),
    file_name=f"{ticker}_quantum_forecast.csv",
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
