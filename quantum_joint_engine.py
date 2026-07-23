# ============================================================
# QUANTUM_JOINT_ENGINE.PY
# Quantum Equity Forecast Engine — Joint Multi-Factor Extension
# ============================================================
import numpy as np
import pandas as pd

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

MAX_TOTAL_QUBITS = 12
DEFAULT_QUBITS_PER_FACTOR = 2
UPGRADED_QUBITS_PER_FACTOR = 3
MIN_ROWS_FOR_UPGRADE = 252
MIN_SHOTS_FOR_UPGRADE = 2000
FACTOR_NAMES = ["price_return", "volatility", "momentum", "macro"]

def build_factor_frame(market_data, spy_data=None, sector_data=None):
    df = market_data.copy()
    if "Date" not in df.columns:
        raise ValueError("market_data must have a 'Date' column to align macro factor data.")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna(subset=["Date", "Close"]).drop_duplicates("Date").sort_values("Date").reset_index(drop=True)
    if len(df) < 30:
        raise ValueError("market_data needs at least 30 valid dated closing prices.")
    close = df["Close"].astype(float)
    price_return = close.pct_change()
    volatility = price_return.rolling(30, min_periods=10).std()
    momentum = (close / close.shift(20) - 1)
    
    macro = combine_macro_proxy(df["Date"], spy_data, sector_data)
    macro.index = df.index
    macro_ok = macro.notna().any()
    
    frame = pd.DataFrame({
        "price_return": price_return, "volatility": volatility, "momentum": momentum, "macro": macro,
    }, index=df.index)
    
    if macro_ok:
        frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
    else:
        core = frame[["price_return", "volatility", "momentum"]].replace([np.inf, -np.inf], np.nan).dropna()
        frame = frame.loc[core.index]
    return frame, macro_ok

def combine_macro_proxy(date_column, spy_data, sector_data):
    target_dates = pd.to_datetime(pd.Series(date_column).reset_index(drop=True), errors="coerce")
    spy_ret, sector_ret = None, None
    def aligned_returns(data):
        if data is None or data.empty or not {"Close", "Date"}.issubset(data.columns):
            return None
        series = data[["Date", "Close"]].copy()
        series["Date"] = pd.to_datetime(series["Date"], errors="coerce")
        series["Close"] = pd.to_numeric(series["Close"], errors="coerce")
        series = series.dropna().drop_duplicates("Date").sort_values("Date")
        if len(series) < 2:
            return None
        indexed = series.set_index("Date")["Close"].pct_change()
        # Forward fill uses only information available on or before each asset
        # date; nearest-neighbour alignment can leak future market returns.
        return indexed.reindex(target_dates, method="ffill").reset_index(drop=True)

    if spy_data is not None and not spy_data.empty and "Close" in spy_data.columns and "Date" in spy_data.columns:
        spy_ret = aligned_returns(spy_data)
    if sector_data is not None and not sector_data.empty and "Close" in sector_data.columns and "Date" in sector_data.columns:
        sector_ret = aligned_returns(sector_data)
    if spy_ret is not None and sector_ret is not None:
        combined = pd.concat([spy_ret, sector_ret], axis=1)
        combined.columns = ["spy", "sector"]
        return combined.mean(axis=1, skipna=True)
    if spy_ret is not None: return spy_ret
    if sector_ret is not None: return sector_ret
    return pd.Series(np.nan, index=range(len(target_dates)))

def quantile_bin(series, k):
    values = series.to_numpy(dtype=float)
    edges = np.unique(np.quantile(values, np.linspace(0, 1, k + 1)))
    if len(edges) < 2: return np.zeros(len(values), dtype=int)
    edges[0] -= 1e-9
    edges[-1] += 1e-9
    return np.clip(np.digitize(values, edges) - 1, 0, k - 1)

def build_joint_distribution(factor_frame, factor_names, bins_per_factor):
    dim = bins_per_factor ** len(factor_names)
    bin_indices, bin_edges = {}, {}
    for name in factor_names:
        series = factor_frame[name]
        bin_indices[name] = quantile_bin(series, bins_per_factor)
        bin_edges[name] = np.quantile(series.to_numpy(dtype=float), np.linspace(0, 1, bins_per_factor + 1))
    joint_index = np.zeros(len(factor_frame), dtype=np.int64)
    for name in factor_names:
        joint_index = joint_index * bins_per_factor + bin_indices[name]
    pmf = np.bincount(joint_index, minlength=dim).astype(float)
    if pmf.sum() == 0: pmf = np.ones(dim)
    return pmf / pmf.sum(), bin_edges, bin_indices

