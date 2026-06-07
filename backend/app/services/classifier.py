"""Toxicity classifier with word-level attribution.

Uses a trained logistic regression model with TF-IDF features to score
comments for toxicity and identify which words contributed most to the score.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

from app.config import settings


@dataclass
class ToxicityResult:
    """Result of toxicity classification for a single comment."""

    score: float = 0.0  # 0-1 probability of toxicity
    is_toxic: bool = False  # True if score >= threshold
    trigger_words: list[str] = field(default_factory=list)


class ToxicityClassifier:
    """Toxicity classifier using scikit-learn logistic regression + TF-IDF."""

    DEFAULT_THRESHOLD = 0.5
    TOP_N_TRIGGER_WORDS = 5

    def __init__(
        self,
        model_path: Optional[Path] = None,
        vectorizer_path: Optional[Path] = None,
        threshold: float = DEFAULT_THRESHOLD,
    ):
        self.threshold = threshold
        model_path = model_path or settings.model_path
        vectorizer_path = vectorizer_path or settings.vectorizer_path

        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)

        # Cache feature names for word attribution
        self._feature_names = self.vectorizer.get_feature_names_out()
        # Model coefficients for the toxic class
        self._coefficients = self.model.coef_[0]

    def predict(self, text: str) -> ToxicityResult:
        """Score a single text for toxicity.

        Args:
            text: Comment text to classify.

        Returns:
            ToxicityResult with score, is_toxic flag, and trigger words.
        """
        if not text or not text.strip():
            return ToxicityResult(score=0.0, is_toxic=False, trigger_words=[])

        tfidf_vector = self.vectorizer.transform([text])
        proba = self.model.predict_proba(tfidf_vector)[0]
        toxic_score = float(proba[1])  # Probability of toxic class

        trigger_words = self._get_trigger_words(tfidf_vector) if toxic_score > 0.3 else []

        return ToxicityResult(
            score=round(toxic_score, 4),
            is_toxic=toxic_score >= self.threshold,
            trigger_words=trigger_words,
        )

    def predict_batch(self, texts: list[str]) -> list[ToxicityResult]:
        """Score multiple texts for toxicity.

        Args:
            texts: List of comment texts to classify.

        Returns:
            List of ToxicityResult objects.
        """
        if not texts:
            return []

        # Handle empty strings
        results = []
        non_empty_indices = []
        non_empty_texts = []

        for i, text in enumerate(texts):
            if not text or not text.strip():
                results.append((i, ToxicityResult(score=0.0, is_toxic=False, trigger_words=[])))
            else:
                non_empty_indices.append(i)
                non_empty_texts.append(text)

        if non_empty_texts:
            tfidf_matrix = self.vectorizer.transform(non_empty_texts)
            probas = self.model.predict_proba(tfidf_matrix)

            for idx, (orig_idx, proba) in enumerate(zip(non_empty_indices, probas)):
                toxic_score = float(proba[1])
                row_vector = tfidf_matrix[idx]
                trigger_words = self._get_trigger_words(row_vector) if toxic_score > 0.3 else []

                results.append((orig_idx, ToxicityResult(
                    score=round(toxic_score, 4),
                    is_toxic=toxic_score >= self.threshold,
                    trigger_words=trigger_words,
                )))

        # Sort by original index to maintain order
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]

    def _get_trigger_words(self, tfidf_vector, top_n: int = None) -> list[str]:
        """Identify words that contributed most to the toxicity score.

        Uses model coefficients * TF-IDF weights to determine word importance.
        This approach is valid for linear models (logistic regression, linear SVM).

        Args:
            tfidf_vector: Sparse TF-IDF vector for a single text.
            top_n: Number of top trigger words to return.

        Returns:
            List of words sorted by contribution to toxicity score.
        """
        top_n = top_n or self.TOP_N_TRIGGER_WORDS

        # Element-wise multiplication of TF-IDF weights and model coefficients
        tfidf_array = tfidf_vector.toarray().flatten()
        contribution = tfidf_array * self._coefficients

        # Get indices of non-zero contributions sorted by magnitude (descending)
        nonzero_mask = tfidf_array > 0
        positive_mask = contribution > 0  # Only words that push toward toxic
        combined_mask = nonzero_mask & positive_mask

        if not combined_mask.any():
            return []

        masked_contributions = np.where(combined_mask, contribution, 0)
        top_indices = np.argsort(masked_contributions)[-top_n:][::-1]

        trigger_words = []
        for idx in top_indices:
            if masked_contributions[idx] > 0:
                word = self._feature_names[idx]
                trigger_words.append(word)

        return trigger_words
