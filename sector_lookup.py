# ============================================================
# quantum_joint_engine.py
# Quantum Equity Forecast Engine — Joint Multi-Factor Extension
#
# Adds a genuinely joint quantum sampling stage on top of the
# existing classical pipeline in quantum_engine.py. Instead of
# quantum-sampling a single precomputed price distribution
# (which is mathematically just noisy resampling of a classical
# curve), this module:
#
#   1. Builds four factor series from real data:
#        - price return
#        - volatility regime
#        - momentum
#        - macro/sector tilt (SPY + sector ETF average)
#   2. Estimates their historical correlation structure directly
#      from data using an empirical (quantile-rank) copula — no
#      assumed or synthetic correlations.
#   3. Encodes the resulting JOINT distribution as amplitudes on
#      a multi-register circuit, so entanglement in the circuit
#      reflects real historical co-movement between factors.
#   4. Measures the joint state and reports both the marginal
#      price forecast AND real conditional probabilities, e.g.
#      P(price drop > 5% | high volatility regime), which the
#      single-factor pipeline cannot produce at all.
#
# HONESTY NOTE (kept deliberately explicit in code and outputs):
# This does not create predictive power beyond what the
# historical correlation matrix already contains. The circuit
# is a faithful re-encoding of a classical joint distribution,
# not a source of new information. Its value is (a) making
# factor interdependence a first-class, inspectable output via
# genuine multi-qubit entanglement, and (b) sampling a joint
# space that would otherwise have to be stored as an explicit
# 4-D probability table. It is NOT a claim of quantum advantage
# over classical multivariate sampling.
# ============================================================

import numpy as np
import pandas as pd

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


# ============================================================
# CONFIG / SAFETY LIMITS
# ============================================================

# Hard ceiling on total qubits regardless of any user input.
# 12 qubits -> 4096-dim dense statevector; verified safe latency
# (<1s) for circuit.initialize + measurement in this environment.
MAX_TOTAL_QUBITS = 12

# Default (always-safe) resolution.
DEFAULT_QUBITS_PER_FACTOR = 2   # 4 factors x 2 = 8 qubits, 256-dim

# Upgraded resolution, used only if upgrade conditions are met.
UPGRADED_QUBITS_PER_FACTOR = 3  # 4 factors x 3 = 12 qubits, 4096-dim

# Minimum rows of history required to trust a 4x4 correlation
# estimate enough to justify the higher resolution.
MIN_ROWS_FOR_UPGRADE = 252

# Minimum shots required before 4096 bins would be mostly empty
# noise rather than a meaningful sampled distribution.
MIN_SHOTS_FOR_UPGRADE = 2000

FACTOR_NAMES = ["price_return", "volatility", "momentum", "macro"]


# ============================================================
# FACTOR CONSTRUCTION
# ============================================================

def build_factor_frame(market_data, spy_data=None, sector_data=None):
    """
    Build the four aligned factor series used for joint sampling.

    price_return : daily return of Close
    volatility   : rolling realized volatility (30d std of returns)
    momentum     : 20-day price momentum
    macro        : average of SPY return and sector ETF return,
                   aligned by the 'Date' COLUMN, not market_data's
                   row index. data_provider.get_stock_data returns
                   a DataFrame with a plain RangeIndex (0,1,2,...)
                   and dates stored in a 'Date' column -- confirmed
                   by direct inspection of that function's output.
                   Aligning on the row index instead of the Date
                   column was caught in testing (it raised a dtype
                   comparison error immediately, rather than
                   silently misaligning, which is what led to this
                   fix). Falls back to whichever of SPY/sector is
                   available; if neither is available, the macro
                   column is all-NaN and the caller should detect
                   this via the returned macro_ok flag and run in
                   3-factor mode instead of fabricating a signal.

    Returns (frame, macro_was_available). frame carries the same
    row index as market_data, with columns FACTOR_NAMES.
    """

    df = market_data.copy()

    if "Date" not in df.columns:
        raise ValueError(
            "market_data must have a 'Date' column to align macro "
            "factor data (this matches the shape produced by "
            "data_provider.get_stock_data)."
        )

    close = df["Close"].astype(float)

    price_return = close.pct_change()
    volatility = price_return.rolling(30, min_periods=10).std()
    momentum = (close / close.shift(20) - 1)

    macro = combine_macro_proxy(df["Date"], spy_data, sector_data)
    macro.index = df.index  # re-attach to market_data's actual row index

    macro_ok = macro.notna().any()

    frame = pd.DataFrame({
        "price_return": price_return,
        "volatility": volatility,
        "momentum": momentum,
        "macro": macro,
    }, index=df.index)

    if macro_ok:
        frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
    else:
        # Drop NaNs on the three real factors only; macro stays NaN
        # and the joint-sampling step will run in 3-factor mode.
        core = frame[["price_return", "volatility", "momentum"]]
        core = core.replace([np.inf, -np.inf], np.nan).dropna()
        frame = frame.loc[core.index]

    return frame, macro_ok


