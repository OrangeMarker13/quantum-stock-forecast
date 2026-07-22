# ============================================================
# quantum_engine.py
# Quantum Equity Forecast Engine
# Part 1/3
# ============================================================

import numpy as np

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator



# ============================================================
# DATA CLEANING
# ============================================================

def clean_data(data):

    df = data.copy()

    df["Close"] = (
        df["Close"]
        .astype(float)
    )

    df = (
        df.replace(
            [np.inf, -np.inf],
            np.nan
        )
        .dropna(
            subset=["Close"]
        )
    )

    return df



# ============================================================
# FEATURE ENGINEERING
# ============================================================

def add_features(data):

    df = clean_data(data)

    close = df["Close"]


    # Returns

    df["Return"] = (
        close
        .pct_change()
        .fillna(0)
    )


    # Moving averages

    df["MA7"] = (
        close
        .rolling(7)
        .mean()
        .fillna(close)
    )


    df["MA30"] = (
        close
        .rolling(30)
        .mean()
        .fillna(close)
    )


    df["MA90"] = (
        close
        .rolling(90)
        .mean()
        .fillna(close)
    )


    # Volatility

    df["Volatility"] = (
        df["Return"]
        .rolling(30)
        .std()
        .fillna(0)
    )


    # Momentum

    df["Momentum"] = (

        close /
        close.shift(20)
        -
        1

    ).fillna(0)



    # RSI

    delta = close.diff()


    gains = delta.clip(
        lower=0
    )


    losses = -delta.clip(
        upper=0
    )


    avg_gain = (
        gains
        .rolling(14)
        .mean()
    )


    avg_loss = (
        losses
        .rolling(14)
        .mean()
    )


    rs = (
        avg_gain /
        (avg_loss + 1e-9)
    )


    df["RSI"] = (

        100 -

        (
            100 /
            (1 + rs)
        )

    ).fillna(50)



    # Market strength

    df["Market_Strength"] = np.clip(

        (

            df["MA30"] /

            (df["MA90"] + 1e-9)

        )
        *
        50,

        0,

        100

    )


    return (

        df

        .replace(
            [np.inf,-np.inf],
            np.nan
        )

        .fillna(0)

    )



# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_state(data):

    row = data.iloc[-1]


    return {

        "price":
            float(row["Close"]),

        "volatility":
            float(row["Volatility"]),

        "momentum":
            float(row["Momentum"]),

        "rsi":
            float(row["RSI"]),

        "market_strength":
            float(row["Market_Strength"])

    }



# ============================================================
# MARKET SIGNAL ENGINE
# ============================================================

def calculate_market_state(
    prices,
    external_features=None
):

    if external_features is None:

        external_features = {}



    def trend(days):

        if len(prices) < days:

            return 0


        return (

            prices.iloc[-1]

            /

            prices.iloc[-days]

            -

            1

        )



    technical = (

        trend(7)*0.15

        +

        trend(30)*0.35

        +

        trend(90)*0.50

    )


    technical = np.clip(
        technical,
        -0.20,
        0.20
    )



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



    weights = {

        "technical":0.45,

        "macro":0.15,

        "global":0.15,

        "sector":0.10,

        "sentiment":0.10,

        "earnings":0.05

    }



    state = (

        technical *
        weights["technical"]

        +

        macro *
        weights["macro"]

        +

        global_market *
        weights["global"]

        +

        sector *
        weights["sector"]

        +

        sentiment *
        weights["sentiment"]

        +

        earnings *
        weights["earnings"]

        +

        rates*.05

    )


    return (

        np.clip(
            state,
            -.35,
            .35
        ),

        weights,

        technical

    )
  # ============================================================
# quantum_engine.py
# Quantum Equity Forecast Engine
# Part 2/3
# ============================================================


# ============================================================
# QUANTUM STATE SAMPLER
# ============================================================

def quantum_sample(
    probabilities,
    qubits,
    shots
):

    states = 2 ** qubits


    amplitudes = np.sqrt(
        probabilities
    )


    amplitudes /= np.linalg.norm(
        amplitudes
    )


    circuit = QuantumCircuit(
        qubits
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



    for state,count in counts.items():

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

        return probabilities



    return (

        quantum_probability /

        quantum_probability.sum()

    )



# ============================================================
# PRICE DISTRIBUTION ENGINE
# ============================================================

def create_price_distribution(
    starting_price,
    expected_return,
    volatility,
    days,
    qubits
):

    states = 2 ** qubits



    movement = (

        volatility *

        np.sqrt(
            max(days,1)
            /
            252
        )

    )



    movement = np.clip(

        movement,

        .03,

        .40

    )



    lower = (

        starting_price *

        (1 - movement)

    )


    upper = (

        starting_price *

        (1 + movement)

    )



    price_grid = np.linspace(

        lower,

        upper,

        states

    )



    return_grid = (

        price_grid /

        starting_price

        -

        1

    )



    uncertainty = max(
        movement,
        .02
    )



    z = (

        return_grid

        -

        expected_return

    ) / uncertainty



    probabilities = np.exp(

        -.5 *

        z**2

    )



    probabilities = np.nan_to_num(

        probabilities,

        nan=1,

        posinf=1,

        neginf=0

    )



    if probabilities.sum() == 0:

        probabilities = np.ones(
            states
        )



    probabilities /= (
        probabilities.sum()
    )



    return (

        price_grid,

        return_grid,

        probabilities

    )



# ============================================================
# DRIFT CALCULATION
# ============================================================

def calculate_expected_return(
    returns,
    market_state,
    days
):


    historical_return = float(
        returns.mean()
    )



    drift = (

        historical_return *

        .60

        +

        market_state *

        .40

    )



    drift = np.clip(

        drift,

        -.0015,

        .0015

    )



    expected_return = (

        drift *

        days

    )



    limits = {

        1:.03,

        2:.05,

        7:.10,

        30:.18,

        60:.25,

        90:.35

    }



    allowed = limits.get(

        days,

        .35

    )



    return np.clip(

        expected_return,

        -allowed,

        allowed

    )



# ============================================================
# CONFIDENCE ENGINE
# ============================================================

def calculate_confidence(
    probability,
    states,
    volatility,
    market_state
):

    entropy = -np.sum(

        probability *

        np.log(
            probability + 1e-12
        )

    )



    entropy_score = (

        1 -

        entropy /

        np.log(states)

    ) * 100



    volatility_score = np.clip(

        100 -

        volatility * 100,

        10,

        90

    )



    confidence = (

        entropy_score*.50

        +

        volatility_score*.30

        +

        abs(market_state)

        *

        100

        *

        .20

    )



    return np.clip(

        confidence,

        10,

        95

    )



# ============================================================
# RISK ENGINE
# ============================================================

def calculate_risk(
    probability,
    return_grid,
    annual_volatility
):

    downside = (

        probability[
            return_grid < -.05
        ]

        .sum()

        *

        100

    )


    risk = (

        annual_volatility *

        100 *

        downside /

        100

    )


    return (

        risk,

        downside

    )
  # ============================================================
# quantum_engine.py
# Quantum Equity Forecast Engine
# Part 3/3
# ============================================================


# ============================================================
# MAIN FORECAST FUNCTION
# ============================================================

def quantum_forecast(
    market_data,
    starting_price,
    days=30,
    qubits=6,
    shots=1500,
    external_features=None
):


    if external_features is None:

        external_features = {}



    # --------------------------------------------------------
    # Prepare market data
    # --------------------------------------------------------

    data = add_features(
        market_data
    )


    prices = data["Close"]


    returns = (

        prices

        .pct_change()

        .replace(
            [np.inf,-np.inf],
            np.nan
        )

        .dropna()

    )



    if len(returns) < 30:

        raise ValueError(
            "Not enough market history."
        )



    # --------------------------------------------------------
    # Volatility
    # --------------------------------------------------------

    daily_volatility = float(
        returns.std()
    )


    if daily_volatility <= 0:

        daily_volatility = .01



    annual_volatility = (

        daily_volatility *

        np.sqrt(252)

    )



    # --------------------------------------------------------
    # Market state
    # --------------------------------------------------------

    market_state, weights, technical_signal = calculate_market_state(

        prices,

        external_features

    )



    # --------------------------------------------------------
    # Expected movement
    # --------------------------------------------------------

    expected_return = calculate_expected_return(

        returns,

        market_state,

        days

    )



    classical_expected_price = (

        starting_price *

        np.exp(
            expected_return
        )

    )



    # --------------------------------------------------------
    # Create probability space
    # --------------------------------------------------------

    price_grid, return_grid, classical_probability = create_price_distribution(

        starting_price,

        expected_return,

        annual_volatility,

        days,

        qubits

    )



    # --------------------------------------------------------
    # Quantum sampling
    # --------------------------------------------------------

    try:

        quantum_probability = quantum_sample(

            classical_probability,

            qubits,

            shots

        )

    except Exception:

        quantum_probability = (
            classical_probability.copy()
        )



    # --------------------------------------------------------
    # Quantum expected price
    # --------------------------------------------------------

    quantum_expected_price = np.sum(

        price_grid *

        quantum_probability

    )



    # --------------------------------------------------------
    # Probability zones
    # --------------------------------------------------------

    upside_probability = (

        quantum_probability[

            return_grid > .05

        ]

        .sum()

        *

        100

    )



    downside_probability = (

        quantum_probability[

            return_grid < -.05

        ]

        .sum()

        *

        100

    )



    neutral_probability = (

        100

        -

        upside_probability

        -

        downside_probability

    )



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



    # --------------------------------------------------------
    # Confidence + risk
    # --------------------------------------------------------

    confidence_score = calculate_confidence(

        quantum_probability,

        2 ** qubits,

        annual_volatility,

        market_state

    )



    risk_score, downside = calculate_risk(

        quantum_probability,

        return_grid,

        annual_volatility

    )



    # --------------------------------------------------------
    # Market regime
    # --------------------------------------------------------

    if market_state > .08:

        regime = "Bullish"


    elif market_state < -.08:

        regime = "Bearish"


    else:

        regime = "Neutral"



    # --------------------------------------------------------
    # Model trace
    # --------------------------------------------------------

    metadata = {

        "weights": {

            key:

            round(

                value * 100,

                2

            )

            for key,value in weights.items()

        },


        "technical_signal":

            round(

                float(
                    technical_signal
                ),

                4

            ),


        "market_state":

            round(

                float(
                    market_state
                ),

                4

            )

    }



    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    return {


        "starting_price":

            starting_price,


        "classical_expected_price":

            classical_expected_price,


        "expected_price":

            quantum_expected_price,


        "price_grid":

            price_grid,


        "return_grid":

            return_grid,


        "probability":

            quantum_probability,


        "classical_probability":

            classical_probability,


        "returns":

            returns,


        "volatility":

            annual_volatility * 100,


        "market_regime":

            regime,


        "confidence_score":

            confidence_score,


        "risk_score":

            risk_score,


        "market_state":

            market_state,


        "upside_probability":

            upside_probability,


        "downside_probability":

            downside_probability,


        "neutral_probability":

            neutral_probability,


        "model_metadata":

            metadata

    }
