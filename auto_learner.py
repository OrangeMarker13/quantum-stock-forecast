# ============================================================
# AUTO_LEARNER.PY
# Autonomous Prediction Settlement Worker
# ============================================================

from prediction_memory import complete_prediction, evaluate_predictions


def run_learning_cycle():

    predictions = evaluate_predictions()

    updated = 0

    for prediction in predictions:

        if not prediction.get("completed"):

            success = complete_prediction(
                prediction["id"]
            )

            if success:
                updated += 1

    print(f"Learning cycle complete. Updated {updated} predictions.")


if __name__ == "__main__":
    run_learning_cycle()
