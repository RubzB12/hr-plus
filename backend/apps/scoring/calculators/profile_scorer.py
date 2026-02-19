"""
Score a candidate's profile against a requisition's RequisitionCriteria.

Returns a dict:
{
    'score': int 0-100 | None,
    'meets_required_criteria': bool,
    'breakdown': [
        {
            'criterion_id': str,
            'criterion_type': str,
            'value': str,
            'weight': int,
            'is_required': bool,
            'factor': float,  # 0.0 – 1.0
            'earned': float,
            'detail': str,
        },
        ...
    ]
}
"""

from __future__ import annotations

from datetime import date


PROFICIENCY_RANK = {
    'beginner': 1,
    'intermediate': 2,
    'advanced': 3,
    'expert': 4,
}

PROFICIENCY_FACTOR = {
    'beginner': 0.3,
    'intermediate': 0.6,
    'advanced': 0.85,
    'expert': 1.0,
}

DEGREE_RANK = {
    'associate': 1,
    'bachelors': 2,
    'bachelor': 2,
    'masters': 3,
    'master': 3,
    'mba': 3,
    'phd': 4,
    'doctorate': 4,
}


def _proficiency_factor(candidate_proficiency: str, min_proficiency: str) -> float:
    """Return factor 0-1 based on proficiency level vs minimum required."""
    candidate_rank = PROFICIENCY_RANK.get(candidate_proficiency, 0)
    min_rank = PROFICIENCY_RANK.get(min_proficiency, 0)

    if min_proficiency and candidate_rank < min_rank:
        # Below minimum — partial credit based on candidate's actual level
        return PROFICIENCY_FACTOR.get(candidate_proficiency, 0.0)
    return PROFICIENCY_FACTOR.get(candidate_proficiency, 0.5)


def _experience_years(experiences) -> float:
    """Sum total work experience in years across all WorkExperience entries."""
    total = 0.0
    today = date.today()
    for exp in experiences:
        end = exp.end_date if exp.end_date else today
        delta = (end - exp.start_date).days / 365.25
        total += max(delta, 0)
    return total


def _highest_degree_rank(education_entries) -> int:
    """Return numeric rank of the highest degree held by the candidate."""
    best = 0
    for edu in education_entries:
        degree_lower = edu.degree.lower()
        for keyword, rank in DEGREE_RANK.items():
            if keyword in degree_lower:
                best = max(best, rank)
    return best


def _job_title_overlap(experiences, value: str) -> float:
    """
    Token overlap between candidate's past job titles and the criterion value.
    Returns a factor between 0.0 and 1.0.
    """
    value_tokens = set(value.lower().split())
    if not value_tokens:
        return 0.0
    matched = 0
    for exp in experiences:
        title_tokens = set(exp.title.lower().split())
        matched += len(value_tokens & title_tokens)
    if not matched:
        return 0.0
    return min(matched / len(value_tokens), 1.0)


def score_profile(candidate, requisition) -> dict:
    """
    Score the candidate's profile against requisition criteria.

    Expects candidate.skills, candidate.experiences, candidate.education,
    and requisition.criteria to already be prefetched.
    """
    criteria = list(requisition.criteria.all().order_by('order'))

    if not criteria:
        return {
            'score': None,
            'meets_required_criteria': True,
            'breakdown': [],
        }

    skills_map = {s.name.lower(): s for s in candidate.skills.all()}
    experiences = list(candidate.experiences.all())
    education_entries = list(candidate.education.all())

    meets_required = True
    breakdown = []
    total_weight = sum(c.weight for c in criteria)

    if total_weight == 0:
        return {
            'score': None,
            'meets_required_criteria': True,
            'breakdown': [],
        }

    earned_total = 0.0

    for criterion in criteria:
        factor = 0.0
        detail = ''

        if criterion.criterion_type == 'skill':
            skill = skills_map.get(criterion.value.lower())
            if skill:
                proficiency = skill.proficiency or 'intermediate'
                factor = _proficiency_factor(proficiency, criterion.min_proficiency)
                detail = f'Skill found (proficiency: {proficiency})'
            else:
                factor = 0.0
                detail = 'Skill not found in candidate profile'
                if criterion.is_required:
                    meets_required = False

        elif criterion.criterion_type == 'experience_years':
            actual_years = _experience_years(experiences)
            min_years = criterion.min_years or 1
            factor = min(actual_years / min_years, 1.0)
            detail = f'{actual_years:.1f} actual vs {min_years} required years'
            if criterion.is_required and actual_years < min_years:
                meets_required = False

        elif criterion.criterion_type == 'education':
            required_value = criterion.value.lower()
            required_rank = DEGREE_RANK.get(required_value, 0)
            candidate_rank = _highest_degree_rank(education_entries)
            factor = 1.0 if candidate_rank >= required_rank else 0.0
            detail = f'Candidate degree rank {candidate_rank} vs required {required_rank}'
            if criterion.is_required and candidate_rank < required_rank:
                meets_required = False

        elif criterion.criterion_type == 'job_title':
            factor = _job_title_overlap(experiences, criterion.value)
            detail = f'Job title overlap factor: {factor:.2f}'

        earned = criterion.weight * factor
        earned_total += earned

        breakdown.append({
            'criterion_id': str(criterion.id),
            'criterion_type': criterion.criterion_type,
            'value': criterion.value,
            'weight': criterion.weight,
            'is_required': criterion.is_required,
            'factor': round(factor, 3),
            'earned': round(earned, 2),
            'detail': detail,
        })

    raw_score = earned_total / total_weight * 100
    profile_score = max(0, min(100, int(round(raw_score))))

    return {
        'score': profile_score,
        'meets_required_criteria': meets_required,
        'breakdown': breakdown,
    }
