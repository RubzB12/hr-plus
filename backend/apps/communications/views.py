"""API views for communications app."""

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsInternalUser
from apps.applications.models import Application

from .models import EmailLog, EmailTemplate, MessageThread, Notification
from .serializers import (
    BulkEmailSerializer,
    EmailLogSerializer,
    EmailTemplateListSerializer,
    EmailTemplateSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    MessageThreadCreateSerializer,
    MessageThreadDetailSerializer,
    MessageThreadSerializer,
    NotificationSerializer,
    SendEmailSerializer,
)
from .services import EmailService, MessagingService, NotificationService


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing email templates (internal users only)."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    queryset = EmailTemplate.objects.all().order_by('category', 'name')

    def get_serializer_class(self):
        if self.action == 'list':
            return EmailTemplateListSerializer
        return EmailTemplateSerializer


class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing email logs (internal users only)."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = EmailLogSerializer
    queryset = EmailLog.objects.select_related(
        'template',
        'application__candidate__user',
    ).order_by('-created_at')

    def get_queryset(self):
        qs = super().get_queryset()

        # Filter by application if provided
        application_id = self.request.query_params.get('application_id')
        if application_id:
            qs = qs.filter(application_id=application_id)

        # Filter by recipient
        recipient = self.request.query_params.get('recipient')
        if recipient:
            qs = qs.filter(recipient__icontains=recipient)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs


class SendEmailToApplicationView(generics.GenericAPIView):
    """Send an email to a candidate from an application."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = SendEmailSerializer

    def post(self, request, application_id):
        from django.shortcuts import get_object_or_404

        application = get_object_or_404(Application, id=application_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # If template_id provided, use templated email
        if data.get('template_id'):
            template = EmailTemplate.objects.get(id=data['template_id'])

            # Default context from application
            context = {
                'candidate_name': application.candidate.user.get_full_name(),
                'job_title': application.requisition.title,
                'application_id': application.application_id,
            }

            from .services import TemplateService

            subject, body_html, body_text = TemplateService.render_template(
                template,
                context,
            )

            email_log = EmailService.send_email(
                recipient=application.candidate.user.email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                template=template,
                application=application,
            )
        else:
            # Send custom email
            email_log = EmailService.send_email(
                recipient=application.candidate.user.email,
                subject=data.get('subject', 'Update from HR-Plus'),
                body_text=data['body_text'],
                body_html=data.get('body_html', ''),
                application=application,
            )

        return Response(
            EmailLogSerializer(email_log).data,
            status=status.HTTP_201_CREATED,
        )


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user notifications."""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        # Users only see their own notifications
        return Notification.objects.filter(
            recipient=self.request.user,
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification = NotificationService.mark_as_read(notification)
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        count = NotificationService.mark_all_as_read(request.user)
        return Response(
            {'marked_read': count},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = NotificationService.get_unread_count(request.user)
        return Response(
            {'unread_count': count},
            status=status.HTTP_200_OK,
        )


class MessageThreadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing message threads."""

    permission_classes = [IsAuthenticated]
    serializer_class = MessageThreadSerializer

    def get_queryset(self):
        """Users only see threads they're participating in."""
        qs = MessageThread.objects.filter(
            participants=self.request.user,
        ).prefetch_related(
            'participants',
            'messages__sender',
        ).select_related('application__requisition')

        # Filter archived threads
        show_archived = self.request.query_params.get('archived', 'false').lower() == 'true'
        if not show_archived:
            qs = qs.filter(is_archived=False)

        # Filter by application
        application_id = self.request.query_params.get('application_id')
        if application_id:
            qs = qs.filter(application_id=application_id)

        return qs.order_by('-updated_at')

    def get_serializer_class(self):
        """Use detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return MessageThreadDetailSerializer
        if self.action == 'create':
            return MessageThreadCreateSerializer
        return MessageThreadSerializer

    def perform_create(self, serializer):
        """Create a new message thread."""
        from django.contrib.auth import get_user_model
        User = get_user_model()  # noqa: N806

        # Get participants
        participant_ids = serializer.validated_data.pop('participants')
        participants = User.objects.filter(id__in=participant_ids)

        # Get initial message if provided
        initial_message = serializer.validated_data.pop('initial_message', None)

        # Create thread
        thread = MessagingService.create_thread(
            subject=serializer.validated_data.get('subject', ''),
            participants=list(participants),
            application=serializer.validated_data.get('application'),
            created_by=self.request.user,
        )

        # Send initial message if provided
        if initial_message and initial_message.strip():
            MessagingService.send_message(
                thread=thread,
                sender=self.request.user,
                body=initial_message,
            )

        # Set instance for response
        serializer.instance = thread

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in this thread."""
        thread = self.get_object()
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = MessagingService.send_message(
            thread=thread,
            sender=request.user,
            body=serializer.validated_data['body'],
            attachments=serializer.validated_data.get('attachments', []),
        )

        return Response(
            MessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark all messages in thread as read."""
        thread = self.get_object()
        count = MessagingService.mark_thread_as_read(thread, request.user)
        return Response(
            {'marked_read': count},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive this thread."""
        thread = self.get_object()
        thread = MessagingService.archive_thread(thread, request.user)
        return Response(
            MessageThreadSerializer(thread, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='add-participant')
    def add_participant(self, request, pk=None):
        """Add a participant to the thread."""
        from django.contrib.auth import get_user_model
        from django.shortcuts import get_object_or_404
        User = get_user_model()  # noqa: N806

        thread = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(User, id=user_id)
        thread = MessagingService.add_participant(thread, user, request.user)

        return Response(
            MessageThreadSerializer(thread, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='remove-participant')
    def remove_participant(self, request, pk=None):
        """Remove a participant from the thread."""
        from django.contrib.auth import get_user_model
        from django.shortcuts import get_object_or_404
        User = get_user_model()  # noqa: N806

        thread = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(User, id=user_id)
        thread = MessagingService.remove_participant(thread, user, request.user)

        return Response(
            MessageThreadSerializer(thread, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get count of unread messages across all threads."""
        count = MessagingService.get_unread_count(request.user)
        return Response(
            {'unread_count': count},
            status=status.HTTP_200_OK,
        )


class BulkEmailView(generics.GenericAPIView):
    """Send bulk emails to multiple candidates."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = BulkEmailSerializer

    def post(self, request):
        """Send email to multiple candidates."""
        from django.db import transaction

        from apps.accounts.models import CandidateProfile

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Get candidates
        candidates = CandidateProfile.objects.filter(
            id__in=data['candidate_ids']
        ).select_related('user')

        # Get template if provided
        template = None
        if data.get('template_id'):
            template = EmailTemplate.objects.get(id=data['template_id'])

        # Send emails
        email_logs = []
        with transaction.atomic():
            for candidate in candidates:
                context = {
                    'candidate_name': candidate.user.get_full_name(),
                    'company_name': 'HR-Plus',
                }

                if template:
                    from .services import TemplateService
                    subject, body_html, body_text = TemplateService.render_template(
                        template,
                        context,
                    )
                else:
                    subject = data['subject']
                    body_text = data['body_text']
                    body_html = data.get('body_html', '')

                email_log = EmailService.send_email(
                    recipient=candidate.user.email,
                    subject=subject,
                    body_text=body_text,
                    body_html=body_html,
                    template=template,
                )
                email_logs.append(email_log)

        return Response(
            {
                'sent': len(email_logs),
                'emails': EmailLogSerializer(email_logs, many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )
