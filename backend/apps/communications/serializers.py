"""Serializers for communications app."""

from rest_framework import serializers

from .models import EmailLog, EmailTemplate, Notification


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for email templates."""

    class Meta:
        model = EmailTemplate
        fields = [
            'id',
            'name',
            'category',
            'subject',
            'body_html',
            'body_text',
            'variables',
            'department',
            'is_active',
            'version',
            'created_at',
            'updated_at',
        ]


class EmailTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for email template list."""

    class Meta:
        model = EmailTemplate
        fields = ['id', 'name', 'category', 'subject', 'is_active', 'version']


class EmailLogSerializer(serializers.ModelSerializer):
    """Serializer for email logs."""

    template_name = serializers.CharField(source='template.name', read_only=True, allow_null=True)
    application_id_display = serializers.CharField(
        source='application.application_id',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = EmailLog
        fields = [
            'id',
            'template',
            'template_name',
            'application',
            'application_id_display',
            'sender',
            'recipient',
            'subject',
            'status',
            'sent_at',
            'opened_at',
            'message_id',
            'error_message',
            'created_at',
        ]


class SendEmailSerializer(serializers.Serializer):
    """Serializer for sending email to a candidate."""

    template_id = serializers.UUIDField(required=False, allow_null=True)
    subject = serializers.CharField(required=False, allow_blank=True, max_length=500)
    body_text = serializers.CharField(required=False, allow_blank=True)
    body_html = serializers.CharField(required=False, allow_blank=True)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    class Meta:
        model = Notification
        fields = [
            'id',
            'type',
            'title',
            'body',
            'link',
            'is_read',
            'read_at',
            'metadata',
            'created_at',
        ]
