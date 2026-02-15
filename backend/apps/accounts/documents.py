"""Elasticsearch document definitions for accounts app."""

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from .models import CandidateProfile


@registry.register_document
class CandidateDocument(Document):
    """Elasticsearch document for candidate search."""

    # User fields
    user_id = fields.KeywordField(attr='user.id')
    email = fields.TextField(attr='user.email')
    first_name = fields.TextField(attr='user.first_name')
    last_name = fields.TextField(attr='user.last_name')
    full_name = fields.TextField()

    # Profile fields
    phone = fields.TextField()
    location_city = fields.TextField()
    location_country = fields.KeywordField()
    work_authorization = fields.KeywordField()

    # Resume data
    resume_parsed = fields.ObjectField()

    # Skills and experience (extracted from resume_parsed)
    skills = fields.TextField()
    experience_years = fields.IntegerField()

    # URLs
    linkedin_url = fields.KeywordField()
    portfolio_url = fields.KeywordField()

    # Preferences
    preferred_salary_min = fields.IntegerField()
    preferred_salary_max = fields.IntegerField()
    preferred_job_types = fields.KeywordField()

    # Metadata
    source = fields.KeywordField()
    profile_completeness = fields.IntegerField()
    created_at = fields.DateField()
    updated_at = fields.DateField()

    class Index:
        name = 'candidates'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'candidate_analyzer': {
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
        model = CandidateProfile
        fields = []  # Using custom fields above
        related_models = ['user']

    def get_queryset(self):
        """Optimize queryset for indexing."""
        return super().get_queryset().select_related('user')

    def prepare_full_name(self, instance):
        """Prepare full name for search."""
        return instance.user.get_full_name()

    def prepare_skills(self, instance):
        """Extract skills from resume_parsed."""
        if instance.resume_parsed and 'skills' in instance.resume_parsed:
            skills = instance.resume_parsed['skills']
            if isinstance(skills, list):
                return ' '.join(skills)
            return str(skills)
        return ''

    def prepare_experience_years(self, instance):
        """Calculate total years of experience from resume."""
        if instance.resume_parsed and 'experience' in instance.resume_parsed:
            # Simple calculation - can be enhanced
            return len(instance.resume_parsed['experience'])
        return 0

    def get_instances_from_related(self, related_instance):
        """Update document when related User is updated."""
        if isinstance(related_instance.__class__.__name__, 'User'):
            return related_instance.candidate_profile
        return None
