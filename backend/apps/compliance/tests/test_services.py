"""Tests for compliance services."""

import pytest
from django.utils import timezone

from apps.accounts.tests.factories import CandidateProfileFactory, UserFactory
from apps.applications.tests.factories import ApplicationFactory
from apps.compliance.models import AnonymizationRecord, AuditLog, ConsentRecord, EEOData
from apps.compliance.services import EEOService, GDPRService
from apps.core.exceptions import BusinessValidationError


@pytest.mark.django_db
class TestGDPRService:
    """Tests for GDPR compliance service."""

    def test_export_candidate_data(self):
        """Candidate data export includes all personal information."""
        candidate = CandidateProfileFactory()
        ApplicationFactory(candidate=candidate, status='applied')
        ApplicationFactory(candidate=candidate, status='hired')

        data = GDPRService.export_candidate_data(candidate)

        assert 'profile' in data
        assert 'applications' in data
        assert 'interviews' in data
        assert 'audit_trail' in data
        assert 'consents' in data
        assert 'exported_at' in data

        # Verify profile data
        assert data['profile']['user']['email'] == candidate.user.email
        assert data['profile']['phone'] == candidate.phone

        # Verify applications
        assert len(data['applications']) == 2
        assert data['applications'][0]['status'] in ['applied', 'hired']

        # Verify audit log was created
        log = AuditLog.objects.filter(
            action='data_export', resource_type='candidate', resource_id=str(candidate.id)
        ).first()
        assert log is not None

    def test_anonymize_candidate_removes_pii(self):
        """Anonymization removes all PII from candidate."""
        candidate = CandidateProfileFactory(
            phone='+1234567890', linkedin_url='https://linkedin.com/in/candidate'
        )
        ApplicationFactory(
            candidate=candidate,
            cover_letter='My cover letter',
            screening_responses={'question': 'answer'},
        )

        # Anonymize
        record = GDPRService.anonymize_candidate(
            candidate, reason='User requested deletion', anonymized_by=None
        )

        # Refresh from database
        candidate.refresh_from_db()
        candidate.user.refresh_from_db()

        # Verify user data anonymized
        assert candidate.user.email.startswith('deleted_')
        assert candidate.user.email.endswith('@anonymized.local')
        assert candidate.user.first_name == 'Deleted'
        assert candidate.user.last_name == 'User'
        assert not candidate.user.is_active

        # Verify candidate data anonymized
        assert candidate.phone == ''
        assert candidate.linkedin_url == ''

        # Verify application data anonymized
        app = candidate.applications.first()
        assert app.cover_letter == ''
        assert app.screening_responses == {}

        # Verify anonymization record created
        assert isinstance(record, AnonymizationRecord)
        assert record.candidate_id == candidate.id
        assert record.reason == 'User requested deletion'
        assert record.applications_count == 1

    def test_anonymize_candidate_preserves_audit_trail(self):
        """Anonymization creates audit trail."""
        candidate = CandidateProfileFactory()
        actor = UserFactory()

        GDPRService.anonymize_candidate(
            candidate, reason='Test deletion', anonymized_by=actor
        )

        # Verify audit log created
        log = AuditLog.objects.filter(
            action='anonymize', resource_type='candidate', resource_id=str(candidate.id)
        ).first()
        assert log is not None
        assert log.actor == actor
        assert log.metadata['reason'] == 'Test deletion'

    def test_anonymize_candidate_deletes_eeo_data(self):
        """Anonymization deletes EEO data."""
        candidate = CandidateProfileFactory()

        # Create EEO data
        EEOData.objects.create(
            candidate=candidate,
            gender='Female',
            race_ethnicity='Asian',
            veteran_status='Not a veteran',
            disability_status='No disability',
        )

        assert hasattr(candidate, 'eeo_data')

        # Anonymize
        GDPRService.anonymize_candidate(candidate, reason='User request', anonymized_by=None)

        # Verify EEO data deleted
        candidate.refresh_from_db()
        assert not hasattr(candidate, 'eeo_data')

    def test_record_consent_creates_consent(self):
        """Recording consent creates consent record."""
        user = UserFactory()

        consent = GDPRService.record_consent(
            user=user,
            consent_type='data_processing',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
        )

        assert isinstance(consent, ConsentRecord)
        assert consent.user == user
        assert consent.consent_type == 'data_processing'
        assert consent.ip_address == '192.168.1.1'
        assert consent.user_agent == 'Mozilla/5.0'
        assert consent.is_active

        # Verify audit log
        log = AuditLog.objects.filter(
            action='consent_given', resource_type='consent'
        ).first()
        assert log is not None

    def test_record_consent_reuses_existing_active(self):
        """Recording consent reuses existing active consent."""
        user = UserFactory()

        # Create first consent
        consent1 = GDPRService.record_consent(user=user, consent_type='marketing')

        # Try to create again
        consent2 = GDPRService.record_consent(user=user, consent_type='marketing')

        assert consent1.id == consent2.id

    def test_record_consent_invalid_type_raises_error(self):
        """Invalid consent type raises error."""
        user = UserFactory()

        with pytest.raises(BusinessValidationError, match='Invalid consent type'):
            GDPRService.record_consent(user=user, consent_type='invalid_type')

    def test_withdraw_consent_updates_timestamp(self):
        """Withdrawing consent sets withdrawn_at timestamp."""
        user = UserFactory()

        # Create consent
        consent = GDPRService.record_consent(user=user, consent_type='data_sharing')

        # Withdraw
        GDPRService.withdraw_consent(user=user, consent_type='data_sharing')

        # Verify withdrawn
        consent.refresh_from_db()
        assert consent.withdrawn_at is not None
        assert not consent.is_active

        # Verify audit log
        log = AuditLog.objects.filter(
            action='consent_withdrawn', resource_type='consent'
        ).first()
        assert log is not None

    def test_withdraw_consent_no_active_raises_error(self):
        """Withdrawing non-existent consent raises error."""
        user = UserFactory()

        with pytest.raises(BusinessValidationError, match='No active consent found'):
            GDPRService.withdraw_consent(user=user, consent_type='marketing')

    def test_process_data_retention_deletes_old_applications(self):
        """Data retention processing deletes old rejected applications."""
        from apps.compliance.models import DataRetentionPolicy

        # Create retention policy for applications (30 days + 7 days grace)
        DataRetentionPolicy.objects.create(
            data_type='candidate_application',
            retention_days=30,
            grace_period_days=7,
            is_active=True,
        )

        # Create old rejected application (40 days ago)
        old_app = ApplicationFactory(status='rejected')
        from apps.applications.models import Application

        Application.objects.filter(id=old_app.id).update(
            updated_at=timezone.now() - timezone.timedelta(days=40)
        )

        # Create recent rejected application (10 days ago)
        recent_app = ApplicationFactory(status='rejected')
        Application.objects.filter(id=recent_app.id).update(
            updated_at=timezone.now() - timezone.timedelta(days=10)
        )

        # Process retention
        counts = GDPRService.process_data_retention()

        # Verify old application's candidate was anonymized
        old_app.candidate.refresh_from_db()
        assert old_app.candidate.user.email.startswith('deleted_')

        # Verify recent application still exists
        recent_app.candidate.refresh_from_db()
        assert not recent_app.candidate.user.email.startswith('deleted_')


