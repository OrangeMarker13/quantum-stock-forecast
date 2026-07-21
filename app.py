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
    get_live_price
)



# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================


st.set_page_config(

    page_title="Quantum Stock Forecast & Risk Analytics",

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



# ============================================================
# LIVE DASHBOARD REFRESH
# ============================================================


st_autorefresh(

    interval=15000,

    key="market_refresh"

)



# ============================================================
# STYLE
# ============================================================


st.markdown(

    """

<style>

.metric-card {

    background-color:#f8f9fa;

    border-left:5px solid #1f77b4;

    padding:15px;

    border-radius:5px;

}



.stApp {

    font-family:Inter,sans-serif;

}

</style>

""",

    unsafe_allow_html=True

)



# ============================================================
# HEADER
# ============================================================


st.title(

    "Quantum Equity Research & Risk Analytics Engine"

)



st.markdown(

    """

This platform combines quantum probability sampling,

financial statistics, technical indicators,

and risk analytics to estimate future price distributions.

"""

)



st.divider()



# ============================================================
# SIDEBAR CONTROLS
# ============================================================


st.sidebar.header(

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

    "BRK-B",

    "JPM",

    "V",

    "UNH",

    "PG",

    "MA",

    "HD",

    "DIS",

    "NFLX",

    "AMD",

    "COIN",

    "SPY",

    "QQQ",

    "^GSPC",

    "BTC-USD"

]



selected_ticker = st.sidebar.selectbox(

    "Select Asset:",

    options=popular_tickers,

    index=0,

    accept_new_options=True

)



selected_ticker = (

    selected_ticker

    .upper()

    .strip()

)



forecast_days = st.sidebar.selectbox(

    "Forecast Horizon:",

    options=[

        7,

        30,

        60,

        90

    ],

    index=1

)



# ============================================================
# SAFE QUANTUM SETTINGS
# ============================================================


num_qubits = st.sidebar.slider(

    "Quantum Register Resolution:",

    min_value=3,

    max_value=6,

    value=5

)



shots = st.sidebar.slider(

    "Quantum Measurement Shots:",

    min_value=250,

    max_value=2000,

    value=1000,

    step=250

)



if num_qubits == 6 and shots >= 1500:


    st.sidebar.warning(

        "High quantum workload selected. Runtime may increase."

    )



run_button = st.sidebar.button(

    "Run Quantum Analysis",

    type="primary",

    width="stretch"

)



if st.sidebar.button(

    "Clear Quantum Cache"

):


    st.cache_data.clear()


    st.session_state.forecast_data = None


    st.session_state.forecast_settings = None


    st.rerun()



# ============================================================
# LIVE PRICE DISPLAY
# ============================================================


live_data = get_live_price(

    selected_ticker

)



if live_data is not None:


    live_price = live_data["price"]


    daily_change = live_data["change"]


    daily_change_percent = live_data["change_percent"]


else:


    live_price = None


    daily_change = None


    daily_change_percent = None



price_col1, price_col2 = st.columns(2)



with price_col1:


    if live_price is not None:


        st.metric(

            "Live Price",

            f"${live_price:.2f}",

            f"{daily_change_percent:+.2f}%"

        )


    else:


        st.metric(

            "Live Price",

            "Unavailable"

        )



with price_col2:


    st.metric(

        "Selected Asset",

        selected_ticker

    )



st.caption(

    f"Market updated: {datetime.datetime.now().strftime('%H:%M:%S')}"

)



# ============================================================
# MARKET DATA LOADING
# ============================================================


@st.cache_data(

    ttl=3600,

    max_entries=100

)

def load_market_data(ticker):


    data = get_stock_data(

        ticker

    )


    if data is None:


        return pd.DataFrame()



    data = data.dropna()



    return data



market_data = load_market_data(

    selected_ticker

)



if market_data.empty:


    st.error(

        "No market data found for this stock."

    )
# ============================================================
# QUANTUM FORECAST ENGINE
# ============================================================


@st.cache_data(

    ttl=1800,

    max_entries=50

)

def run_quantum_engine(

    market_data,

    live_price,

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

            "Not enough historical data."

        )



    returns = (

        prices

        .pct_change()

        .dropna()

    )



    # ========================================================
    # STARTING PRICE
    # ========================================================


    if live_price is not None:


        S0 = float(live_price)


    else:


        S0 = float(prices.iloc[-1])



    # ========================================================
    # SAFE FEATURE LOADING
    # ========================================================


    def latest_value(

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



    rsi = latest_value(

        "RSI",

        50

    )



    momentum = latest_value(

        "Momentum",

        0

    )



    volatility_indicator = latest_value(

        "Volatility",

        returns.std()

    )



    sma20 = latest_value(

        "SMA20",

        S0

    )



    sma50 = latest_value(

        "SMA50",

        S0

    )



    volume_change = latest_value(

        "Volume_Change",

        0

    )



    # ========================================================
    # BASE STATISTICS
    # ========================================================


    mu = float(

        returns.mean()

    )



    sigma = float(

        returns.std()

    )



    if sigma <= 0 or np.isnan(sigma):


        sigma = 1e-9



    # ========================================================
    # MARKET FEATURE BIAS
    # ========================================================


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



    # ========================================================
    # PRICE DISTRIBUTION
    # ========================================================


    dt = days / 252



    states = 2 ** qubits



    drift = (

        adjusted_mu -

        0.5 *

        sigma ** 2

    ) * dt



    # Reduced multiplier keeps long forecasts realistic

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



    total = np.sum(

        distribution

    )



    if total <= 0:


        distribution = np.ones(

            states

        )


        total = states



    distribution /= total



    # ========================================================
    # QUANTUM CIRCUIT
    # ========================================================


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



    backend = AerSimulator(

        method="matrix_product_state"

    )



    result = backend.run(

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



    probability_total = np.sum(

        quantum_probs

    )



    if probability_total <= 0:


        quantum_probs = distribution



    else:


        quantum_probs /= probability_total
# ============================================================
# RISK CALCULATIONS
# ============================================================


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

        len(price_grid) - 1

    )



    var_95_price = price_grid[var_index]



    var_95_pct = pct_grid[var_index]



    tail_prices = price_grid[:var_index + 1]



    tail_probs = quantum_probs[:var_index + 1]



    if np.sum(tail_probs) > 0:


        expected_tail_loss = (

            np.sum(

                tail_prices *

                tail_probs

            )

            /

            np.sum(tail_probs)

        )


    else:


        expected_tail_loss = var_95_price



    etl_pct = (

        (

            expected_tail_loss -

            S0

        )

        /

        S0

    ) * 100



    prob_positive = np.sum(

        quantum_probs[pct_grid >= 0]

    ) * 100



    prob_up_5 = np.sum(

        quantum_probs[pct_grid >= 5]

    ) * 100



    prob_down_5 = np.sum(

        quantum_probs[pct_grid <= -5]

    ) * 100



    return {


        "S0":

        S0,


        "mu":

        adjusted_mu,


        "sigma":

        sigma,


        "ann_vol":

        sigma * np.sqrt(252) * 100,


        "price_grid":

        price_grid,


        "pct_grid":

        pct_grid,


        "quantum_probs":

        quantum_probs,


        "cdf":

        cdf,


        "expected_price":

        expected_price,


        "expected_pct":

        expected_pct,


        "var_95_price":

        var_95_price,


        "var_95_pct":

        var_95_pct,


        "expected_tail_loss":

        expected_tail_loss,


        "etl_pct":

        etl_pct,


        "prob_positive":

        prob_positive,


        "prob_up_5":

        prob_up_5,


        "prob_down_5":

        prob_down_5,


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
# RUN OR LOAD FORECAST
# ============================================================


current_settings = (

    selected_ticker,

    forecast_days,

    num_qubits,

    shots

)



if run_button:


    fresh_live_data = get_live_price(

        selected_ticker

    )



    if fresh_live_data is not None:


        fresh_live_price = (

            fresh_live_data["price"]

        )


    else:


        fresh_live_price = None



    try:


        with st.spinner(

            "Running quantum probability simulation..."

        ):


            st.session_state.forecast_data = run_quantum_engine(

                market_data,

                fresh_live_price,

                forecast_days,

                num_qubits,

                shots

            )



            st.session_state.forecast_settings = current_settings



            st.session_state.forecast_time = (

                datetime.datetime.now()

                .strftime("%H:%M:%S")

            )



    except Exception as error:


        st.error(

            f"Analysis failed: {error}"

        )


        st.stop()



# ============================================================
# CHECK FORECAST EXISTS
# ============================================================


if st.session_state.forecast_data is None:


    st.info(

        "Choose settings and press Run Quantum Analysis."

    )


    st.stop()



if (

    st.session_state.forecast_settings

    !=

    current_settings

):


    st.warning(

        "Settings changed. Run analysis again to update forecast."

    )



data = st.session_state.forecast_data



# ============================================================
# SUMMARY METRICS
# ============================================================


st.divider()



col1, col2, col3, col4, col5 = st.columns(5)



col1.metric(

    "Forecast Starting Price",

    f"${data['S0']:.2f}"

)



col2.metric(

    "Forecast Target",

    f"${data['expected_price']:.2f}",

    f"{data['expected_pct']:+.2f}%"

)



col3.metric(

    "Annual Volatility",

    f"{data['ann_vol']:.1f}%"

)



col4.metric(

    "95% VaR",

    f"{data['var_95_pct']:.2f}%"

)



col5.metric(

    "Gain Probability",

    f"{data['prob_positive']:.1f}%"

)



st.caption(

    f"Forecast generated at {st.session_state.forecast_time}"

)
# ============================================================
# MARKET FACTORS
# ============================================================


st.divider()



st.subheader(

    "Market Factors"

)



factor1, factor2, factor3, factor4 = st.columns(4)



factor1.metric(

    "RSI",

    f"{data['rsi']:.1f}"

)



factor2.metric(

    "Momentum",

    f"{data['momentum'] * 100:.2f}%"

)



factor3.metric(

    "Moving Average",

    "Bullish"

    if data["sma20"] > data["sma50"]

    else

    "Bearish"

)



factor4.metric(

    "Volume Change",

    f"{data['volume_change'] * 100:.2f}%"

)



st.divider()



# ============================================================
# TABS
# ============================================================


tab1, tab2, tab3, tab4 = st.tabs(

    [

        "Forecast",

        "Risk",

        "Report",

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



    percentile_levels = [

        0.05,

        0.20,

        0.35,

        0.50,

        0.65,

        0.80,

        0.95

    ]



    percentile_returns = []



    for level in percentile_levels:


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



    time_axis = np.arange(

        0,

        forecast_days + 1

    )



    time_factor = np.sqrt(

        time_axis /

        forecast_days

    )



    paths = [

        value * time_factor

        for value in percentile_returns

    ]



    p5, p20, p35, p50, p65, p80, p95 = paths



    forecast_fig, forecast_ax = plt.subplots(

        figsize=(10,4)

    )



    forecast_ax.fill_between(

        time_axis,

        p35,

        p65,

        alpha=0.5,

        label="Core Range"

    )



    forecast_ax.fill_between(

        time_axis,

        p20,

        p80,

        alpha=0.25,

        label="Extended Range"

    )



    forecast_ax.fill_between(

        time_axis,

        p5,

        p95,

        alpha=0.15,

        label="Tail Risk"

    )



    forecast_ax.plot(

        time_axis,

        p50,

        linewidth=2,

        label="Median Forecast"

    )



    forecast_ax.axhline(

        0,

        linestyle="--"

    )



    forecast_ax.set_xlabel(

        "Days"

    )



    forecast_ax.set_ylabel(

        "Return (%)"

    )



    forecast_ax.grid(

        True,

        alpha=0.25

    )



    forecast_ax.legend()



    st.pyplot(

        forecast_fig

    )



    plt.close(

        forecast_fig

    )



# ============================================================
# RISK TAB
# ============================================================


with tab2:


    st.subheader(

        "Quantum Probability Distribution"

    )



    risk_fig, risk_ax = plt.subplots(

        figsize=(8,4)

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

        label="Expected Return"

    )



    risk_ax.axvline(

        data["var_95_pct"],

        linestyle="--",

        label="VaR 95%"

    )



    risk_ax.set_xlabel(

        "Return (%)"

    )



    risk_ax.set_ylabel(

        "Probability"

    )



    risk_ax.grid(

        True,

        alpha=0.25

    )



    risk_ax.legend()



    st.pyplot(

        risk_fig

    )



    plt.close(

        risk_fig

    )



    st.subheader(

        "Risk Metrics"

    )



    st.write(

        f"Expected Price: ${data['expected_price']:.2f}"

    )



    st.write(

        f"95% VaR: {data['var_95_pct']:.2f}%"

    )



    st.write(

        f"Expected Tail Loss: {data['etl_pct']:.2f}%"

    )



    st.write(

        f"+5% Gain Probability: {data['prob_up_5']:.1f}%"

    )



    st.write(

        f"-5% Loss Probability: {data['prob_down_5']:.1f}%"

    )
    # ============================================================
# REPORT TAB
# ============================================================


with tab3:


    st.subheader(

        f"Quantum Equity Report: {selected_ticker}"

    )



    if (

        data["expected_pct"] > 1.5

        and

        data["prob_positive"] > 55

    ):


        signal = "BULLISH OUTLOOK"



    elif (

        data["expected_pct"] < -1.5

        or

        data["prob_down_5"] > 30

    ):


        signal = "BEARISH / CAUTION"



    else:


        signal = "NEUTRAL"



    st.subheader(

        signal

    )



    st.write(

        f"""

Asset:

{selected_ticker}



Forecast Starting Price:

${data['S0']:.2f}



Forecast Horizon:

{forecast_days} days



Expected Price:

${data['expected_price']:.2f}



Expected Return:

{data['expected_pct']:+.2f}%



Positive Return Probability:

{data['prob_positive']:.1f}%



Annual Volatility:

{data['ann_vol']:.1f}%



RSI:

{data['rsi']:.1f}



Momentum:

{data['momentum'] * 100:.2f}%



Moving Average:

{"Bullish" if data["sma20"] > data["sma50"] else "Bearish"}

"""

    )



# ============================================================
# DATA TAB
# ============================================================


with tab4:


    dataframe = pd.DataFrame(

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

        dataframe,

        width="stretch"

    )



    csv_data = dataframe.to_csv(

        index=False

    )



    st.download_button(

        "Download Forecast CSV",

        csv_data,

        file_name=(

            f"{selected_ticker}_"

            "quantum_forecast.csv"

        ),

        mime="text/csv"

    )



# ============================================================
# HISTORICAL PRICE
# ============================================================


st.divider()



with st.expander(

    "View Historical Price Data"

):


    historical_fig, historical_ax = plt.subplots(

        figsize=(10,3)

    )



    historical_ax.plot(

        data["prices"].values

    )



    historical_ax.set_title(

        f"{selected_ticker} Historical Prices"

    )



    historical_ax.set_xlabel(

        "Trading Days"

    )



    historical_ax.set_ylabel(

        "Price"

    )



    historical_ax.grid(

        True,

        alpha=0.25

    )



    st.pyplot(

        historical_fig

    )



    plt.close(

        historical_fig

    )



# ============================================================
# FOOTER
# ============================================================


st.divider()



st.caption(

    """

Quantum Stock Forecast is an educational research model.

Forecast outputs are statistical estimates and are not financial advice.

"""

)

    st.stop()
