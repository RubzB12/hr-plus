"""API views for communications app."""

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsInternalUser
from apps.applications.models import Application

from .models import EmailLog, EmailTemplate, Notification
from .serializers import (
    EmailLogSerializer,
    EmailTemplateListSerializer,
    EmailTemplateSerializer,
    NotificationSerializer,
    SendEmailSerializer,
)
from .services import EmailService, NotificationService


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