@pytest.mark.django_db
class TestEEOService:
    """Tests for EEO compliance service."""

    def test_collect_eeo_data_creates_record(self):
        """Collecting EEO data creates encrypted record."""
        candidate = CandidateProfileFactory()

        eeo_data = EEOService.collect_eeo_data(
            candidate=candidate,
            gender='Female',
            race_ethnicity='Hispanic or Latino',
            veteran_status='Not a veteran',
            disability_status='No disability',
            consent_given=True,
        )

        assert isinstance(eeo_data, EEOData)
        assert eeo_data.candidate == candidate
        assert eeo_data.gender == 'Female'
        assert eeo_data.race_ethnicity == 'Hispanic or Latino'
        assert eeo_data.veteran_status == 'Not a veteran'
        assert eeo_data.disability_status == 'No disability'
        assert eeo_data.consent_given

        # Verify audit log (without sensitive data)
        log = AuditLog.objects.filter(
            action='eeo_data_collected', resource_type='eeo_data'
        ).first()
        assert log is not None
        assert 'gender' not in log.metadata  # Sensitive data not in logs

    def test_collect_eeo_data_updates_existing(self):
        """Collecting EEO data updates existing record."""
        candidate = CandidateProfileFactory()

        # Create initial EEO data
        eeo1 = EEOService.collect_eeo_data(
            candidate=candidate,
            gender='Male',
            race_ethnicity='White',
            veteran_status='Not a veteran',
            disability_status='No disability',
            consent_given=True,
        )

        # Update
        eeo2 = EEOService.collect_eeo_data(
            candidate=candidate,
            gender='Female',
            race_ethnicity='White',
            veteran_status='Not a veteran',
            disability_status='No disability',
            consent_given=True,
        )

        assert eeo1.id == eeo2.id
        eeo1.refresh_from_db()
        assert eeo1.gender == 'Female'

    def test_generate_eeo_report_aggregates_data(self):
        """EEO report contains only aggregate data, no individuals."""
        # Create candidates with EEO data
        for i in range(10):
            candidate = CandidateProfileFactory()
            ApplicationFactory(candidate=candidate, status='applied')
            EEOService.collect_eeo_data(
                candidate=candidate,
                gender='Female' if i % 2 == 0 else 'Male',
                race_ethnicity='Asian' if i < 5 else 'White',
                veteran_status='Not a veteran',
                disability_status='No disability',
                consent_given=True,
            )

        # Generate report
        report = EEOService.generate_eeo_report()

        assert report['report_type'] == 'EEO-1 Aggregate Report'
        assert report['total_applicants'] == 10
        assert report['total_with_eeo_data'] == 10

        # Verify gender breakdown
        assert 'breakdown' in report
        assert 'gender' in report['breakdown']
        assert report['breakdown']['gender']['Female'] == 5
        assert report['breakdown']['gender']['Male'] == 5

        # Verify race breakdown
        assert 'race_ethnicity' in report['breakdown']
        assert report['breakdown']['race_ethnicity']['Asian'] == 5
        assert report['breakdown']['race_ethnicity']['White'] == 5

        # Ensure no individual data
        assert 'candidates' not in report
        assert 'applications' not in report

    def test_generate_eeo_report_only_includes_consented(self):
        """EEO report only includes candidates who consented."""
        # Candidate with consent
        candidate1 = CandidateProfileFactory()
        ApplicationFactory(candidate=candidate1)
        EEOService.collect_eeo_data(
            candidate=candidate1,
            gender='Female',
            race_ethnicity='Asian',
            veteran_status='Not a veteran',
            disability_status='No disability',
            consent_given=True,
        )

        # Candidate without consent
        candidate2 = CandidateProfileFactory()
        ApplicationFactory(candidate=candidate2)
        EEOService.collect_eeo_data(
            candidate=candidate2,
            gender='Male',
            race_ethnicity='White',
            veteran_status='Not a veteran',
            disability_status='No disability',
            consent_given=False,
        )

        # Generate report
        report = EEOService.generate_eeo_report()

        # Should only count the consented candidate
        assert report['total_applicants'] == 2
        assert report['total_with_eeo_data'] == 1
        assert report['breakdown']['gender'] == {'Female': 1}

    def test_adverse_impact_analysis_detects_disparity(self):
        """Adverse impact analysis detects hiring disparities."""
        from apps.jobs.tests.factories import PipelineStageFactory, RequisitionFactory

        requisition = RequisitionFactory()

        # Create a pipeline stage for the requisition
        stage = PipelineStageFactory(requisition=requisition, order=0)

        # Create applications: 10 from Group A, 10 from Group B
        # Group A: 8 hired (80% hire rate)
        # Group B: 4 hired (40% hire rate) - potential adverse impact

        for i in range(10):
            candidate = CandidateProfileFactory()
            app = ApplicationFactory(
                candidate=candidate,
                requisition=requisition,
                current_stage=stage,
                status='hired' if i < 8 else 'rejected',
            )
            EEOService.collect_eeo_data(
                candidate=candidate,
                gender='Not disclosed',
                race_ethnicity='Group A',
                veteran_status='Not disclosed',
                disability_status='Not disclosed',
                consent_given=True,
            )

        for i in range(10):
            candidate = CandidateProfileFactory()
            app = ApplicationFactory(
                candidate=candidate,
                requisition=requisition,
                current_stage=stage,
                status='hired' if i < 4 else 'rejected',
            )
            EEOService.collect_eeo_data(
                candidate=candidate,
                gender='Not disclosed',
                race_ethnicity='Group B',
                veteran_status='Not disclosed',
                disability_status='Not disclosed',
                consent_given=True,
            )

        # Run analysis
        analysis = EEOService.adverse_impact_analysis(requisition_id=str(requisition.id))

        assert analysis['report_type'] == 'Adverse Impact Analysis'
        assert 'analysis' in analysis
        assert 'race_ethnicity' in analysis['analysis']

        race_analysis = analysis['analysis']['race_ethnicity']

        # Group A should have 80% hire rate
        assert race_analysis['Group A']['hire_rate'] == 80.0
        assert race_analysis['Group A']['applied'] == 10
        assert race_analysis['Group A']['hired'] == 8

        # Group B should have 40% hire rate
        assert race_analysis['Group B']['hire_rate'] == 40.0
        assert race_analysis['Group B']['applied'] == 10
        assert race_analysis['Group B']['hired'] == 4

        # Group B should be flagged for adverse impact (40/80 = 0.5 < 0.8)
        assert race_analysis['Group B']['ratio_to_highest'] == 0.5
        assert race_analysis['Group B']['potential_adverse_impact'] is True

        # Group A should not be flagged
        assert race_analysis['Group A']['ratio_to_highest'] == 1.0
        assert race_analysis['Group A']['potential_adverse_impact'] is False
