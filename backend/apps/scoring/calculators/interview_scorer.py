"""
Aggregate all submitted scorecards for an application into an interview_score.

Returns:
{
    'score': int 0-100 | None,
    'breakdown': [
        {
            'scorecard_id': str,
            'interviewer_name': str,
            'normalized_score': float,
            'criterion_ratings': [...],
            'source': str,
        }
    ]
}
"""

from __future__ import annotations


def score_interviews(application) -> dict:
    """
    Compute interview score from submitted scorecards.

    Expects application.interviews to be prefetched with
    scorecards__criterion_ratings__criterion and scorecards__interviewer__user.
    """
    breakdown = []
    scorecard_scores = []

    for interview in application.interviews.all():
        for scorecard in interview.scorecards.filter(is_draft=False):
            ratings = list(
                scorecard.criterion_ratings.select_related('criterion').all()
            )

            if not ratings:
                # Fall back to overall_rating if no criterion ratings
                if scorecard.overall_rating is not None:
                    normalized = (scorecard.overall_rating - 1) / 4.0 * 100
                    scorecard_scores.append(normalized)
                    breakdown.append({
                        'scorecard_id': str(scorecard.id),
                        'interviewer_name': scorecard.interviewer.user.get_full_name(),
                        'normalized_score': round(normalized, 2),
                        'criterion_ratings': [],
                        'source': 'overall_rating',
                    })
                continue

            weight_sum = sum(float(r.criterion.weight) for r in ratings)

            if weight_sum == 0:
                continue

            weighted_sum = sum(r.rating * float(r.criterion.weight) for r in ratings)
            raw_weighted_avg = weighted_sum / weight_sum
            normalized = (raw_weighted_avg - 1) / 4.0 * 100

            scorecard_scores.append(normalized)

            breakdown.append({
                'scorecard_id': str(scorecard.id),
                'interviewer_name': scorecard.interviewer.user.get_full_name(),
                'normalized_score': round(normalized, 2),
                'criterion_ratings': [
                    {
                        'criterion_name': r.criterion.name,
                        'rating': r.rating,
                        'weight': float(r.criterion.weight),
                    }
                    for r in ratings
                ],
                'source': 'criterion_ratings',
            })

    if not scorecard_scores:
        return {'score': None, 'breakdown': []}

    interview_score = int(round(sum(scorecard_scores) / len(scorecard_scores)))
    interview_score = max(0, min(100, interview_score))

    return {
        'score': interview_score,
        'breakdown': breakdown,
    }