def combine_macro_proxy(date_column, spy_data, sector_data):
    """
    Build the macro/sector factor as the average of SPY returns and
    a sector ETF's returns, aligned to `date_column` (the target
    ticker's real calendar dates) by nearest date.

    spy_data / sector_data are expected in the same shape as
    data_provider.get_stock_data's output: a 'Date' column plus a
    'Close' column, RangeIndex rows.

    If only one of the two is available, use it alone. If neither
    is available, return an all-NaN series (positional 0..n-1) so
    downstream code can detect and handle the missing-macro case
    explicitly rather than fabricating a signal.
    """

    target_dates = pd.to_datetime(pd.Series(date_column).reset_index(drop=True))

    spy_ret = None
    sector_ret = None

    if spy_data is not None and not spy_data.empty and "Close" in spy_data.columns and "Date" in spy_data.columns:
        s = spy_data.copy()
        s["Date"] = pd.to_datetime(s["Date"])
        s = s.set_index("Date")["Close"].astype(float).pct_change().sort_index()
        spy_ret = s.reindex(target_dates, method="nearest").reset_index(drop=True)

    if sector_data is not None and not sector_data.empty and "Close" in sector_data.columns and "Date" in sector_data.columns:
        s = sector_data.copy()
        s["Date"] = pd.to_datetime(s["Date"])
        s = s.set_index("Date")["Close"].astype(float).pct_change().sort_index()
        sector_ret = s.reindex(target_dates, method="nearest").reset_index(drop=True)

    if spy_ret is not None and sector_ret is not None:
        combined = pd.concat([spy_ret, sector_ret], axis=1)
        combined.columns = ["spy", "sector"]
        return combined.mean(axis=1, skipna=True)

    if spy_ret is not None:
        return spy_ret

    if sector_ret is not None:
        return sector_ret

    return pd.Series(np.nan, index=range(len(target_dates)))


# ============================================================
# EMPIRICAL JOINT DISTRIBUTION (DATA-DRIVEN CORRELATION)
# ============================================================

def quantile_bin(series, k):
    """
    Bin a series into k quantile-based buckets (roughly equal
    counts per bucket). This is what makes the joint distribution
    data-driven: bucket edges come directly from the empirical
    distribution of each factor, and co-occurrence across factors
    in the same historical rows is what encodes their correlation.

    Returns integer bin indices in [0, k-1].
    """

    values = series.to_numpy(dtype=float)

    edges = np.quantile(values, np.linspace(0, 1, k + 1))

    # Guard against degenerate (constant / near-constant) series,
    # which would otherwise produce duplicate edges and break
    # np.digitize. Widen edges slightly and de-duplicate.
    edges = np.unique(edges)

    if len(edges) < 2:
        # Completely constant series: everything falls in bin 0.
        return np.zeros(len(values), dtype=int)

    edges[0] -= 1e-9
    edges[-1] += 1e-9

    idx = np.digitize(values, edges) - 1
    idx = np.clip(idx, 0, k - 1)

    return idx


