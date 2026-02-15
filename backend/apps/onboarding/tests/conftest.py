"""Pytest configuration and fixtures for onboarding tests."""

import pytest


@pytest.fixture(autouse=True)
def onboarding_email_templates(db):
    """Create required email templates for onboarding tests."""
    from apps.communications.models import EmailTemplate

    # Create "Onboarding Completed" template for candidates
    EmailTemplate.objects.get_or_create(
        name='Onboarding Completed',
        defaults={
            'category': 'onboarding',
            'subject': 'Welcome to {{company_name}} - Onboarding Complete!',
            'body_html': '<p>Dear {{candidate_name}},</p><p>Congratulations! You have successfully completed your onboarding for the {{job_title}} position.</p><p>Completion Date: {{completion_date}}</p>',
            'body_text': 'Dear {{candidate_name}},\n\nCongratulations! You have successfully completed your onboarding for the {{job_title}} position.\n\nCompletion Date: {{completion_date}}',
            'is_active': True,
            'variables': {
                'candidate_name': 'string',
                'job_title': 'string',
                'completion_date': 'string',
                'company_name': 'string',
            },
        },
    )

    # Create "Onboarding Completed (HR)" template for HR contacts
    EmailTemplate.objects.get_or_create(
        name='Onboarding Completed (HR)',
        defaults={
            'category': 'onboarding',
            'subject': '{{candidate_name}} - Onboarding Completed',
            'body_html': '<p>Dear {{hr_name}},</p><p>{{candidate_name}} has successfully completed onboarding for the {{job_title}} position.</p><p>Completion Date: {{completion_date}}</p>',
            'body_text': 'Dear {{hr_name}},\n\n{{candidate_name}} has successfully completed onboarding for the {{job_title}} position.\n\nCompletion Date: {{completion_date}}',
            'is_active': True,
            'variables': {
                'hr_name': 'string',
                'candidate_name': 'string',
                'job_title': 'string',
                'completion_date': 'string',
            },
        },
    )
