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
    format_volume
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


if "forecast_data" not in st.session_state:

    st.session_state.forecast_data = None



if "forecast_settings" not in st.session_state:

    st.session_state.forecast_settings = None



if "forecast_time" not in st.session_state:

    st.session_state.forecast_time = None



if "last_run_price" not in st.session_state:

    st.session_state.last_run_price = None



# ============================================================
# AUTO REFRESH LIVE DATA
# ============================================================


st_autorefresh(

    interval=15000,

    key="market_refresh"

)



# ============================================================
# PROFESSIONAL TERMINAL STYLE
# ============================================================


st.markdown(

"""

<style>


.stApp {

    background-color: #0b1120;

    color: #e5e7eb;

}


section[data-testid="stSidebar"] {

    background-color: #111827;

}


.metric-card {

    background-color: #111827;

    border: 1px solid #273449;

    border-radius: 10px;

    padding: 18px;

    margin-bottom: 12px;

}



.status-card {

    background-color: #111827;

    border-left: 4px solid #00b4d8;

    padding: 12px;

    border-radius: 6px;

}



h1 {

    color: #f8fafc;

}


h2 {

    color: #f8fafc;

}


h3 {

    color: #e2e8f0;

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

    "Institutional-style market analytics with quantum probability simulation."

)



st.divider()



# ============================================================
# SIDEBAR
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

    index=3

)



num_qubits = st.sidebar.slider(

    "Quantum Resolution (Qubits)",

    min_value=3,

    max_value=6,

    value=5

)



shots = st.sidebar.slider(

    "Quantum Measurement Shots",

    min_value=250,

    max_value=2000,

    value=1000,

    step=250

)



if num_qubits >= 6:


    st.sidebar.warning(

        "6 qubits uses more memory. Use only with lower shot counts if needed."

    )



run_button = st.sidebar.button(

    "Run Quantum Analysis",

    type="primary",

    width="stretch"

)



# ============================================================
# LIVE MARKET HEADER
# ============================================================


live_data = get_live_price(

    selected_ticker

)



company = get_company_info(

    selected_ticker

)



if live_data:


    current_price = live_data["price"]


else:


    current_price = None



header1, header2, header3, header4 = st.columns(4)



with header1:


    st.metric(

        "Asset",

        company["name"]

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


        st.metric(

            "Daily Change",

            format_percent(

                live_data["change_percent"]

            )

        )


    else:


        st.metric(

            "Daily Change",

            "N/A"

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

Last market update:

{datetime.datetime.now().strftime('%H:%M:%S')}

"""
)
# ============================================================
# MARKET DATA LOADING
# ============================================================


