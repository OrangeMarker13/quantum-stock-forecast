"""Simple, investor-facing Streamlit interface for the forecast service."""

from __future__ import annotations

import html
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from analytics import add_features, create_forecast_report, extract_inputs, validate_inputs
from data_provider import (
    clear_data_cache,
    format_price,
    get_company_info,
    get_live_price,
    get_stock_data,
    search_stocks,
    validate_market_data,
)
from prediction_memory import apply_learning_adjustment, get_prediction_adjustment, store_prediction
from quantum_joint_engine import quantum_joint_forecast
from sector_lookup import get_sector_etf


st.set_page_config(page_title="Market Outlook", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.set_option("client.showErrorDetails", False)

HORIZON_LABELS = {
    1: "Next trading day",
    2: "2 trading days",
    7: "1 week (7 trading days)",
    30: "1 month (30 trading days)",
    60: "3 months (60 trading days)",
    90: "About 4 months (90 trading days)",
}

DEFAULT_STATE = {"forecast": None, "forecast_settings": None, "prediction_id": None, "theme": "Dark"}
for state_key, default_value in DEFAULT_STATE.items():
    st.session_state.setdefault(state_key, default_value)


def apply_app_style(theme: str) -> None:
    if theme == "Dark":
        bg_color = "#0e1117"
        sidebar_bg = "#262730"
        text_color = "#fafafa"
        header_color = "#ffffff"
        input_bg = "#2b2b36"
        input_text = "#ffffff"
        border_color = "#4b4c53"
        card_bg = "#1e1e24"
    else:
        bg_color = "#f7f9fc"
        sidebar_bg = "#ffffff"
        text_color = "#172033"
        header_color = "#14213d"
        input_bg = "#ffffff"
        input_text = "#14213d"
        border_color = "#cbd5e1"
        card_bg = "#ffffff"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {bg_color};
            color: {text_color};
        }}

        section[data-testid="stSidebar"] {{
            background: {sidebar_bg};
            border-right: 1px solid {border_color};
        }}

        h1, h2, h3 {{
            color: {header_color} !important;
            letter-spacing: -0.02em;
        }}

        label, p, span, div {{
            color: {text_color};
        }}

        div[data-baseweb="input"] {{
            background: {input_bg};
            border: 1px solid {border_color};
            border-radius: 8px;
        }}

        div[data-baseweb="input"] input {{
            color: {input_text} !important;
            background: {input_bg} !important;
        }}

        div[data-baseweb="input"] input::placeholder {{
            color: #64748b !important;
        }}

        div[data-baseweb="select"] > div {{
            background: {input_bg};
            border: 1px solid {border_color};
            border-radius: 8px;
        }}

        div[data-baseweb="select"] span {{
            color: {input_text} !important;
        }}

        ul[role="listbox"] {{
            background: {input_bg};
        }}

        ul[role="listbox"] li {{
            color: {input_text} !important;
        }}

        .stButton > button {{
            background: #1d4ed8;
            color: #ffffff !important;
            border: 0;
            border-radius: 9px;
            font-weight: 650;
            padding: .55rem 1rem;
            width: 100%;
        }}

        .stButton > button:hover {{
            background: #1e40af;
            color: #ffffff !important;
        }}

        .metric-card {{
            background: {card_bg};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 16px 18px;
            min-height: 112px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, .04);
        }}

        .metric-label {{
            color: #667085;
            font-size: .82rem;
            font-weight: 650;
            margin-bottom: 7px;
        }}

        .metric-value {{
            color: {header_color};
            font-size: 1.55rem;
            font-weight: 750;
            line-height: 1.2;
        }}

        .metric-detail {{
            color: #667085;
            font-size: .82rem;
            margin-top: 6px;
        }}

        .positive {{
            color: #087443;
        }}

        .negative {{
            color: #b42318;
        }}

        .neutral {{
            color: #475467;
        }}

        .outlook {{
            display: inline-block;
            padding: 6px 11px;
            border-radius: 999px;
            font-weight: 650;
            font-size: .87rem;
            background: #eef4ff;
            color: #1d4ed8;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        value = float(value)
        return value if np.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def percent_text(value: float) -> str:
    return f"{value:+.2f}%"


def metric_card(label: str, value: str, detail: str = "", tone: str = "neutral") -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value {tone}">{html.escape(value)}</div>'
        f'<div class="metric-detail">{html.escape(detail)}</div></div>',
        unsafe_allow_html=True,
    )


def reset_app() -> None:
    clear_data_cache()
    for state_key, default_value in DEFAULT_STATE.items():
        if state_key != "theme":
            st.session_state[state_key] = default_value


def forecast_chart(forecast: dict, theme: str) -> None:
    grid = np.asarray(forecast["price_grid"], dtype=float)
    probability = np.asarray(forecast["probability"], dtype=float)
    fig, axis = plt.subplots(figsize=(10, 3.6))

    bg_color = "#1e1e24" if theme == "Dark" else "#ffffff"
    text_color = "#fafafa" if theme == "Dark" else "#172033"
    grid_color = "#32323d" if theme == "Dark" else "#eaecf0"

    fig.patch.set_facecolor(bg_color)
    axis.set_facecolor(bg_color)
    axis.plot(grid, probability, color="#2563eb", linewidth=2.5)
    axis.fill_between(grid, probability, color="#2563eb", alpha=0.12)
    axis.axvline(forecast["starting_price"], color="#98a2b3", linewidth=1.2, linestyle="--", label="Current price")
    axis.axvline(forecast["expected_price"], color="#087443", linewidth=1.4, linestyle="--", label="Forecast")
    
    axis.set_xlabel("Possible future price", color=text_color)
    axis.set_ylabel("Relative likelihood", color=text_color)
    axis.tick_params(colors=text_color)
    axis.grid(axis="y", color=grid_color, linewidth=.8)
    axis.spines[["top", "right"]].set_visible(False)
    for spine in axis.spines.values():
        spine.set_edgecolor(text_color)
        
    legend = axis.legend(frameon=False, loc="upper right")
    for text in legend.get_texts():
        text.set_color(text_color)
        
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


col_empty, col_toggle = st.columns([8, 2])
with col_toggle:
    is_dark = st.toggle("Dark Mode", value=(st.session_state.theme == "Dark"))
    st.session_state.theme = "Dark" if is_dark else "Light"

apply_app_style(st.session_state.theme)

with st.sidebar:
    st.header("Find a stock")
    search_query = st.text_input("Company or ticker", value="Microsoft", placeholder="e.g., Apple or AAPL")
    try:
        search_results = search_stocks(search_query)
    except Exception:
        search_results = []
    if search_results:
        selected = st.selectbox(
            "Select a result",
            search_results,
            format_func=lambda item: item.get("label", item.get("symbol", "Unknown"))
        )
        ticker = selected.get("symbol", search_query).upper()
        company_name = selected.get("name", ticker)
    else:
        ticker = search_query.upper().strip()
        company_name = ticker

    forecast_days = st.selectbox(
        "Forecast period",
        list(HORIZON_LABELS),
        index=3,
        format_func=HORIZON_LABELS.get
    )
    run_button = st.button("Create forecast", type="primary")

    if st.button("Clear saved view"):
        reset_app()
        st.rerun()

    st.caption("Forecasts are estimates, not investment advice.")
live_data = get_live_price(ticker) or {}
company = get_company_info(ticker) or {"name": company_name}
current_price = safe_float(live_data.get("price"))
daily_change = safe_float(live_data.get("change_percent"))

st.title(company.get("name", company_name))
st.caption(f"{ticker} · Prices may be delayed · Updated {datetime.now().strftime('%I:%M %p')}")

summary_columns = st.columns(3)

with summary_columns[0]:
    metric_card(
        "Current price",
        format_price(current_price) if current_price else "Unavailable",
        "Latest available quote"
    )

with summary_columns[1]:
    change_tone = "positive" if daily_change > 0 else "negative" if daily_change < 0 else "neutral"
    metric_card(
        "Today",
        percent_text(daily_change) if live_data else "Unavailable",
        "Change from prior close",
        change_tone
    )

with summary_columns[2]:
    metric_card(
        "Forecast period",
        HORIZON_LABELS[forecast_days],
        "Choose a period in the sidebar"
    )


market_data = get_stock_data(ticker)
spy_data = get_stock_data("SPY")
sector_etf = get_sector_etf(ticker)
sector_data = get_stock_data(sector_etf) if sector_etf else pd.DataFrame()

if market_data.empty or not validate_market_data(market_data):
    st.error("We could not load enough reliable price history for this symbol. Try a listed U.S. stock or ETF.")
    st.stop()

market_data = market_data.copy()
market_data["Close"] = pd.to_numeric(market_data["Close"], errors="coerce")
market_data = market_data.replace([np.inf, -np.inf], np.nan).dropna(subset=["Close"])

features = add_features(market_data)

if not validate_inputs(features, extract_inputs(features)):
    st.error("The available history is incomplete. Please try another stock.")
    st.stop()


if run_button:
    base_price = current_price or safe_float(market_data["Close"].iloc[-1])

    try:
        with st.spinner("Reviewing price history and market context…"):
            raw_forecast = quantum_joint_forecast(
                market_data,
                base_price,
                days=forecast_days,
                shots=1500,
                spy_data=spy_data,
                sector_data=sector_data,
            )

        learned_bias = get_prediction_adjustment(ticker, forecast_days)
        forecast = apply_learning_adjustment(raw_forecast, learned_bias)

        prediction_id = store_prediction(
            ticker,
            forecast_days,
            base_price,
            forecast["expected_price"]
        )

        st.session_state.forecast = forecast
        st.session_state.forecast_settings = (ticker, forecast_days)
        st.session_state.prediction_id = prediction_id

        st.success("Forecast ready.")

    except Exception:
        st.error("We could not complete this forecast. Please try again in a moment.")


forecast = st.session_state.forecast
settings = st.session_state.forecast_settings

if forecast is not None and settings and settings[0] != ticker:
    forecast = None


if forecast is None:
    st.info("Choose a stock and forecast period, then select **Create forecast**.")
    st.stop()


expected_move = (forecast["expected_price"] / forecast["starting_price"] - 1) * 100
risk = forecast["risk_score"]

risk_label = "Lower" if risk < 3.5 else "Moderate" if risk < 6.5 else "Higher"
outlook = forecast.get("market_regime", "Neutral")


st.divider()
st.subheader("Your forecast")

forecast_columns = st.columns(4)

with forecast_columns[0]:
    metric_card(
        "Expected price",
        format_price(forecast["expected_price"]),
        f"Over {HORIZON_LABELS[settings[1]].lower()}"
    )

with forecast_columns[1]:
    movement_tone = "positive" if expected_move > 0 else "negative" if expected_move < 0 else "neutral"

    metric_card(
        "Expected move",
        percent_text(expected_move),
        "From the current price",
        movement_tone
    )

with forecast_columns[2]:
    metric_card(
        "Forecast confidence",
        f"{forecast['confidence_score']:.0f}/100",
        "Higher means a more concentrated estimate"
    )

with forecast_columns[3]:
    metric_card(
        "Market risk",
        risk_label,
        "Based on recent price swings"
    )


st.markdown(
    f'<span class="outlook">Market outlook: {html.escape(outlook)}</span>',
    unsafe_allow_html=True
)

st.subheader("Possible price range")
st.caption(
    "This shows the range of outcomes the model considers more or less likely. It is not a guarantee."
)

forecast_chart(forecast, st.session_state.theme)


probability_columns = st.columns(3)

with probability_columns[0]:
    metric_card(
        "Chance of a gain above 5%",
        f"{forecast['upside_probability']:.0f}%",
        "Within the forecast period"
    )

with probability_columns[1]:
    metric_card(
        "Chance of a loss above 5%",
        f"{forecast['downside_probability']:.0f}%",
        "Within the forecast period"
    )

with probability_columns[2]:
    metric_card(
        "Most likely range",
        f"{forecast['neutral_probability']:.0f}%",
        "Moves between −5% and +5%"
    )


if abs(forecast.get("adaptive_adjustment", 0.0)) >= 0.001:
    st.caption(
        "This forecast incorporates the model’s results from comparable, previously settled forecasts."
    )


with st.expander("Forecast details"):
    st.write(
        f"Uses {len(market_data)} recent market sessions plus broad-market and sector context when available."
    )

    st.dataframe(
        market_data[["Date", "Close"]]
        .tail(30)
        .rename(columns={"Close": "Closing price"}),
        use_container_width=True,
        hide_index=True
    )

    report = create_forecast_report(forecast)

    st.download_button(
        "Download forecast summary (CSV)",
        report.to_csv(index=False),
        file_name=f"{ticker}_forecast.csv",
        mime="text/csv"
    )
