"""
Management command to seed email templates into the database.

Usage:
    python manage.py seed_email_templates
    python manage.py seed_email_templates --clear  # Clear existing first
"""

from django.core.management.base import BaseCommand
from apps.communications.models import EmailTemplate


class Command(BaseCommand):
    help = 'Seeds email templates into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing templates before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = EmailTemplate.objects.all().count()
            EmailTemplate.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing templates'))

        templates = [
            # Password Reset
            {
                'name': 'Password Reset',
                'category': 'general',
                'subject': 'Reset Your HR-Plus Password',
                'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; }
        .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
        .content { padding: 40px 30px; }
        .button { display: inline-block; background: #667eea; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }
        .button:hover { background: #5568d3; }
        .footer { background: #f8f9fa; padding: 20px 30px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #e9ecef; }
        .info-box { background: #f8f9fa; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .token { font-family: 'Courier New', monospace; background: #e9ecef; padding: 10px; border-radius: 4px; font-size: 18px; letter-spacing: 2px; text-align: center; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Password Reset</h1>
        </div>
        <div class="content">
            <p>Hi {{user_name}},</p>

            <p>We received a request to reset your password for your HR-Plus account. If you didn't make this request, you can safely ignore this email.</p>

            <p>To reset your password, click the button below:</p>

            <center>
                <a href="{{reset_link}}" class="button">Reset Password</a>
            </center>

            <div class="info-box">
                <strong>⏱️ This link expires in {{expiry_hours}} hours</strong><br>
                For security reasons, password reset links are only valid for a limited time.
            </div>

            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #667eea;">{{reset_link}}</p>

            <p style="margin-top: 30px; color: #6c757d; font-size: 14px;">If you didn't request a password reset, please contact our support team immediately.</p>
        </div>
        <div class="footer">
            <p><strong>HR-Plus</strong> - Enterprise HR Platform</p>
            <p>This is an automated message. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
''',
                'body_text': '''Hi {{user_name}},

We received a request to reset your password for your HR-Plus account. If you didn't make this request, you can safely ignore this email.

To reset your password, visit this link:
{{reset_link}}

This link expires in {{expiry_hours}} hours.

If you didn't request a password reset, please contact our support team immediately.

---
HR-Plus - Enterprise HR Platform
This is an automated message. Please do not reply to this email.
''',
                'is_active': True,
                'variables': {
                    'user_name': 'string',
                    'reset_link': 'string',
                    'expiry_hours': 'integer',
                },
            },
            # Application Confirmation
            {
                'name': 'Application Confirmation',
                'category': 'application',
                'subject': 'Application Received - {{job_title}}',
                'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; }
        .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
        .content { padding: 40px 30px; }
        .success-badge { background: #d4edda; color: #155724; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; border: 2px solid #c3e6cb; }
        .info-box { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .info-box h3 { margin-top: 0; color: #667eea; }
        .button { display: inline-block; background: #667eea; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }
        .footer { background: #f8f9fa; padding: 20px 30px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #e9ecef; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Application Received!</h1>
        </div>
        <div class="content">
            <div class="success-badge">
                <strong>Your application has been successfully submitted</strong>
            </div>

            <p>Hi {{candidate_name}},</p>

            <p>Thank you for applying to <strong>{{company_name}}</strong>! We're excited that you're interested in the <strong>{{job_title}}</strong> position.</p>

            <div class="info-box">
                <h3>Application Details</h3>
                <p><strong>Application ID:</strong> {{application_id}}</p>
                <p><strong>Position:</strong> {{job_title}}</p>
                <p><strong>Submitted:</strong> {{submitted_date}}</p>
            </div>

            <p><strong>What happens next?</strong></p>
            <ul>
                <li>Our hiring team will review your application</li>
                <li>We'll notify you of any updates via email</li>
                <li>If selected, we'll reach out to schedule an interview</li>
            </ul>

            <center>
                <a href="{{dashboard_link}}" class="button">View Application Status</a>
            </center>

            <p style="margin-top: 30px;">We review all applications carefully. Due to the high volume of applications, we may take some time to respond. We appreciate your patience!</p>
        </div>
        <div class="footer">
            <p><strong>{{company_name}}</strong></p>
            <p>Questions? Contact us at <a href="mailto:careers@hrplus.com">careers@hrplus.com</a></p>
        </div>
    </div>
</body>
</html>
''',
                'body_text': '''Hi {{candidate_name}},

Thank you for applying to {{company_name}}! We're excited that you're interested in the {{job_title}} position.

Application Details:
- Application ID: {{application_id}}
- Position: {{job_title}}
- Submitted: {{submitted_date}}

What happens next?
- Our hiring team will review your application
- We'll notify you of any updates via email
- If selected, we'll reach out to schedule an interview

View your application status: {{dashboard_link}}

We review all applications carefully. Due to the high volume of applications, we may take some time to respond. We appreciate your patience!

---
{{company_name}}
Questions? Contact us at careers@hrplus.com
''',
                'is_active': True,
                'variables': {
                    'candidate_name': 'string',
                    'job_title': 'string',
                    'application_id': 'string',
                    'company_name': 'string',
                    'submitted_date': 'string',
                    'dashboard_link': 'string',
                },
            },
            # Interview Scheduled
            {
                'name': 'Interview Scheduled',
                'category': 'interview',
                'subject': 'Interview Scheduled - {{job_title}}',
                'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center; color: white; }
        .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
        .content { padding: 40px 30px; }
        .interview-card { background: #f0fdf4; border: 2px solid #10b981; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .interview-card h3 { margin-top: 0; color: #059669; }
        .detail-row { display: flex; padding: 10px 0; border-bottom: 1px solid #d1fae5; }
        .detail-label { font-weight: 600; width: 140px; color: #059669; }
        .button { display: inline-block; background: #10b981; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 10px 5px; }
        .button-secondary { background: #6b7280; }
        .prep-notes { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .footer { background: #f8f9fa; padding: 20px 30px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #e9ecef; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 Interview Scheduled</h1>
        </div>
        <div class="content">
            <p>Hi {{candidate_name}},</p>

            <p>Great news! We'd like to invite you to interview for the <strong>{{job_title}}</strong> position.</p>

            <div class="interview-card">
                <h3>Interview Details</h3>
                <div class="detail-row">
                    <div class="detail-label">Type:</div>
                    <div>{{interview_type}}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Date:</div>
                    <div>{{interview_date}}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Time:</div>
                    <div>{{interview_time}}</div>
                </div>
                <div class="detail-row" style="border-bottom: none;">
                    <div class="detail-label">Location:</div>
                    <div>{{interview_location}}</div>
                </div>
            </div>

            {% if video_link %}
            <center>
                <a href="{{video_link}}" class="button">Join Video Interview</a>
                <a href="{{calendar_link}}" class="button button-secondary">Add to Calendar</a>
            </center>
            {% endif %}

            {% if prep_notes %}
            <div class="prep-notes">
                <strong>📝 Preparation Notes:</strong><br>
                {{prep_notes}}
            </div>
            {% endif %}

            <p><strong>What to expect:</strong></p>
            <ul>
                <li>The interview will last approximately 45-60 minutes</li>
                <li>Please arrive 5 minutes early (or join the video call early)</li>
                <li>Bring a copy of your resume and any questions you may have</li>
                <li>Be prepared to discuss your experience and qualifications</li>
            </ul>

            <p>If you need to reschedule, please contact us as soon as possible at <a href="mailto:recruiting@hrplus.com">recruiting@hrplus.com</a></p>

            <p>We're looking forward to meeting you!</p>
        </div>
        <div class="footer">
            <p><strong>{{company_name}}</strong></p>
            <p>Questions? Contact us at <a href="mailto:recruiting@hrplus.com">recruiting@hrplus.com</a></p>
        </div>
    </div>
</body>
</html>
''',
                'body_text': '''Hi {{candidate_name}},

Great news! We'd like to invite you to interview for the {{job_title}} position.

Interview Details:
- Type: {{interview_type}}
- Date: {{interview_date}}
- Time: {{interview_time}}
- Location: {{interview_location}}

{% if video_link %}
Join Video Interview: {{video_link}}
Add to Calendar: {{calendar_link}}
{% endif %}

{% if prep_notes %}
Preparation Notes:
{{prep_notes}}
{% endif %}

What to expect:
- The interview will last approximately 45-60 minutes
- Please arrive 5 minutes early (or join the video call early)
- Bring a copy of your resume and any questions you may have
- Be prepared to discuss your experience and qualifications

If you need to reschedule, please contact us as soon as possible at recruiting@hrplus.com

We're looking forward to meeting you!

---
{{company_name}}
Questions? Contact us at recruiting@hrplus.com
''',
                'is_active': True,
                'variables': {
                    'candidate_name': 'string',
                    'job_title': 'string',
                    'interview_type': 'string',
                    'interview_date': 'string',
                    'interview_time': 'string',
                    'interview_location': 'string',
                    'video_link': 'string',
                    'calendar_link': 'string',
                    'prep_notes': 'string',
                    'company_name': 'string',
                },
            },
            # Application Status Update
            {
                'name': 'Application Status Update',
                'category': 'application',
                'subject': 'Update on Your Application - {{job_title}}',
                'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; }
        .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
        .content { padding: 40px 30px; }
        .status-badge { background: #e0e7ff; color: #4338ca; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; font-size: 18px; font-weight: 600; }
        .button { display: inline-block; background: #667eea; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }
        .footer { background: #f8f9fa; padding: 20px 30px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #e9ecef; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📬 Application Update</h1>
        </div>
        <div class="content">
            <p>Hi {{candidate_name}},</p>

            <p>We have an update regarding your application for the <strong>{{job_title}}</strong> position.</p>

            <div class="status-badge">
                Status: {{new_status}}
            </div>

            <p>{{status_message}}</p>

            <center>
                <a href="{{dashboard_link}}" class="button">View Application Details</a>
            </center>

            <p>Thank you for your continued interest in joining our team!</p>
        </div>
        <div class="footer">
            <p><strong>{{company_name}}</strong></p>
            <p>Questions? Contact us at <a href="mailto:careers@hrplus.com">careers@hrplus.com</a></p>
        </div>
    </div>
</body>
</html>
''',
                'body_text': '''Hi {{candidate_name}},

We have an update regarding your application for the {{job_title}} position.

Status: {{new_status}}

{{status_message}}

View Application Details: {{dashboard_link}}

Thank you for your continued interest in joining our team!

---
{{company_name}}
Questions? Contact us at careers@hrplus.com
''',
                'is_active': True,
                'variables': {
                    'candidate_name': 'string',
                    'job_title': 'string',
                    'new_status': 'string',
                    'status_message': 'string',
                    'dashboard_link': 'string',
                    'company_name': 'string',
                },
            },
            # Offer Extended
            {
                'name': 'Offer Extended',
                'category': 'offer',
                'subject': 'Job Offer - {{job_title}} at {{company_name}}',
                'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 30px; text-align: center; color: white; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 700; }
        .content { padding: 40px 30px; }
        .celebration { text-align: center; font-size: 48px; margin: 20px 0; }
        .offer-card { background: #fffbeb; border: 2px solid #f59e0b; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .button { display: inline-block; background: #f59e0b; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 10px 5px; }
        .button-secondary { background: #6b7280; }
        .footer { background: #f8f9fa; padding: 20px 30px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #e9ecef; }
        .important { background: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Congratulations!</h1>
        </div>
        <div class="content">
            <div class="celebration">🎊 🎈 🎉</div>

            <p>Hi {{candidate_name}},</p>

            <p>We are thrilled to extend an offer for you to join <strong>{{company_name}}</strong> as a <strong>{{job_title}}</strong>!</p>

            <div class="offer-card">
                <h3 style="margin-top: 0; color: #d97706;">Offer Details</h3>
                <p><strong>Position:</strong> {{job_title}}</p>
                <p><strong>Department:</strong> {{department}}</p>
                <p><strong>Start Date:</strong> {{start_date}}</p>
                <p><strong>Offer Valid Until:</strong> {{offer_expiry}}</p>
            </div>

            <p>Your formal offer letter with complete details including compensation, benefits, and other terms is attached to this email and available in your candidate portal.</p>

            <center>
                <a href="{{offer_link}}" class="button">View & Accept Offer</a>
                <a href="{{questions_link}}" class="button button-secondary">Ask Questions</a>
            </center>

            <div class="important">
                <strong>⚠️ Important:</strong> Please review the offer carefully and respond by <strong>{{offer_expiry}}</strong>. If you have any questions, don't hesitate to reach out.
            </div>

            <p>We're excited about the possibility of you joining our team and look forward to your response!</p>

            <p>Best regards,<br><strong>{{recruiter_name}}</strong><br>{{recruiter_title}}</p>
        </div>
        <div class="footer">
            <p><strong>{{company_name}}</strong></p>
            <p>Questions? Contact {{recruiter_email}}</p>
        </div>
    </div>
</body>
</html>
''',
                'body_text': '''Hi {{candidate_name}},

🎉 Congratulations! 🎉

We are thrilled to extend an offer for you to join {{company_name}} as a {{job_title}}!

Offer Details:
- Position: {{job_title}}
- Department: {{department}}
- Start Date: {{start_date}}
- Offer Valid Until: {{offer_expiry}}

Your formal offer letter with complete details including compensation, benefits, and other terms is attached to this email and available in your candidate portal.

View & Accept Offer: {{offer_link}}
Ask Questions: {{questions_link}}

IMPORTANT: Please review the offer carefully and respond by {{offer_expiry}}. If you have any questions, don't hesitate to reach out.

We're excited about the possibility of you joining our team and look forward to your response!

Best regards,
{{recruiter_name}}
{{recruiter_title}}

---
{{company_name}}
Questions? Contact {{recruiter_email}}
''',
                'is_active': True,
                'variables': {
                    'candidate_name': 'string',
                    'job_title': 'string',
                    'company_name': 'string',
                    'department': 'string',
                    'start_date': 'string',
                    'offer_expiry': 'string',
                    'offer_link': 'string',
                    'questions_link': 'string',
                    'recruiter_name': 'string',
                    'recruiter_title': 'string',
                    'recruiter_email': 'string',
                },
            },
            # Rejection (Respectful)
            {
                'name': 'Application Rejected',
                'category': 'rejection',
                'subject': 'Update on Your Application - {{job_title}}',
                'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); padding: 30px; text-align: center; color: white; }
        .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
        .content { padding: 40px 30px; }
        .button { display: inline-block; background: #667eea; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }
        .encouragement { background: #f0fdf4; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .footer { background: #f8f9fa; padding: 20px 30px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #e9ecef; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Application Update</h1>
        </div>
        <div class="content">
            <p>Hi {{candidate_name}},</p>

            <p>Thank you for taking the time to apply for the <strong>{{job_title}}</strong> position at {{company_name}} and for your interest in joining our team.</p>

            <p>After careful consideration, we have decided to move forward with other candidates whose qualifications more closely match our current needs for this specific role.</p>

            <p>This decision was not easy, as we received many strong applications. We truly appreciate the time and effort you invested in the application process.</p>

            <div class="encouragement">
                <strong>💚 We encourage you to apply again!</strong><br>
                We regularly have new openings, and your skills may be a great fit for future opportunities. We'll keep your profile on file for consideration.
            </div>

            <center>
                <a href="{{jobs_link}}" class="button">View Other Openings</a>
            </center>

            <p>We wish you all the best in your job search and your future career endeavors.</p>

            <p>Best regards,<br><strong>{{company_name}} Recruiting Team</strong></p>
        </div>
        <div class="footer">
            <p><strong>{{company_name}}</strong></p>
            <p>Stay connected: <a href="{{careers_page}}">Careers Page</a></p>
        </div>
    </div>
</body>
</html>
''',
                'body_text': '''Hi {{candidate_name}},

Thank you for taking the time to apply for the {{job_title}} position at {{company_name}} and for your interest in joining our team.

After careful consideration, we have decided to move forward with other candidates whose qualifications more closely match our current needs for this specific role.

This decision was not easy, as we received many strong applications. We truly appreciate the time and effort you invested in the application process.

We encourage you to apply again! We regularly have new openings, and your skills may be a great fit for future opportunities. We'll keep your profile on file for consideration.

View Other Openings: {{jobs_link}}

We wish you all the best in your job search and your future career endeavors.

Best regards,
{{company_name}} Recruiting Team

---
{{company_name}}
Stay connected: {{careers_page}}
''',
                'is_active': True,
                'variables': {
                    'candidate_name': 'string',
                    'job_title': 'string',
                    'company_name': 'string',
                    'jobs_link': 'string',
                    'careers_page': 'string',
                },
            },
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates:
            template, created = EmailTemplate.objects.update_or_create(
                name=template_data['name'],
                defaults=template_data,
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {template.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ Updated: {template.name}'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully seeded {created_count + updated_count} email templates '
                f'({created_count} created, {updated_count} updated)'
            )
        )
