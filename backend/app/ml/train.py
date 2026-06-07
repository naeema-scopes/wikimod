"""Toxicity classifier training script.

This is a ONE-TIME developer operation, not run by end users or in production.

Training modes:
1. Full Jigsaw dataset: Download from Kaggle (see README for instructions)
2. Synthetic dataset: For development/demo purposes

Production would use the full Jigsaw Toxic Comment Classification dataset.
The synthetic dataset is sufficient for demonstrating the architecture.

Usage:
    python -m app.ml.train [--synthetic] [--data-path PATH]
"""

import argparse
import json
import random
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def generate_synthetic_dataset(n_per_class: int = 500) -> tuple[list[str], list[int]]:
    """Generate a synthetic training dataset for demo purposes.

    NOTE: Production should use the full Jigsaw Toxic Comment Classification dataset.
    This synthetic data is only suitable for demonstrating the pipeline architecture.
    """
    toxic_templates = [
        "you are such an {insult}",
        "shut up you {insult}",
        "what a {insult} you are",
        "you're the worst {insult} ever",
        "go away you stupid {insult}",
        "nobody likes you, {insult}",
        "you are a complete {insult}",
        "this is garbage written by an {insult}",
        "stop being such a {insult}",
        "I hate everything about your {insult} contribution",
        "your edit is trash, you {insult}",
        "you don't know anything, {insult}",
        "that's the dumbest thing I've ever read",
        "are you even literate you {insult}",
        "you should be banned for this garbage",
        "delete this nonsense immediately",
        "this article is complete crap",
        "whoever wrote this is an {insult}",
        "you're clearly too stupid to understand",
        "what kind of {insult} writes this",
        "kill yourself",
        "die in a fire",
        "you ugly piece of trash",
        "f*** off and never come back",
        "your mother should be ashamed",
        "you're a worthless piece of garbage",
        "this is the most idiotic thing ever written",
        "you are a pathetic excuse for an editor",
        "get the hell out of here",
        "nobody wants your stupid opinion",
    ]

    insults = [
        "idiot", "moron", "fool", "imbecile", "jerk", "loser",
        "troll", "vandal", "clown", "dimwit", "ignoramus",
    ]

    clean_templates = [
        "thank you for your {adj} contribution to this article",
        "I appreciate you taking the time to {verb} this section",
        "could you please provide a {noun} for that claim",
        "I think we should consider {verb_ing} the introduction",
        "great work on {verb_ing} the references",
        "this is a {adj} improvement to the article",
        "I agree with your {adj} analysis of this topic",
        "perhaps we could {verb} this for clarity",
        "welcome to the discussion, your input is {adj}",
        "the article has improved {adv} since the last edit",
        "I'd like to suggest a {adj} alternative approach",
        "let me add some {adj} sources to support this",
        "good point about the need for {adj} citations",
        "this section could benefit from {adj} restructuring",
        "I have a {adj} suggestion for improving this paragraph",
        "your recent edits have been very {adj}",
        "could we reach a consensus on this {adj} issue",
        "I respect your opinion but have a {adj} perspective",
        "let's work together to make this article {adj}",
        "I found a {adj} reference that supports this claim",
        "the formatting looks much {adj} now",
        "nice job organizing the {noun} section",
        "I've reviewed the changes and they look {adj}",
        "would you mind explaining your {adj} reasoning",
        "this is a well-researched and {adj} contribution",
    ]

    adj = ["helpful", "excellent", "thoughtful", "valuable", "constructive",
           "insightful", "balanced", "well-written", "comprehensive", "clear"]
    verb = ["improve", "expand", "reorganize", "update", "clarify", "review", "revise"]
    verb_ing = ["improving", "expanding", "reorganizing", "updating", "clarifying", "revising"]
    noun = ["source", "citation", "reference", "evidence", "explanation"]
    adv = ["significantly", "greatly", "noticeably", "considerably"]

    random.seed(42)
    texts = []
    labels = []

    for _ in range(n_per_class):
        template = random.choice(toxic_templates)
        text = template.replace("{insult}", random.choice(insults))
        texts.append(text)
        labels.append(1)

    for _ in range(n_per_class):
        template = random.choice(clean_templates)
        text = (
            template
            .replace("{adj}", random.choice(adj))
            .replace("{verb}", random.choice(verb))
            .replace("{verb_ing}", random.choice(verb_ing))
            .replace("{noun}", random.choice(noun))
            .replace("{adv}", random.choice(adv))
        )
        texts.append(text)
        labels.append(0)

    return texts, labels


