"""Views for integrations app."""

import hashlib
import hmac
import json
import logging

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsInternalUser
from apps.jobs.models import Requisition

from .models import Integration, JobBoardPosting, WebhookDelivery, WebhookEndpoint
from .serializers import (
    IntegrationCreateSerializer,
    IntegrationSerializer,
    JobBoardPostingCreateSerializer,
    JobBoardPostingSerializer,
    TestConnectionSerializer,
    WebhookDeliverySerializer,
    WebhookEndpointSerializer,
)
from .services import IntegrationService, JobBoardService, WebhookService

logger = logging.getLogger(__name__)


class IntegrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing external integrations.

    Provides standard CRUD operations plus custom actions for testing
    connections and refreshing OAuth tokens.
    """

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = IntegrationSerializer
    queryset = Integration.objects.all().order_by('-created_at')
    filterset_fields = ['provider', 'category', 'is_active', 'sync_status']
    search_fields = ['name', 'provider']
    ordering_fields = ['name', 'created_at', 'last_sync']

    def get_serializer_class(self):
        """Use different serializer for creation."""
        if self.action == 'create':
            return IntegrationCreateSerializer
        return IntegrationSerializer

    def perform_create(self, serializer):
        """Create integration via service layer."""
        integration = IntegrationService.create_integration(
            provider=serializer.validated_data['provider'],
            category=serializer.validated_data['category'],
            name=serializer.validated_data['name'],
            config=serializer.validated_data['config'],
            is_active=serializer.validated_data.get('is_active', True),
            oauth_token=serializer.validated_data.get('oauth_token'),
            oauth_refresh_token=serializer.validated_data.get('oauth_refresh_token'),
            oauth_expires_at=serializer.validated_data.get('oauth_expires_at'),
            metadata=serializer.validated_data.get('metadata', {}),
        )
        return integration

    def perform_update(self, serializer):
        """Update integration config via service layer."""
        instance = self.get_object()

        # Update config if provided
        if 'config' in serializer.validated_data:
            IntegrationService.update_config(
                instance, serializer.validated_data['config']
            )

        # Update other fields
        for field in ['name', 'is_active', 'metadata']:
            if field in serializer.validated_data:
                setattr(instance, field, serializer.validated_data[field])

        if 'oauth_token' in serializer.validated_data:
            instance.oauth_token = serializer.validated_data['oauth_token']
        if 'oauth_refresh_token' in serializer.validated_data:
            instance.oauth_refresh_token = serializer.validated_data['oauth_refresh_token']
        if 'oauth_expires_at' in serializer.validated_data:
            instance.oauth_expires_at = serializer.validated_data['oauth_expires_at']

        instance.save()

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Test connection to external service.

        POST /api/v1/integrations/{id}/test_connection/
        """
        integration = self.get_object()

        result = IntegrationService.test_connection(integration)

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def refresh_token(self, request, pk=None):
        """
        Refresh OAuth access token.

        POST /api/v1/integrations/{id}/refresh_token/
        """
        integration = self.get_object()

        try:
            updated_integration = IntegrationService.refresh_oauth_token(integration)
            return Response(
                {
                    'success': True,
                    'message': 'OAuth token refreshed successfully',
                    'expires_at': updated_integration.oauth_expires_at,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class WebhookEndpointViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing webhook endpoints.

    Allows registration and management of webhook subscriptions.
    """

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = WebhookEndpointSerializer
    queryset = WebhookEndpoint.objects.select_related('integration').order_by('-created_at')
    filterset_fields = ['is_active', 'integration']
    search_fields = ['url']
    ordering_fields = ['created_at', 'last_success', 'failure_count']

    def perform_create(self, serializer):
        """Create webhook endpoint via service layer."""
        endpoint = WebhookService.register_endpoint(
            url=serializer.validated_data['url'],
            events=serializer.validated_data['events'],
            secret=serializer.validated_data.get('secret'),
            headers=serializer.validated_data.get('headers', {}),
            integration=serializer.validated_data.get('integration'),
        )
        return endpoint

    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        """
        List recent deliveries for this endpoint.

        GET /api/v1/webhooks/{id}/deliveries/
        """
        endpoint = self.get_object()

        # Get recent deliveries
        deliveries = WebhookDelivery.objects.filter(endpoint=endpoint).order_by(
            '-created_at'
        )[:50]

        serializer = WebhookDeliverySerializer(deliveries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobBoardPostingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for job board postings.

    Allows viewing postings and manually triggering syncs.
    """

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = JobBoardPostingSerializer
    queryset = JobBoardPosting.objects.select_related(
        'requisition', 'integration'
    ).order_by('-posted_at')
    filterset_fields = ['requisition', 'integration', 'status']
    search_fields = ['requisition__title', 'external_id']
    ordering_fields = ['posted_at', 'last_synced']

    @action(detail=False, methods=['post'])
    def post_job(self, request):
        """
        Post job to external board.

        POST /api/v1/job-postings/post_job/
        Body: { "requisition_id": "uuid", "integration_id": "uuid" }
        """
        serializer = JobBoardPostingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requisition = get_object_or_404(
            Requisition, id=serializer.validated_data['requisition_id']
        )
        integration = get_object_or_404(
            Integration, id=serializer.validated_data['integration_id']
        )

        try:
            posting = JobBoardService.post_job(requisition, integration)
            return Response(
                JobBoardPostingSerializer(posting).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f'Failed to post job: {str(e)}')
            return Response(
                {'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Force sync of job posting.

        POST /api/v1/job-postings/{id}/sync/
        """
        posting = self.get_object()

        try:
            updated_posting = JobBoardService.update_job(posting)
            return Response(
                JobBoardPostingSerializer(updated_posting).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f'Failed to sync posting: {str(e)}')
            return Response(
                {'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """
        Close job posting on external board.

        POST /api/v1/job-postings/{id}/close/
        """
        posting = self.get_object()

        try:
            closed_posting = JobBoardService.close_job(posting)
            return Response(
                JobBoardPostingSerializer(closed_posting).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f'Failed to close posting: {str(e)}')
            return Response(
                {'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


class WebhookReceiverView(APIView):
    """
    Receive incoming webhooks from external systems.

    This endpoint allows external systems to send webhook events to HR-Plus.
    Authentication is via HMAC signature verification, not session auth.

    POST /api/v1/integrations/receive/{integration_id}/
    Headers:
        X-Webhook-Signature: HMAC-SHA256 signature
    """

    permission_classes = [AllowAny]  # Signature verification instead

    def post(self, request, integration_id):
        """Process incoming webhook."""
        try:
            # Get integration
            integration = Integration.objects.get(id=integration_id)
        except Integration.DoesNotExist:
            logger.warning(f'Webhook received for unknown integration: {integration_id}')
            return Response(
                {'detail': 'Integration not found'}, status=status.HTTP_404_NOT_FOUND
            )

        if not integration.is_active:
            logger.warning(f'Webhook received for inactive integration: {integration}')
            return Response(
                {'detail': 'Integration is not active'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Verify signature
        signature = request.headers.get('X-Webhook-Signature', '')
        if not signature:
            logger.warning(f'Webhook received without signature for {integration}')
            return Response(
                {'detail': 'Missing signature'}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Get config with webhook secret
        try:
            config = json.loads(integration.config) if integration.config else {}
            webhook_secret = config.get('webhook_secret', '')

            if not webhook_secret:
                logger.error(f'Integration {integration} missing webhook_secret in config')
                return Response(
                    {'detail': 'Webhook secret not configured'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Verify signature
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                request.body,
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                logger.warning(f'Invalid webhook signature for {integration}')
                return Response(
                    {'detail': 'Invalid signature'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        except Exception as e:
            logger.error(f'Error verifying webhook signature: {str(e)}')
            return Response(
                {'detail': 'Signature verification failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Process webhook payload
        try:
            payload = request.data

            # Log webhook receipt
            logger.info(
                f'Received webhook from {integration}: '
                f'{payload.get("event_type", "unknown")}'
            )

            # Process based on integration type
            if integration.category == 'job_board':
                # Process job board webhook (e.g., new application)
                self._process_job_board_webhook(integration, payload)
            elif integration.category == 'hris':
                # Process HRIS webhook (e.g., employee update)
                self._process_hris_webhook(integration, payload)
            else:
                logger.info(f'No handler for webhook category: {integration.category}')

            return Response({'status': 'received'}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Error processing webhook: {str(e)}')
            return Response(
                {'detail': 'Webhook processing failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _process_job_board_webhook(self, integration, payload):
        """Process webhook from job board (e.g., new application)."""
        # In production, would import applications from job board
        # Placeholder implementation
        logger.info(f'Processing job board webhook from {integration.provider}')

    def _process_hris_webhook(self, integration, payload):
        """Process webhook from HRIS (e.g., employee update)."""
        # In production, would sync employee data
        # Placeholder implementation
        logger.info(f'Processing HRIS webhook from {integration.provider}')
