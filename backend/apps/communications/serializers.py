"""Serializers for communications app."""

from rest_framework import serializers

from .models import EmailLog, EmailTemplate, Message, MessageThread, Notification


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


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages."""

    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    is_read_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'thread',
            'sender',
            'sender_name',
            'sender_email',
            'body',
            'attachments',
            'read_by',
            'is_read_by_user',
            'is_system_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['sender', 'read_by', 'is_system_message']

    def get_is_read_by_user(self, obj):
        """Check if the current user has read this message."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return str(request.user.id) in obj.read_by
        return False


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages."""

    class Meta:
        model = Message
        fields = ['body', 'attachments']

    def validate_body(self, value):
        """Validate message body is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError('Message body cannot be empty')
        return value


class MessageThreadSerializer(serializers.ModelSerializer):
    """Serializer for message threads."""

    participant_count = serializers.IntegerField(source='participants.count', read_only=True)
    participant_names = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    application_title = serializers.CharField(
        source='application.requisition.title',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = MessageThread
        fields = [
            'id',
            'subject',
            'participants',
            'participant_count',
            'participant_names',
            'application',
            'application_title',
            'is_archived',
            'archived_at',
            'last_message',
            'unread_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_archived', 'archived_at']

    def get_participant_names(self, obj):
        """Get list of participant names."""
        return [p.get_full_name() for p in obj.participants.all()]

    def get_last_message(self, obj):
        """Get the most recent message in the thread."""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'id': str(last_message.id),
                'sender_name': last_message.sender.get_full_name(),
                'body': last_message.body[:100] + '...' if len(last_message.body) > 100 else last_message.body,
                'created_at': last_message.created_at,
                'is_system_message': last_message.is_system_message,
            }
        return None

    def get_unread_count(self, obj):
        """Get unread message count for current user."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            from .services import MessagingService
            return MessagingService.get_unread_count(request.user, thread=obj)
        return 0


class MessageThreadDetailSerializer(MessageThreadSerializer):
    """Detailed serializer for message threads with messages."""

    messages = MessageSerializer(many=True, read_only=True)

    class Meta(MessageThreadSerializer.Meta):
        fields = MessageThreadSerializer.Meta.fields + ['messages']


class MessageThreadCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating message threads."""

    participants = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        min_length=1,
    )
    initial_message = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = MessageThread
        fields = ['subject', 'participants', 'application', 'initial_message']

    def validate_participants(self, value):
        """Validate participants exist."""
        from django.contrib.auth import get_user_model
        User = get_user_model()  # noqa: N806

        # Check all UUIDs are valid users
        user_ids = set(value)
        existing_users = User.objects.filter(id__in=user_ids).count()

        if existing_users != len(user_ids):
            raise serializers.ValidationError('One or more participant IDs are invalid')

        if len(user_ids) < 1:
            raise serializers.ValidationError('Thread must have at least one participant')

        return value


class BulkEmailSerializer(serializers.Serializer):
    """Serializer for sending bulk emails."""

    candidate_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,  # Limit bulk operations
    )
    template_id = serializers.UUIDField(required=False, allow_null=True)
    subject = serializers.CharField(max_length=500)
    body_text = serializers.CharField()
    body_html = serializers.CharField(required=False, allow_blank=True)

    def validate_candidate_ids(self, value):
        """Validate candidate IDs exist."""
        from apps.accounts.models import CandidateProfile

        candidate_count = CandidateProfile.objects.filter(id__in=value).count()

        if candidate_count != len(value):
            raise serializers.ValidationError('One or more candidate IDs are invalid')

        return value
