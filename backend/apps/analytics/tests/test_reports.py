"""Tests for report selectors and services."""

import pytest
from django.utils import timezone

from apps.accounts.tests.factories import InternalUserFactory, UserFactory
from apps.analytics.selectors import ReportSelector
from apps.analytics.services import ReportService
from apps.applications.tests.factories import ApplicationFactory
from apps.core.exceptions import BusinessValidationError
from apps.interviews.tests.factories import ScorecardFactory
from apps.jobs.tests.factories import RequisitionFactory
from apps.offers.tests.factories import OfferFactory


@pytest.mark.django_db
class TestPipelineConversionReport:
    """Tests for pipeline conversion report."""

    def test_pipeline_conversion_report(self):
        """Pipeline conversion report shows correct conversions."""
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)

        # Create applications in different statuses
        ApplicationFactory(status='applied', applied_at=start_date + timezone.timedelta(days=1))
        ApplicationFactory(status='applied', applied_at=start_date + timezone.timedelta(days=2))
        ApplicationFactory(status='screening', applied_at=start_date + timezone.timedelta(days=3))
        ApplicationFactory(status='interview', applied_at=start_date + timezone.timedelta(days=4))
        ApplicationFactory(status='hired', applied_at=start_date + timezone.timedelta(days=5))

        report = ReportSelector.get_pipeline_conversion_report(
            start_date=start_date,
            end_date=end_date,
        )

        assert report['total_applications'] == 5
        assert len(report['conversions']) > 0

        # Verify each status is represented
        statuses = [c['stage'] for c in report['conversions']]
        assert 'Applied' in statuses
        assert 'Hired' in statuses


@pytest.mark.django_db
class TestTimeToFillReport:
    """Tests for time-to-fill report."""

    def test_time_to_fill_report(self):
        """Time to fill report shows correct averages."""
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)

        # Create filled requisitions
        req1 = RequisitionFactory(
            status='filled',
            opened_at=start_date,
        )

        # Update closed_at
        from apps.jobs.models import Requisition
        Requisition.objects.filter(id=req1.id).update(
            closed_at=start_date + timezone.timedelta(days=20),
        )

        report = ReportSelector.get_time_to_fill_report(
            start_date=start_date,
            end_date=end_date,
        )

        assert report['overall_avg_days'] > 0
        assert 'by_department' in report
        assert 'by_level' in report


@pytest.mark.django_db
class TestSourceEffectivenessReport:
    """Tests for source effectiveness report."""

    def test_source_effectiveness_report(self):
        """Source effectiveness report shows correct metrics."""
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)

        # Create applications from different sources
        # LinkedIn: 5 total, 1 hired
        for i in range(5):
            ApplicationFactory(
                source='linkedin',
                status='hired' if i == 0 else 'applied',
                applied_at=start_date + timezone.timedelta(days=i),
            )

        # Indeed: 3 total, 0 hired
        for i in range(3):
            ApplicationFactory(
                source='indeed',
                status='applied',
                applied_at=start_date + timezone.timedelta(days=i),
            )

        report = ReportSelector.get_source_effectiveness_report(
            start_date=start_date,
            end_date=end_date,
        )

        sources = report['sources']
        assert len(sources) == 2

        linkedin_source = next((s for s in sources if s['source'] == 'linkedin'), None)
        assert linkedin_source is not None
        assert linkedin_source['applications'] == 5
        assert linkedin_source['hires'] == 1
        assert linkedin_source['hire_rate'] == 20.0


@pytest.mark.django_db
class TestOfferAnalysisReport:
    """Tests for offer analysis report."""

    def test_offer_analysis_report(self):
        """Offer analysis report shows correct metrics."""
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)

        # Create offers with different statuses
        OfferFactory(status='accepted', created_at=start_date + timezone.timedelta(days=1))
        OfferFactory(status='accepted', created_at=start_date + timezone.timedelta(days=2))
        OfferFactory(status='declined', created_at=start_date + timezone.timedelta(days=3))
        OfferFactory(status='active', created_at=start_date + timezone.timedelta(days=4))

        report = ReportSelector.get_offer_analysis_report(
            start_date=start_date,
            end_date=end_date,
        )

        assert report['total_offers'] == 4
        assert report['accepted'] == 2
        assert report['declined'] == 1
        assert report['pending'] == 1
        assert report['acceptance_rate'] == 50.0  # 2/4
        assert report['decline_rate'] == 25.0  # 1/4


