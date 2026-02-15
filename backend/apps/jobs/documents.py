"""Elasticsearch document definitions for jobs app."""

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from .models import Requisition


@registry.register_document
class JobDocument(Document):
    """Elasticsearch document for job search."""

    # Basic fields
    requisition_id = fields.KeywordField()
    title = fields.TextField(
        analyzer='job_analyzer',
        fields={
            'raw': fields.KeywordField(),
            'suggest': fields.CompletionField(),
        },
    )
    status = fields.KeywordField()

    # Organization
    department = fields.TextField(attr='department.name')
    department_id = fields.KeywordField(attr='department.id')
    location = fields.TextField(attr='location.name')
    location_id = fields.KeywordField(attr='location.id')
    location_city = fields.TextField(attr='location.city')
    location_country = fields.KeywordField(attr='location.country')

    # Job details
    employment_type = fields.KeywordField()
    level = fields.TextField(attr='level.name')
    remote_policy = fields.KeywordField()

    # Compensation
    salary_min = fields.IntegerField()
    salary_max = fields.IntegerField()
    salary_currency = fields.KeywordField()

    # Content
    description = fields.TextField(analyzer='job_analyzer')
    requirements_required = fields.TextField(analyzer='job_analyzer')
    requirements_preferred = fields.TextField(analyzer='job_analyzer')

    # Metadata
    published_at = fields.DateField()
    target_start_date = fields.DateField()
    headcount = fields.IntegerField()

    class Index:
        name = 'jobs'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'job_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': [
                            'lowercase',
                            'asciifolding',
                            'stop',
                            'snowball',
                        ],
                    },
                },
            },
        }

    class Django:
        model = Requisition
        fields = []  # Using custom fields above
        related_models = ['department', 'location', 'level']

    def get_queryset(self):
        """Only index published jobs."""
        return super().get_queryset().filter(
            status='open',
        ).select_related('department', 'location', 'level')

    def should_index_object(self, instance):
        """Only index published jobs."""
        return instance.status == 'open'

    def get_instances_from_related(self, related_instance):
        """Update document when related models are updated."""
        if hasattr(related_instance, 'requisitions'):
            return related_instance.requisitions.filter(status='open')
        return None
