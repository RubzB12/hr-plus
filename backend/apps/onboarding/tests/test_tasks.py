"""Tests for onboarding Celery tasks."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.offers.tests.factories import OfferFactory
from apps.onboarding.tasks import (
    auto_complete_stale_plans,
    create_plan_on_offer_acceptance,
    send_overdue_task_notifications,
    send_upcoming_task_reminders,
)

from .factories import OnboardingPlanFactory, OnboardingTaskFactory


@pytest.mark.django_db
class TestCreatePlanOnOfferAcceptance:
    """Tests for create_plan_on_offer_acceptance task."""

    @patch('apps.onboarding.services.OnboardingService.create_plan_from_offer')
    @patch('apps.communications.services.EmailService.send_onboarding_welcome')
    def test_create_plan_success(self, mock_email, mock_create):
        """Test creating onboarding plan when offer is accepted."""
        offer = OfferFactory(status='accepted', start_date=timezone.now().date() + timedelta(days=14))
        # Create a mock plan without linking it to the offer (to avoid early return)
        mock_plan = OnboardingPlanFactory.build(offer=offer)
        mock_plan.id = 'test-plan-id'
        mock_plan.access_token = 'test-token'
        mock_create.return_value = mock_plan

        result = create_plan_on_offer_acceptance(str(offer.id))

        assert result['success'] is True
        assert result['plan_id'] == 'test-plan-id'
        assert 'access_token' in result
        mock_create.assert_called_once()

    def test_create_plan_offer_not_accepted(self):
        """Test that plan is not created if offer is not accepted."""
        offer = OfferFactory(status='pending')

        result = create_plan_on_offer_acceptance(str(offer.id))

        assert result['success'] is False
        assert 'not in accepted status' in result['message']

    @patch('apps.onboarding.services.OnboardingService.create_plan_from_offer')
    @patch('apps.communications.services.EmailService.send_onboarding_welcome')
    def test_create_plan_already_exists(self, mock_email, mock_create):
        """Test that existing plan is detected."""
        offer = OfferFactory(status='accepted')
        existing_plan = OnboardingPlanFactory(offer=offer)

        result = create_plan_on_offer_acceptance(str(offer.id))

        assert result['success'] is True
        assert 'already exists' in result['message']

    def test_create_plan_offer_not_found(self):
        """Test handling of non-existent offer."""
        result = create_plan_on_offer_acceptance('00000000-0000-0000-0000-000000000000')

        assert result['success'] is False
        assert 'not found' in result['message']


@pytest.mark.django_db
class TestSendUpcomingTaskReminders:
    """Tests for send_upcoming_task_reminders task."""

    @patch('apps.communications.services.EmailService.send_task_reminder')
    def test_send_reminders_for_upcoming_tasks(self, mock_email):
        """Test sending reminders for tasks due in next 3 days."""
        today = timezone.now().date()

        # Create tasks due in 2 days (should get reminder)
        due_soon = today + timedelta(days=2)
        task1 = OnboardingTaskFactory(
            due_date=due_soon, status='pending', assigned_to=OnboardingPlanFactory().application.candidate.user
        )

        # Create task due in 5 days (should NOT get reminder)
        due_later = today + timedelta(days=5)
        task2 = OnboardingTaskFactory(
            due_date=due_later, status='pending', assigned_to=OnboardingPlanFactory().application.candidate.user
        )

        # Create completed task (should NOT get reminder)
        task3 = OnboardingTaskFactory(
            due_date=due_soon, status='completed', assigned_to=OnboardingPlanFactory().application.candidate.user
        )

        result = send_upcoming_task_reminders()

        assert result['success'] is True
        assert result['reminders_sent'] == 1
        mock_email.assert_called_once_with(task1)

    @patch('apps.communications.services.EmailService.send_task_reminder')
    def test_no_reminders_if_no_assignee(self, mock_email):
        """Test that tasks without assignee don't get reminders."""
        today = timezone.now().date()
        due_soon = today + timedelta(days=2)

        # Task without assignee
        task = OnboardingTaskFactory(due_date=due_soon, status='pending', assigned_to=None)

        result = send_upcoming_task_reminders()

        assert result['success'] is True
        assert result['reminders_sent'] == 0
        mock_email.assert_not_called()


