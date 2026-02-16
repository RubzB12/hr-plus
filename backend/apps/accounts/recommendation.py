"""Job recommendation engine for candidates."""

from typing import List, Dict, Any
from django.db.models import Q
from apps.jobs.models import Requisition


class JobRecommendationService:
    """
    Intelligent job recommendation system.
    Scores jobs based on candidate profile match.
    """

    @staticmethod
    def get_recommendations(candidate_profile, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Generate personalized job recommendations for a candidate.

        Returns list of dicts with:
        - job: Requisition object
        - score: Match score (0-100)
        - reasons: List of match reasons
        """
        # Get all open, published jobs
        jobs = (
            Requisition.objects
            .filter(status='open', published_at__isnull=False)
            .select_related('department', 'location', 'level')
            .prefetch_related('skills_required')
        )

        # Filter out jobs the candidate has already applied to
        from apps.applications.models import Application
        applied_job_ids = Application.objects.filter(
            candidate=candidate_profile
        ).values_list('requisition_id', flat=True)

        jobs = jobs.exclude(id__in=applied_job_ids)

        # Score each job
        scored_jobs = []
        for job in jobs:
            score, reasons = JobRecommendationService._score_job(
                candidate_profile, job
            )
            if score > 0:  # Only include jobs with some match
                scored_jobs.append({
                    'job': job,
                    'score': score,
                    'reasons': reasons,
                })

        # Sort by score descending
        scored_jobs.sort(key=lambda x: x['score'], reverse=True)

        return scored_jobs[:limit]

    @staticmethod
    def _score_job(candidate_profile, job: Requisition) -> tuple[int, List[str]]:
        """
        Calculate match score (0-100) and reasons for a job.

        Scoring factors:
        - Skills match: 40 points max
        - Location match: 20 points max
        - Experience level match: 15 points max
        - Job type preference match: 10 points max
        - Remote policy match: 10 points max
        - Salary match: 5 points max
        """
        score = 0
        reasons = []

        # 1. Skills Match (40 points max)
        candidate_skills = set(
            candidate_profile.skills.values_list('name', flat=True)
        )

        if candidate_skills:
            # Get job required skills from description (parse keywords)
            # For now, use a simple keyword match
            job_description = job.description.lower()
            matching_skills = [
                skill for skill in candidate_skills
                if skill.lower() in job_description
            ]

            if matching_skills:
                # Score based on how many skills match
                skill_score = min(40, len(matching_skills) * 8)
                score += skill_score

                if skill_score >= 16:  # 2+ skills match
                    reasons.append(
                        f"Matches {len(matching_skills)} of your skills: "
                        f"{', '.join(list(matching_skills)[:3])}"
                    )

        # 2. Location Match (20 points max)
        if candidate_profile.location_city and job.location:
            if (
                candidate_profile.location_city.lower()
                in job.location.city.lower()
            ):
                score += 20
                reasons.append(f"Located in {candidate_profile.location_city}")
            elif (
                candidate_profile.location_country.lower()
                == job.location.country.lower()
            ):
                score += 10
                reasons.append(f"Located in {candidate_profile.location_country}")

        # Remote jobs are always location-friendly
        if job.remote_policy == 'remote':
            score += 15
            reasons.append("Remote work available")

        # 3. Experience Level Match (15 points max)
        candidate_exp = candidate_profile.experiences.count()

        if job.level:
            level_name = job.level.name.lower()

            if candidate_exp == 0 and 'junior' in level_name or 'entry' in level_name:
                score += 15
                reasons.append(f"Entry-level position")
            elif 1 <= candidate_exp <= 2 and 'junior' in level_name:
                score += 15
                reasons.append(f"Matches your experience level")
            elif 3 <= candidate_exp <= 5 and ('mid' in level_name or 'intermediate' in level_name):
                score += 15
                reasons.append(f"Matches your experience level")
            elif candidate_exp >= 6 and ('senior' in level_name or 'lead' in level_name or 'principal' in level_name):
                score += 15
                reasons.append(f"Senior-level opportunity")
            elif 2 <= candidate_exp <= 8:
                # Reasonable match for mid-range experience
                score += 8

        # 4. Job Type Preference Match (10 points max)
        if candidate_profile.preferred_job_types:
            if job.employment_type in candidate_profile.preferred_job_types:
                score += 10
                job_type_label = job.employment_type.replace('_', '-')
                reasons.append(f"Preferred job type: {job_type_label}")

        # 5. Remote Policy Match (10 points max)
        # Candidates with remote location preferences likely want remote work
        if candidate_profile.location_city.lower() in ['remote', 'anywhere']:
            if job.remote_policy == 'remote':
                score += 10
                reasons.append("Fully remote position")
            elif job.remote_policy == 'hybrid':
                score += 5

        # 6. Salary Match (5 points max)
        if (
            candidate_profile.preferred_salary_min
            and job.salary_max
        ):
            candidate_min = float(candidate_profile.preferred_salary_min)
            job_max = float(job.salary_max)

            if job_max >= candidate_min:
                score += 5
                reasons.append("Matches your salary expectations")

        # 7. Work Authorization Match (bonus 5 points)
        if candidate_profile.work_authorization in ['citizen', 'permanent_resident']:
            # All jobs available
            score += 5
        elif candidate_profile.work_authorization == 'visa_holder':
            # Check if job doesn't require sponsorship
            if 'sponsorship' not in job.description.lower():
                score += 3

        # Cap score at 100
        score = min(100, score)

        # Ensure we have at least one reason if score > 0
        if score > 0 and not reasons:
            reasons.append("Good match for your profile")

        return score, reasons