def build_joint_distribution(factor_frame, factor_names, bins_per_factor):
    """
    Build the empirical joint probability table over the given
    factors, using historical co-occurrence to encode correlation.

    Returns:
        pmf         : 1-D array of length bins_per_factor**len(factor_names),
                      the flattened joint probability mass function.
        bin_edges   : dict factor_name -> array of quantile edges,
                      needed later to map bin indices back to real
                      values (e.g. price return ranges).
        bin_indices : dict factor_name -> integer array of per-row
                      bin assignments (useful for diagnostics/tests).
    """

    n_factors = len(factor_names)
    dim = bins_per_factor ** n_factors

    bin_indices = {}
    bin_edges = {}

    for name in factor_names:
        series = factor_frame[name]
        bin_indices[name] = quantile_bin(series, bins_per_factor)
        edges = np.quantile(series.to_numpy(dtype=float),
                             np.linspace(0, 1, bins_per_factor + 1))
        bin_edges[name] = edges

    n_rows = len(factor_frame)

    joint_index = np.zeros(n_rows, dtype=np.int64)

    # Mixed-radix encoding: factor 0 is the most significant digit.
    # This ordering is arbitrary but must stay consistent between
    # encoding here and decoding in the circuit / marginalization step.
    for name in factor_names:
        joint_index = joint_index * bins_per_factor + bin_indices[name]

    pmf = np.bincount(joint_index, minlength=dim).astype(float)

    if pmf.sum() == 0:
        # Should not happen with real data, but guard anyway.
        pmf = np.ones(dim)

    pmf /= pmf.sum()

    return pmf, bin_edges, bin_indices


# ============================================================
# ADAPTIVE RESOLUTION SELECTION
# ============================================================

def choose_resolution(n_rows, macro_ok, shots):
    """
    Decide qubits-per-factor and which factors are active.

    Upgrades from 2 to 3 qubits/factor only when:
      - enough history exists to trust the correlation estimate
      - shots are high enough that the extra bins won't be mostly
        empty noise

    Falls back to 3-factor mode (dropping macro) if macro data is
    unavailable, rather than fabricating a macro signal.

    Always respects MAX_TOTAL_QUBITS as a hard ceiling.
    """

    active_factors = list(FACTOR_NAMES) if macro_ok else \
        [f for f in FACTOR_NAMES if f != "macro"]

    n_factors = len(active_factors)

    qubits_per_factor = DEFAULT_QUBITS_PER_FACTOR

    can_upgrade = (
        n_rows >= MIN_ROWS_FOR_UPGRADE
        and shots >= MIN_SHOTS_FOR_UPGRADE
    )

    if can_upgrade:
        candidate = UPGRADED_QUBITS_PER_FACTOR
        if candidate * n_factors <= MAX_TOTAL_QUBITS:
            qubits_per_factor = candidate

    total_qubits = qubits_per_factor * n_factors

    # Absolute safety net: if somehow still over the ceiling
    # (shouldn't happen given the checks above), force back down
    # to the default resolution.
    if total_qubits > MAX_TOTAL_QUBITS:
        qubits_per_factor = DEFAULT_QUBITS_PER_FACTOR
        total_qubits = qubits_per_factor * n_factors

    resolution_note = "upgraded" if qubits_per_factor == UPGRADED_QUBITS_PER_FACTOR else "default"

    return active_factors, qubits_per_factor, total_qubits, resolution_note


# ============================================================
# QUANTUM JOINT CIRCUIT
# ============================================================

def run_joint_circuit(pmf, total_qubits, shots):
    """
    Encode the empirical joint pmf as amplitudes on a single dense
    statevector spanning all factor registers combined, then
    measure. Because arbitrary correlation structure (as opposed
    to e.g. simple pairwise linear coupling) generally cannot be
    written as a short sequence of two-qubit gates, we use
    `initialize` on the full joint amplitude vector. The resulting
    circuit is genuinely entangled across factor registers whenever
    the historical data shows correlation (i.e. the joint pmf does
    not factor into independent per-factor marginals) — measuring
    any one register's qubits then depends statistically on the
    others, which is the defining signature of entanglement in the
    classical-outcome (measured) sense.

    Returns raw counts dict: bitstring -> count.
    """

    amplitudes = np.sqrt(pmf)
    amplitudes = amplitudes / np.linalg.norm(amplitudes)

    circuit = QuantumCircuit(total_qubits)
    circuit.initialize(amplitudes, range(total_qubits))
    circuit.measure_all()

    simulator = AerSimulator(method="matrix_product_state")

    result = simulator.run(circuit, shots=shots).result()

    return result.get_counts()


