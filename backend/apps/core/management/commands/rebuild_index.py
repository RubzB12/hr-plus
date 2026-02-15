"""Management command to rebuild Elasticsearch indexes."""

from django.core.management.base import BaseCommand
from django_elasticsearch_dsl.management.commands import search_index


class Command(BaseCommand):
    help = 'Rebuild Elasticsearch indexes for candidates and jobs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            nargs='+',
            default=['candidates', 'jobs'],
            help='Models to reindex (candidates, jobs, or both)',
        )

    def handle(self, *args, **options):
        models = options['models']

        if 'candidates' in models:
            self.stdout.write('Rebuilding candidate index...')
            self._rebuild_candidates()

        if 'jobs' in models:
            self.stdout.write('Rebuilding job index...')
            self._rebuild_jobs()

        self.stdout.write(
            self.style.SUCCESS('Successfully rebuilt search indexes!')
        )

    def _rebuild_candidates(self):
        """Rebuild candidate search index."""
        from apps.accounts.documents import CandidateDocument
        from apps.accounts.models import CandidateProfile

        try:
            # Delete and recreate the index
            CandidateDocument._index.delete(ignore=404)
            CandidateDocument.init()

            # Index all candidates
            candidates = CandidateProfile.objects.select_related('user')
            count = 0
            for candidate in candidates:
                CandidateDocument().update(candidate)
                count += 1

            self.stdout.write(f'  Indexed {count} candidates')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error rebuilding candidate index: {e}')
            )

    def _rebuild_jobs(self):
        """Rebuild job search index."""
        from apps.jobs.documents import JobDocument
        from apps.jobs.models import Requisition

        try:
            # Delete and recreate the index
            JobDocument._index.delete(ignore=404)
            JobDocument.init()

            # Index all open jobs
            jobs = Requisition.objects.filter(
                status='open',
            ).select_related('department', 'location', 'level')
            count = 0
            for job in jobs:
                JobDocument().update(job)
                count += 1

            self.stdout.write(f'  Indexed {count} jobs')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error rebuilding job index: {e}')
            )
