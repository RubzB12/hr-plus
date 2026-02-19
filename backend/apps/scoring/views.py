"""API views for scoring and requisition criteria."""

import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsInternalUser
from apps.jobs.models import Requisition, RequisitionCriteria

from .serializers import RequisitionCriteriaSerializer
from .tasks import rescore_requisition_task, score_application_task

logger = logging.getLogger(__name__)


class RequisitionCriteriaView(APIView):
    """
    GET  /api/v1/internal/requisitions/{id}/criteria/  — list criteria
    POST /api/v1/internal/requisitions/{id}/criteria/  — replace all criteria
    """

    permission_classes = [IsAuthenticated, IsInternalUser]

    def get(self, request, requisition_id):
        requisition = get_object_or_404(Requisition, id=requisition_id)
        criteria = requisition.criteria.all().order_by('order')
        return Response(
            RequisitionCriteriaSerializer(criteria, many=True).data
        )

    def post(self, request, requisition_id):
        requisition = get_object_or_404(Requisition, id=requisition_id)
        serializer = RequisitionCriteriaSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        from django.db import transaction

        with transaction.atomic():
            requisition.criteria.all().delete()
            created = []
            for item in serializer.validated_data:
                criterion = RequisitionCriteria.objects.create(
                    requisition=requisition,
                    criterion_type=item['criterion_type'],
                    value=item.get('value', ''),
                    weight=item.get('weight', 10),
                    is_required=item.get('is_required', False),
                    min_proficiency=item.get('min_proficiency', ''),
                    min_years=item.get('min_years'),
                    order=item.get('order', 0),
                )
                created.append(criterion)

        # Trigger batch re-score asynchronously
        try:
            rescore_requisition_task.delay(str(requisition.id))
        except Exception:
            logger.exception(
                'Failed to trigger rescore for requisition %s', requisition.id
            )

        return Response(
            RequisitionCriteriaSerializer(created, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class ApplicationRescoreView(APIView):
    """
    POST /api/v1/internal/applications/{id}/rescore/
    Synchronously re-scores the application and returns the updated score.
    Also dispatches an async task if Celery is available (for cache warm-up etc).
    """

    permission_classes = [IsAuthenticated, IsInternalUser]

    def post(self, request, application_id):
        from apps.applications.models import Application

        from .serializers import CandidateScoreSerializer
        from .services import ScoringService

        application = get_object_or_404(Application, id=application_id)

        try:
            candidate_score = ScoringService.score_application(application)
        except Exception:
            logger.exception(
                'Failed to score application %s', application.id
            )
            return Response(
                {'detail': 'Scoring failed.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Best-effort async dispatch for any post-score side effects
        try:
            score_application_task.delay(str(application.id))
        except Exception:
            pass

        return Response(
            CandidateScoreSerializer(candidate_score).data,
            status=status.HTTP_200_OK,
        )