def counts_to_joint_pmf(counts, total_qubits, shots):
    """
    Convert Qiskit measurement counts into a dense joint pmf array
    indexed the same way as build_joint_distribution's output.

    VERIFIED EMPIRICALLY (see test harness in development): when a
    statevector is loaded via circuit.initialize(amplitudes, range(n)),
    the amplitude at array index i lands on the computational basis
    state whose bitstring, read directly with int(bitstring, 2),
    equals i. No bit-reversal is needed to recover the original
    joint_index used when building the pmf in
    build_joint_distribution. (An earlier version of this function
    incorrectly reversed the bitstring based on a plausible-sounding
    but unverified assumption; a direct round-trip test caught and
    corrected this before use.)
    """

    dim = 2 ** total_qubits
    pmf = np.zeros(dim)

    for bitstring, count in counts.items():
        index = int(bitstring, 2)
        if index < dim:
            pmf[index] += count

    total = pmf.sum()

    if total == 0:
        return np.ones(dim) / dim

    return pmf / total


# ============================================================
# MARGINALS AND CONDITIONALS
# ============================================================

def reshape_joint(pmf, n_factors, bins_per_factor):
    """Reshape flat pmf into an n_factors-dimensional array, axis
    order matching factor_names order used at construction time
    (factor 0 = axis 0, most significant)."""
    return pmf.reshape([bins_per_factor] * n_factors)


def marginal_for_factor(joint_nd, factor_index):
    """Sum out all axes except factor_index to get that factor's
    marginal distribution over its own bins."""
    axes = tuple(i for i in range(joint_nd.ndim) if i != factor_index)
    return joint_nd.sum(axis=axes)


def conditional_distribution(joint_nd, factor_index, target_factor_index, bin_selector):
    """
    P(target_factor bins | factor_index is in bin_selector).

    bin_selector: a boolean array or list of bin indices for
    `factor_index` defining the conditioning event (e.g. "top bin"
    for high volatility).

    Returns a 1-D array over target_factor's bins, normalized to
    sum to 1 (or None if the conditioning event has ~zero mass).
    """

    n_factors = joint_nd.ndim

    # Build a boolean mask selecting the conditioning slice.
    slicer = [slice(None)] * n_factors
    slicer[factor_index] = bin_selector
    sliced = joint_nd[tuple(slicer)]

    # Sum out everything except the target factor.
    axes = tuple(
        i for i in range(sliced.ndim)
        if i != (target_factor_index if target_factor_index < factor_index
                  else target_factor_index)
    )

    # Careful: after fancy-indexing with a list on `factor_index`,
    # numpy keeps that axis in place (advanced indexing with a list
    # preserves dimensionality here since bin_selector is 1-D list),
    # so axis positions are unchanged. Sum all axes except target.
    sum_axes = tuple(i for i in range(sliced.ndim) if i != target_factor_index)
    target_marginal = sliced.sum(axis=sum_axes)

    total_mass = target_marginal.sum()

    if total_mass <= 1e-12:
        return None

    return target_marginal / total_mass


def probability_of_event(joint_nd, factor_index, bin_selector):
    """Total probability mass where `factor_index` falls in the
    bins listed in bin_selector (marginal event probability)."""
    axes = tuple(i for i in range(joint_nd.ndim) if i != factor_index)
    marg = joint_nd.sum(axis=axes)
    return float(marg[bin_selector].sum())


# ============================================================
# PRICE-BIN <-> DOLLAR-PRICE MAPPING
# ============================================================

