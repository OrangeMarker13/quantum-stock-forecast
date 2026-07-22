# ============================================================
# APP.PY
# Quantum Equity Research Terminal
# CLEAN VERSION USING quantum_engine.py + analytics.py
# PART 1/3
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gc
import time

from datetime import datetime


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
    store_prediction,
    evaluate_predictions,
    get_prediction_adjustment,
    complete_prediction
)


from quantum_engine import (
    quantum_forecast
)


from analytics import (
    add_features,
    extract_inputs,
    validate_inputs,
    create_forecast_report
)



# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="Quantum Equity Research Terminal",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.set_option(
    "client.showErrorDetails",
    False
)



# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {

    "forecast": None,

    "forecast_settings": None,

    "last_run": "Never",

    "last_price": None,

    "prediction_id": None

}



for key,value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value



# ============================================================
# UI STYLING
# ============================================================

def apply_quantum_ui():

    st.markdown(
        """
        <style>

        .stApp {

            background:
            radial-gradient(
                circle at 10% 10%,
                rgba(34,211,238,.18),
                transparent 35%
            ),
            radial-gradient(
                circle at 90% 90%,
                rgba(139,92,246,.18),
                transparent 40%
            ),
            linear-gradient(
                135deg,
                #020617,
                #0f172a
            );

        }


        h1 {

            color:#22d3ee !important;

            font-weight:900;

        }


        h2,h3,h4 {

            color:#e0f2fe !important;

        }


        p {

            color:#cbd5e1;

        }


        section[data-testid="stSidebar"] {

            background:#020617;

        }


        .stButton button {

            background:
            linear-gradient(
                90deg,
                #06b6d4,
                #8b5cf6
            );

            color:white;

            border-radius:16px;

            font-weight:900;

        }


        .metric-box {

            background:
            rgba(15,23,42,.8);

            border:
            1px solid rgba(34,211,238,.25);

            border-radius:18px;

            padding:18px;

            text-align:center;

        }


        .positive {

            color:#22ff88;

            font-weight:900;

        }


        .negative {

            color:#ff5555;

            font-weight:900;

        }


        .neutral {

            color:#22d3ee;

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

def safe_float(value, default=0):

    try:

        return float(value)

    except:

        return default



def format_percent(value):

    try:

        value=float(value)

        arrow="▲" if value >= 0 else "▼"

        return f"{arrow} {value:+.2f}%"

    except:

        return "N/A"



def metric_card(
    title,
    value,
    change=None
):

    extra=""

    if change is not None:

        color = (
            "positive"
            if change > 0
            else
            "negative"
        )

        extra=f"""

        <div class="{color}">

        {format_percent(change)}

        </div>

        """


    st.markdown(
        f"""

        <div class="metric-box">

        <h4>{title}</h4>

        <h2>{value}</h2>

        {extra}

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
        ">

        {text}

        </div>

        """,
        unsafe_allow_html=True
    )



# ============================================================
# LOADING
# ============================================================

def quantum_loading():

    box=st.empty()

    frames=[

        "⚛️ Initializing probability space",

        "⚛️ Encoding market variables",

        "⚛️ Running quantum simulation",

        "⚛️ Measuring forecast states"

    ]


    for frame in frames:

        box.markdown(
            f"""

            <div class="metric-box">

            <h3>{frame}</h3>

            </div>

            """,
            unsafe_allow_html=True
        )

        time.sleep(.3)


    box.empty()



# ============================================================
# RESET
# ============================================================

def reset_forecast_state():

    for key,value in DEFAULT_STATE.items():

        st.session_state[key]=value

    gc.collect()



# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "⚛️ Quantum Forecast Controls"
)



search_query = st.sidebar.text_input(
    "Search Company or Symbol",
    "Microsoft"
)



try:

    search_results = search_stocks(
        search_query
    )

except:

    search_results=[]



if search_results:

    selected = st.sidebar.selectbox(
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


    ticker = selected.get(
        "symbol",
        search_query
    ).upper()


    company_name = selected.get(
        "name",
        ticker
    )


else:

    ticker=search_query.upper()

    company_name=ticker



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



run_button = st.sidebar.button(
    "🚀 Run Quantum Forecast"
)



clear_button = st.sidebar.button(
    "🧹 Clear"
)



if clear_button:

    reset_forecast_state()

    st.rerun()
    # ============================================================
# APP.PY
# PART 2/3
# DATA PIPELINE + FORECAST EXECUTION
# ============================================================


# ============================================================
# LIVE PRICE CACHE
# ============================================================

@st.cache_data(
    ttl=60,
    max_entries=100
)
def cached_price(symbol):

    try:

        return get_live_price(symbol)

    except:

        return {}



live_data = cached_price(
    ticker
)



# ============================================================
# COMPANY DATA CACHE
# ============================================================

@st.cache_data(
    ttl=3600,
    max_entries=100
)
def cached_company(symbol):

    try:

        return get_company_info(symbol)

    except:

        return {}



company = cached_company(
    ticker
)



if not company:

    company = {
        "name": company_name
    }



# ============================================================
# CURRENT PRICE
# ============================================================

current_price = None

daily_change = 0



if live_data:

    current_price = safe_float(
        live_data.get(
            "price"
        )
    )


    daily_change = safe_float(
        live_data.get(
            "change_percent"
        )
    )



# ============================================================
# HEADER METRICS
# ============================================================

c1,c2,c3 = st.columns(3)



with c1:

    metric_card(
        "Company",
        company.get(
            "name",
            ticker
        )
    )



with c2:

    metric_card(
        "Live Price",
        format_price(
            current_price
        )
    )



with c3:

    metric_card(
        "Daily Change",
        format_percent(
            daily_change
        ),
        daily_change
    )



st.caption(
    f"""
Last Update:
{datetime.now().strftime('%H:%M:%S')}

|

Ticker:
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
def cached_history(symbol):

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



    except:

        return pd.DataFrame()



market_data = cached_history(
    ticker
)



# ============================================================
# DATA VALIDATION
# ============================================================

if market_data.empty:

    st.error(
        "No historical market data available."
    )

    st.stop()



if "Close" not in market_data.columns:

    st.error(
        "Missing Close price data."
    )

    st.stop()



market_data["Close"] = pd.to_numeric(
    market_data["Close"],
    errors="coerce"
)



market_data = (

    market_data

    .replace(
        [
            np.inf,
            -np.inf
        ],
        np.nan
    )

    .dropna(
        subset=[
            "Close"
        ]
    )

)



if len(market_data) < 120:

    st.warning(
        "Limited historical data detected."
    )



# ============================================================
# MARKET DATA VIEW
# ============================================================

with st.expander(
    "📈 Recent Market Data"
):

    recent = market_data.tail(
        50
    ).copy()


    recent["Return %"] = (

        recent["Close"]

        .pct_change()

        *

        100

    )


    st.dataframe(
        recent,
        use_container_width=True
    )



# ============================================================
# ANALYTICS ENGINE
# ============================================================

market_data = add_features(
    market_data
)



quantum_inputs = extract_inputs(
    market_data
)



if not validate_inputs(
    market_data,
    quantum_inputs
):

    st.error(
        "Model inputs failed validation."
    )

    st.stop()



with st.expander(
    "⚛️ Market Feature State"
):

    feature_table = pd.DataFrame(
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
        feature_table,
        use_container_width=True
    )



# ============================================================
# FORECAST SETTINGS
# ============================================================

forecast_settings = [

    ticker,

    forecast_days,

    qubits,

    shots

]



# ============================================================
# RUN FORECAST
# ============================================================

if run_button:


    execution_price = (

        safe_float(
            current_price
        )

        if current_price

        else

        safe_float(
            market_data["Close"].iloc[-1]
        )

    )



    try:


        quantum_loading()



        with st.spinner(
            "Running quantum forecast engine..."
        ):


            result = quantum_forecast(

                market_data,

                execution_price,

                forecast_days,

                qubits,

                shots

            )



        prediction_id = store_prediction(

            ticker,

            forecast_days,

            execution_price,

            result["expected_price"]

        )



        st.session_state.forecast = result


        st.session_state.forecast_settings = (

            forecast_settings

        )


        st.session_state.last_run = (

            datetime.now()

            .strftime(
                "%H:%M:%S"
            )

        )


        st.session_state.last_price = (

            execution_price

        )


        st.session_state.prediction_id = (

            prediction_id

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
# LOAD FORECAST
# ============================================================

forecast = (

    st.session_state.forecast

)



# ============================================================
# ADAPTIVE MEMORY
# ============================================================

try:

    adaptive_adjustment = (

        get_prediction_adjustment()

    )


except:

    adaptive_adjustment = 0



if forecast:


    forecast["adaptive_adjustment"] = (

        adaptive_adjustment

    )


    forecast["adjusted_price"] = (

        forecast["expected_price"]

        +

        adaptive_adjustment

    )



# ============================================================
# MEMORY STATUS
# ============================================================

with st.sidebar.expander(
    "🧠 Model Learning Status"
):

    try:

        history = evaluate_predictions()


        st.write(
            f"Stored Predictions: {len(history)}"
        )


        st.write(
            f"Adaptive Bias: {adaptive_adjustment:.4f}"
        )


    except:

        st.write(
            "Memory system initializing..."
        )



if len(gc.get_objects()) > 500000:

    gc.collect()
# ============================================================
# APP.PY
# PART 3/3
# DASHBOARD + ANALYTICS + EXPORT
# ============================================================


# ============================================================
# MAIN HEADER
# ============================================================

st.title(
    "⚛️ Quantum Equity Research Terminal"
)



if forecast is None:

    st.info(
        "Run a quantum forecast from the sidebar."
    )

    st.stop()



# ============================================================
# SUMMARY METRICS
# ============================================================

expected_return = (

    forecast["expected_price"]

    /

    forecast["starting_price"]

    -

    1

) * 100



c1,c2,c3,c4 = st.columns(4)



with c1:

    metric_card(
        "Expected Price",
        format_price(
            forecast["expected_price"]
        )
    )



with c2:

    metric_card(
        "Expected Return",
        f"{expected_return:+.2f}%",
        expected_return
    )



with c3:

    metric_card(
        "Confidence",
        f"{forecast['confidence_score']:.1f}%"
    )



with c4:

    metric_card(
        "Risk Score",
        f"{forecast['risk_score']:.2f}"
    )



st.divider()



# ============================================================
# MARKET REGIME
# ============================================================

c1,c2,c3 = st.columns(3)



with c1:

    regime = forecast.get(
        "market_regime",
        "Unknown"
    )


    status = {

        "Bullish":
        "positive",

        "Bearish":
        "negative",

        "Neutral":
        "neutral"

    }.get(
        regime,
        "neutral"
    )


    render_status_badge(
        regime,
        status
    )



with c2:

    st.metric(

        "Upside Probability",

        f"{forecast['upside_probability']:.2f}%"

    )



with c3:

    st.metric(

        "Downside Probability",

        f"{forecast['downside_probability']:.2f}%"

    )



# ============================================================
# QUANTUM DISTRIBUTION
# ============================================================

st.subheader(
    "⚛️ Quantum Price Probability"
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



plt.close(
    fig
)



# ============================================================
# RETURN DISTRIBUTION
# ============================================================

st.subheader(
    "📈 Return Probability"
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


ax.set_title(
    "Future Return Distribution"
)



st.pyplot(
    fig,
    clear_figure=True
)



plt.close(
    fig
)



# ============================================================
# FORECAST SUMMARY
# ============================================================

with st.expander(
    "📊 Forecast Summary"
):


    summary = pd.DataFrame(

        {

            "Metric":[

                "Ticker",

                "Forecast Horizon",

                "Starting Price",

                "Expected Price",

                "Volatility",

                "Market Regime",

                "Confidence",

                "Risk Score"

            ],


            "Value":[

                ticker,

                f"{forecast_days} days",

                format_price(
                    forecast["starting_price"]
                ),


                format_price(
                    forecast["expected_price"]
                ),


                f"{forecast['volatility']:.2f}%",


                forecast["market_regime"],


                f"{forecast['confidence_score']:.2f}%",


                f"{forecast['risk_score']:.2f}"

            ]

        }

    )


    st.dataframe(

        summary,

        hide_index=True,

        use_container_width=True

    )



# ============================================================
# DECISION TRACE
# ============================================================

with st.expander(
    "⚛️ Quantum Decision Trace"
):


    metadata = forecast.get(
        "model_metadata",
        {}
    )


    weights = metadata.get(
        "weights",
        {}
    )



    if weights:


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

                    weights.get(
                        "technical",
                        0
                    ),

                    weights.get(
                        "macro",
                        0
                    ),

                    weights.get(
                        "global",
                        0
                    ),

                    weights.get(
                        "sector",
                        0
                    ),

                    weights.get(
                        "sentiment",
                        0
                    )

                ]

            }

        )


        weight_table["Weight"] = (

            weight_table["Weight"]

            .apply(
                lambda x:
                f"{x:.2f}%"
            )

        )


        st.dataframe(
            weight_table,
            use_container_width=True,
            hide_index=True
        )



    c1,c2 = st.columns(2)



    with c1:

        st.metric(

            "Market State",

            f"{metadata.get('market_state',0):.4f}"

        )



    with c2:

        st.metric(

            "Technical Signal",

            f"{metadata.get('technical_signal',0):.4f}"

        )



# ============================================================
# MEMORY DASHBOARD
# ============================================================

with st.expander(
    "🧠 Prediction Memory System"
):


    try:


        history = evaluate_predictions()


        adjustment = (

            get_prediction_adjustment()

        )


        st.metric(

            "Adaptive Adjustment",

            f"{adjustment:.4f}"

        )


        if history:


            memory_df = pd.DataFrame(
                history
            )


            st.dataframe(
                memory_df,
                use_container_width=True
            )


        else:

            st.info(
                "No completed predictions yet."
            )



    except Exception as error:


        st.warning(
            f"Memory unavailable: {error}"
        )



# ============================================================
# FEEDBACK LOOP
# ============================================================

with st.expander(
    "📊 Prediction Accuracy Feedback"
):


    prediction_id = (

        st.session_state.prediction_id

    )


    if prediction_id:


        actual_price = st.number_input(

            "Actual Price",

            min_value=0.0,

            value=0.0

        )



        if st.button(
            "Submit Prediction Result"
        ):


            if actual_price > 0:


                complete_prediction(

                    prediction_id,

                    actual_price

                )


                st.success(
                    "Prediction updated."
                )


            else:

                st.warning(
                    "Enter a valid price."
                )


    else:

        st.info(
            "Run a forecast before submitting results."
        )



# ============================================================
# PERFORMANCE
# ============================================================

with st.expander(
    "📈 Model Performance"
):


    try:

        history = evaluate_predictions()


        if history:


            performance = pd.DataFrame(
                history
            )


            st.dataframe(

                performance,

                use_container_width=True

            )


        else:

            st.info(
                "Waiting for completed predictions."
            )


    except Exception as error:


        st.warning(
            f"Performance unavailable: {error}"
        )



# ============================================================
# EXPORT
# ============================================================

if st.session_state.forecast:


    with st.expander(
        "📄 Export Forecast Report"
    ):


        report = create_forecast_report(

            st.session_state.forecast

        )


        csv = report.to_csv(
            index=False
        )


        st.download_button(

            "Download Forecast CSV",

            csv,

            file_name=f"{ticker}_quantum_forecast.csv",

            mime="text/csv"

        )



# ============================================================
# CACHE MANAGEMENT
# ============================================================

with st.sidebar.expander(
    "🧹 System Maintenance"
):


    if st.button(
        "Clear Data Cache"
    ):


        try:

            clear_data_cache()

            st.cache_data.clear()

            gc.collect()


            st.success(
                "Cache cleared."
            )


        except Exception as error:


            st.error(
                f"Cache clear failed: {error}"
            )



# ============================================================
# FOOTER
# ============================================================

st.divider()



st.caption(
    """
⚛️ Quantum Equity Research Terminal

Hybrid forecasting system combining:

• Market statistics
• Technical indicators
• Probability modeling
• Quantum circuit sampling
• Adaptive prediction memory

Built for research and experimentation.
"""
)



gc.collect()
