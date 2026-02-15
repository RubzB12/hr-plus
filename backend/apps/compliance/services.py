"""Compliance services for GDPR and EEO."""

import hashlib
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.accounts.models import CandidateProfile, User
from apps.applications.models import Application
from apps.core.exceptions import BusinessValidationError
from apps.interviews.models import Scorecard

from .models import AnonymizationRecord, AuditLog, ConsentRecord, DataRetentionPolicy, EEOData


class GDPRService:
    """Service for GDPR compliance operations."""

    @staticmethod
    def export_candidate_data(candidate: CandidateProfile) -> dict[str, Any]:
        """
        Export all data for a candidate (GDPR Right to Access).

        Returns machine-readable JSON with all personal data.
        """
        # Gather all candidate data
        data = {
            'profile': {
                'id': str(candidate.id),
                'user': {
                    'id': str(candidate.user.id),
                    'email': candidate.user.email,
                    'first_name': candidate.user.first_name,
                    'last_name': candidate.user.last_name,
                },
                'phone': candidate.phone,
                'location_city': candidate.location_city,
                'location_country': candidate.location_country,
                'work_authorization': candidate.work_authorization,
                'linkedin_url': candidate.linkedin_url,
                'portfolio_url': candidate.portfolio_url,
                'preferred_salary_min': str(candidate.preferred_salary_min)
                if candidate.preferred_salary_min
                else None,
                'preferred_salary_max': str(candidate.preferred_salary_max)
                if candidate.preferred_salary_max
                else None,
                'preferred_job_types': candidate.preferred_job_types,
                'source': candidate.source,
                'resume_file': candidate.resume_file.url if candidate.resume_file else None,
                'created_at': candidate.created_at.isoformat(),
                'updated_at': candidate.updated_at.isoformat(),
            },
            'applications': [
                {
                    'id': str(app.id),
                    'application_id': app.application_id,
                    'requisition_title': app.requisition.title,
                    'status': app.status,
                    'applied_at': app.applied_at.isoformat(),
                    'cover_letter': app.cover_letter,
                    'screening_responses': app.screening_responses,
                }
                for app in candidate.applications.select_related('requisition').all()
            ],
            'interviews': [
                {
                    'id': str(interview.id),
                    'scheduled_start': interview.scheduled_start.isoformat(),
                    'scheduled_end': interview.scheduled_end.isoformat()
                    if interview.scheduled_end
                    else None,
                    'status': interview.status,
                    'type': interview.type,
                    'location': interview.location,
                }
                for app in candidate.applications.all()
                for interview in app.interviews.all()
            ],
            'audit_trail': [
                {
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.action,
                    'resource_type': log.resource_type,
                    'metadata': log.metadata,
                }
                for log in AuditLog.objects.filter(
                    Q(actor=candidate.user)
                    | Q(resource_type='candidate', resource_id=str(candidate.id))
                ).order_by('-timestamp')[:100]
            ],
            'consents': [
                {
                    'consent_type': consent.consent_type,
                    'given_at': consent.given_at.isoformat(),
                    'withdrawn_at': consent.withdrawn_at.isoformat()
                    if consent.withdrawn_at
                    else None,
                    'is_active': consent.is_active,
                }
                for consent in candidate.user.consent_records.all()
            ],
            'exported_at': timezone.now().isoformat(),
            'exported_by': 'candidate_request',
        }

        # Log the export
        AuditLog.objects.create(
            actor=candidate.user,
            action='data_export',
            resource_type='candidate',
            resource_id=str(candidate.id),
            metadata={'export_timestamp': timezone.now().isoformat()},
        )

        return data

    @staticmethod
    def send_data_export(candidate: CandidateProfile) -> None:
        """
        Generate and email data export to candidate.
        """
        import json

        data = GDPRService.export_candidate_data(candidate)

        # Create email with JSON attachment
        email = EmailMessage(
            subject='Your Personal Data Export',
            body=f"""Dear {candidate.user.get_full_name()},

As requested, please find attached a complete export of all personal data we hold about you.

This export includes:
- Your profile information
- All job applications
- Interview records
- Audit trail of system actions
- Consent records

If you have any questions, please contact our Privacy Team at privacy@company.com.

Best regards,
HR Team""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[candidate.user.email],
        )

        # Attach JSON export
        email.attach(
            f'data_export_{candidate.user.id}.json',
            json.dumps(data, indent=2),
            'application/json',
        )

        email.send()

    @staticmethod
    @transaction.atomic
    def anonymize_candidate(
        candidate: CandidateProfile, *, reason: str, anonymized_by: User | None = None
    ) -> AnonymizationRecord:
        """
        Anonymize candidate data (GDPR Right to Erasure).

        Removes all PII while preserving aggregate statistics.
        Creates an anonymization record for audit trail.
        """
        # Store original data for audit record
        original_email = candidate.user.email
        original_id = candidate.id
        applications_count = candidate.applications.count()

        # Create email hash for duplicate detection
        email_hash = hashlib.sha256(original_email.encode()).hexdigest()

        # Log before anonymization
        AuditLog.objects.create(
            actor=anonymized_by,
            action='anonymize',
            resource_type='candidate',
            resource_id=str(candidate.id),
            metadata={
                'reason': reason,
                'original_email_hash': email_hash,
                'applications_count': applications_count,
            },
        )

        # Anonymize user data
        user = candidate.user
        user.email = f'deleted_{user.id}@anonymized.local'
        user.first_name = 'Deleted'
        user.last_name = 'User'
        user.is_active = False
        user.save(update_fields=['email', 'first_name', 'last_name', 'is_active'])

        # Anonymize candidate profile
        candidate.phone = ''
        candidate.linkedin_url = ''
        candidate.portfolio_url = ''
        candidate.work_authorization = ''
        candidate.preferred_salary_min = None
        candidate.preferred_salary_max = None
        candidate.preferred_job_types = []

        # Delete resume file if exists
        if candidate.resume_file:
            candidate.resume_file.delete()

        candidate.resume_parsed = {}
        candidate.save()

        # Anonymize applications
        for app in candidate.applications.all():
            app.cover_letter = ''
            app.screening_responses = {}
            app.save(update_fields=['cover_letter', 'screening_responses'])

        # Anonymize interview prep notes
        from apps.interviews.models import Interview

        for app in candidate.applications.all():
            Interview.objects.filter(application=app).update(
                prep_notes_candidate='[Redacted]', prep_notes_interviewer='[Redacted]'
            )

        # Anonymize scorecards
        for app in candidate.applications.all():
            for interview in app.interviews.all():
                Scorecard.objects.filter(interview=interview).update(
                    notes='[Redacted]', strengths='[Redacted]', concerns='[Redacted]'
                )

        # Delete EEO data if exists
        if hasattr(candidate, 'eeo_data'):
            candidate.eeo_data.delete()

        # Create anonymization record
        record = AnonymizationRecord.objects.create(
            candidate_id=original_id,
            candidate_email_hash=email_hash,
            anonymized_by=anonymized_by,
            reason=reason,
            applications_count=applications_count,
            metadata={
                'anonymized_at': timezone.now().isoformat(),
                'user_id': str(user.id),
            },
        )

        return record

    @staticmethod
    @transaction.atomic
    def process_data_retention() -> dict[str, int]:
        """
        Process data retention policies and delete old data.

        Returns counts of records deleted by data type.
        """
        deleted_counts = {}
        now = timezone.now()

        # Get active retention policies
        policies = DataRetentionPolicy.objects.filter(is_active=True)

        for policy in policies:
            cutoff_date = now - timedelta(days=policy.retention_days + policy.grace_period_days)

            if policy.data_type == 'candidate_application':
                # Delete old rejected/withdrawn applications
                applications = Application.objects.filter(
                    status__in=['rejected', 'withdrawn'],
                    updated_at__lt=cutoff_date,
                )
                count = applications.count()

                # Anonymize candidates instead of deleting
                for app in applications:
                    if app.candidate.applications.count() == 1:
                        # This is the candidate's only application
                        GDPRService.anonymize_candidate(
                            app.candidate,
                            reason='Automatic data retention policy',
                            anonymized_by=None,
                        )

                deleted_counts['applications'] = count

            elif policy.data_type == 'audit_logs':
                # Keep audit logs for minimum 7 years (legal requirement)
                if policy.retention_days < 2555:  # 7 years
                    continue

                count = AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()[0]
                deleted_counts['audit_logs'] = count

            # Update last executed timestamp
            policy.last_executed = now
            policy.save(update_fields=['last_executed'])

        return deleted_counts

    @staticmethod
    def record_consent(
        *, user: User, consent_type: str, ip_address: str | None = None, user_agent: str = ''
    ) -> ConsentRecord:
        """
        Record user consent for data processing.
        """
        if consent_type not in dict(ConsentRecord.CONSENT_TYPES):
            raise BusinessValidationError(f'Invalid consent type: {consent_type}')

        # Check if consent already exists and is active
        existing = ConsentRecord.objects.filter(
            user=user, consent_type=consent_type, withdrawn_at__isnull=True
        ).first()

        if existing:
            return existing

        consent = ConsentRecord.objects.create(
            user=user,
            consent_type=consent_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        AuditLog.objects.create(
            actor=user,
            action='consent_given',
            resource_type='consent',
            resource_id=str(consent.id),
            metadata={'consent_type': consent_type},
        )

        return consent

    @staticmethod
    @transaction.atomic
    def withdraw_consent(*, user: User, consent_type: str) -> None:
        """
        Withdraw user consent.
        """
        consents = ConsentRecord.objects.filter(
            user=user, consent_type=consent_type, withdrawn_at__isnull=True
        )

        if not consents.exists():
            raise BusinessValidationError('No active consent found for this type')

        for consent in consents:
            consent.withdrawn_at = timezone.now()
            consent.save(update_fields=['withdrawn_at'])

            AuditLog.objects.create(
                actor=user,
                action='consent_withdrawn',
                resource_type='consent',
                resource_id=str(consent.id),
                metadata={'consent_type': consent_type},
            )


class EEOService:
    """Service for EEO compliance and reporting."""

    @staticmethod
    def collect_eeo_data(
        *,
        candidate: CandidateProfile,
        gender: str | None = None,
        race_ethnicity: str | None = None,
        veteran_status: str | None = None,
        disability_status: str | None = None,
        consent_given: bool = True,
    ) -> EEOData:
        """
        Collect voluntary EEO self-identification data.

        CRITICAL: This data is encrypted and stored separately.
        It must NEVER be shown to hiring team.
        """
        # Check if EEO data already exists
        eeo_data, created = EEOData.objects.get_or_create(
            candidate=candidate,
            defaults={
                'gender': gender,
                'race_ethnicity': race_ethnicity,
                'veteran_status': veteran_status,
                'disability_status': disability_status,
                'consent_given': consent_given,
            },
        )

        if not created:
            # Update existing record
            eeo_data.gender = gender
            eeo_data.race_ethnicity = race_ethnicity
            eeo_data.veteran_status = veteran_status
            eeo_data.disability_status = disability_status
            eeo_data.consent_given = consent_given
            eeo_data.save()

        # Log collection (without sensitive data)
        AuditLog.objects.create(
            actor=candidate.user,
            action='eeo_data_collected',
            resource_type='eeo_data',
            resource_id=str(eeo_data.id),
            metadata={
                'consent_given': consent_given,
                'timestamp': timezone.now().isoformat(),
            },
        )

        return eeo_data

    @staticmethod
    def generate_eeo_report(
        *, start_date=None, end_date=None, department_id: str | None = None
    ) -> dict[str, Any]:
        """
        Generate aggregated EEO-1 report.

        CRITICAL: NO individual data is included, only aggregate counts.
        This ensures EEO data is never shown to hiring team.
        """
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Get applications in date range
        applications_qs = Application.objects.filter(
            applied_at__gte=start_date, applied_at__lte=end_date
        )

        if department_id:
            applications_qs = applications_qs.filter(requisition__department_id=department_id)

        # Get candidates who applied in this period
        candidate_ids = applications_qs.values_list('candidate_id', flat=True).distinct()

        # Get EEO data for these candidates (only if consent given)
        eeo_data = EEOData.objects.filter(
            candidate_id__in=candidate_ids, consent_given=True
        ).select_related('candidate')

        # Aggregate by categories (NO individual records)
        # Gender breakdown
        gender_counts = {}
        race_counts = {}
        veteran_counts = {}
        disability_counts = {}

        for data in eeo_data:
            # Gender
            gender = data.gender or 'Not Disclosed'
            gender_counts[gender] = gender_counts.get(gender, 0) + 1

            # Race/Ethnicity
            race = data.race_ethnicity or 'Not Disclosed'
            race_counts[race] = race_counts.get(race, 0) + 1

            # Veteran Status
            veteran = data.veteran_status or 'Not Disclosed'
            veteran_counts[veteran] = veteran_counts.get(veteran, 0) + 1

            # Disability Status
            disability = data.disability_status or 'Not Disclosed'
            disability_counts[disability] = disability_counts.get(disability, 0) + 1

        return {
            'report_type': 'EEO-1 Aggregate Report',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_applicants': len(candidate_ids),
            'total_with_eeo_data': eeo_data.count(),
            'breakdown': {
                'gender': gender_counts,
                'race_ethnicity': race_counts,
                'veteran_status': veteran_counts,
                'disability_status': disability_counts,
            },
            'generated_at': timezone.now().isoformat(),
            'note': 'This report contains only aggregated data. Individual responses are encrypted and not accessible.',
        }

    @staticmethod
    def adverse_impact_analysis(
        *, requisition_id: str | None = None, start_date=None, end_date=None
    ) -> dict[str, Any]:
        """
        Analyze for potential adverse impact in hiring.

        Uses the 4/5ths rule to identify disparate impact.
        Returns only statistical analysis, no individual data.
        """
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Get applications
        applications_qs = Application.objects.filter(
            applied_at__gte=start_date, applied_at__lte=end_date
        )

        if requisition_id:
            applications_qs = applications_qs.filter(requisition_id=requisition_id)

        # Get candidates
        candidate_ids = applications_qs.values_list('candidate_id', flat=True).distinct()

        # Get EEO data
        eeo_data = EEOData.objects.filter(
            candidate_id__in=candidate_ids, consent_given=True
        ).select_related('candidate')

        # Calculate hire rates by protected category
        analyses = []

        # Analyze by race/ethnicity
        race_analysis = {}
        for data in eeo_data:
            race = data.race_ethnicity or 'Not Disclosed'
            if race not in race_analysis:
                race_analysis[race] = {'applied': 0, 'hired': 0}

            race_analysis[race]['applied'] += 1

            # Check if hired
            if data.candidate.applications.filter(status='hired').exists():
                race_analysis[race]['hired'] += 1

        # Calculate rates and 4/5ths test
        max_hire_rate = 0
        for category, stats in race_analysis.items():
            if stats['applied'] > 0:
                stats['hire_rate'] = (stats['hired'] / stats['applied']) * 100
                max_hire_rate = max(max_hire_rate, stats['hire_rate'])

        # Check for adverse impact
        for category, stats in race_analysis.items():
            if stats['applied'] > 0 and max_hire_rate > 0:
                ratio = stats['hire_rate'] / max_hire_rate
                stats['ratio_to_highest'] = ratio
                stats['potential_adverse_impact'] = ratio < 0.8  # 4/5ths rule

        return {
            'report_type': 'Adverse Impact Analysis',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_applicants_analyzed': len(candidate_ids),
            'analysis': {
                'race_ethnicity': race_analysis,
            },
            'methodology': '4/5ths rule (80% rule) - hire rate for any group should be at least 80% of the highest group',
            'generated_at': timezone.now().isoformat(),
            'disclaimer': 'This analysis uses only consented, aggregated data. Results should be reviewed by legal counsel.',
        }