def choose_resolution(n_rows, macro_ok, shots):
    active_factors = list(FACTOR_NAMES) if macro_ok else [f for f in FACTOR_NAMES if f != "macro"]
    qubits_per_factor = DEFAULT_QUBITS_PER_FACTOR
    if n_rows >= MIN_ROWS_FOR_UPGRADE and shots >= MIN_SHOTS_FOR_UPGRADE:
        if UPGRADED_QUBITS_PER_FACTOR * len(active_factors) <= MAX_TOTAL_QUBITS:
            qubits_per_factor = UPGRADED_QUBITS_PER_FACTOR
    total_qubits = qubits_per_factor * len(active_factors)
    return active_factors, qubits_per_factor, total_qubits, ("upgraded" if qubits_per_factor == UPGRADED_QUBITS_PER_FACTOR else "default")

def classical_joint_sampling(pmf, total_qubits, shots, seed=None):
    dim = len(pmf)
    sampled = np.random.default_rng(seed).choice(np.arange(dim), size=shots, p=pmf)
    counts = {}
    for idx in sampled:
        bitstr = format(idx, f"0{total_qubits}b")
        counts[bitstr] = counts.get(bitstr, 0) + 1
    return counts

def run_joint_circuit(pmf, total_qubits, shots, seed=None):
    if not QISKIT_AVAILABLE:
        return classical_joint_sampling(pmf, total_qubits, shots, seed), True
    try:
        amplitudes = np.sqrt(pmf)
        amplitudes = amplitudes / np.linalg.norm(amplitudes)
        circuit = QuantumCircuit(total_qubits)
        circuit.initialize(amplitudes, range(total_qubits))
        circuit.measure_all()
        simulator = AerSimulator(seed_simulator=seed)
        return simulator.run(circuit, shots=shots).result().get_counts(), False
    except Exception as e:
        print("Fallback triggered. Circuit error:", e)
        return classical_joint_sampling(pmf, total_qubits, shots, seed), True

def counts_to_joint_pmf(counts, total_qubits, shots):
    dim = 2 ** total_qubits
    pmf = np.zeros(dim)
    for bitstring, count in counts.items():
        idx = int(bitstring, 2)
        if idx < dim: pmf[idx] += count
    return pmf / (pmf.sum() + 1e-15)

def reshape_joint(pmf, n_factors, bins_per_factor):
    return pmf.reshape([bins_per_factor] * n_factors)

def marginal_for_factor(joint_nd, factor_index):
    axes = tuple(i for i in range(joint_nd.ndim) if i != factor_index)
    return joint_nd.sum(axis=axes)

def conditional_distribution(joint_nd, factor_index, target_factor_index, bin_selector):
    slicer = [slice(None)] * joint_nd.ndim
    slicer[factor_index] = bin_selector
    sliced = joint_nd[tuple(slicer)]
    # Slicing a preceding factor removes one axis, so the target axis shifts.
    reduced_target_index = target_factor_index - int(factor_index < target_factor_index)
    sum_axes = tuple(i for i in range(sliced.ndim) if i != reduced_target_index)
    target_marginal = sliced.sum(axis=sum_axes)
    total_mass = target_marginal.sum()
    return None if total_mass <= 1e-12 else target_marginal / total_mass

def price_bin_edges_to_dollar_grid(price_return_edges, starting_price, bins_per_factor, days, expected_return, daily_volatility):
    mids = (price_return_edges[:-1] + price_return_edges[1:]) / 2.0
    daily_std = float(np.std(mids))
    standardized = (mids - float(np.mean(mids))) / daily_std if daily_std > 1e-12 else np.zeros_like(mids)
    # A one-day 3% minimum distorted the distribution for low-volatility
    # equities.  Use the observed horizon volatility instead, with only a
    # numerical floor to preserve a valid grid for near-constant series.
    horizon_movement = max(float(daily_volatility) * np.sqrt(max(int(days), 1)), 1e-6)
    return_grid = expected_return + standardized * horizon_movement
    return float(starting_price) * np.exp(return_grid), return_grid

def calculate_entanglement_entropy(pmf, qubits_per_factor, n_factors):
    amplitudes = np.sqrt(pmf)
    amplitudes /= (np.linalg.norm(amplitudes) + 1e-15)
    dim_A, dim_B = 2 ** qubits_per_factor, 2 ** (qubits_per_factor * (n_factors - 1))
    try:
        U, s, Vt = np.linalg.svd(amplitudes.reshape(dim_A, dim_B))
        lambdas = s[s > 1e-15] ** 2
        entropy = -np.sum(lambdas * np.log2(lambdas))
        max_entropy = np.log2(dim_A)
        norm_ent = (entropy / max_entropy) * 100 if max_entropy > 0 else 0.0
    except: entropy, norm_ent = 0.0, 0.0
    return float(entropy), float(norm_ent)

