"""Scoring service — orchestrates all calculators and persists CandidateScore."""

from __future__ import annotations

import logging

from apps.applications.models import Application

from .calculators.assessment_scorer import score_assessments
from .calculators.interview_scorer import score_interviews
from .calculators.profile_scorer import score_profile
from .models import CandidateScore

logger = logging.getLogger(__name__)

# Global default weights
WEIGHT_PROFILE = 0.50
WEIGHT_INTERVIEW = 0.35
WEIGHT_ASSESSMENT = 0.15


def _compute_final_score(
    profile_score: int | None,
    interview_score: int | None,
    assessment_score: int | None,
    meets_required_criteria: bool,
) -> int | None:
    """
    Combine sub-scores using global weights, redistributing when data is absent.
    Returns None only when profile_score is also None.
    """
    if profile_score is None:
        return None

    if interview_score is None and assessment_score is None:
        final = float(profile_score)

    elif interview_score is None:
        # Redistribute: profile 0.70, assessment 0.30
        final = profile_score * 0.70 + assessment_score * 0.30

    elif assessment_score is None:
        # Redistribute: profile 0.59, interview 0.41
        final = profile_score * 0.59 + interview_score * 0.41

    else:
        final = (
            profile_score * WEIGHT_PROFILE
            + interview_score * WEIGHT_INTERVIEW
            + assessment_score * WEIGHT_ASSESSMENT
        )

    final_int = max(0, min(100, int(round(final))))

    if not meets_required_criteria:
        final_int = min(final_int, 40)

    return final_int


class ScoringService:
    """Orchestrates profile, interview, and assessment scoring."""

    @staticmethod
    def score_application(application: Application) -> CandidateScore:
        """
        Compute and persist a CandidateScore for the given application.
        Safe to call multiple times — uses update_or_create.
        """
        # Re-fetch with all necessary prefetches to avoid N+1 queries
        application = (
            Application.objects
            .select_related(
                'candidate',
                'requisition',
            )
            .prefetch_related(
                'candidate__skills',
                'candidate__experiences',
                'candidate__education',
                'requisition__criteria',
                'interviews__scorecards__criterion_ratings__criterion',
                'interviews__scorecards__interviewer__user',
                'assessments__template',
            )
            .get(pk=application.pk)
        )

        profile_result = score_profile(application.candidate, application.requisition)
        interview_result = score_interviews(application)
        assessment_result = score_assessments(application)

        meets_required = profile_result['meets_required_criteria']

        final = _compute_final_score(
            profile_result['score'],
            interview_result['score'],
            assessment_result['score'],
            meets_required,
        )

        score_obj, _ = CandidateScore.objects.update_or_create(
            application=application,
            defaults={
                'profile_score': profile_result['score'],
                'interview_score': interview_result['score'],
                'assessment_score': assessment_result['score'],
                'final_score': final,
                'profile_breakdown': {'items': profile_result['breakdown']},
                'interview_breakdown': {'scorecards': interview_result['breakdown']},
                'assessment_breakdown': {'assessments': assessment_result['breakdown']},
                'meets_required_criteria': meets_required,
                'scoring_version': '1.0',
            },
        )

        logger.info(
            'Scored application %s: final=%s profile=%s interview=%s assessment=%s',
            application.application_id,
            final,
            profile_result['score'],
            interview_result['score'],
            assessment_result['score'],
        )

        return score_obj