@pytest.mark.django_db
class TestSendOverdueTaskNotifications:
    """Tests for send_overdue_task_notifications task."""

    @patch('apps.communications.services.NotificationService.create_notification')
    def test_send_notifications_for_overdue_tasks(self, mock_notification):
        """Test sending notifications for overdue tasks."""
        today = timezone.now().date()
        past_date = today - timedelta(days=5)

        # Create overdue task
        plan = OnboardingPlanFactory()
        task = OnboardingTaskFactory(
            plan=plan, due_date=past_date, status='pending', assigned_to=plan.application.candidate.user
        )

        result = send_overdue_task_notifications()

        assert result['success'] is True
        assert result['overdue_tasks'] == 1
        # Should send notification to assignee
        assert mock_notification.call_count >= 1

    @patch('apps.communications.services.NotificationService.create_notification')
    def test_no_notifications_for_future_tasks(self, mock_notification):
        """Test that future tasks don't trigger notifications."""
        today = timezone.now().date()
        future_date = today + timedelta(days=5)

        # Create future task
        task = OnboardingTaskFactory(
            due_date=future_date, status='pending', assigned_to=OnboardingPlanFactory().application.candidate.user
        )

        result = send_overdue_task_notifications()

        assert result['success'] is True
        assert result['overdue_tasks'] == 0
        mock_notification.assert_not_called()

    @patch('apps.communications.services.NotificationService.create_notification')
    def test_no_notifications_for_completed_tasks(self, mock_notification):
        """Test that completed tasks don't trigger notifications."""
        today = timezone.now().date()
        past_date = today - timedelta(days=5)

        # Create completed overdue task
        task = OnboardingTaskFactory(
            due_date=past_date, status='completed', assigned_to=OnboardingPlanFactory().application.candidate.user
        )

        result = send_overdue_task_notifications()

        assert result['success'] is True
        assert result['overdue_tasks'] == 0
        mock_notification.assert_not_called()

    @patch('apps.communications.services.NotificationService.create_notification')
    def test_notify_hr_contact(self, mock_notification):
        """Test that HR contact is also notified of overdue tasks."""
        today = timezone.now().date()
        past_date = today - timedelta(days=5)

        # Create plan with HR contact
        plan = OnboardingPlanFactory()
        task = OnboardingTaskFactory(
            plan=plan, due_date=past_date, status='pending', assigned_to=plan.application.candidate.user
        )

        result = send_overdue_task_notifications()

        # Should notify both assignee and HR contact
        assert mock_notification.call_count >= 2


@pytest.mark.django_db
class TestAutoCompleteStalePlans:
    """Tests for auto_complete_stale_plans task."""

    @patch('apps.onboarding.services.OnboardingService.complete_plan')
    @patch('apps.communications.services.EmailService.send_onboarding_completed')
    def test_auto_complete_stale_plans(self, mock_email, mock_complete):
        """Test auto-completing plans past start date + 30 days with all tasks done."""
        cutoff_date = timezone.now().date() - timedelta(days=31)

        # Create stale plan with all tasks completed
        plan = OnboardingPlanFactory(status='in_progress', start_date=cutoff_date)
        OnboardingTaskFactory.create_batch(3, plan=plan, status='completed')

        result = auto_complete_stale_plans()

        assert result['success'] is True
        assert result['completed_count'] == 1
        mock_complete.assert_called_once_with(plan)

    @patch('apps.onboarding.services.OnboardingService.complete_plan')
    def test_do_not_complete_recent_plans(self, mock_complete):
        """Test that recent plans are not auto-completed."""
        recent_date = timezone.now().date() - timedelta(days=15)

        # Create recent plan
        plan = OnboardingPlanFactory(status='in_progress', start_date=recent_date)
        OnboardingTaskFactory.create_batch(3, plan=plan, status='completed')

        result = auto_complete_stale_plans()

        assert result['success'] is True
        assert result['completed_count'] == 0
        mock_complete.assert_not_called()

    @patch('apps.onboarding.services.OnboardingService.complete_plan')
    def test_do_not_complete_with_pending_tasks(self, mock_complete):
        """Test that plans with pending tasks are not auto-completed."""
        cutoff_date = timezone.now().date() - timedelta(days=31)

        # Create stale plan with pending tasks
        plan = OnboardingPlanFactory(status='in_progress', start_date=cutoff_date)
        OnboardingTaskFactory.create_batch(2, plan=plan, status='completed')
        OnboardingTaskFactory(plan=plan, status='pending')  # One pending task

        result = auto_complete_stale_plans()

        assert result['success'] is True
        assert result['completed_count'] == 0
        mock_complete.assert_not_called()

    @patch('apps.onboarding.services.OnboardingService.complete_plan')
    def test_do_not_complete_already_completed_plans(self, mock_complete):
        """Test that already completed plans are not processed."""
        cutoff_date = timezone.now().date() - timedelta(days=31)

        # Create completed plan
        plan = OnboardingPlanFactory(status='completed', start_date=cutoff_date)
        OnboardingTaskFactory.create_batch(3, plan=plan, status='completed')

        result = auto_complete_stale_plans()

        assert result['success'] is True
        assert result['completed_count'] == 0
        mock_complete.assert_not_called()
