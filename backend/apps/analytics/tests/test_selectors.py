"""Tests for analytics selectors."""

import pytest
from django.utils import timezone

from apps.accounts.tests.factories import DepartmentFactory, InternalUserFactory, UserFactory
from apps.analytics.selectors import DashboardSelector
from apps.applications.tests.factories import ApplicationFactory
from apps.jobs.tests.factories import PipelineStageFactory, RequisitionApprovalFactory, RequisitionFactory


@pytest.mark.django_db
class TestDashboardSelector:
    """Tests for DashboardSelector."""

    def test_get_recruiter_dashboard_no_profile(self):
        """User without internal profile gets zeros for all metrics."""
        user = UserFactory()

        dashboard = DashboardSelector.get_recruiter_dashboard(user)

        assert dashboard['open_requisitions'] == 0
        assert dashboard['active_candidates'] == 0
        assert dashboard['pending_scorecards'] == 0
        assert dashboard['upcoming_interviews'] == 0
        assert dashboard['pending_approvals'] == 0
        assert dashboard['overdue_actions'] == 0

    def test_get_recruiter_dashboard_with_data(self):
        """Dashboard shows correct metrics for recruiter with data."""
        # Setup
        department = DepartmentFactory()
        internal_user = InternalUserFactory(department=department)

        # Create open requisition with stage
        req1 = RequisitionFactory(department=department, status='open')
        stage = PipelineStageFactory(requisition=req1, order=0)

        # Create application (applied in last 30 days)
        ApplicationFactory(
            requisition=req1,
            current_stage=stage,
            status='screening',
        )

        # Create old application (>30 days, should not count as active)
        app2 = ApplicationFactory(
            requisition=req1,
            current_stage=stage,
            status='screening',
        )
        # Update applied_at to 40 days ago (can't set in factory due to auto_now_add)
        from apps.applications.models import Application
        Application.objects.filter(id=app2.id).update(
            applied_at=timezone.now() - timezone.timedelta(days=40)
        )

        # Create pending approval
        RequisitionApprovalFactory(
            requisition=req1,
            approver=internal_user,
            status='pending',
        )

        # Create overdue application (>14 days without update)
        app3 = ApplicationFactory(
            requisition=req1,
            current_stage=stage,
            status='interview',
        )
        # Update timestamps to 20 days ago
        Application.objects.filter(id=app3.id).update(
            applied_at=timezone.now() - timezone.timedelta(days=20),
            updated_at=timezone.now() - timezone.timedelta(days=20),
        )

        dashboard = DashboardSelector.get_recruiter_dashboard(internal_user.user)

        assert dashboard['open_requisitions'] == 1
        assert dashboard['active_candidates'] == 2  # app1 and app3 (last 30 days)
        assert dashboard['pending_approvals'] == 1
        assert dashboard['overdue_actions'] == 1  # app3 is overdue

    def test_get_recruiter_dashboard_filters_by_department(self):
        """Dashboard only shows data for recruiter's department."""
        # Setup recruiter in Engineering
        eng_dept = DepartmentFactory(name='Engineering')
        internal_user = InternalUserFactory(department=eng_dept)

        # Create requisition in Engineering
        eng_req = RequisitionFactory(department=eng_dept, status='open')

        # Create requisition in different department
        sales_dept = DepartmentFactory(name='Sales')
        sales_req = RequisitionFactory(department=sales_dept, status='open')

        # Create applications for both
        ApplicationFactory(
            requisition=eng_req,
            status='applied',
            applied_at=timezone.now() - timezone.timedelta(days=5),
        )

        ApplicationFactory(
            requisition=sales_req,
            status='applied',
            applied_at=timezone.now() - timezone.timedelta(days=5),
        )

        dashboard = DashboardSelector.get_recruiter_dashboard(internal_user.user)

        # Should only see Engineering requisition and candidate
        assert dashboard['open_requisitions'] == 1
        assert dashboard['active_candidates'] == 1

    def test_get_recruiter_dashboard_no_department(self):
        """Recruiter without department sees all requisitions (admin behavior)."""
        internal_user = InternalUserFactory(department=None)

        # Create requisition
        RequisitionFactory(status='open')

        dashboard = DashboardSelector.get_recruiter_dashboard(internal_user.user)

        # No department filter = sees all requisitions (admin/super-user behavior)
        assert dashboard['open_requisitions'] == 1
        assert dashboard['pending_approvals'] == 0

    def test_get_pipeline_metrics(self):
        """Pipeline metrics show correct application counts per stage."""
        # Setup
        requisition = RequisitionFactory(status='open')

        # Create stages
        stage1 = PipelineStageFactory(requisition=requisition, name='Applied', order=0)
        stage2 = PipelineStageFactory(requisition=requisition, name='Screening', order=1)
        PipelineStageFactory(requisition=requisition, name='Interview', order=2)

        # Create applications
        ApplicationFactory(
            requisition=requisition,
            status='active',
            current_stage=stage1,
        )
        ApplicationFactory(
            requisition=requisition,
            status='active',
            current_stage=stage2,
        )

        # Create rejected application (should not count)
        ApplicationFactory(
            requisition=requisition,
            status='rejected',
            current_stage=stage1,
        )

        metrics = DashboardSelector.get_pipeline_metrics(str(requisition.id))

        assert len(metrics['stages']) == 3
        assert metrics['stages'][0]['name'] == 'Applied'
        assert metrics['stages'][0]['count'] == 1  # Only active applications
        assert metrics['stages'][1]['name'] == 'Screening'
        assert metrics['stages'][1]['count'] == 1
        assert metrics['stages'][2]['name'] == 'Interview'
        assert metrics['stages'][2]['count'] == 0
