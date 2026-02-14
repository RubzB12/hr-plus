"""Filters for applications app."""

import django_filters

from .models import Application


class ApplicationFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Application.STATUS_CHOICES)
    requisition = django_filters.UUIDFilter(field_name='requisition__id')
    source = django_filters.ChoiceFilter(choices=Application.SOURCE_CHOICES)

    class Meta:
        model = Application
        fields = ['status', 'requisition', 'source']
