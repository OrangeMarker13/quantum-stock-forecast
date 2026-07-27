import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

import prediction_memory as memory
from autonomous_forecaster import _in_market_window
from quantum_joint_engine import quantum_joint_forecast


class PredictionMemoryTests(unittest.TestCase):
    def test_prediction_is_not_settled_before_its_horizon(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(memory, "MEMORY_FILE", Path(directory) / "memory.json"):
            identifier = memory.store_prediction(
                "MSFT", 2, 100, 105, created_at=datetime(2026, 7, 22, 16, tzinfo=timezone.utc)
            )
            self.assertFalse(memory.complete_prediction(identifier))
            record = memory.evaluate_predictions()[0]
            self.assertEqual(record["target_date"], "2026-07-24")
            self.assertFalse(record["completed"])

    def test_due_prediction_uses_the_first_close_after_target(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(memory, "MEMORY_FILE", Path(directory) / "memory.json"):
            identifier = memory.store_prediction(
                "MSFT", 1, 100, 100, created_at=datetime(2020, 1, 1, tzinfo=timezone.utc)
            )
            self.assertTrue(memory.complete_prediction(identifier, lambda ticker, target: (110.0, date(2020, 1, 2))))
            record = memory.evaluate_predictions()[0]
            self.assertEqual(record["actual_date"], "2020-01-02")
            self.assertAlmostEqual(record["error_percent"], 0.10)

    def test_adjustment_requires_enough_local_evidence(self):
        records = [{"id": index, "error_percent": 0.02, "completed": True} for index in range(3)]
        self.assertAlmostEqual(memory.get_prediction_adjustment_advanced(records), 0.02)

    def test_same_day_close_prediction_has_an_explicit_target(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(memory, "MEMORY_FILE", Path(directory) / "memory.json"):
            identifier = memory.store_prediction(
                "AAPL", 1, 100, 101, created_at=datetime(2026, 7, 22, tzinfo=timezone.utc),
                target_date="2026-07-22", prediction_type="intraday_close"
            )
            self.assertTrue(memory.prediction_exists("AAPL", 1, "2026-07-22", "intraday_close"))
            self.assertEqual(memory.evaluate_predictions()[0]["id"], identifier)

    def test_learning_adjustment_moves_the_full_price_grid(self):
        forecast = {"starting_price": 100, "expected_price": 102, "price_grid": np.array([95, 102, 110]),
                    "probability": np.array([0.2, 0.5, 0.3])}
        adjusted = memory.apply_learning_adjustment(forecast, 0.02)
        self.assertAlmostEqual(adjusted["expected_price"], 104.04)
        self.assertTrue(np.allclose(adjusted["price_grid"], [96.9, 104.04, 112.2]))


class QuantumEngineTests(unittest.TestCase):
    def test_joint_forecast_returns_a_finite_normalized_distribution(self):
        rng = np.random.default_rng(7)
        dates = pd.date_range("2024-01-01", periods=320, freq="B")
        close = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, len(dates))))
        market = pd.DataFrame({"Date": dates, "Close": close})
        benchmark = pd.DataFrame({"Date": dates, "Close": close * 1.02})
        forecast = quantum_joint_forecast(market, close[-1], days=30, shots=500, spy_data=benchmark, seed=11)
        probabilities = np.asarray(forecast["probability"])
        self.assertTrue(np.isfinite(forecast["expected_price"]))
        self.assertAlmostEqual(float(probabilities.sum()), 1.0, places=8)
        self.assertTrue(np.all(np.asarray(forecast["price_grid"]) > 0))


class MarketScheduleTests(unittest.TestCase):
    def test_market_windows_are_eastern_business_hours(self):
        self.assertTrue(_in_market_window("open", datetime(2026, 7, 22, 9, 45)))
        self.assertTrue(_in_market_window("close", datetime(2026, 7, 22, 16, 10)))
        self.assertFalse(_in_market_window("open", datetime(2026, 7, 22, 12, 0)))


if __name__ == "__main__":
    unittest.main()
