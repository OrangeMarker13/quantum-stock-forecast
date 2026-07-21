import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import hashlib

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

    format_volume,

    clear_data_cache

)



# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================


st.set_page_config(

    page_title="Quantum Equity Research Terminal",

    page_icon="Q",

    layout="wide",

    initial_sidebar_state="expanded"

)



# ============================================================
# SESSION STATE
# ============================================================


default_state = {


    "forecast_data": None,


    "forecast_settings": None,


    "forecast_time": None,


    "last_run_price": None,


    "run_id": None

}



for key, value in default_state.items():


    if key not in st.session_state:


        st.session_state[key] = value





# ============================================================
# LIVE PRICE REFRESH ONLY
# ============================================================


st_autorefresh(

    interval=15000,

    key="live_market_refresh"

)





# ============================================================
# PROFESSIONAL TERMINAL UI
# ============================================================


st.markdown(

"""

<style>


.stApp {

    background-color:#0b1220;

    color:#e5e7eb;

}



section[data-testid="stSidebar"] {

    background-color:#111827;

}



.metric-card {

    background:#111827;

    border:1px solid #273449;

    border-radius:10px;

    padding:15px;

}



.status-card {

    background:#111827;

    border-left:4px solid #00b4d8;

    padding:12px;

    border-radius:6px;

}



</style>


""",

unsafe_allow_html=True

)





# ============================================================
# HEADER
# ============================================================


st.title(

    "Quantum Equity Research Terminal"

)


st.caption(

    "Quantum probability sampling, market statistics, and risk analytics."

)


st.divider()





# ============================================================
# SIDEBAR CONTROLS
# ============================================================


st.sidebar.title(

    "Simulation Controls"

)



popular_tickers = [

    "AAPL",

    "MSFT",

    "GOOGL",

    "AMZN",

    "NVDA",

    "META",

    "TSLA",

    "AMD",

    "NFLX",

    "SPY",

    "QQQ",

    "BTC-USD"

]



selected_ticker = st.sidebar.selectbox(

    "Asset",

    popular_tickers,

    index=0,

    accept_new_options=True

)



selected_ticker = (

    selected_ticker

    .upper()

    .strip()

)





forecast_days = st.sidebar.selectbox(

    "Forecast Horizon",

    [

        7,

        30,

        60,

        90

    ],

    index=1

)





num_qubits = st.sidebar.slider(

    "Quantum Resolution",

    min_value=3,

    max_value=6,

    value=5,

    help="6 qubits is the safe upper limit for Streamlit Cloud."

)





shots = st.sidebar.slider(

    "Quantum Shots",

    min_value=250,

    max_value=1500,

    value=750,

    step=250

)





if num_qubits == 6:


    st.sidebar.warning(

        "6 qubits selected. Keep shots below 1000 for faster runs."

    )





run_button = st.sidebar.button(

    "Run Quantum Analysis",

    type="primary",

    width="stretch"

)





clear_button = st.sidebar.button(

    "Clear Cache"

)



if clear_button:


    clear_data_cache()


    st.session_state.forecast_data = None


    st.success(

        "Cache cleared."

    )
    # ============================================================
# LIVE MARKET HEADER
# ============================================================


live_data = get_live_price(

    selected_ticker

)



company_data = get_company_info(

    selected_ticker

)



if live_data is not None:


    current_price = live_data.get(

        "price"

    )


    daily_change = live_data.get(

        "change_percent"

    )


else:


    current_price = None


    daily_change = None





header1, header2, header3, header4 = st.columns(4)





