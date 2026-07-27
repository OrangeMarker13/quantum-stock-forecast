# Market Outlook

A Streamlit app that presents an approachable stock forecast, expected price range, confidence, risk, and potential upside/downside outcomes.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Forecasts are estimates based on historical market data and are not investment advice.

## Optional unattended forecasting

The GitHub Actions workflow creates forecasts shortly after U.S. market open and settles them after close. It includes same-day close forecasts plus 7-, 30-, 60-, and 90-trading-day forecasts.

- It starts with up to 75 liquid U.S. symbols per day.
- Create `stock_universe.json` with `{"tickers": ["AAPL", "MSFT"]}` to use a custom list.
- Set `AUTONOMOUS_MAX_TICKERS` in the runner environment to tune the daily batch size.
- Enable GitHub Actions and grant the workflow write permission to persist `prediction_memory.json`.
