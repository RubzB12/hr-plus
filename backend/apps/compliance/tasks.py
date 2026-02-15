"""Celery tasks for compliance automation."""

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from apps.core.exceptions import BusinessValidationError

from .models import AuditLog, DataRetentionPolicy
from .services import EEOService, GDPRService


@shared_task(name='compliance.process_data_retention')
def process_data_retention():
    """
    Process all active data retention policies.

    This task should be scheduled to run daily (e.g., 2 AM).
    It automatically deletes/anonymizes data based on configured retention policies.
    """
    try:
        deleted_counts = GDPRService.process_data_retention()

        # Log results
        AuditLog.objects.create(
            actor=None,
            action='data_retention_processed',
            resource_type='system',
            resource_id='data_retention',
            metadata={
                'deleted_counts': deleted_counts,
                'timestamp': timezone.now().isoformat(),
            },
        )

        return {
            'success': True,
            'deleted_counts': deleted_counts,
            'message': f'Data retention processed. Deleted: {deleted_counts}',
        }
    except Exception as e:
        # Log error
        AuditLog.objects.create(
            actor=None,
            action='data_retention_failed',
            resource_type='system',
            resource_id='data_retention',
            metadata={
                'error': str(e),
                'timestamp': timezone.now().isoformat(),
            },
        )
        raise


@shared_task(name='compliance.generate_monthly_eeo_report')
def generate_monthly_eeo_report(department_id=None):
    """
    Generate and email monthly EEO compliance report.

    This task should be scheduled to run monthly (e.g., 1st of each month).
    Sends aggregated EEO reports to compliance team.
    """
    from datetime import timedelta

    try:
        # Calculate last month's date range
        today = timezone.now()
        first_of_month = today.replace(day=1)
        end_date = first_of_month
        start_date = (first_of_month - timedelta(days=1)).replace(day=1)

        # Generate report
        report = EEOService.generate_eeo_report(
            start_date=start_date, end_date=end_date, department_id=department_id
        )

        # Email to compliance team
        compliance_emails = getattr(settings, 'COMPLIANCE_TEAM_EMAILS', [])

        if compliance_emails:
            email = EmailMessage(
                subject=f'Monthly EEO Report - {start_date.strftime("%B %Y")}',
                body=f"""Monthly EEO Compliance Report

Period: {start_date.strftime("%B %d, %Y")} - {end_date.strftime("%B %d, %Y")}

Total Applicants: {report['total_applicants']}
Total with EEO Data: {report['total_with_eeo_data']}

Breakdown:
- Gender: {report['breakdown']['gender']}
- Race/Ethnicity: {report['breakdown']['race_ethnicity']}
- Veteran Status: {report['breakdown']['veteran_status']}
- Disability Status: {report['breakdown']['disability_status']}

This report contains only aggregated data. Individual responses are encrypted and not accessible.

Generated: {report['generated_at']}
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=compliance_emails,
            )

            # Attach JSON report
            import json

            email.attach(
                f'eeo_report_{start_date.strftime("%Y_%m")}.json',
                json.dumps(report, indent=2),
                'application/json',
            )

            email.send()

        # Log report generation
        AuditLog.objects.create(
            actor=None,
            action='eeo_report_generated',
            resource_type='report',
            resource_id='monthly_eeo',
            metadata={
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'total_applicants': report['total_applicants'],
                'department_id': department_id,
            },
        )

        return {
            'success': True,
            'report': report,
            'message': f'EEO report generated for {start_date.strftime("%B %Y")}',
        }
    except Exception as e:
        AuditLog.objects.create(
            actor=None,
            action='eeo_report_generation_failed',
            resource_type='report',
            resource_id='monthly_eeo',
            metadata={'error': str(e), 'timestamp': timezone.now().isoformat()},
        )
        raise


@shared_task(name='compliance.generate_adverse_impact_analysis')
def generate_adverse_impact_analysis(requisition_id=None):
    """
    Generate adverse impact analysis for hiring patterns.

    This task should be run quarterly or as needed to check for
    potential disparate impact in hiring decisions.
    """
    try:
        analysis = EEOService.adverse_impact_analysis(requisition_id=requisition_id)

        # Check for potential issues
        has_adverse_impact = False
        flagged_categories = []

        if 'analysis' in analysis and 'race_ethnicity' in analysis['analysis']:
            for category, stats in analysis['analysis']['race_ethnicity'].items():
                if stats.get('potential_adverse_impact'):
                    has_adverse_impact = True
                    flagged_categories.append(category)

        # If adverse impact detected, email compliance team
        if has_adverse_impact:
            compliance_emails = getattr(settings, 'COMPLIANCE_TEAM_EMAILS', [])

            if compliance_emails:
                email = EmailMessage(
                    subject='⚠️ Adverse Impact Analysis - Action Required',
                    body=f"""ALERT: Potential Adverse Impact Detected

Requisition: {requisition_id or 'All Positions'}

Flagged Categories: {', '.join(flagged_categories)}

The 4/5ths rule analysis has detected potential disparate impact in hiring.
These categories have hire rates below 80% of the highest group.

This requires immediate review by legal counsel and HR leadership.

Generated: {analysis['generated_at']}

Please review the full analysis attached.
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=compliance_emails,
                )

                # Attach full analysis
                import json

                email.attach(
                    'adverse_impact_analysis.json',
                    json.dumps(analysis, indent=2),
                    'application/json',
                )

                email.send()

        # Log analysis
        AuditLog.objects.create(
            actor=None,
            action='adverse_impact_analyzed',
            resource_type='report',
            resource_id='adverse_impact',
            metadata={
                'requisition_id': requisition_id,
                'has_adverse_impact': has_adverse_impact,
                'flagged_categories': flagged_categories,
                'timestamp': timezone.now().isoformat(),
            },
        )

        return {
            'success': True,
            'has_adverse_impact': has_adverse_impact,
            'flagged_categories': flagged_categories,
            'analysis': analysis,
        }
    except Exception as e:
        AuditLog.objects.create(
            actor=None,
            action='adverse_impact_analysis_failed',
            resource_type='report',
            resource_id='adverse_impact',
            metadata={'error': str(e), 'timestamp': timezone.now().isoformat()},
        )
        raise