with header1:


    st.metric(

        "Asset",

        company_data.get(

            "name",

            selected_ticker

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

        "Today's Change",

        format_percent(

            daily_change

        )

    )





with header4:


    st.metric(

        "Market Status",

        get_market_status(

            live_data

        )

    )





st.caption(

    f"""

Live data updated:

{datetime.datetime.now().strftime('%H:%M:%S')}

"""

)





# ============================================================
# HISTORICAL MARKET DATA
# ============================================================


@st.cache_data(

    ttl=300,

    max_entries=100

)

def load_market_data(

    ticker

):


    data = get_stock_data(

        ticker

    )



    if data is None:


        return pd.DataFrame()



    if data.empty:


        return pd.DataFrame()



    return data





market_data = load_market_data(

    selected_ticker

)





if market_data.empty:


    st.error(

        "No historical market data available."

    )


    st.stop()





# ============================================================
# DATA VALIDATION
# ============================================================


required_columns = [

    "Close",

    "RSI",

    "Momentum",

    "Volatility",

    "SMA20",

    "SMA50"

]





for column in required_columns:


    if column not in market_data.columns:


        market_data[column] = 0





market_data = market_data.replace(

    [

        np.inf,

        -np.inf

    ],

    np.nan

)



market_data = market_data.ffill()



market_data = market_data.bfill()




# ============================================================
# CURRENT PRICE FOR FORECAST
# ============================================================


def get_forecast_price():


    fresh_live = get_live_price(

        selected_ticker

    )


    if fresh_live is not None:


        return float(

            fresh_live["price"]

        )



    return float(

        market_data["Close"]

        .iloc[-1]

    )
    # ============================================================
# QUANTUM FORECAST ENGINE
# ============================================================


def generate_run_id(

    ticker,

    price,

    days,

    qubits,

    shots

):


    raw = (

        f"{ticker}"

        f"{price}"

        f"{days}"

        f"{qubits}"

        f"{shots}"

        f"{datetime.datetime.now()}"

    )



    return hashlib.md5(

        raw.encode()

    ).hexdigest()





def run_quantum_engine(

    market_data,

    starting_price,

    days,

    qubits,

    shots

):


    data = market_data.copy()



    prices = (

        data["Close"]

        .astype(float)

        .dropna()

    )



    if len(prices) < 50:


        raise ValueError(

            "Need at least 50 historical price points."

        )



    returns = (

        prices

        .pct_change()

        .dropna()

    )





    # ========================================================
    # STARTING PRICE
    # ========================================================


    S0 = float(

        starting_price

    )





    # ========================================================
    # FEATURES
    # ========================================================


    def feature_value(

        column,

        default

    ):


        if column not in data.columns:


            return default



        values = (

            data[column]

            .dropna()

        )



        if values.empty:


            return default



        return float(

            values.iloc[-1]

        )





    rsi = feature_value(

        "RSI",

        50

    )



    momentum = feature_value(

        "Momentum",

        0

    )



    sma20 = feature_value(

        "SMA20",

        S0

    )



    sma50 = feature_value(

        "SMA50",

        S0

    )



    volatility = float(

        returns.std()

    )



    if np.isnan(volatility) or volatility <= 0:


        volatility = 0.01





    volume_change = feature_value(

        "Volume_Change",

        0

    )





    # ========================================================
    # MARKET MODEL
    # ========================================================


    mu = float(

        returns.mean()

    )



    bias = 0





    if sma20 > sma50:


        bias += 0.002



    else:


        bias -= 0.002





    bias += (

        momentum *

        0.10

    )





    if rsi > 55:


        bias += 0.001



    elif rsi < 45:


        bias -= 0.001





    adjusted_mu = (

        mu +

        bias

    )





    # ========================================================
    # PRICE DISTRIBUTION
    # ========================================================


    dt = days / 252



    states = 2 ** qubits





    drift = (

        adjusted_mu -

        0.5 *

        volatility ** 2

    ) * dt





    spread = (

        2 *

        volatility *

        np.sqrt(dt)

    )





    min_price = S0 * np.exp(

        drift -

        spread

    )



    max_price = S0 * np.exp(

        drift +

        spread

    )





    price_grid = np.linspace(

        min_price,

        max_price,

        states

    )





    pct_grid = (

        (

            price_grid -

            S0

        )

        /

        S0

    ) * 100





    distribution = np.exp(

        -(

            (

                np.log(

                    price_grid /

                    S0

                )

                -

                drift

            )

            ** 2

        )

        /

        (

            2 *

            volatility ** 2 *

            dt

        )

    )





    distribution = np.nan_to_num(

        distribution

    )





    total = distribution.sum()



    if total <= 0:


        distribution = np.ones(

            states

        )

        total = states





    distribution /= total





    # ========================================================
    # QUANTUM SIMULATION
    # ========================================================


    circuit = QuantumCircuit(

        qubits

    )



    circuit.initialize(

        np.sqrt(

            distribution

        ),

        range(

            qubits

        )

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





    quantum_probs = np.zeros(

        states

    )





    for state, count in counts.items():


        index = int(

            state,

            2

        )


        if index < states:


            quantum_probs[index] = (

                count /

                shots

            )





    if quantum_probs.sum() == 0:


        quantum_probs = distribution



    else:


        quantum_probs /= quantum_probs.sum()
    # ========================================================
    # RISK CALCULATIONS
    # ========================================================


    expected_price = np.sum(

        price_grid *

        quantum_probs

    )



    expected_pct = (

        (

            expected_price -

            S0

        )

        /

        S0

    ) * 100





    cdf = np.cumsum(

        quantum_probs

    )





    var_index = np.searchsorted(

        cdf,

        0.05

    )



    var_index = min(

        var_index,

        states - 1

    )





    var_price = price_grid[var_index]



    var_pct = pct_grid[var_index]





    tail_prices = price_grid[:var_index + 1]



    tail_probs = quantum_probs[:var_index + 1]





    if tail_probs.sum() > 0:


        expected_tail_loss = (

            np.sum(

                tail_prices *

                tail_probs

            )

            /

            tail_probs.sum()

        )


    else:


        expected_tail_loss = var_price





    etl_pct = (

        (

            expected_tail_loss -

            S0

        )

        /

        S0

    ) * 100





    probability_gain = np.sum(

        quantum_probs[

            pct_grid >= 0

        ]

    ) * 100





    probability_up_5 = np.sum(

        quantum_probs[

            pct_grid >= 5

        ]

    ) * 100





    probability_down_5 = np.sum(

        quantum_probs[

            pct_grid <= -5

        ]

    ) * 100





    return {


        "S0":

        S0,


        "expected_price":

        expected_price,


        "expected_pct":

        expected_pct,


        "price_grid":

        price_grid,


        "pct_grid":

        pct_grid,


        "quantum_probs":

        quantum_probs,


        "cdf":

        cdf,


        "var_95_price":

        var_price,


        "var_95_pct":

        var_pct,


        "expected_tail_loss":

        expected_tail_loss,


        "etl_pct":

        etl_pct,


        "prob_positive":

        probability_gain,


        "prob_up_5":

        probability_up_5,


        "prob_down_5":

        probability_down_5,


        "ann_vol":

        volatility * np.sqrt(252) * 100,


        "prices":

        prices,


        "rsi":

        rsi,


        "momentum":

        momentum,


        "sma20":

        sma20,


        "sma50":

        sma50,


        "volume_change":

        volume_change


    }





# ============================================================
# RUN BUTTON LOGIC
# ============================================================


current_settings = (

    selected_ticker,

    forecast_days,

    num_qubits,

    shots

)





if run_button:


    try:


        with st.spinner(

            "Running quantum probability simulation..."

        ):


            run_price = get_forecast_price()



            run_id = generate_run_id(

                selected_ticker,

                run_price,

                forecast_days,

                num_qubits,

                shots

            )



            forecast = run_quantum_engine(

                market_data,

                run_price,

                forecast_days,

                num_qubits,

                shots

            )



            st.session_state.forecast_data = forecast



            st.session_state.forecast_settings = current_settings



            st.session_state.last_run_price = run_price



            st.session_state.forecast_time = (

                datetime.datetime.now()

                .strftime(

                    "%H:%M:%S"

                )

            )



            st.session_state.run_id = run_id



    except Exception as error:


        st.error(

            f"Quantum analysis failed: {error}"

        )


        st.stop()
# ============================================================
# DISPLAY CHECK
# ============================================================


if st.session_state.forecast_data is None:


    st.info(

        "Select an asset and click Run Quantum Analysis."

    )


    st.stop()





data = st.session_state.forecast_data





if st.session_state.forecast_settings != current_settings:


    st.warning(

        "Settings changed. Run the analysis again to update the forecast."

    )





# ============================================================
# DASHBOARD SUMMARY
# ============================================================


st.divider()



st.subheader(

    "Quantum Market Overview"

)





summary1, summary2, summary3, summary4 = st.columns(4)





summary1.metric(

    "Forecast Start Price",

    format_price(

        data["S0"]

    )

)





summary2.metric(

    "Expected Target",

    format_price(

        data["expected_price"]

    ),

    f"{data['expected_pct']:+.2f}%"

)





summary3.metric(

    "Gain Probability",

    f"{data['prob_positive']:.1f}%"

)





summary4.metric(

    "Annual Volatility",

    f"{data['ann_vol']:.1f}%"

)





st.caption(

    f"""

Last quantum run:

{st.session_state.forecast_time}

|

Starting price:

{format_price(st.session_state.last_run_price)}

"""

)





# ============================================================
# ANALYTICS TABS
# ============================================================


tab1, tab2, tab3, tab4 = st.tabs(

    [

        "Forecast",

        "Risk Analytics",

        "Quantum Model",

        "Data"

    ]

)





# ============================================================
# FORECAST TAB
# ============================================================


with tab1:


    st.subheader(

        f"{selected_ticker} {forecast_days}-Day Forecast"

    )



    levels = [

        0.05,

        0.20,

        0.35,

        0.50,

        0.65,

        0.80,

        0.95

    ]



    percentile_returns = []



    for level in levels:


        index = np.searchsorted(

            data["cdf"],

            level

        )


        index = min(

            index,

            len(data["pct_grid"]) - 1

        )


        percentile_returns.append(

            data["pct_grid"][index]

        )





    days = np.arange(

        forecast_days + 1

    )



    factor = np.sqrt(

        days /

        forecast_days

    )





    paths = [

        value * factor

        for value in percentile_returns

    ]





    p5, p20, p35, p50, p65, p80, p95 = paths





    fig, ax = plt.subplots(

        figsize=(10,4)

    )



    ax.fill_between(

        days,

        p35,

        p65,

        alpha=0.45,

        label="Core Range"

    )



    ax.fill_between(

        days,

        p20,

        p80,

        alpha=0.25,

        label="Extended Range"

    )



    ax.fill_between(

        days,

        p5,

        p95,

        alpha=0.15,

        label="Tail Risk"

    )



    ax.plot(

        days,

        p50,

        linewidth=2,

        label="Median Forecast"

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


    plt.close(fig)





# ============================================================
# RISK TAB
# ============================================================


with tab2:


    st.subheader(

        "Quantum Probability Distribution"

    )



    fig, ax = plt.subplots(

        figsize=(9,4)

    )



    ax.plot(

        data["pct_grid"],

        data["quantum_probs"]

    )



    ax.fill_between(

        data["pct_grid"],

        data["quantum_probs"],

        alpha=0.25

    )



    ax.axvline(

        data["expected_pct"],

        linestyle="-",

        label="Expected"

    )



    ax.axvline(

        data["var_95_pct"],

        linestyle="--",

        label="95% VaR"

    )



    ax.legend()

    ax.grid(True)



    st.pyplot(fig)



    plt.close(fig)





    r1, r2, r3 = st.columns(3)



    r1.metric(

        "95% VaR",

        f"{data['var_95_pct']:.2f}%"

    )



    r2.metric(

        "Expected Tail Loss",

        f"{data['etl_pct']:.2f}%"

    )



    r3.metric(

        "5% Downside Probability",

        f"{data['prob_down_5']:.1f}%"

    )





# ============================================================
# QUANTUM MODEL TAB
# ============================================================


with tab3:


    st.subheader(

        "Simulation Architecture"

    )


    st.write(

        """

Market Data

↓

Technical Indicators

↓

Probability Distribution

↓

Quantum State Preparation

↓

Qiskit Aer MPS Sampling

↓

Risk Analytics

"""

    )



    q1, q2, q3 = st.columns(3)



    q1.metric(

        "Backend",

        "Aer MPS"

    )



    q2.metric(

        "Qubits",

        num_qubits

    )



    q3.metric(

        "Shots",

        shots

    )





# ============================================================
# DATA TAB
# ============================================================


with tab4:


    forecast_table = pd.DataFrame(

        {


            "Price":

            data["price_grid"],


            "Return %":

            data["pct_grid"],


            "Quantum Probability":

            data["quantum_probs"],


            "CDF":

            data["cdf"]


        }

    )



    st.dataframe(

        forecast_table,

        width="stretch"

    )



    st.download_button(

        "Download Forecast CSV",

        forecast_table.to_csv(

            index=False

        ),

        file_name=(

            f"{selected_ticker}_"

            "quantum_forecast.csv"

        ),

        mime="text/csv"

    )





# ============================================================
# HISTORICAL DATA
# ============================================================


st.divider()



with st.expander(

    "Historical Price Data"

):


    fig, ax = plt.subplots(

        figsize=(10,3)

    )



    ax.plot(

        data["prices"].values

    )



    ax.set_title(

        f"{selected_ticker} Historical Prices"

    )



    ax.grid(True)



    st.pyplot(fig)



    plt.close(fig)





# ============================================================
# FOOTER
# ============================================================


st.divider()



st.caption(

"""

Quantum Equity Research Terminal



Data Source:

Yahoo Finance



Quantum Engine:

Qiskit Aer Matrix Product State Simulation



Purpose:

Educational quantitative research and probability modeling.



Forecasts are statistical estimates, not financial advice.

"""

)

