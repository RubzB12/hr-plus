"""
Average completed Assessment.score values for an application.

Returns:
{
    'score': int 0-100 | None,
    'breakdown': [
        {
            'assessment_id': str,
            'template_name': str,
            'score': float,
        }
    ]
}
"""

from __future__ import annotations


def score_assessments(application) -> dict:
    """
    Average all completed assessment scores.

    Expects application.assessments to be prefetched with template.
    """
    completed = list(
        application.assessments
        .filter(status='completed', score__isnull=False)
        .select_related('template')
    )

    if not completed:
        return {'score': None, 'breakdown': []}

    breakdown = [
        {
            'assessment_id': str(a.id),
            'template_name': a.template.name,
            'score': float(a.score),
        }
        for a in completed
    ]

    avg = sum(b['score'] for b in breakdown) / len(breakdown)
    assessment_score = max(0, min(100, int(round(avg))))

    return {
        'score': assessment_score,
        'breakdown': breakdown,
    }
