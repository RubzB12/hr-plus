"""Services for candidate profile management."""

import logging
from typing import Dict, Optional

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from .models import CandidateProfile, WorkExperience, Education, Skill

logger = logging.getLogger(__name__)


class ResumeParsingService:
    """Service for parsing resume files and extracting structured data."""

    @staticmethod
    def parse_resume(resume_file: UploadedFile) -> Dict:
        """
        Parse resume file and extract structured data.

        This is a placeholder implementation. In production, integrate with:
        - Affinda Resume Parser
        - Sovren Resume Parser
        - Custom AI/ML model
        - OpenAI GPT-4 for extraction

        Args:
            resume_file: Uploaded resume file (PDF, DOCX, TXT)

        Returns:
            Dictionary with extracted data:
            {
                'summary': str,
                'skills': List[str],
                'experiences': List[Dict],
                'education': List[Dict],
                'contact': Dict
            }
        """
        # Placeholder: Return empty structure
        # In production, implement actual parsing logic
        logger.info(f"Parsing resume: {resume_file.name} ({resume_file.size} bytes)")

        return {
            'summary': '',
            'skills': [],
            'experiences': [],
            'education': [],
            'contact': {
                'email': '',
                'phone': '',
                'linkedin': '',
                'location': '',
            },
            'raw_text': '',
        }


class CandidateProfileService:
    """Service for managing candidate profiles and related data."""

    @staticmethod
    @transaction.atomic
    def upload_and_parse_resume(
        candidate: CandidateProfile,
        resume_file: UploadedFile,
        auto_populate: bool = True
    ) -> CandidateProfile:
        """
        Upload resume file and optionally auto-populate profile from parsed data.

        Args:
            candidate: CandidateProfile instance
            resume_file: Uploaded resume file
            auto_populate: If True, automatically create experience/education records

        Returns:
            Updated CandidateProfile instance
        """
        # Delete old resume if exists
        if candidate.resume_file:
            candidate.resume_file.delete(save=False)

        # Save new resume
        candidate.resume_file = resume_file

        # Parse resume content
        parsed_data = ResumeParsingService.parse_resume(resume_file)
        candidate.resume_parsed = parsed_data

        # Auto-populate profile fields if enabled
        if auto_populate and parsed_data:
            contact = parsed_data.get('contact', {})

            # Update phone if not set
            if not candidate.phone and contact.get('phone'):
                candidate.phone = contact['phone']

            # Update LinkedIn if not set
            if not candidate.linkedin_url and contact.get('linkedin'):
                candidate.linkedin_url = contact['linkedin']

            # Update location if not set
            if not candidate.location_city and contact.get('location'):
                location_parts = contact['location'].split(',')
                if len(location_parts) >= 2:
                    candidate.location_city = location_parts[0].strip()
                    candidate.location_country = location_parts[-1].strip()

        # Recalculate completeness
        candidate.profile_completeness = candidate.calculate_completeness()
        candidate.save()

        logger.info(f"Resume uploaded for candidate {candidate.id}: {resume_file.name}")

        return candidate

    @staticmethod
    @transaction.atomic
    def auto_populate_from_resume(candidate: CandidateProfile) -> Dict[str, int]:
        """
        Auto-populate experience, education, and skills from parsed resume data.

        This should be called after resume is parsed and saved.

        Args:
            candidate: CandidateProfile instance with resume_parsed data

        Returns:
            Dictionary with counts: {'experiences': 2, 'education': 1, 'skills': 15}
        """
        if not candidate.resume_parsed:
            return {'experiences': 0, 'education': 0, 'skills': 0}

        parsed = candidate.resume_parsed
        counts = {'experiences': 0, 'education': 0, 'skills': 0}

        # Create work experiences
        for exp_data in parsed.get('experiences', []):
            try:
                WorkExperience.objects.create(
                    candidate=candidate,
                    company_name=exp_data.get('company', 'Unknown'),
                    title=exp_data.get('title', 'Unknown'),
                    start_date=exp_data.get('start_date'),
                    end_date=exp_data.get('end_date'),
                    is_current=exp_data.get('is_current', False),
                    description=exp_data.get('description', ''),
                )
                counts['experiences'] += 1
            except Exception as e:
                logger.warning(f"Failed to create experience: {e}")

        # Create education records
        for edu_data in parsed.get('education', []):
            try:
                Education.objects.create(
                    candidate=candidate,
                    institution=edu_data.get('institution', 'Unknown'),
                    degree=edu_data.get('degree', 'Unknown'),
                    field_of_study=edu_data.get('field_of_study', ''),
                    start_date=edu_data.get('start_date'),
                    end_date=edu_data.get('end_date'),
                    gpa=edu_data.get('gpa'),
                )
                counts['education'] += 1
            except Exception as e:
                logger.warning(f"Failed to create education: {e}")

        # Create skills
        for skill_name in parsed.get('skills', []):
            try:
                Skill.objects.get_or_create(
                    candidate=candidate,
                    name=skill_name.strip(),
                    defaults={'proficiency': ''},
                )
                counts['skills'] += 1
            except Exception as e:
                logger.warning(f"Failed to create skill: {e}")

        # Recalculate completeness
        candidate.profile_completeness = candidate.calculate_completeness()
        candidate.save(update_fields=['profile_completeness'])

        logger.info(
            f"Auto-populated from resume for candidate {candidate.id}: "
            f"{counts['experiences']} experiences, {counts['education']} education, "
            f"{counts['skills']} skills"
        )

        return counts
