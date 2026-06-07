"""Model information API routes.

GET /model/metrics: Model evaluation metrics
GET /model/limitations: Known limitations and biases
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas import ModelMetrics, ModelLimitations

router = APIRouter()

KNOWN_LIMITATIONS = [
    "Trained on English Wikipedia talk page data (Jigsaw dataset, 2015-2017).",
    "May not generalize well to non-English Wikipedia editions.",
    "Sarcasm and context-dependent toxicity may be missed.",
    "Model reflects biases present in the training data.",
    (
        "Identity term bias: The model may score comments containing identity terms "
        "(e.g., 'gay', 'Muslim', 'Black') as toxic because these words frequently appear "
        "in toxic comments about those groups. A sentence like 'I am a gay man' may be "
        "incorrectly flagged. This is a well-documented limitation of Jigsaw-trained models "
        "(Borkan et al., 2019)."
    ),
    (
        "Adversarial evasion: Obfuscated slurs (e.g., leetspeak, Unicode substitutions, "
        "deliberate misspellings) are likely to evade detection. The TF-IDF model has no "
        "character-level awareness."
    ),
    (
        "Temporal bias: The training data is from 2015-2017 Wikipedia discussions. "
        "Language norms, slang, and toxicity patterns evolve over time. The model may "
        "underperform on contemporary language."
    ),
    (
        "Context-window limitation: Each comment is scored in isolation. The model cannot "
        "consider conversational context, so a reply like 'No, YOU are wrong' may be scored "
        "differently depending on whether the preceding comment was civil or hostile."
    ),
    (
        "False positive harm: Incorrectly flagging a comment as toxic can discourage "
        "good-faith contributors. Health scores should be treated as signals for human review, "
        "not automated moderation decisions."
    ),
]

REFERENCES = [
    "Jigsaw Toxic Comment Classification Challenge: https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge",
    "Borkan, D., et al. (2019). Nuanced Metrics for Measuring Unintended Bias with Real Data for Text Classification.",
    "Wulczyn, E., Thain, N., & Dixon, L. (2023). Ex Machina: Personal Attacks Seen at Scale.",
]


@router.get("/model/metrics", response_model=ModelMetrics)
async def get_model_metrics():
    """Return model evaluation metrics."""
    metrics_path = settings.metrics_path
    if metrics_path.exists():
        with open(metrics_path) as f:
            data = json.load(f)
        return ModelMetrics(**data)

    return ModelMetrics(
        note="Model metrics not available. Run evaluation script first."
    )


@router.get("/model/limitations", response_model=ModelLimitations)
async def get_model_limitations():
    """Return known model limitations and biases."""
    return ModelLimitations(
        limitations=KNOWN_LIMITATIONS,
        references=REFERENCES,
    )
