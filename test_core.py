import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

import prediction_memory as memory
from quantum_joint_engine import quantum_joint_forecast


class PredictionMemoryTests(unittest.TestCase):
    def test_prediction_is_not_settled_before_its_horizon(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(memory, "MEMORY_FILE", Path(directory) / "memory.json"):
            identifier = memory.store_prediction(
                "MSFT", 2, 100, 105, created_at=datetime(2026, 7, 22, tzinfo=timezone.utc)
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


if __name__ == "__main__":
    unittest.main()