@pytest.mark.django_db
class TestInterviewerCalibrationReport:
    """Tests for interviewer calibration report."""

    def test_interviewer_calibration_report(self):
        """Interviewer calibration report shows correct metrics."""
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)

        interviewer1 = InternalUserFactory()
        interviewer2 = InternalUserFactory()

        # Create scorecards for interviewer 1 (3 scorecards, 2 hire recommendations)
        for i in range(3):
            ScorecardFactory(
                interviewer=interviewer1,
                overall_rating=4,
                recommendation='hire' if i < 2 else 'no_hire',
                submitted_at=start_date + timezone.timedelta(days=i),
            )

        # Create scorecards for interviewer 2 (2 scorecards, 0 hire recommendations)
        for i in range(2):
            ScorecardFactory(
                interviewer=interviewer2,
                overall_rating=2,
                recommendation='no_hire',
                submitted_at=start_date + timezone.timedelta(days=i),
            )

        report = ReportSelector.get_interviewer_calibration_report(
            start_date=start_date,
            end_date=end_date,
        )

        assert report['total_scorecards'] == 5
        assert len(report['interviewers']) == 2

        # Find interviewer 1 in results
        int1_data = next(
            (i for i in report['interviewers']
             if interviewer1.user.get_full_name() in i['interviewer']),
            None,
        )
        assert int1_data is not None
        assert int1_data['scorecards_count'] == 3
        assert int1_data['hire_rate'] == pytest.approx(66.67, rel=0.1)


@pytest.mark.django_db
class TestRequisitionAgingReport:
    """Tests for requisition aging report."""

    def test_requisition_aging_report(self):
        """Requisition aging report shows correct age buckets."""
        now = timezone.now()

        # Create requisitions with different ages
        req1 = RequisitionFactory(
            status='open',
            opened_at=now - timezone.timedelta(days=10),
        )
        req2 = RequisitionFactory(
            status='open',
            opened_at=now - timezone.timedelta(days=50),
        )
        req3 = RequisitionFactory(
            status='open',
            opened_at=now - timezone.timedelta(days=100),
        )

        report = ReportSelector.get_requisition_aging_report()

        assert report['total_open'] == 3
        assert 'by_age_bucket' in report

        # Check buckets
        assert report['by_age_bucket']['0-30 days']['count'] == 1
        assert report['by_age_bucket']['31-60 days']['count'] == 1
        assert report['by_age_bucket']['90+ days']['count'] == 1


@pytest.mark.django_db
class TestReportService:
    """Tests for ReportService."""

    def test_generate_report_json_format(self):
        """Report is generated in JSON format."""
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)

        # Create some data
        ApplicationFactory(status='applied', applied_at=start_date + timezone.timedelta(days=1))

        report = ReportService.generate_report(
            report_type='pipeline_conversion',
            format='json',
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(report, dict)
        assert 'total_applications' in report
        assert 'conversions' in report

    def test_generate_report_csv_format(self):
        """Report is generated in CSV format."""
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)

        ApplicationFactory(status='applied', applied_at=start_date + timezone.timedelta(days=1))

        report = ReportService.generate_report(
            report_type='pipeline_conversion',
            format='csv',
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(report, str)
        assert 'Pipeline Conversion Report' in report
        assert 'Stage' in report

    def test_generate_report_excel_format(self):
        """Report is generated in Excel format."""
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)

        ApplicationFactory(status='applied', applied_at=start_date + timezone.timedelta(days=1))

        report = ReportService.generate_report(
            report_type='pipeline_conversion',
            format='excel',
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(report, bytes)
        assert len(report) > 0

    def test_generate_report_invalid_type(self):
        """Invalid report type raises error."""
        with pytest.raises(BusinessValidationError, match='Invalid report type'):
            ReportService.generate_report(
                report_type='invalid_type',
                format='json',
            )

    def test_generate_report_invalid_format(self):
        """Invalid format raises error."""
        with pytest.raises(BusinessValidationError, match='Invalid format'):
            ReportService.generate_report(
                report_type='pipeline_conversion',
                format='pdf',
            )

    def test_generate_report_uses_default_dates(self):
        """Report uses default date range if not provided."""
        report = ReportService.generate_report(
            report_type='pipeline_conversion',
            format='json',
        )

        assert isinstance(report, dict)
        assert 'period' in report

    def test_generate_source_effectiveness_csv(self):
        """Source effectiveness report generates CSV correctly."""
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)

        ApplicationFactory(
            source='linkedin',
            status='hired',
            applied_at=start_date + timezone.timedelta(days=1),
        )

        report = ReportService.generate_report(
            report_type='source_effectiveness',
            format='csv',
            start_date=start_date,
            end_date=end_date,
        )

        assert 'Source Effectiveness Report' in report
        assert 'linkedin' in report
        assert 'Applications' in report
