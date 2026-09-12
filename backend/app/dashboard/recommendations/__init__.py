"""
app/dashboard/recommendations/__init__.py
-----------------------------------------
Sprint 6 — Executive Recommendation Aggregator Package.
"""

from app.dashboard.recommendations.aggregator import (
    RecommendationAggregator,
    aggregate_recommendations,
)

__all__ = [
    "RecommendationAggregator",
    "aggregate_recommendations",
]