def quantum_joint_forecast(market_data, starting_price, days=30, shots=1500, spy_data=None, sector_data=None, external_features=None, seed=None):
    import quantum_engine as qe
    frame, macro_ok = build_factor_frame(market_data, spy_data, sector_data)
    if len(frame) < 30:
        raise ValueError("Not enough overlapping factor history to build a joint distribution (need at least 30 aligned rows).")
    
    active_factors, qubits_per_factor, total_qubits, res_note = choose_resolution(len(frame), macro_ok, shots)
    bins_per_factor = 2 ** qubits_per_factor
    pmf, bin_edges, bin_indices = build_joint_distribution(frame, active_factors, bins_per_factor)
    
    if not np.isfinite(float(starting_price)) or float(starting_price) <= 0:
        raise ValueError("starting_price must be a finite positive number.")
    if int(days) < 1 or int(shots) < 1:
        raise ValueError("days and shots must be positive integers.")
    counts, fallback_used = run_joint_circuit(pmf, total_qubits, int(shots), seed)
    joint_pmf = counts_to_joint_pmf(counts, total_qubits, shots)
    joint_nd = reshape_joint(joint_pmf, len(active_factors), bins_per_factor)
    
    price_idx = active_factors.index("price_return")
    price_marginal = marginal_for_factor(joint_nd, price_idx)
    returns_series = frame["price_return"]
    
    market_state, weights, tech_signal = qe.calculate_market_state(market_data["Close"], external_features)
    expected_return = qe.calculate_expected_return(returns_series, market_state, days)
    classical_expected_price = starting_price * np.exp(expected_return)
    
    daily_volatility = float(returns_series.std(ddof=1)) if len(returns_series) > 1 else 0.01
    daily_volatility = daily_volatility if np.isfinite(daily_volatility) and daily_volatility > 0 else 0.01
    annual_volatility = daily_volatility * np.sqrt(252)
    
    price_grid, return_grid = price_bin_edges_to_dollar_grid(bin_edges["price_return"], starting_price, bins_per_factor, days, expected_return, daily_volatility)
    joint_expected_price = float(np.sum(price_grid * price_marginal))
    
    confidence_score = qe.calculate_confidence(price_marginal, bins_per_factor, annual_volatility, market_state)
    risk_score, downside = qe.calculate_risk(price_marginal, return_grid, annual_volatility)
    
    upside_probability = float(np.clip(price_marginal[return_grid > .05].sum() * 100, 0, 95))
    downside_probability = float(np.clip(price_marginal[return_grid < -.05].sum() * 100, 0, 95))
    neutral_probability = float(np.clip(100 - upside_probability - downside_probability, 5, 95))
    regime = "Bullish" if market_state > .08 else ("Bearish" if market_state < -.08 else "Neutral")
    
    conditionals = {}
    for factor in active_factors:
        if factor == "price_return": continue
        f_idx = active_factors.index(factor)
        cond_high = conditional_distribution(joint_nd, f_idx, price_idx, [bins_per_factor - 1])
        cond_low = conditional_distribution(joint_nd, f_idx, price_idx, [0])
        conditionals[factor] = {
            "p_drop_given_high": float(cond_high[return_grid < -.05].sum()) if cond_high is not None else None,
            "p_drop_given_low": float(cond_low[return_grid < -.05].sum()) if cond_low is not None else None,
            "p_drop_unconditional": float(price_marginal[return_grid < -.05].sum()),
        }
    
    entropy, normalized_entanglement = calculate_entanglement_entropy(joint_pmf, qubits_per_factor, len(active_factors))
    metadata = {
        "weights": {k: round(v * 100, 2) for k, v in weights.items()},
        "technical_signal": round(float(tech_signal), 4),
        "market_state": round(float(market_state), 4),
        "active_factors": active_factors,
        "qubits_per_factor": qubits_per_factor,
        "total_qubits": total_qubits,
        "resolution": res_note,
        "macro_available": macro_ok,
        "fallback_to_classical": fallback_used,
        "history_rows_used": len(frame),
        "quantum_entropy": round(entropy, 4),
        "entanglement_score": round(normalized_entanglement, 2),
        "note": "Joint empirical correlation modeled. Entangled register states sampled to obtain outcome probabilities."
    }
    
    return {
        "starting_price": starting_price, "classical_expected_price": classical_expected_price,
        "expected_price": joint_expected_price, "price_grid": price_grid, "return_grid": return_grid,
        "probability": price_marginal, "joint_probability": joint_pmf, "joint_shape": [bins_per_factor] * len(active_factors),
        "bin_edges": bin_edges, "returns": returns_series, "volatility": annual_volatility * 100,
        "market_regime": regime, "confidence_score": confidence_score, "risk_score": risk_score,
        "market_state": market_state, "upside_probability": upside_probability,
        "downside_probability": downside_probability, "neutral_probability": neutral_probability,
        "conditionals": conditionals, "model_metadata": metadata,
    }