@shared_task(name='compliance.cleanup_old_audit_logs')
def cleanup_old_audit_logs(retention_years=7):
    """
    Archive/cleanup old audit logs while maintaining minimum 7-year retention.

    This task should be scheduled to run monthly.
    Audit logs must be kept for at least 7 years for legal compliance.
    """
    from datetime import timedelta

    try:
        # Calculate cutoff date (7 years ago by default)
        cutoff_date = timezone.now() - timedelta(days=retention_years * 365)

        # Count logs older than retention period
        old_logs_count = AuditLog.objects.filter(timestamp__lt=cutoff_date).count()

        if old_logs_count > 0:
            # In production, you might want to:
            # 1. Export to long-term storage (S3, etc.)
            # 2. Compress and archive
            # 3. Then delete from active database

            # For now, we'll just log the count
            # DO NOT actually delete yet - implement archival first
            pass

        # Log cleanup operation
        AuditLog.objects.create(
            actor=None,
            action='audit_log_cleanup_checked',
            resource_type='system',
            resource_id='audit_logs',
            metadata={
                'retention_years': retention_years,
                'cutoff_date': cutoff_date.isoformat(),
                'old_logs_count': old_logs_count,
                'archived': False,  # Set to True when archival is implemented
                'timestamp': timezone.now().isoformat(),
            },
        )

        return {
            'success': True,
            'old_logs_count': old_logs_count,
            'cutoff_date': cutoff_date.isoformat(),
            'message': f'Found {old_logs_count} audit logs older than {retention_years} years',
        }
    except Exception as e:
        AuditLog.objects.create(
            actor=None,
            action='audit_log_cleanup_failed',
            resource_type='system',
            resource_id='audit_logs',
            metadata={'error': str(e), 'timestamp': timezone.now().isoformat()},
        )
        raise


@shared_task(name='compliance.send_consent_renewal_reminders')
def send_consent_renewal_reminders():
    """
    Send reminders to users to renew their data processing consents.

    Some jurisdictions require periodic consent renewal.
    This task identifies consents older than 1 year and sends renewal requests.
    """
    from datetime import timedelta

    from apps.accounts.models import User

    from .models import ConsentRecord

    try:
        # Find consents given more than 1 year ago
        one_year_ago = timezone.now() - timedelta(days=365)

        old_consents = ConsentRecord.objects.filter(
            given_at__lt=one_year_ago, withdrawn_at__isnull=True
        ).select_related('user')

        reminders_sent = 0

        for consent in old_consents:
            # Check if user still active
            if not consent.user.is_active:
                continue

            # Send renewal reminder email
            email = EmailMessage(
                subject='Action Required: Renew Your Data Processing Consent',
                body=f"""Dear {consent.user.get_full_name()},

Your consent for {consent.get_consent_type_display()} was given on {consent.given_at.strftime("%B %d, %Y")}.

To continue using our services, please renew your consent by logging into your account
and reviewing your privacy settings.

If you have any questions, please contact our Privacy Team at privacy@company.com.

Best regards,
HR Team
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[consent.user.email],
            )

            email.send()
            reminders_sent += 1

        # Log reminder operation
        AuditLog.objects.create(
            actor=None,
            action='consent_renewal_reminders_sent',
            resource_type='system',
            resource_id='consent_renewal',
            metadata={
                'reminders_sent': reminders_sent,
                'cutoff_date': one_year_ago.isoformat(),
                'timestamp': timezone.now().isoformat(),
            },
        )

        return {
            'success': True,
            'reminders_sent': reminders_sent,
            'message': f'Sent {reminders_sent} consent renewal reminders',
        }
    except Exception as e:
        AuditLog.objects.create(
            actor=None,
            action='consent_renewal_reminders_failed',
            resource_type='system',
            resource_id='consent_renewal',
            metadata={'error': str(e), 'timestamp': timezone.now().isoformat()},
        )
        raise