def price_bin_edges_to_dollar_grid(
    price_return_edges, starting_price, bins_per_factor,
    days, expected_return, daily_volatility,
):
    """
    Convert the quantile edges of the historical DAILY price_return
    factor into an actual dollar price grid for the requested
    forecast horizon.

    IMPORTANT: the joint distribution is built from daily returns
    (so the empirical correlation structure is estimated on daily
    co-movement, which is the data we actually have day by day).
    But daily-return bins are the wrong scale to evaluate at a
    30/60/90-day horizon directly -- e.g. a "+5%" daily-return bin
    edge does not mean "+5% over 30 days". Conflating the two was
    caught during testing (all drop/upside probabilities were
    silently coming out as 0 or degenerate at longer horizons).

    Fix: use the bins' RANK/SHAPE (their relative position and the
    correlation structure they encode) from the empirical daily
    distribution, but rescale the numeric return values to the
    requested horizon using the same convention already used
    elsewhere in this codebase (quantum_engine.create_price_distribution):
    the horizon spread scales with sqrt(days/252) off of annualized
    volatility, and the horizon drift is the `expected_return` already
    computed classically for that horizon. This keeps one source of
    truth for "how far can price move in `days` days" (the classical
    calculation) while still using the joint/empirical model for
    *shape and correlation*, which is what the quantum joint step is
    actually for.
    """

    mids = (price_return_edges[:-1] + price_return_edges[1:]) / 2.0

    # Standardize daily-bin midpoints into z-like ranks (mean 0, unit
    # spread) using the empirical daily distribution's own spread,
    # then re-express them at the target horizon's drift/spread.
    daily_std = float(np.std(mids))
    if daily_std <= 1e-12:
        daily_std = 1e-6

    standardized = mids / daily_std

    annual_volatility = daily_volatility * np.sqrt(252)
    horizon_movement = annual_volatility * np.sqrt(max(days, 1) / 252)
    horizon_movement = np.clip(horizon_movement, .03, .40)

    horizon_returns = expected_return + standardized * horizon_movement

    price_grid = starting_price * (1 + horizon_returns)
    return_grid = horizon_returns

    return price_grid, return_grid


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def quantum_joint_forecast(
    market_data,
    starting_price,
    days=30,
    shots=1500,
    spy_data=None,
    sector_data=None,
    external_features=None,
):
    """
    Joint multi-factor quantum forecast.

    Builds a genuinely entangled joint distribution over
    (price_return, volatility, momentum, macro) from real
    historical correlations, samples it via a quantum circuit,
    and returns both the marginal price forecast (compatible
    with the existing single-factor output shape where possible)
    and new conditional-probability outputs that the single-factor
    pipeline cannot produce.

    Falls back gracefully (reduced resolution, or 3-factor mode
    without macro) rather than crashing, and always reports what
    it actually did in `model_metadata` / `resolution_note` /
    `active_factors` so the UI can be honest about it.
    """

    # Local import to avoid a hard circular dependency at module
    # load time; quantum_engine.py has no dependency on this module.
    import quantum_engine as qe

    frame, macro_ok = build_factor_frame(market_data, spy_data, sector_data)

    if len(frame) < 30:
        raise ValueError(
            "Not enough overlapping factor history to build a joint "
            "distribution (need at least 30 aligned rows)."
        )

    active_factors, qubits_per_factor, total_qubits, resolution_note = choose_resolution(
        n_rows=len(frame), macro_ok=macro_ok, shots=shots
    )

    bins_per_factor = 2 ** qubits_per_factor

    pmf, bin_edges, bin_indices = build_joint_distribution(
        frame, active_factors, bins_per_factor
    )

    fallback_used = False

    try:
        counts = run_joint_circuit(pmf, total_qubits, shots)
        joint_pmf = counts_to_joint_pmf(counts, total_qubits, shots)
    except Exception:
        # Hard fallback: if circuit execution fails for any reason
        # (e.g. transient simulator issue), fall back to the exact
        # classical joint pmf rather than crashing the app. This is
        # reported, not hidden.
        joint_pmf = pmf.copy()
        fallback_used = True

    joint_nd = reshape_joint(joint_pmf, len(active_factors), bins_per_factor)

    price_idx = active_factors.index("price_return")
    price_marginal = marginal_for_factor(joint_nd, price_idx)

    # --------------------------------------------------------
    # Reuse classical helpers for expected return, risk, and
    # confidence, but drive the price probability SHAPE from the
    # genuinely joint/entangled marginal rather than a
    # single-factor Gaussian resample. The numeric SCALE of the
    # return grid must match the requested horizon (see
    # price_bin_edges_to_dollar_grid docstring for why this can't
    # just use the raw daily-return bin edges).
    # --------------------------------------------------------

    returns_series = frame["price_return"]

    market_state, weights, technical_signal = qe.calculate_market_state(
        market_data["Close"], external_features
    )

    expected_return = qe.calculate_expected_return(returns_series, market_state, days)

    classical_expected_price = starting_price * np.exp(expected_return)

    daily_volatility = float(returns_series.std())
    if daily_volatility <= 0:
        daily_volatility = .01
    annual_volatility = daily_volatility * np.sqrt(252)

    price_grid, return_grid = price_bin_edges_to_dollar_grid(
        bin_edges["price_return"], starting_price, bins_per_factor,
        days, expected_return, daily_volatility,
    )

    joint_expected_price = float(np.sum(price_grid * price_marginal))

    confidence_score = qe.calculate_confidence(
        price_marginal, bins_per_factor, annual_volatility, market_state
    )

    risk_score, downside = qe.calculate_risk(price_marginal, return_grid, annual_volatility)

    upside_probability = float(np.clip(price_marginal[return_grid > .05].sum() * 100, 0, 95))
    downside_probability = float(np.clip(price_marginal[return_grid < -.05].sum() * 100, 0, 95))
    neutral_probability = float(np.clip(100 - upside_probability - downside_probability, 5, 95))

    if market_state > .08:
        regime = "Bullish"
    elif market_state < -.08:
        regime = "Bearish"
    else:
        regime = "Neutral"

    # --------------------------------------------------------
    # Genuine conditional outputs (not available in the
    # single-factor pipeline): condition price on the TOP bin
    # (highest values) of each other active factor.
    # --------------------------------------------------------

    conditionals = {}

    for factor in active_factors:
        if factor == "price_return":
            continue
        f_idx = active_factors.index(factor)
        top_bin = [bins_per_factor - 1]
        bottom_bin = [0]

        cond_high = conditional_distribution(joint_nd, f_idx, price_idx, top_bin)
        cond_low = conditional_distribution(joint_nd, f_idx, price_idx, bottom_bin)

        conditionals[factor] = {
            "p_drop_given_high": (
                float(cond_high[return_grid < -.05].sum()) if cond_high is not None else None
            ),
            "p_drop_given_low": (
                float(cond_low[return_grid < -.05].sum()) if cond_low is not None else None
            ),
            "p_drop_unconditional": float(price_marginal[return_grid < -.05].sum()),
        }

    metadata = {
        "weights": {k: round(v * 100, 2) for k, v in weights.items()},
        "technical_signal": round(float(technical_signal), 4),
        "market_state": round(float(market_state), 4),
        "active_factors": active_factors,
        "qubits_per_factor": qubits_per_factor,
        "total_qubits": total_qubits,
        "resolution": resolution_note,
        "macro_available": macro_ok,
        "fallback_to_classical": fallback_used,
        "history_rows_used": len(frame),
        "note": (
            "Joint distribution is an empirical (quantile-binned) "
            "encoding of real historical correlations between "
            "price return, volatility, momentum, and macro/sector "
            "tilt. The quantum circuit reproduces this distribution "
            "via entangled amplitude encoding and shot-based "
            "measurement; it does not add information beyond what "
            "the historical correlation structure already contains."
        ),
    }

    return {
        "starting_price": starting_price,
        "classical_expected_price": classical_expected_price,
        "expected_price": joint_expected_price,
        "price_grid": price_grid,
        "return_grid": return_grid,
        "probability": price_marginal,
        "joint_probability": joint_pmf,
        "joint_shape": [bins_per_factor] * len(active_factors),
        "bin_edges": bin_edges,
        "returns": returns_series,
        "volatility": annual_volatility * 100,
        "market_regime": regime,
        "confidence_score": confidence_score,
        "risk_score": risk_score,
        "market_state": market_state,
        "upside_probability": upside_probability,
        "downside_probability": downside_probability,
        "neutral_probability": neutral_probability,
        "conditionals": conditionals,
        "model_metadata": metadata,
    }
