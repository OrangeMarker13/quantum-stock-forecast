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

    get_market_status,

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
# SESSION STATE
# ============================================================


session_defaults = {

    "forecast": None,

    "forecast_settings": None,

    "last_run": None,

    "last_price": None,

    "neutral_probability": None,

    "risk_score": None

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

    background-color:#080d18;

    color:#e5e7eb;

}



[data-testid="stSidebar"] {

    background-color:#111827;

}



.metric-box {

    background:#111827;

    border:1px solid #263246;

    padding:16px;

    border-radius:12px;

}



.status-box {

    background:#0f172a;

    border-left:4px solid #22c55e;

    padding:12px;

    border-radius:8px;

}



h1,h2,h3 {

    color:#f8fafc;

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





popular_assets = [

    "AAPL",

    "MSFT",

    "NVDA",

    "GOOGL",

    "AMZN",

    "META",

    "TSLA",

    "AMD",

    "NFLX",

    "SPY",

    "QQQ",

    "BTC-USD"

]





ticker = st.sidebar.selectbox(

    "Asset",

    popular_assets

)



ticker = ticker.upper().strip()





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

        "Large quantum simulation detected. Lower shots for improved stability."

    )





if qubits == 6 and shots > 3000:


    st.sidebar.warning(

        "High shot count detected. Consider reducing shots."

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





header1, header2, header3, header4 = st.columns(4)





with header1:

    st.metric(

        "Company",

        company.get(

            "name",

            ticker

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

    st.metric(

        "Daily Change",

        format_percent(

            live_data.get(

                "change_percent",

                0

            )

        )

        if live_data

        else "N/A"

    )





with header4:

    st.metric(

        "Market Status",

        get_market_status(

            live_data

        )

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


    if not validate_market_data(data):

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


@st.cache_data(

    ttl=1800,

    max_entries=50

)

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



    if len(prices) < 30:


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

            "Invalid return data."

        )





    S0 = float(starting_price)





    # --------------------------------------------------------
    # MARKET STATISTICS
    # --------------------------------------------------------


    daily_mean = float(

        returns.mean()

    )


    daily_volatility = float(

        returns.std()

    )



    if np.isnan(daily_volatility) or daily_volatility <= 0:

        daily_volatility = 0.01





    # Recent trend influence

    recent_returns = returns.tail(

        60

    )



    recent_factor = (

        recent_returns.mean()

        /

        (

            recent_returns.std()

            +

            1e-9

        )

    )



    recent_factor = np.clip(

        recent_factor,

        -0.5,

        0.5

    )





    adjusted_mean = (

        daily_mean

        +

        recent_factor * 0.05

    )





    # Volatility drag

    drift = (

        adjusted_mean

        -

        0.5 *

        daily_volatility ** 2

    )





    time_years = days / 252





    expected_center = S0 * np.exp(

        drift * days

    )





    spread = (

        S0 *

        daily_volatility *

        np.sqrt(time_years)

        *

        3

    )





    states = 2 ** qubits





    price_grid = np.linspace(

        max(

            expected_center - spread,

            S0 * 0.5

        ),

        expected_center + spread,

        states

    )





    return_grid = (

        (

            price_grid -

            S0

        )

        /

        S0

    )

    * 100





    # --------------------------------------------------------
    # PROBABILITY DISTRIBUTION
    # --------------------------------------------------------


    expected_return = drift * days



    volatility_range = (

        daily_volatility *

        np.sqrt(days)

    )





    if volatility_range <= 0:


        volatility_range = 0.01





    probabilities = np.exp(

        -0.5 *

        (

            (

                (

                    return_grid / 100

                )

                -

                expected_return

            )

            /

            volatility_range

        )

        ** 2

    )





    probabilities = np.nan_to_num(

        probabilities

    )





    if probabilities.sum() == 0:


        probabilities = np.ones(

            states

        )





    probabilities /= probabilities.sum()





    # --------------------------------------------------------
    # QUANTUM SAMPLING
    # --------------------------------------------------------


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


        index = int(

            state,

            2

        )


        if index < states:


            quantum_probability[index] = (

                count /

                shots

            )





    if quantum_probability.sum() == 0:


        quantum_probability = probabilities



    else:


        quantum_probability /= quantum_probability.sum()





    expected_price = np.sum(

        price_grid *

        quantum_probability

    )





    # volatility penalty

    penalty = min(

        daily_volatility *

        np.sqrt(days),

        0.25

    )



    expected_price *= (

        1 -

        penalty

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

        expected_price,


        "volatility":

        daily_volatility *

        np.sqrt(252)

        *

        100,


        "returns":

        returns

    }
    # ============================================================
# RUN QUANTUM ANALYSIS
# ============================================================


settings = (

    ticker,

    forecast_days,

    qubits,

    shots

)





if run_button:


    run_price = None



    if live_data:


        run_price = live_data.get(

            "price"

        )



    if run_price is None:


        run_price = float(

            market_data["Close"]

            .iloc[-1]

        )





    try:


        if qubits >= 7 and shots > 3000:


            shots = 3000



            st.warning(

                "Shot count automatically reduced for stability."

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





    except Exception as error:


        st.error(

            f"Quantum simulation failed: {error}"

        )


        st.stop()






# ============================================================
# FORECAST CHECK
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
# DASHBOARD METRICS
# ============================================================


st.divider()



st.subheader(

    "Quantum Market Dashboard"

)





expected_price = forecast["expected_price"]





expected_change = (

    (

        expected_price -

        forecast["starting_price"]

    )

    /

    forecast["starting_price"]

) * 100






# ============================================================
# REALISTIC PROBABILITY CALCULATIONS
# ============================================================


returns_grid = forecast["return_grid"]


probabilities = forecast["probability"]





# meaningful moves only

upside_probability = np.sum(

    probabilities[

        returns_grid > 2

    ]

) * 100





downside_probability = np.sum(

    probabilities[

        returns_grid < -2

    ]

) * 100





neutral_probability = (

    100 -

    upside_probability -

    downside_probability

)





upside_probability = np.clip(

    upside_probability,

    5,

    95

)





downside_probability = np.clip(

    downside_probability,

    5,

    95

)





neutral_probability = max(

    0,

    100 -

    upside_probability -

    downside_probability

)





# risk score

risk_score = (

    forecast["volatility"]

    *

    (

        downside_probability /

        100

    )

)





st.session_state.neutral_probability = neutral_probability


st.session_state.risk_score = risk_score





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

        <h4>Gain Probability</h4>

        <h2>{upside_probability:.1f}%</h2>

        <p>Moves above +2%</p>

        </div>

        """,

        unsafe_allow_html=True

    )





with card4:


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Market Volatility</h4>

        <h2>{forecast['volatility']:.1f}%</h2>

        <p>Annualized</p>

        </div>

        """,

        unsafe_allow_html=True

    )





risk_col1, risk_col2, risk_col3 = st.columns(3)





with risk_col1:


    st.metric(

        "Upside Scenario",

        f"{upside_probability:.1f}%"

    )





with risk_col2:


    st.metric(

        "Neutral Scenario",

        f"{neutral_probability:.1f}%"

    )





with risk_col3:


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





status1, status2, status3 = st.columns(3)





with status1:


    st.markdown(

        """

        <div class="status-box">

        ✓ Market Data Connected

        </div>

        """,

        unsafe_allow_html=True

    )





with status2:


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





with status3:


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

            "Best Trading Day",

            f"{returns.max()*100:.2f}%"

        )





    with c4:

        st.metric(

            "Worst Trading Day",

            f"{returns.min()*100:.2f}%"

        )








# ============================================================
# FORECAST TAB
# ============================================================


with tab2:


    st.subheader(

        f"{ticker} {forecast_days}-Day Probability Forecast"

    )



    days = np.arange(

        forecast_days + 1

    )



    median_return = np.median(

        forecast["return_grid"]

    )



    lower = np.percentile(

        forecast["return_grid"],

        10

    )



    upper = np.percentile(

        forecast["return_grid"],

        90

    )





    scaling = np.sqrt(

        days /

        forecast_days

    )





    fig, ax = plt.subplots(

        figsize=(10,4)

    )





    ax.fill_between(

        days,

        lower * scaling,

        upper * scaling,

        alpha=0.25,

        label="Probability Range"

    )





    ax.plot(

        days,

        median_return * scaling,

        linewidth=2,

        label="Median Outcome"

    )





    ax.axhline(

        0,

        linestyle="--"

    )





    ax.set_xlabel(

        "Trading Days"

    )



    ax.set_ylabel(

        "Return (%)"

    )



    ax.grid(

        True,

        alpha=0.25

    )



    ax.legend()



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

        "Quantum Risk Distribution"

    )



    probabilities = forecast["probability"]

    returns_grid = forecast["return_grid"]





    fig, ax = plt.subplots(

        figsize=(10,4)

    )





    ax.plot(

        returns_grid,

        probabilities,

        linewidth=2

    )





    ax.fill_between(

        returns_grid,

        probabilities,

        alpha=0.25

    )





    expected_return = np.sum(

        returns_grid *

        probabilities

    )





    cumulative = np.cumsum(

        probabilities

    )





    var_index = np.searchsorted(

        cumulative,

        0.05

    )





    var_index = min(

        var_index,

        len(returns_grid)-1

    )





    var_95 = returns_grid[var_index]





    ax.axvline(

        expected_return,

        linestyle="--",

        label="Expected"

    )





    ax.axvline(

        var_95,

        linestyle=":",

        label="95% VaR"

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



    ax.legend()



    st.pyplot(

        fig

    )



    plt.close(

        fig

    )





    r1, r2, r3 = st.columns(3)





    with r1:


        st.metric(

            "Expected Return",

            f"{expected_return:.2f}%"

        )





    with r2:


        st.metric(

            "95% VaR",

            f"{var_95:.2f}%"

        )





    with r3:


        st.metric(

            "Risk Score",

            f"{st.session_state.risk_score:.2f}"

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

The system converts historical market behavior into a probability distribution.

The quantum circuit samples possible future states from this distribution.

The result is a risk-weighted probability forecast, not a guaranteed prediction.

"""

    )



    q1, q2, q3 = st.columns(3)





    with q1:

        st.metric(

            "Backend",

            "Aer MPS"

        )





    with q2:

        st.metric(

            "Qubits",

            qubits

        )





    with q3:

        st.metric(

            "Shots",

            shots

        )







# ============================================================
# RAW DATA
# ============================================================


with tab5:


    st.subheader(

        "Quantum Probability Table"

    )



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



Probability analysis is for research purposes only.

"""

)
