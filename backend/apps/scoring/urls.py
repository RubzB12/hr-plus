"""URL routing for scoring app."""

from django.urls import path

from . import views

urlpatterns = [
    path(
        'internal/requisitions/<uuid:requisition_id>/criteria/',
        views.RequisitionCriteriaView.as_view(),
        name='requisition-criteria',
    ),
    path(
        'internal/applications/<uuid:application_id>/rescore/',
        views.ApplicationRescoreView.as_view(),
        name='application-rescore',
    ),
]
