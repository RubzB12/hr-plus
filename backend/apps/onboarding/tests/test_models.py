"""Tests for onboarding models."""

import pytest
from django.utils import timezone

from apps.onboarding.models import OnboardingPlan, OnboardingTask

from .factories import (
    OnboardingDocumentFactory,
    OnboardingFormFactory,
    OnboardingPlanFactory,
    OnboardingTaskFactory,
    OnboardingTemplateFactory,
)


@pytest.mark.django_db
class TestOnboardingTemplate:
    """Tests for OnboardingTemplate model."""

    def test_create_template(self):
        """Test creating an onboarding template."""
        template = OnboardingTemplateFactory()

        assert template.name
        assert template.is_active is True
        assert isinstance(template.tasks, list)
        assert isinstance(template.required_documents, list)
        assert isinstance(template.forms, list)

    def test_template_str(self):
        """Test template string representation."""
        template = OnboardingTemplateFactory(name='Engineering Onboarding')

        assert str(template) == 'Engineering Onboarding'


@pytest.mark.django_db
class TestOnboardingPlan:
    """Tests for OnboardingPlan model."""

    def test_create_plan(self):
        """Test creating an onboarding plan."""
        plan = OnboardingPlanFactory()

        assert plan.application
        assert plan.offer
        assert plan.template
        assert plan.status == 'pending'
        assert plan.start_date
        assert plan.access_token
        assert len(plan.access_token) > 0

    def test_plan_str(self):
        """Test plan string representation."""
        plan = OnboardingPlanFactory()
        candidate_name = plan.application.candidate.user.get_full_name()

        assert candidate_name in str(plan)
        assert str(plan.start_date) in str(plan)

    def test_progress_percentage_no_tasks(self):
        """Test progress calculation with no tasks."""
        plan = OnboardingPlanFactory()

        assert plan.progress_percentage == 0

    def test_progress_percentage_with_tasks(self):
        """Test progress calculation with tasks."""
        plan = OnboardingPlanFactory()

        # Create 4 tasks, complete 2
        OnboardingTaskFactory.create_batch(2, plan=plan, status='completed')
        OnboardingTaskFactory.create_batch(2, plan=plan, status='pending')

        # Should be 50%
        assert plan.progress_percentage == 50

    def test_progress_percentage_all_complete(self):
        """Test progress calculation with all tasks complete."""
        plan = OnboardingPlanFactory()

        OnboardingTaskFactory.create_batch(5, plan=plan, status='completed')

        assert plan.progress_percentage == 100

    def test_is_overdue_with_overdue_tasks(self):
        """Test is_overdue property with overdue tasks."""
        plan = OnboardingPlanFactory()

        # Create overdue task
        past_date = timezone.now().date() - timezone.timedelta(days=5)
        OnboardingTaskFactory(plan=plan, due_date=past_date, status='pending')

        assert plan.is_overdue is True

    def test_is_overdue_no_overdue_tasks(self):
        """Test is_overdue property with no overdue tasks."""
        plan = OnboardingPlanFactory()

        # Create future task
        future_date = timezone.now().date() + timezone.timedelta(days=5)
        OnboardingTaskFactory(plan=plan, due_date=future_date, status='pending')

        assert plan.is_overdue is False

    def test_is_overdue_completed_tasks_not_counted(self):
        """Test that completed tasks don't count as overdue."""
        plan = OnboardingPlanFactory()

        # Create overdue but completed task
        past_date = timezone.now().date() - timezone.timedelta(days=5)
        OnboardingTaskFactory(plan=plan, due_date=past_date, status='completed')

        assert plan.is_overdue is False


@pytest.mark.django_db
class TestOnboardingTask:
    """Tests for OnboardingTask model."""

    def test_create_task(self):
        """Test creating an onboarding task."""
        task = OnboardingTaskFactory()

        assert task.plan
        assert task.title
        assert task.category in dict(OnboardingTask.CATEGORY_CHOICES)
        assert task.status == 'pending'

    def test_task_str(self):
        """Test task string representation."""
        task = OnboardingTaskFactory(title='Setup Email', status='pending')

        assert 'Setup Email' in str(task)
        assert 'Pending' in str(task)


@pytest.mark.django_db
class TestOnboardingDocument:
    """Tests for OnboardingDocument model."""

    def test_create_document(self):
        """Test creating an onboarding document."""
        document = OnboardingDocumentFactory()

        assert document.plan
        assert document.document_type == 'i9'
        assert document.status == 'pending'

    def test_document_str(self):
        """Test document string representation."""
        document = OnboardingDocumentFactory(document_type='i9', status='pending')

        assert 'I-9 Form' in str(document)
        assert 'Pending Upload' in str(document)


@pytest.mark.django_db
class TestOnboardingForm:
    """Tests for OnboardingForm model."""

    def test_create_form(self):
        """Test creating an onboarding form."""
        form = OnboardingFormFactory()

        assert form.plan
        assert form.form_type == 'equipment_preferences'
        assert isinstance(form.data, dict)

    def test_form_str(self):
        """Test form string representation."""
        form = OnboardingFormFactory(form_type='equipment_preferences')

        assert 'Equipment Preferences' in str(form)

    def test_is_submitted_false(self):
        """Test is_submitted property when not submitted."""
        form = OnboardingFormFactory(submitted_at=None)

        assert form.is_submitted is False

    def test_is_submitted_true(self):
        """Test is_submitted property when submitted."""
        form = OnboardingFormFactory(submitted_at=timezone.now())

        assert form.is_submitted is True

    def test_unique_together(self):
        """Test that plan + form_type are unique together."""
        plan = OnboardingPlanFactory()
        OnboardingFormFactory(plan=plan, form_type='equipment_preferences')

        # Attempting to create another form with same plan and type should fail
        with pytest.raises(Exception):  # IntegrityError
            OnboardingFormFactory(plan=plan, form_type='equipment_preferences')
