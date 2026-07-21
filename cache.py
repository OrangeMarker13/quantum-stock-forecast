import os
import pandas as pd
from datetime import datetime, timedelta


CACHE_FOLDER = "stock_cache"


os.makedirs(
    CACHE_FOLDER,
    exist_ok=True
)



def get_cache_path(ticker):

    return os.path.join(
        CACHE_FOLDER,
        f"{ticker}.csv"
    )



def save_cache(
    ticker,
    prices
):

    path = get_cache_path(
        ticker
    )

    df = pd.DataFrame(
        {
            "Close": prices
        }
    )

    df.to_csv(
        path
    )



def load_cache(
    ticker,
    max_age_minutes=30
):

    path = get_cache_path(
        ticker
    )


    if not os.path.exists(path):

        return None



    modified_time = datetime.fromtimestamp(
        os.path.getmtime(path)
    )


    age = datetime.now() - modified_time



    if age > timedelta(
        minutes=max_age_minutes
    ):

        return None



    try:

        df = pd.read_csv(
            path,
            index_col=0,
            parse_dates=True
        )


        return df["Close"]



    except Exception:

        return None
