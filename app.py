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

    format_volume,

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


defaults = {


    "forecast":

    None,


    "forecast_settings":

    None,


    "last_run":

    None,


    "last_price":

    None

}



for key, value in defaults.items():


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

    "Quantum probability simulation combined with market analytics."

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



ticker = (

    ticker

    .upper()

    .strip()

)





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





# Safety check

if qubits >= 7 and shots > 2000:


    st.sidebar.warning(

        "7 qubits with high shots may use more memory. Reduce shots for stability."

    )





if qubits == 6 and shots > 3000:


    st.sidebar.warning(

        "Large simulation detected. Consider fewer shots."

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


    if live_data:


        st.metric(

            "Daily Change",

            format_percent(

                live_data.get(

                    "change_percent"

                )

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

    f"Last update: {datetime.datetime.now().strftime('%H:%M:%S')}"

)






# ============================================================
# LOAD HISTORICAL DATA
# ============================================================


@st.cache_data(

    ttl=900,

    max_entries=100

)

def load_market_data(

    symbol

):


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


    st.info(

        "Try another ticker or clear the cache."

    )


    if st.button(

        "Clear Data Cache"

    ):


        clear_data_cache()

        st.rerun()



    st.stop()






# ============================================================
# QUANTUM ENGINE
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

        .dropna()

    )





    S0 = float(

        starting_price

    )





    mu = float(

        returns.mean()

    )



    sigma = float(

        returns.std()

    )



    if sigma <= 0 or np.isnan(sigma):


        sigma = 0.01






    # ========================================================
    # PRICE DISTRIBUTION
    # ========================================================


    states = 2 ** qubits



    time_factor = np.sqrt(

        days / 252

    )



    center = S0 * (

        1 +

        mu * days

    )



    spread = S0 * sigma * time_factor * 2





    price_grid = np.linspace(

        max(

            center - spread,

            S0 * 0.5

        ),

        center + spread,

        states

    )





    returns_grid = (

        (

            price_grid -

            S0

        )

        /

        S0

    )





    probabilities = np.exp(

        -0.5 *

        (

            (

                returns_grid -

                mu * days

            )

            /

            (

                sigma *

                time_factor +

                1e-9

            )

        )

        ** 2

    )



    probabilities = (

        probabilities /

        probabilities.sum()

    )






    # ========================================================
    # QUANTUM STATE
    # ========================================================


    circuit = QuantumCircuit(

        qubits

    )



    circuit.initialize(

        np.sqrt(

            probabilities

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




    return {


        "starting_price":

        S0,


        "price_grid":

        price_grid,


        "return_grid":

        returns_grid * 100,


        "probability":

        quantum_probability,


        "expected_price":

        np.sum(

            price_grid *

            quantum_probability

        ),


        "volatility":

        sigma * np.sqrt(252) * 100,


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


    if live_data:


        run_price = live_data.get(

            "price"

        )


    else:


        run_price = float(

            market_data["Close"]

            .iloc[-1]

        )





    try:


        # Extra safety protection

        if qubits >= 7 and shots > 3000:


            st.warning(

                "Reducing shots automatically for system stability."

            )


            shots = 3000





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


        st.info(

            "Try lowering qubits or shots."

        )


        st.stop()






# ============================================================
# CHECK FOR FORECAST
# ============================================================


if st.session_state.forecast is None:


    st.info(

        "Choose settings and run quantum analysis."

    )


    st.stop()





if st.session_state.forecast_settings != settings:


    st.warning(

        "Settings changed. Run analysis again."

    )





forecast = st.session_state.forecast





# ============================================================
# SUMMARY DASHBOARD
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






gain_probability = np.sum(

    forecast["probability"]

    [

        forecast["return_grid"] >= 0

    ]

) * 100






loss_probability = np.sum(

    forecast["probability"]

    [

        forecast["return_grid"] < 0

    ]

) * 100






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

        <h2>{gain_probability:.1f}%</h2>

        </div>

        """,

        unsafe_allow_html=True

    )





with card4:


    st.markdown(

        f"""

        <div class="metric-box">

        <h4>Annual Volatility</h4>

        <h2>{forecast['volatility']:.1f}%</h2>

        </div>

        """,

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
# OVERVIEW TAB
# ============================================================


with tab1:


    st.subheader(

        "Historical Statistics"

    )



    returns = forecast["returns"]



    col1, col2, col3, col4 = st.columns(4)





    with col1:


        st.metric(

            "Average Daily Return",

            f"{returns.mean()*100:.3f}%"

        )





    with col2:


        st.metric(

            "Daily Volatility",

            f"{returns.std()*100:.3f}%"

        )





    with col3:


        st.metric(

            "Best Day",

            f"{returns.max()*100:.2f}%"

        )





    with col4:


        st.metric(

            "Worst Day",

            f"{returns.min()*100:.2f}%"

        )






# ============================================================
# FORECAST TAB
# ============================================================


with tab2:


    st.subheader(

        f"{ticker} {forecast_days}-Day Quantum Forecast"

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





    path = (

        median_return *

        np.sqrt(

            days /

            forecast_days

        )

    )





    fig, ax = plt.subplots(

        figsize=(10,4)

    )



    ax.fill_between(

        days,

        lower *

        np.sqrt(

            days /

            forecast_days

        ),

        upper *

        np.sqrt(

            days /

            forecast_days

        ),

        alpha=0.25,

        label="Probability Range"

    )



    ax.plot(

        days,

        path,

        linewidth=2,

        label="Median Path"

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
# RISK ANALYTICS TAB
# ============================================================


with tab3:


    st.subheader(

        "Quantum Risk Distribution"

    )



    probabilities = forecast["probability"]

    returns_grid = forecast["return_grid"]





    risk_fig, risk_ax = plt.subplots(

        figsize=(10,4)

    )



    risk_ax.plot(

        returns_grid,

        probabilities,

        linewidth=2

    )



    risk_ax.fill_between(

        returns_grid,

        probabilities,

        alpha=0.25

    )



    expected_return = np.sum(

        returns_grid *

        probabilities

    )



    var_index = np.searchsorted(

        np.cumsum(

            probabilities

        ),

        0.05

    )



    var_index = min(

        var_index,

        len(

            returns_grid

        ) - 1

    )



    var_95 = returns_grid[var_index]





    risk_ax.axvline(

        expected_return,

        linestyle="--",

        label="Expected"

    )



    risk_ax.axvline(

        var_95,

        linestyle=":",

        label="95% VaR"

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





    risk1, risk2, risk3 = st.columns(3)





    with risk1:


        st.metric(

            "Expected Return",

            f"{expected_return:.2f}%"

        )





    with risk2:


        st.metric(

            "95% VaR",

            f"{var_95:.2f}%"

        )





    with risk3:


        st.metric(

            "Downside Probability",

            f"{loss_probability:.1f}%"

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

The model transforms a statistical market probability

distribution into a quantum state.

Qiskit Aer Matrix Product State simulation samples

possible future outcomes.

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



    st.divider()



    st.code(

        """

Historical Prices

        ↓

Return Distribution

        ↓

Probability Encoding

        ↓

Quantum State Preparation

        ↓

Measurement Sampling

        ↓

Risk Forecast

        """,

        language="text"

    )
    # ============================================================
# RAW DATA TAB
# ============================================================


with tab5:


    st.subheader(

        "Quantum Probability Table"

    )



    forecast_table = pd.DataFrame(

        {

            "Future Price":

            forecast["price_grid"],



            "Return (%)":

            forecast["return_grid"],



            "Quantum Probability":

            forecast["probability"]

        }

    )



    forecast_table["Quantum Probability"] = (

        forecast_table["Quantum Probability"]

        * 100

    )



    st.dataframe(

        forecast_table,

        width="stretch"

    )





    csv = forecast_table.to_csv(

        index=False

    )



    st.download_button(

        label="Download Forecast CSV",

        data=csv,

        file_name=(

            f"{ticker}_quantum_forecast.csv"

        ),

        mime="text/csv"

    )






# ============================================================
# HISTORICAL DATA CHART
# ============================================================


st.divider()



with st.expander(

    "Historical Market Data"

):


    history_fig, history_ax = plt.subplots(

        figsize=(10,4)

    )



    history_ax.plot(

        market_data["Close"],

        linewidth=2

    )



    history_ax.set_title(

        f"{ticker} Historical Price"

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



This application provides statistical probability

analysis for educational research purposes.

It is not financial advice.

"""

)

)
