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
    target_dates = pd.to_datetime(pd.Series(date_column).reset_index(drop=True))
    spy_ret, sector_ret = None, None
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

def classical_joint_sampling(pmf, total_qubits, shots):
    dim = len(pmf)
    sampled = np.random.choice(np.arange(dim), size=shots, p=pmf)
    counts = {}
    for idx in sampled:
        bitstr = format(idx, f"0{total_qubits}b")
        counts[bitstr] = counts.get(bitstr, 0) + 1
    return counts

def run_joint_circuit(pmf, total_qubits, shots):
    if not QISKIT_AVAILABLE: return classical_joint_sampling(pmf, total_qubits, shots)
    try:
        amplitudes = np.sqrt(pmf)
        amplitudes = amplitudes / np.linalg.norm(amplitudes)
        circuit = QuantumCircuit(total_qubits)
        circuit.initialize(amplitudes, range(total_qubits))
        circuit.measure_all()
        simulator = AerSimulator()
        return simulator.run(circuit, shots=shots).result().get_counts()
    except Exception as e:
        print("Fallback triggered. Circuit error:", e)
        return classical_joint_sampling(pmf, total_qubits, shots)

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
    sum_axes = tuple(i for i in range(sliced.ndim) if i != target_factor_index)
    target_marginal = sliced.sum(axis=sum_axes)
    total_mass = target_marginal.sum()
    return None if total_mass <= 1e-12 else target_marginal / total_mass

def price_bin_edges_to_dollar_grid(price_return_edges, starting_price, bins_per_factor, days, expected_return, daily_volatility):
    mids = (price_return_edges[:-1] + price_return_edges[1:]) / 2.0
    daily_std = float(np.std(mids)) if float(np.std(mids)) > 1e-12 else 1e-6
    standardized = mids / daily_std
    horizon_movement = np.clip((daily_volatility * np.sqrt(252)) * np.sqrt(max(days, 1) / 252), 0.03, 0.40)
    return starting_price * (1 + (expected_return + standardized * horizon_movement)), (expected_return + standardized * horizon_movement)

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

def quantum_joint_forecast(market_data, starting_price, days=30, shots=1500, spy_data=None, sector_data=None, external_features=None):
    import quantum_engine as qe
    frame, macro_ok = build_factor_frame(market_data, spy_data, sector_data)
    if len(frame) < 30:
        raise ValueError("Not enough overlapping factor history to build a joint distribution (need at least 30 aligned rows).")
    
    active_factors, qubits_per_factor, total_qubits, res_note = choose_resolution(len(frame), macro_ok, shots)
    bins_per_factor = 2 ** qubits_per_factor
    pmf, bin_edges, bin_indices = build_joint_distribution(frame, active_factors, bins_per_factor)
    
    fallback_used = not QISKIT_AVAILABLE
    counts = run_joint_circuit(pmf, total_qubits, shots)
    joint_pmf = counts_to_joint_pmf(counts, total_qubits, shots)
    joint_nd = reshape_joint(joint_pmf, len(active_factors), bins_per_factor)
    
    price_idx = active_factors.index("price_return")
    price_marginal = marginal_for_factor(joint_nd, price_idx)
    returns_series = frame["price_return"]
    
    market_state, weights, tech_signal = qe.calculate_market_state(market_data["Close"], external_features)
    expected_return = qe.calculate_expected_return(returns_series, market_state, days)
    classical_expected_price = starting_price * np.exp(expected_return)
    
    daily_volatility = float(returns_series.std()) if float(returns_series.std()) > 0 else 0.01
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
        "technical_signal": round(float(technical_signal), 4),
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
