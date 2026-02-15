"""Selectors for analytics app."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone

from apps.applications.models import Application
from apps.jobs.models import Requisition


class DashboardSelector:
    """Selector for dashboard data aggregation."""

    @staticmethod
    def get_recruiter_dashboard(user):
        """
        Get recruiter dashboard data.

        Args:
            user: User requesting dashboard data

        Returns:
            Dictionary with dashboard metrics
        """
        # Get requisitions for departments user has access to
        if hasattr(user, 'internal_profile'):
            accessible_departments = [user.internal_profile.department_id] if user.internal_profile.department else []
        else:
            accessible_departments = []

        # Open requisitions
        open_reqs = Requisition.objects.filter(
            status='open',
        )
        if accessible_departments:
            open_reqs = open_reqs.filter(department_id__in=accessible_departments)

        open_reqs_count = open_reqs.count()

        # Active candidates (applied in last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        active_candidates = Application.objects.filter(
            applied_at__gte=thirty_days_ago,
            status__in=['applied', 'screening', 'interview'],
        )
        if accessible_departments:
            active_candidates = active_candidates.filter(
                requisition__department_id__in=accessible_departments,
            )

        active_candidates_count = active_candidates.count()

        # Pending scorecards for user
        if hasattr(user, 'internal_profile'):
            from apps.interviews.selectors import InterviewSelector

            pending_scorecards = InterviewSelector.get_pending_scorecards(
                user.internal_profile,
            )
            pending_scorecards_count = pending_scorecards.count()
        else:
            pending_scorecards_count = 0

        # Upcoming interviews (next 7 days) for user
        if hasattr(user, 'internal_profile'):
            from apps.interviews.selectors import InterviewSelector

            upcoming_interviews = InterviewSelector.get_upcoming_interviews(
                user=user,
                days_ahead=7,
            )
            upcoming_interviews_count = upcoming_interviews.count()
            upcoming_interviews_list = list(upcoming_interviews[:5])  # Top 5
        else:
            upcoming_interviews_count = 0
            upcoming_interviews_list = []

        # Pending approvals
        from apps.jobs.models import RequisitionApproval

        pending_approvals = RequisitionApproval.objects.filter(
            approver__user=user,
            status='pending',
        ).select_related('requisition')
        pending_approvals_count = pending_approvals.count()

        # Overdue actions (applications in screening/interview for > 14 days)
        fourteen_days_ago = timezone.now() - timezone.timedelta(days=14)
        overdue_applications = Application.objects.filter(
            status__in=['screening', 'interview'],
            updated_at__lt=fourteen_days_ago,
        )
        if accessible_departments:
            overdue_applications = overdue_applications.filter(
                requisition__department_id__in=accessible_departments,
            )

        overdue_actions_count = overdue_applications.count()

        return {
            'open_requisitions': open_reqs_count,
            'active_candidates': active_candidates_count,
            'pending_scorecards': pending_scorecards_count,
            'upcoming_interviews': upcoming_interviews_count,
            'upcoming_interviews_list': upcoming_interviews_list,
            'pending_approvals': pending_approvals_count,
            'overdue_actions': overdue_actions_count,
        }

    @staticmethod
    def get_pipeline_metrics(requisition_id: str):
        """
        Get pipeline metrics for a specific requisition.

        Args:
            requisition_id: Requisition UUID

        Returns:
            Dictionary with pipeline stage counts
        """
        from apps.jobs.models import PipelineStage

        stages = PipelineStage.objects.filter(
            requisition_id=requisition_id,
        ).annotate(
            application_count=Count(
                'applications',
                filter=Q(applications__status='active'),
            ),
        ).order_by('order')

        return {
            'stages': [
                {
                    'id': str(stage.id),
                    'name': stage.name,
                    'count': stage.application_count,
                }
                for stage in stages
            ],
        }


class ExecutiveDashboardSelector:
    """Selector for executive dashboard metrics."""

    @staticmethod
    def get_dashboard_data(*, start_date=None, end_date=None, department_id=None):
        """
        Get executive dashboard metrics.

        Args:
            start_date: Start date for metrics (optional)
            end_date: End date for metrics (optional)
            department_id: Filter by department (optional)

        Returns:
            Dictionary with executive metrics
        """
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=90)  # Last 90 days by default

        # Base querysets
        reqs_qs = Requisition.objects.all()
        apps_qs = Application.objects.all()

        if department_id:
            reqs_qs = reqs_qs.filter(department_id=department_id)
            apps_qs = apps_qs.filter(requisition__department_id=department_id)

        # Open requisitions
        open_reqs = reqs_qs.filter(status='open').count()

        # Filled positions in date range
        filled_reqs = reqs_qs.filter(
            status='filled',
            closed_at__gte=start_date,
            closed_at__lte=end_date,
        )

        # Time to fill (average days from opened to closed/filled)
        time_to_fill_data = filled_reqs.aggregate(
            avg_days=Avg(
                F('closed_at') - F('opened_at'),
            ),
        )
        avg_time_to_fill = time_to_fill_data['avg_days'].days if time_to_fill_data['avg_days'] else 0

        # Offer acceptance rate
        offers_extended = apps_qs.filter(
            status='offer',
            created_at__gte=start_date,
            created_at__lte=end_date,
        ).count()

        offers_accepted = apps_qs.filter(
            status='hired',
            created_at__gte=start_date,
            created_at__lte=end_date,
        ).count()

        offer_acceptance_rate = (
            (offers_accepted / offers_extended * 100) if offers_extended > 0 else 0
        )

        # Pipeline conversion (applied → hired)
        applications_in_period = apps_qs.filter(
            applied_at__gte=start_date,
            applied_at__lte=end_date,
        ).count()

        hired_in_period = apps_qs.filter(
            status='hired',
            applied_at__gte=start_date,
            applied_at__lte=end_date,
        ).count()

        pipeline_conversion_rate = (
            (hired_in_period / applications_in_period * 100)
            if applications_in_period > 0
            else 0
        )

        # Hiring velocity (hires per month)
        days_in_period = (end_date - start_date).days
        months_in_period = max(days_in_period / 30, 1)
        hiring_velocity = hired_in_period / months_in_period

        # Requisition aging (open reqs by age buckets)
        now = timezone.now()
        open_reqs_list = reqs_qs.filter(status='open')

        req_aging = {
            '0-30_days': open_reqs_list.filter(
                opened_at__gte=now - timedelta(days=30),
            ).count(),
            '31-60_days': open_reqs_list.filter(
                opened_at__gte=now - timedelta(days=60),
                opened_at__lt=now - timedelta(days=30),
            ).count(),
            '61-90_days': open_reqs_list.filter(
                opened_at__gte=now - timedelta(days=90),
                opened_at__lt=now - timedelta(days=60),
            ).count(),
            '90+_days': open_reqs_list.filter(
                opened_at__lt=now - timedelta(days=90),
            ).count(),
        }

        # Source effectiveness
        source_data = apps_qs.filter(
            applied_at__gte=start_date,
            applied_at__lte=end_date,
        ).values('source').annotate(
            total_applications=Count('id'),
            hired_count=Count('id', filter=Q(status='hired')),
        ).order_by('-total_applications')[:10]

        source_effectiveness = [
            {
                'source': item['source'] or 'Direct',
                'applications': item['total_applications'],
                'hires': item['hired_count'],
                'conversion_rate': (
                    (item['hired_count'] / item['total_applications'] * 100)
                    if item['total_applications'] > 0
                    else 0
                ),
            }
            for item in source_data
        ]

        return {
            'open_requisitions': open_reqs,
            'avg_time_to_fill': round(avg_time_to_fill, 1),
            'offer_acceptance_rate': round(offer_acceptance_rate, 1),
            'pipeline_conversion_rate': round(pipeline_conversion_rate, 1),
            'hiring_velocity': round(hiring_velocity, 1),
            'requisition_aging': req_aging,
            'source_effectiveness': source_effectiveness,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
        }


class ReportSelector:
    """Selector for generating various reports."""

    @staticmethod
    def get_pipeline_conversion_report(*, start_date, end_date, department_id=None):
        """
        Generate pipeline conversion report.

        Shows conversion rates between each pipeline stage.
        """
        apps_qs = Application.objects.filter(
            applied_at__gte=start_date,
            applied_at__lte=end_date,
        )

        if department_id:
            apps_qs = apps_qs.filter(requisition__department_id=department_id)

        # Get counts by status
        status_counts = apps_qs.values('status').annotate(
            count=Count('id'),
        ).order_by('status')

        total_applications = apps_qs.count()

        conversions = []
        for status_data in status_counts:
            status = status_data['status']
            count = status_data['count']
            conversion_rate = (count / total_applications * 100) if total_applications > 0 else 0

            conversions.append({
                'stage': status.replace('_', ' ').title(),
                'count': count,
                'conversion_rate': round(conversion_rate, 2),
            })

        return {
            'total_applications': total_applications,
            'conversions': conversions,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
        }

    @staticmethod
    def get_time_to_fill_report(*, start_date, end_date, department_id=None):
        """
        Generate time-to-fill report.

        Shows average time to fill by department, level, location.
        """
        reqs_qs = Requisition.objects.filter(
            status='filled',
            closed_at__gte=start_date,
            closed_at__lte=end_date,
        )

        if department_id:
            reqs_qs = reqs_qs.filter(department_id=department_id)

        # Overall average
        overall_avg = reqs_qs.aggregate(
            avg_days=Avg(F('closed_at') - F('opened_at')),
        )
        overall_days = overall_avg['avg_days'].days if overall_avg['avg_days'] else 0

        # By department
        by_department = reqs_qs.values('department__name').annotate(
            avg_days=Avg(F('closed_at') - F('opened_at')),
            count=Count('id'),
        ).order_by('-count')

        department_data = [
            {
                'department': item['department__name'] or 'Unknown',
                'avg_days': item['avg_days'].days if item['avg_days'] else 0,
                'positions_filled': item['count'],
            }
            for item in by_department
        ]

        # By level
        by_level = reqs_qs.values('level__name').annotate(
            avg_days=Avg(F('closed_at') - F('opened_at')),
            count=Count('id'),
        ).order_by('-count')

        level_data = [
            {
                'level': item['level__name'] or 'Unknown',
                'avg_days': item['avg_days'].days if item['avg_days'] else 0,
                'positions_filled': item['count'],
            }
            for item in by_level
        ]

        return {
            'overall_avg_days': round(overall_days, 1),
            'by_department': department_data,
            'by_level': level_data,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
        }

    @staticmethod
    def get_source_effectiveness_report(*, start_date, end_date, department_id=None):
        """
        Generate source effectiveness report.

        Shows application sources and their conversion rates.
        """
        apps_qs = Application.objects.filter(
            applied_at__gte=start_date,
            applied_at__lte=end_date,
        )

        if department_id:
            apps_qs = apps_qs.filter(requisition__department_id=department_id)

        source_data = apps_qs.values('source').annotate(
            total=Count('id'),
            screened=Count('id', filter=Q(status__in=['screening', 'interview', 'offer', 'hired'])),
            interviewed=Count('id', filter=Q(status__in=['interview', 'offer', 'hired'])),
            offered=Count('id', filter=Q(status__in=['offer', 'hired'])),
            hired=Count('id', filter=Q(status='hired')),
        ).order_by('-total')

        sources = []
        for item in source_data:
            source_name = item['source'] or 'Direct'
            total = item['total']

            sources.append({
                'source': source_name,
                'applications': total,
                'screen_rate': round((item['screened'] / total * 100) if total > 0 else 0, 2),
                'interview_rate': round((item['interviewed'] / total * 100) if total > 0 else 0, 2),
                'offer_rate': round((item['offered'] / total * 100) if total > 0 else 0, 2),
                'hire_rate': round((item['hired'] / total * 100) if total > 0 else 0, 2),
                'hires': item['hired'],
            })

        return {
            'sources': sources,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
        }

    @staticmethod
    def get_offer_analysis_report(*, start_date, end_date, department_id=None):
        """
        Generate offer analysis report.

        Shows offer metrics including acceptance/decline rates and reasons.
        """
        from apps.offers.models import Offer

        offers_qs = Offer.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
        )

        if department_id:
            offers_qs = offers_qs.filter(application__requisition__department_id=department_id)

        total_offers = offers_qs.count()
        accepted = offers_qs.filter(status='accepted').count()
        declined = offers_qs.filter(status='declined').count()
        pending = offers_qs.filter(status='active').count()
        withdrawn = offers_qs.filter(status='withdrawn').count()

        acceptance_rate = (accepted / total_offers * 100) if total_offers > 0 else 0
        decline_rate = (declined / total_offers * 100) if total_offers > 0 else 0

        # Decline reasons
        decline_reasons = offers_qs.filter(
            status='declined',
            decline_reason__isnull=False,
        ).values('decline_reason').annotate(
            count=Count('id'),
        ).order_by('-count')

        return {
            'total_offers': total_offers,
            'accepted': accepted,
            'declined': declined,
            'pending': pending,
            'withdrawn': withdrawn,
            'acceptance_rate': round(acceptance_rate, 2),
            'decline_rate': round(decline_rate, 2),
            'decline_reasons': list(decline_reasons),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
        }

    @staticmethod
    def get_interviewer_calibration_report(*, start_date, end_date):
        """
        Generate interviewer calibration report.

        Shows interviewer scoring patterns and alignment.
        """
        from apps.interviews.models import Scorecard

        scorecards = Scorecard.objects.filter(
            submitted_at__gte=start_date,
            submitted_at__lte=end_date,
            submitted_at__isnull=False,
        ).select_related('interviewer__user', 'interview__application')

        # Overall stats
        total_scorecards = scorecards.count()
        avg_overall_rating = scorecards.aggregate(
            avg=Avg('overall_rating'),
        )['avg'] or 0

        # By interviewer
        by_interviewer = scorecards.values(
            'interviewer__user__first_name',
            'interviewer__user__last_name',
        ).annotate(
            count=Count('id'),
            avg_rating=Avg('overall_rating'),
            hire_recommendations=Count('id', filter=Q(recommendation='hire')),
            no_hire_recommendations=Count('id', filter=Q(recommendation='no_hire')),
        ).order_by('-count')

        interviewers = []
        for item in by_interviewer:
            total_recs = item['count']
            interviewers.append({
                'interviewer': f"{item['interviewer__user__first_name']} {item['interviewer__user__last_name']}",
                'scorecards_count': total_recs,
                'avg_rating': round(item['avg_rating'], 2),
                'hire_rate': round((item['hire_recommendations'] / total_recs * 100) if total_recs > 0 else 0, 2),
            })

        return {
            'total_scorecards': total_scorecards,
            'avg_overall_rating': round(avg_overall_rating, 2),
            'interviewers': interviewers,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
        }

    @staticmethod
    def get_requisition_aging_report():
        """
        Generate requisition aging report.

        Shows all open requisitions grouped by age.
        """
        now = timezone.now()
        open_reqs = Requisition.objects.filter(status='open').select_related(
            'department',
            'level',
            'location',
            'hiring_manager__user',
        )

        aged_reqs = []
        for req in open_reqs:
            days_open = (now - req.opened_at).days
            application_count = req.applications.filter(status='active').count()

            aged_reqs.append({
                'requisition_id': req.requisition_id,
                'title': req.title,
                'department': req.department.name if req.department else 'Unknown',
                'hiring_manager': req.hiring_manager.user.get_full_name() if req.hiring_manager else 'Unassigned',
                'opened_at': req.opened_at.isoformat(),
                'days_open': days_open,
                'applications': application_count,
            })

        # Sort by days open descending
        aged_reqs.sort(key=lambda x: x['days_open'], reverse=True)

        # Group by age bucket
        buckets = {
            '0-30 days': [r for r in aged_reqs if r['days_open'] <= 30],
            '31-60 days': [r for r in aged_reqs if 30 < r['days_open'] <= 60],
            '61-90 days': [r for r in aged_reqs if 60 < r['days_open'] <= 90],
            '90+ days': [r for r in aged_reqs if r['days_open'] > 90],
        }

        return {
            'total_open': len(aged_reqs),
            'by_age_bucket': {
                bucket: {
                    'count': len(reqs),
                    'requisitions': reqs,
                }
                for bucket, reqs in buckets.items()
            },
            'all_requisitions': aged_reqs,
        }