def train_model(
    texts: list[str],
    labels: list[int],
    output_dir: Path,
) -> dict:
    """Train a logistic regression toxicity classifier.

    Args:
        texts: Training text samples.
        labels: Binary labels (1=toxic, 0=clean).
        output_dir: Directory to save model artifacts.

    Returns:
        Dictionary of evaluation metrics.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    print(f"Toxic ratio (train): {sum(y_train) / len(y_train):.2%}")

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # Train logistic regression
    model = LogisticRegression(
        max_iter=1000,
        C=1.0,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(X_train_tfidf, y_train)

    # Evaluate
    y_pred = model.predict(X_test_tfidf)
    accuracy = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred).tolist()

    report = classification_report(y_test, y_pred, target_names=["clean", "toxic"], output_dict=True)

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
        "training_samples": len(texts),
        "note": "Trained on synthetic data for demo purposes. Production should use the full Jigsaw dataset.",
    }

    print(f"\nAccuracy: {accuracy:.4f}")
    print(f"Weighted F1: {metrics['weighted_f1']:.4f}")
    print(f"Toxic class - P: {metrics['precision_toxic']:.4f}, R: {metrics['recall_toxic']:.4f}, F1: {metrics['f1_toxic']:.4f}")
    print(f"Clean class - P: {metrics['precision_clean']:.4f}, R: {metrics['recall_clean']:.4f}, F1: {metrics['f1_clean']:.4f}")
    print(f"Confusion Matrix:\n{np.array(cm)}")

    # Save artifacts
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "model.pkl"
    vectorizer_path = output_dir / "vectorizer.pkl"
    metrics_path = output_dir / "metrics.json"

    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nModel saved to {model_path}")
    print(f"Vectorizer saved to {vectorizer_path}")
    print(f"Metrics saved to {metrics_path}")

    return metrics


def train_from_jigsaw(data_path: Path, output_dir: Path) -> dict:
    """Train from the Jigsaw Toxic Comment Classification dataset.

    The dataset has six toxicity labels: toxic, severe_toxic, obscene,
    threat, insult, identity_hate. We collapse them into a single binary
    label: toxic if ANY of the six labels is 1.
    """
    try:
        import pandas as pd
    except ImportError:
        print("pandas is required for Jigsaw dataset training. Install with: pip install pandas")
        sys.exit(1)

    train_csv = data_path / "train.csv"
    if not train_csv.exists():
        print(f"Jigsaw dataset not found at {train_csv}")
        print("See README for download instructions.")
        sys.exit(1)

    print(f"Loading Jigsaw dataset from {train_csv}...")
    df = pd.read_csv(train_csv)

    toxicity_cols = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
    df["is_toxic"] = df[toxicity_cols].max(axis=1)

    texts = df["comment_text"].tolist()
    labels = df["is_toxic"].tolist()

    print(f"Total samples: {len(texts)}")
    print(f"Toxic: {sum(labels)} ({sum(labels)/len(labels):.2%})")
    print(f"Clean: {len(labels) - sum(labels)} ({(len(labels)-sum(labels))/len(labels):.2%})")

    return train_model(texts, labels, output_dir)


def main():
    parser = argparse.ArgumentParser(description="Train WikiMod toxicity classifier")
    parser.add_argument(
        "--synthetic", action="store_true",
        help="Use synthetic training data instead of Jigsaw dataset"
    )
    parser.add_argument(
        "--data-path", type=Path, default=Path(__file__).parent.parent.parent / "data",
        help="Path to Jigsaw dataset directory"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).parent,
        help="Directory to save model artifacts"
    )
    parser.add_argument(
        "--n-samples", type=int, default=500,
        help="Number of samples per class for synthetic data"
    )
    args = parser.parse_args()

    if args.synthetic:
        print("Training with synthetic dataset...")
        texts, labels = generate_synthetic_dataset(args.n_samples)
        train_model(texts, labels, args.output_dir)
    else:
        train_from_jigsaw(args.data_path, args.output_dir)


if __name__ == "__main__":
    main()
