"""Scheduled worker that settles only forecasts whose horizons have elapsed."""

from prediction_memory import settle_due_predictions


def run_learning_cycle() -> dict[str, int]:
    result = settle_due_predictions()
    print(
        "Learning cycle complete. "
        f"Checked {result['checked']}; settled {result['settled']}; "
        f"pending {result['pending']}; unavailable {result['unavailable']}."
    )
    return result


if __name__ == "__main__":
    run_learning_cycle()
