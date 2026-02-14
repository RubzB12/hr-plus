"""Tests for JobSelector."""

import pytest

from apps.accounts.tests.factories import DepartmentFactory, JobLevelFactory
from apps.jobs.selectors import JobSelector

from .factories import PublishedRequisitionFactory, RequisitionFactory


@pytest.mark.django_db
class TestJobSelector:
    def test_get_active_jobs_excludes_drafts(self):
        PublishedRequisitionFactory(title='Open Job')
        RequisitionFactory(title='Draft Job', status='draft')

        jobs = list(JobSelector.get_active_jobs())

        titles = [j.title for j in jobs]
        assert 'Open Job' in titles
        assert 'Draft Job' not in titles

    def test_get_active_jobs_filter_by_department(self):
        eng = DepartmentFactory(name='Engineering')
        mkt = DepartmentFactory(name='Marketing')
        PublishedRequisitionFactory(department=eng, title='Eng Role')
        PublishedRequisitionFactory(department=mkt, title='Mkt Role')

        jobs = list(JobSelector.get_active_jobs({'department': 'Engineering'}))

        titles = [j.title for j in jobs]
        assert 'Eng Role' in titles
        assert 'Mkt Role' not in titles

    def test_get_active_jobs_filter_by_search(self):
        PublishedRequisitionFactory(title='Python Developer')
        PublishedRequisitionFactory(title='Java Developer')

        jobs = list(JobSelector.get_active_jobs({'search': 'Python'}))

        titles = [j.title for j in jobs]
        assert 'Python Developer' in titles
        assert 'Java Developer' not in titles

    def test_get_job_by_slug(self):
        job = PublishedRequisitionFactory(title='Test Job')

        result = JobSelector.get_job_by_slug(job.slug)

        assert result is not None
        assert result.title == 'Test Job'

    def test_get_job_by_slug_returns_none_for_draft(self):
        job = RequisitionFactory(title='Draft Job', status='draft')

        result = JobSelector.get_job_by_slug(job.slug)

        assert result is None

    def test_get_categories_returns_department_counts(self):
        eng = DepartmentFactory(name='Engineering')
        PublishedRequisitionFactory(department=eng)
        PublishedRequisitionFactory(department=eng)

        categories = list(JobSelector.get_categories())

        eng_cat = next(
            c for c in categories
            if c['department__name'] == 'Engineering'
        )
        assert eng_cat['job_count'] == 2

    def test_get_similar_jobs(self):
        eng = DepartmentFactory(name='Engineering')
        level = JobLevelFactory()
        target = PublishedRequisitionFactory(
            department=eng, level=level, title='Target',
        )
        PublishedRequisitionFactory(
            department=eng, title='Same Dept',
        )
        PublishedRequisitionFactory(
            level=level, title='Same Level',
        )

        similar = list(JobSelector.get_similar_jobs(target))

        titles = [j.title for j in similar]
        assert 'Same Dept' in titles
        assert 'Same Level' in titles
        assert 'Target' not in titles
