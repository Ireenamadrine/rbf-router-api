"""
RLVR (Reinforcement Learning from Verified Rewards) feedback engine.

Every /feedback call is one "experience." This engine scores each experience
with a Virtual Repetition Score (VRS): a measure of how much that experience
should influence the next retrain. Surprising experiences (the router was
confident but wrong, or unsure but right) get a high VRS and are virtually
repeated more times in the next fit() call — so the RBF centers and weights
shift toward correcting the mistake, without ever training a neural network.
"""
from typing import Optional
import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class FeedbackSignal(BaseModel):
    """One scored experience: a route recommendation plus what actually happened."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    request_id: str
    query_embedding: np.ndarray  # the feature vector stored at route time
    recommended_tier: str
    tier_used: str
    succeeded: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class RLVRFeedbackEngine:
    """Turns raw feedback into retraining signal."""

    def __init__(
        self,
        min_feedback_to_retrain: int = 3,
        retrain_every_n_new: int = 3,
        vrs_min: float = 0.5,
        vrs_max: float = 5.0,
    ):
        self.min_feedback_to_retrain = min_feedback_to_retrain
        self.retrain_every_n_new = retrain_every_n_new
        self.vrs_min = vrs_min
        self.vrs_max = vrs_max

    def compute_vrs(self, signal: FeedbackSignal) -> float:
        """Virtual Repetition Score.

        High VRS = surprising experience (the router's confidence didn't match
        the outcome) -> weight it more heavily in the next retrain.
        Low VRS = the router already had this right -> little new information.
        """
        target = 1.0 if signal.succeeded else 0.0
        td_error = abs(target - signal.confidence)  # how wrong was the router's confidence?

        quality = signal.quality_score if signal.quality_score is not None else target

        # Grows with surprise (td_error), shrinks with quality (a low-quality
        # success is still worth exploring further).
        vrs = (1.0 + 2.0 * td_error) * (1.5 - 0.5 * quality)
        return float(np.clip(vrs, self.vrs_min, self.vrs_max))

    def repetitions_for(self, vrs: float) -> int:
        """Convert a VRS float into an integer number of virtual repetitions
        to use when this experience is included in the next fit() call."""
        return int(max(1, round(vrs)))

    def should_retrain(self, total_feedback: int, last_train_at: int) -> bool:
        """True once enough total feedback exists, and enough NEW feedback has
        arrived since the last retrain."""
        if total_feedback < self.min_feedback_to_retrain:
            return False
        return (total_feedback - last_train_at) >= self.retrain_every_n_new