@st.cache_data(

    ttl=3600,

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



    return data.dropna(

        subset=[

            "Close"

        ]

    )





market_data = load_market_data(

    selected_ticker

)



if market_data.empty:


    st.error(

        "No historical market data available."

    )


    st.stop()





# ============================================================
# QUANTUM FORECAST ENGINE
# ============================================================


@st.cache_data(

    ttl=1800,

    max_entries=50

)

def run_quantum_engine(

    market_data,

    starting_price,

    days,

    qubits,

    measurement_shots

):


    data = market_data.copy()



    prices = (

        data["Close"]

        .dropna()

        .astype(float)

    )



    if len(prices) < 50:


        raise ValueError(

            "Insufficient historical data."

        )



    returns = (

        prices

        .pct_change()

        .dropna()

    )



    # --------------------------------------------------------
    # STARTING PRICE
    # --------------------------------------------------------


    if starting_price is not None:


        S0 = float(

            starting_price

        )


    else:


        S0 = float(

            prices.iloc[-1]

        )



    # --------------------------------------------------------
    # SAFE FEATURE READING
    # --------------------------------------------------------


    def get_feature(

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



    rsi = get_feature(

        "RSI",

        50

    )



    momentum = get_feature(

        "Momentum",

        0

    )



    volatility = get_feature(

        "Volatility",

        returns.std()

    )



    sma20 = get_feature(

        "SMA20",

        S0

    )



    sma50 = get_feature(

        "SMA50",

        S0

    )



    volume_change = get_feature(

        "Volume_Change",

        0

    )



    # --------------------------------------------------------
    # MARKET STATISTICS
    # --------------------------------------------------------


    mu = float(

        returns.mean()

    )



    sigma = float(

        returns.std()

    )



    if (

        sigma <= 0

        or

        np.isnan(sigma)

    ):


        sigma = 1e-9





    # --------------------------------------------------------
    # FEATURE BIAS
    # --------------------------------------------------------


    feature_bias = 0



    if sma20 > sma50:


        feature_bias += 0.002



    else:


        feature_bias -= 0.002



    feature_bias += (

        momentum *

        0.15

    )



    if rsi > 55:


        feature_bias += 0.001



    elif rsi < 45:


        feature_bias -= 0.001



    if volume_change > 0:


        feature_bias += 0.0005



    elif volume_change < 0:


        feature_bias -= 0.0005



    adjusted_mu = (

        mu +

        feature_bias

    )



    # --------------------------------------------------------
    # PRICE GRID
    # --------------------------------------------------------


    dt = days / 252



    states = 2 ** qubits



    drift = (

        adjusted_mu -

        0.5 *

        sigma ** 2

    ) * dt



    volatility_range = (

        2.0 *

        sigma *

        np.sqrt(dt)

    )



    min_price = (

        S0 *

        np.exp(

            drift -

            volatility_range

        )

    )



    max_price = (

        S0 *

        np.exp(

            drift +

            volatility_range

        )

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
    # --------------------------------------------------------
    # PROBABILITY DISTRIBUTION
    # --------------------------------------------------------


    log_returns = np.log(

        price_grid /

        S0

    )



    distribution = np.exp(

        -(

            (

                log_returns -

                drift

            )

            ** 2

        )

        /

        (

            2 *

            sigma ** 2 *

            dt

        )

    )



    distribution = np.nan_to_num(

        distribution,

        nan=0

    )



    total_probability = np.sum(

        distribution

    )



    if total_probability <= 0:


        distribution = np.ones(

            states

        )

        total_probability = states



    distribution /= total_probability



    # --------------------------------------------------------
    # QUANTUM SIMULATION
    # --------------------------------------------------------


    circuit = QuantumCircuit(

        qubits

    )



    circuit.initialize(

        np.sqrt(

            distribution

        ),

        range(qubits)

    )



    circuit.measure_all()



    simulator = AerSimulator(

        method="matrix_product_state"

    )



    result = simulator.run(

        circuit,

        shots=measurement_shots

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

                measurement_shots

            )



    probability_sum = np.sum(

        quantum_probs

    )



    if probability_sum <= 0:


        quantum_probs = distribution



    else:


        quantum_probs /= probability_sum





    # --------------------------------------------------------
    # RISK CALCULATIONS
    # --------------------------------------------------------


    expected_price = np.sum(

        price_grid *

        quantum_probs

    )



    expected_return = (

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



    var_price = (

        price_grid[var_index]

    )



    var_percent = (

        pct_grid[var_index]

    )



    tail_prices = (

        price_grid[

            :var_index + 1

        ]

    )



    tail_probabilities = (

        quantum_probs[

            :var_index + 1

        ]

    )



    if np.sum(tail_probabilities) > 0:


        expected_tail_loss = (

            np.sum(

                tail_prices *

                tail_probabilities

            )

            /

            np.sum(

                tail_probabilities

            )

        )


    else:


        expected_tail_loss = var_price



    expected_tail_loss_percent = (

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





    # --------------------------------------------------------
    # RETURN FORECAST DATA
    # --------------------------------------------------------


    return {


        "S0":

        S0,



        "expected_price":

        expected_price,



        "expected_pct":

        expected_return,



        "ann_vol":

        sigma *

        np.sqrt(252) *

        100,



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

        var_percent,



        "expected_tail_loss":

        expected_tail_loss,



        "etl_pct":

        expected_tail_loss_percent,



        "prob_positive":

        probability_gain,



        "prob_up_5":

        probability_up_5,



        "prob_down_5":

        probability_down_5,



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
# RUN QUANTUM ANALYSIS
# ============================================================


current_settings = (

    selected_ticker,

    forecast_days,

    num_qubits,

    shots

)



if run_button:


    # Force fresh live price only when user runs analysis


    latest_market_data = get_live_price(

        selected_ticker

    )



    if latest_market_data:


        run_price = latest_market_data["price"]



    else:


        run_price = (

            market_data["Close"]

            .iloc[-1]

        )



    try:


        with st.spinner(

            "Running quantum probability simulation..."

        ):


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



    except Exception as error:


        st.error(

            f"Quantum analysis failed: {error}"

        )


        st.stop()





# ============================================================
# FORECAST CHECK
# ============================================================


if st.session_state.forecast_data is None:


    st.info(

        "Select an asset and run quantum analysis."

    )


    st.stop()



if (

    st.session_state.forecast_settings

    !=

    current_settings

):


    st.warning(

        "Settings changed. Run analysis again."

    )



data = st.session_state.forecast_data





# ============================================================
# OVERVIEW DASHBOARD
# ============================================================


st.divider()



st.subheader(

    "Market Overview"

)



overview1, overview2, overview3, overview4 = st.columns(4)



with overview1:


    st.markdown(

        "<div class='metric-card'>"

        "<h4>Forecast Starting Price</h4>"

        f"<h2>{format_price(data['S0'])}</h2>"

        "</div>",

        unsafe_allow_html=True

    )



with overview2:


    st.markdown(

        "<div class='metric-card'>"

        "<h4>Forecast Target</h4>"

        f"<h2>{format_price(data['expected_price'])}</h2>"

        f"<p>{data['expected_pct']:+.2f}%</p>"

        "</div>",

        unsafe_allow_html=True

    )



with overview3:


    st.markdown(

        "<div class='metric-card'>"

        "<h4>Probability Gain</h4>"

        f"<h2>{data['prob_positive']:.1f}%</h2>"

        "</div>",

        unsafe_allow_html=True

    )



with overview4:


    st.markdown(

        "<div class='metric-card'>"

        "<h4>Annual Volatility</h4>"

        f"<h2>{data['ann_vol']:.1f}%</h2>"

        "</div>",

        unsafe_allow_html=True

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

        <div class='status-card'>

        ✓ Market Data Connected

        </div>

        """,

        unsafe_allow_html=True

    )



with status2:


    st.markdown(

        f"""

        <div class='status-card'>

        ✓ Quantum Simulation Ready

        <br>

        {num_qubits} Qubits |

        {shots} Shots

        </div>

        """,

        unsafe_allow_html=True

    )



with status3:


    st.markdown(

        f"""

        <div class='status-card'>

        ✓ Last Run

        <br>

        {st.session_state.forecast_time}

        </div>

        """,

        unsafe_allow_html=True

    )
# ============================================================
# MAIN ANALYTICS TABS
# ============================================================


tab1, tab2, tab3, tab4, tab5 = st.tabs(

    [

        "Overview",

        "Forecast",

        "Risk Analytics",

        "Quantum Model",

        "Data"

    ]

)



# ============================================================
# OVERVIEW TAB
# ============================================================


with tab1:


    st.subheader(

        "Technical Indicators"

    )



    ind1, ind2, ind3, ind4 = st.columns(4)



    ind1.metric(

        "RSI",

        f"{data['rsi']:.1f}"

    )



    ind2.metric(

        "Momentum",

        f"{data['momentum'] * 100:.2f}%"

    )



    ind3.metric(

        "Trend",

        "Bullish"

        if data["sma20"] > data["sma50"]

        else

        "Bearish"

    )



    ind4.metric(

        "Volume Change",

        f"{data['volume_change'] * 100:.2f}%"

    )





# ============================================================
# FORECAST TAB
# ============================================================


with tab2:


    st.subheader(

        f"{selected_ticker} {forecast_days}-Day Quantum Forecast"

    )



    percentile_levels = [

        0.05,

        0.20,

        0.35,

        0.50,

        0.65,

        0.80,

        0.95

    ]



    percentile_values = []



    for level in percentile_levels:


        index = np.searchsorted(

            data["cdf"],

            level

        )



        index = min(

            index,

            len(data["pct_grid"]) - 1

        )



        percentile_values.append(

            data["pct_grid"][index]

        )



    days = np.arange(

        0,

        forecast_days + 1

    )



    factor = np.sqrt(

        days /

        forecast_days

    )



    forecast_paths = [

        value * factor

        for value in percentile_values

    ]



    p5, p20, p35, p50, p65, p80, p95 = forecast_paths



    fig, ax = plt.subplots(

        figsize=(10,4)

    )



    ax.fill_between(

        days,

        p35,

        p65,

        alpha=0.45,

        label="Core Probability"

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

        alpha=0.12,

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

        "Expected Return (%)"

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
# RISK ANALYTICS TAB
# ============================================================


with tab3:


    st.subheader(

        "Quantum Risk Distribution"

    )



    risk_fig, risk_ax = plt.subplots(

        figsize=(9,4)

    )



    risk_ax.plot(

        data["pct_grid"],

        data["quantum_probs"]

    )



    risk_ax.fill_between(

        data["pct_grid"],

        data["quantum_probs"],

        alpha=0.25

    )



    risk_ax.axvline(

        data["expected_pct"],

        linestyle="-",

        label="Expected"

    )



    risk_ax.axvline(

        data["var_95_pct"],

        linestyle="--",

        label="95% VaR"

    )



    risk_ax.set_xlabel(

        "Return (%)"

    )



    risk_ax.set_ylabel(

        "Probability"

    )



    risk_ax.legend()



    risk_ax.grid(

        True,

        alpha=0.25

    )



    st.pyplot(

        risk_fig

    )



    plt.close(

        risk_fig

    )



    risk1, risk2, risk3 = st.columns(3)



    risk1.metric(

        "95% VaR",

        f"{data['var_95_pct']:.2f}%"

    )



    risk2.metric(

        "Expected Tail Loss",

        f"{data['etl_pct']:.2f}%"

    )



    risk3.metric(

        "Loss Probability",

        f"{data['prob_down_5']:.1f}%"

    )





# ============================================================
# QUANTUM MODEL TAB
# ============================================================


with tab4:


    st.subheader(

        "Quantum Simulation Architecture"

    )



    st.write(

        """

The model converts a financial probability distribution

into a quantum state and samples possible outcomes

using Qiskit Aer simulation.

"""

    )



    q1, q2, q3 = st.columns(3)



    q1.metric(

        "Quantum Backend",

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



    st.divider()



    st.write(

        """

Model Pipeline:



Historical Market Data

↓

Technical Indicators

↓

Statistical Distribution

↓

Quantum Probability Sampling

↓

Risk & Forecast Output

"""

    )
# ============================================================
# DATA TAB
# ============================================================


with tab5:


    st.subheader(

        "Forecast Data"

    )



    forecast_table = pd.DataFrame(

        {


            "Price Outcome":

            data["price_grid"],



            "Return (%)":

            data["pct_grid"],



            "Quantum Probability":

            data["quantum_probs"],



            "Cumulative Probability":

            data["cdf"]


        }

    )



    st.dataframe(

        forecast_table,

        width="stretch"

    )



    csv = forecast_table.to_csv(

        index=False

    )



    st.download_button(

        label="Download Forecast Data",

        data=csv,

        file_name=(

            f"{selected_ticker}_"

            "quantum_forecast.csv"

        ),

        mime="text/csv"

    )





# ============================================================
# HISTORICAL PRICE SECTION
# ============================================================


st.divider()



with st.expander(

    "Historical Market Data"

):


    history_fig, history_ax = plt.subplots(

        figsize=(10,4)

    )



    history_ax.plot(

        data["prices"].values,

        linewidth=2

    )



    history_ax.set_title(

        f"{selected_ticker} Historical Price Movement"

    )



    history_ax.set_xlabel(

        "Trading Days"

    )



    history_ax.set_ylabel(

        "Price"

    )



    history_ax.grid(

        True,

        alpha=0.25

    )



    st.pyplot(

        history_fig

    )



    plt.close(

        history_fig

    )





# ============================================================
# FOOTER INFORMATION
# ============================================================


st.divider()



st.caption(

"""

Quantum Equity Research Terminal



Data:

Yahoo Finance market data



Simulation:

Qiskit Aer Matrix Product State



Model Purpose:

Educational quantitative research and probability analysis.



Forecast outputs represent statistical estimates and are not financial advice.

"""

)

