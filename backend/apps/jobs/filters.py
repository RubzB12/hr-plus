"""Filters for jobs app."""

import django_filters

from .models import Requisition


class PublicJobFilter(django_filters.FilterSet):
    """Filters for public job listing API."""

    department = django_filters.CharFilter(
        field_name='department__name',
        lookup_expr='iexact',
    )
    location = django_filters.CharFilter(method='filter_location')
    employment_type = django_filters.ChoiceFilter(
        choices=Requisition.EMPLOYMENT_TYPE_CHOICES,
    )
    remote_policy = django_filters.ChoiceFilter(
        choices=Requisition.REMOTE_POLICY_CHOICES,
    )
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Requisition
        fields = ['department', 'location', 'employment_type', 'remote_policy']

    def filter_location(self, queryset, _name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(location__city__icontains=value)
            | Q(location__country__icontains=value)
        )

    def filter_search(self, queryset, _name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(title__icontains=value)
            | Q(description__icontains=value)
        )


class RequisitionFilter(django_filters.FilterSet):
    """Filters for internal requisition list."""

    status = django_filters.ChoiceFilter(
        choices=Requisition.STATUS_CHOICES,
    )
    department = django_filters.UUIDFilter(field_name='department__id')
    recruiter = django_filters.UUIDFilter(field_name='recruiter__id')
    hiring_manager = django_filters.UUIDFilter(
        field_name='hiring_manager__id',
    )

    class Meta:
        model = Requisition
        fields = ['status', 'department', 'recruiter', 'hiring_manager']
