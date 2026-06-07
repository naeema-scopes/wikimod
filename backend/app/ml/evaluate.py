"""Model evaluation script.

Loads a trained model and evaluates it, printing metrics and saving to metrics.json.

Usage:
    python -m app.ml.evaluate [--model-dir PATH]
"""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from app.ml.train import generate_synthetic_dataset


def evaluate_model(model_dir: Path) -> dict:
    """Load and evaluate the trained model."""
    model_path = model_dir / "model.pkl"
    vectorizer_path = model_dir / "vectorizer.pkl"

    if not model_path.exists() or not vectorizer_path.exists():
        print(f"Model artifacts not found in {model_dir}")
        print("Run training first: python -m app.ml.train --synthetic")
        return {}

    print(f"Loading model from {model_path}")
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    # Generate evaluation data (different seed for test variety)
    texts, labels = generate_synthetic_dataset(200)

    X = vectorizer.transform(texts)
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]

    accuracy = accuracy_score(labels, y_pred)
    cm = confusion_matrix(labels, y_pred).tolist()
    report = classification_report(labels, y_pred, target_names=["clean", "toxic"], output_dict=True)

    metrics = {
        "accuracy": round(accuracy, 4),
        "precision_toxic": round(report["toxic"]["precision"], 4),
        "recall_toxic": round(report["toxic"]["recall"], 4),
        "f1_toxic": round(report["toxic"]["f1-score"], 4),
        "precision_clean": round(report["clean"]["precision"], 4),
        "recall_clean": round(report["clean"]["recall"], 4),
        "f1_clean": round(report["clean"]["f1-score"], 4),
        "weighted_f1": round(report["weighted avg"]["f1-score"], 4),
        "confusion_matrix": cm,
        "training_samples": 1000,
        "note": "Trained on synthetic data for demo purposes. Production should use the full Jigsaw dataset.",
    }

    print(f"\nEvaluation Results:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Weighted F1: {metrics['weighted_f1']:.4f}")
    print(f"\nPer-class metrics:")
    print(f"  Toxic  - Precision: {metrics['precision_toxic']:.4f}, Recall: {metrics['recall_toxic']:.4f}, F1: {metrics['f1_toxic']:.4f}")
    print(f"  Clean  - Precision: {metrics['precision_clean']:.4f}, Recall: {metrics['recall_clean']:.4f}, F1: {metrics['f1_clean']:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"  {np.array(cm)}")

    # Save metrics
    metrics_path = model_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nMetrics saved to {metrics_path}")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate WikiMod toxicity classifier")
    parser.add_argument(
        "--model-dir", type=Path, default=Path(__file__).parent,
        help="Directory containing model artifacts"
    )
    args = parser.parse_args()
    evaluate_model(args.model_dir)


if __name__ == "__main__":
    main()
