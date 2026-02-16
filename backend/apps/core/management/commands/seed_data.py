"""Management command to seed database with test data."""

# ruff: noqa: S311
# S311 disabled: This is a development seed script, not production cryptographic code.
# Using standard random module is acceptable for generating test data.

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import (
    CandidateProfile,
    Department,
    Education,
    InternalUser,
    JobLevel,
    Location,
    Permission,
    Role,
    Skill,
    Team,
    WorkExperience,
)
from apps.applications.models import Application, ApplicationEvent, Tag, TalentPool
from apps.assessments.models import AssessmentTemplate, Assessment, ReferenceCheckRequest
from apps.communications.models import MessageThread, Message
from apps.jobs.models import PipelineStage, Requisition
from apps.onboarding.models import OnboardingTemplate

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with test data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing data...')
            )
            self.clear_data()

        self.stdout.write('Seeding database with test data...')

        with transaction.atomic():
            # 1. Create permissions and roles
            self.stdout.write('Creating permissions and roles...')
            self.create_permissions_and_roles()

            # 2. Create departments
            self.stdout.write('Creating departments...')
            departments = self.create_departments()

            # 3. Create locations
            self.stdout.write('Creating locations...')
            locations = self.create_locations()

            # 4. Create job levels
            self.stdout.write('Creating job levels...')
            job_levels = self.create_job_levels()

            # 5. Create internal users
            self.stdout.write('Creating internal users...')
            internal_users = self.create_internal_users(departments)

            # 6. Create teams
            self.stdout.write('Creating teams...')
            self.create_teams(departments, internal_users)

            # 7. Create candidate profiles
            self.stdout.write('Creating candidate profiles...')
            candidates = self.create_candidates()

            # 8. Create requisitions
            self.stdout.write('Creating requisitions...')
            requisitions = self.create_requisitions(
                departments, locations, job_levels, internal_users
            )

            # 9. Create applications
            self.stdout.write('Creating applications...')
            applications = self.create_applications(candidates, requisitions)

            # 10. Create assessment templates
            self.stdout.write('Creating assessment templates...')
            templates = self.create_assessment_templates(internal_users)

            # 11. Create assessments
            self.stdout.write('Creating assessments...')
            self.create_assessments(applications, templates, internal_users)

            # 12. Create reference check requests
            self.stdout.write('Creating reference check requests...')
            self.create_reference_checks(applications, internal_users)

            # 13. Create talent pools
            self.stdout.write('Creating talent pools...')
            self.create_talent_pools(candidates, internal_users)

            # 14. Create message threads
            self.stdout.write('Creating message threads...')
            self.create_message_threads(applications, internal_users, candidates)

            # 15. Create compliance data
            self.stdout.write('Creating compliance data...')
            self.create_compliance_data(candidates, internal_users)

            # 16. Create onboarding templates
            self.stdout.write('Creating onboarding templates...')
            self.create_onboarding_data(departments, job_levels)

            # 17. Create integrations
            self.stdout.write('Creating integrations...')
            self.create_integrations()

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully seeded database with test data!'
            )
        )
        self.print_credentials()

    def clear_data(self):
        """Clear existing test data."""
        from django.db.models import signals

        # Temporarily disconnect ES signals to avoid connection errors
        try:
            from django_elasticsearch_dsl import signals as es_signals
            signals.post_save.disconnect(es_signals.handle_save)
            signals.post_delete.disconnect(es_signals.handle_delete)
            es_signals_disconnected = True
        except Exception:
            es_signals_disconnected = False

        try:
            # Import compliance models
            from apps.compliance.models import (
                AnonymizationRecord,
                ConsentRecord,
                DataRetentionPolicy,
                EEOData,
            )

            # Delete compliance data first
            ConsentRecord.objects.all().delete()
            AnonymizationRecord.objects.all().delete()
            EEOData.objects.all().delete()
            DataRetentionPolicy.objects.all().delete()

            # Delete other data
            Message.objects.all().delete()
            MessageThread.objects.all().delete()
            TalentPool.objects.all().delete()
            ReferenceCheckRequest.objects.all().delete()
            Assessment.objects.all().delete()
            AssessmentTemplate.objects.all().delete()
            Application.objects.all().delete()
            Requisition.objects.all().delete()
            CandidateProfile.objects.all().delete()
            InternalUser.objects.all().delete()
            Team.objects.all().delete()
            Department.objects.all().delete()
            Location.objects.all().delete()
        finally:
            # Reconnect ES signals
            if es_signals_disconnected:
                signals.post_save.connect(es_signals.handle_save)
                signals.post_delete.connect(es_signals.handle_delete)
        JobLevel.objects.all().delete()
        Role.objects.all().delete()
        Permission.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Tag.objects.all().delete()

    def create_permissions_and_roles(self):
        """Create RBAC permissions and roles."""
        modules = [
            'accounts',
            'candidates',
            'jobs',
            'applications',
            'interviews',
            'assessments',
            'offers',
            'onboarding',
            'communications',
            'analytics',
            'integrations',
            'compliance',
        ]
        actions = ['view', 'create', 'edit', 'delete', 'approve']

        # Create permissions
        for module in modules:
            for action in actions:
                codename = f'{module}.{action}_{module}'
                Permission.objects.get_or_create(
                    codename=codename,
                    defaults={
                        'name': f'{action.title()} {module.title()}',
                        'module': module,
                        'action': action,
                    },
                )

        # Create roles
        role_configs = {
            'Super Admin': {
                'description': 'Full system access',
                'is_system': True,
                'modules': modules,
                'actions': actions,
            },
            'HR Admin': {
                'description': 'HR administrative access',
                'is_system': True,
                'modules': modules,
                'actions': ['view', 'create', 'edit'],
            },
            'Recruiter': {
                'description': 'Recruiter role',
                'is_system': True,
                'modules': [
                    'candidates',
                    'jobs',
                    'applications',
                    'interviews',
                    'communications',
                ],
                'actions': ['view', 'create', 'edit'],
            },
            'Hiring Manager': {
                'description': 'Hiring manager role',
                'is_system': True,
                'modules': [
                    'jobs',
                    'applications',
                    'interviews',
                    'offers',
                ],
                'actions': ['view', 'approve'],
            },
            'Interviewer': {
                'description': 'Interviewer role',
                'is_system': True,
                'modules': ['applications', 'interviews'],
                'actions': ['view', 'create'],
            },
        }

        for role_name, config in role_configs.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    'description': config['description'],
                    'is_system': config['is_system'],
                },
            )

            # Add permissions
            if created or not role.permissions.exists():
                perms = Permission.objects.filter(
                    module__in=config['modules'],
                    action__in=config['actions'],
                )
                role.permissions.set(perms)

    def create_departments(self):
        """Create departments."""
        dept_data = [
            'Engineering',
            'Product',
            'Design',
            'Marketing',
            'Sales',
            'Customer Success',
            'Finance',
            'People & Culture',
            'Legal',
            'Operations',
        ]

        departments = []
        for name in dept_data:
            dept, _ = Department.objects.get_or_create(
                name=name,
                defaults={'is_active': True},
            )
            departments.append(dept)

        return departments

    def create_locations(self):
        """Create office locations."""
        location_data = [
            {
                'name': 'San Francisco HQ',
                'city': 'San Francisco',
                'country': 'USA',
                'address': '123 Market St, San Francisco, CA 94103',
            },
            {
                'name': 'New York Office',
                'city': 'New York',
                'country': 'USA',
                'address': '456 Broadway, New York, NY 10013',
            },
            {
                'name': 'London Office',
                'city': 'London',
                'country': 'UK',
                'address': '789 Oxford St, London W1D 2HG',
            },
            {
                'name': 'Remote',
                'city': 'Remote',
                'country': 'Global',
                'address': '',
                'is_remote': True,
            },
        ]

        locations = []
        for data in location_data:
            loc, _ = Location.objects.get_or_create(
                name=data['name'],
                defaults=data,
            )
            locations.append(loc)

        return locations

    def create_job_levels(self):
        """Create job levels."""
        level_data = [
            {
                'name': 'Individual Contributor 1',
                'level_number': 1,
                'salary_band_min': Decimal('50000'),
                'salary_band_max': Decimal('70000'),
            },
            {
                'name': 'Individual Contributor 2',
                'level_number': 2,
                'salary_band_min': Decimal('70000'),
                'salary_band_max': Decimal('90000'),
            },
            {
                'name': 'Individual Contributor 3',
                'level_number': 3,
                'salary_band_min': Decimal('90000'),
                'salary_band_max': Decimal('120000'),
            },
            {
                'name': 'Senior Individual Contributor',
                'level_number': 4,
                'salary_band_min': Decimal('120000'),
                'salary_band_max': Decimal('160000'),
            },
            {
                'name': 'Staff / Manager',
                'level_number': 5,
                'salary_band_min': Decimal('160000'),
                'salary_band_max': Decimal('200000'),
            },
            {
                'name': 'Senior Manager / Principal',
                'level_number': 6,
                'salary_band_min': Decimal('200000'),
                'salary_band_max': Decimal('250000'),
            },
            {
                'name': 'Director',
                'level_number': 7,
                'salary_band_min': Decimal('250000'),
                'salary_band_max': Decimal('300000'),
            },
        ]

        job_levels = []
        for data in level_data:
            level, _ = JobLevel.objects.get_or_create(
                level_number=data['level_number'],
                defaults=data,
            )
            job_levels.append(level)

        return job_levels

    def create_internal_users(self, departments):
        """Create internal staff users."""
        # Create superuser - lookup by username since it's the unique identifier
        superuser, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@hrplus.local',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'is_internal': True,
            },
        )
        if created:
            superuser.set_password('admin123')
            superuser.save()
        else:
            # Update existing superuser with seed data values
            superuser.email = 'admin@hrplus.local'
            superuser.first_name = 'Admin'
            superuser.last_name = 'User'
            superuser.is_staff = True
            superuser.is_superuser = True
            superuser.is_internal = True
            superuser.set_password('admin123')
            superuser.save()

        # Create InternalUser profile for admin if it doesn't exist
        admin_internal, admin_created = InternalUser.objects.get_or_create(
            user=superuser,
            defaults={
                'employee_id': 'EMP000',
                'title': 'System Administrator',
                'department': departments[7] if len(departments) > 7 else None,  # People & Culture
            },
        )

        # Assign Super Admin role to admin
        super_admin_role = Role.objects.get(name='Super Admin')
        admin_internal.roles.add(super_admin_role)

        # Create internal users
        users_data = [
            {
                'email': 'sarah.recruiter@hrplus.local',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'employee_id': 'EMP001',
                'title': 'Senior Technical Recruiter',
                'department': departments[0],  # Engineering
                'role': 'Recruiter',
            },
            {
                'email': 'mike.manager@hrplus.local',
                'first_name': 'Mike',
                'last_name': 'Chen',
                'employee_id': 'EMP002',
                'title': 'Engineering Manager',
                'department': departments[0],
                'role': 'Hiring Manager',
            },
            {
                'email': 'jessica.hr@hrplus.local',
                'first_name': 'Jessica',
                'last_name': 'Williams',
                'employee_id': 'EMP003',
                'title': 'HR Manager',
                'department': departments[7],  # People & Culture
                'role': 'HR Admin',
            },
            {
                'email': 'david.interviewer@hrplus.local',
                'first_name': 'David',
                'last_name': 'Brown',
                'employee_id': 'EMP004',
                'title': 'Senior Software Engineer',
                'department': departments[0],
                'role': 'Interviewer',
            },
        ]

        internal_users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'username': user_data['email'].split('@')[0],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_staff': True,
                    'is_internal': True,
                },
            )
            if created:
                user.set_password('password123')
                user.save()

            internal, _ = InternalUser.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': user_data['employee_id'],
                    'title': user_data['title'],
                    'department': user_data['department'],
                },
            )

            # Assign role
            role = Role.objects.get(name=user_data['role'])
            internal.roles.add(role)

            internal_users.append(internal)

        return internal_users

    def create_teams(self, departments, internal_users):
        """Create teams within departments."""
        teams_data = [
            {
                'name': 'Backend',
                'department': departments[0],  # Engineering
                'lead': internal_users[1] if len(internal_users) > 1 else None,
            },
            {
                'name': 'Frontend',
                'department': departments[0],
                'lead': None,
            },
            {
                'name': 'Product Marketing',
                'department': departments[3],  # Marketing
                'lead': None,
            },
        ]

        teams = []
        for data in teams_data:
            team, _ = Team.objects.get_or_create(
                name=data['name'],
                department=data['department'],
                defaults={'lead': data['lead']},
            )
            teams.append(team)

        return teams

    def create_candidates(self):
        """Create candidate profiles."""
        candidates_data = [
            {
                'email': 'john.doe@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '+1-555-0101',
                'location_city': 'San Francisco',
                'location_country': 'USA',
                'work_authorization': 'citizen',
                'linkedin_url': 'https://linkedin.com/in/johndoe',
            },
            {
                'email': 'jane.smith@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'phone': '+1-555-0102',
                'location_city': 'New York',
                'location_country': 'USA',
                'work_authorization': 'citizen',
                'linkedin_url': 'https://linkedin.com/in/janesmith',
            },
            {
                'email': 'alex.kumar@example.com',
                'first_name': 'Alex',
                'last_name': 'Kumar',
                'phone': '+1-555-0103',
                'location_city': 'Austin',
                'location_country': 'USA',
                'work_authorization': 'visa_holder',
                'linkedin_url': 'https://linkedin.com/in/alexkumar',
            },
            {
                'email': 'maria.garcia@example.com',
                'first_name': 'Maria',
                'last_name': 'Garcia',
                'phone': '+1-555-0104',
                'location_city': 'Los Angeles',
                'location_country': 'USA',
                'work_authorization': 'citizen',
                'portfolio_url': 'https://mariagarcia.dev',
            },
            {
                'email': 'thomas.anderson@example.com',
                'first_name': 'Thomas',
                'last_name': 'Anderson',
                'phone': '+1-555-0105',
                'location_city': 'Seattle',
                'location_country': 'USA',
                'work_authorization': 'citizen',
                'linkedin_url': 'https://linkedin.com/in/thomasanderson',
            },
        ]

        candidates = []
        for data in candidates_data:
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'username': data['email'].split('@')[0],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'is_internal': False,
                },
            )
            if created:
                user.set_password('candidate123')
                user.save()

            profile, _ = CandidateProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone': data['phone'],
                    'location_city': data['location_city'],
                    'location_country': data['location_country'],
                    'work_authorization': data['work_authorization'],
                    'linkedin_url': data.get('linkedin_url', ''),
                    'portfolio_url': data.get('portfolio_url', ''),
                    'source': random.choice(
                        ['direct', 'linkedin', 'indeed', 'career_site']
                    ),
                },
            )

            # Add work experience
            self.add_work_experience(profile)

            # Add education
            self.add_education(profile)

            # Add skills
            self.add_skills(profile)

            candidates.append(profile)

        return candidates

    def add_work_experience(self, candidate):
        """Add work experience to candidate."""
        companies = [
            'Google',
            'Microsoft',
            'Amazon',
            'Meta',
            'Apple',
            'Startup Inc',
        ]
        titles = [
            'Software Engineer',
            'Senior Software Engineer',
            'Full Stack Developer',
            'Backend Engineer',
            'Frontend Developer',
        ]

        for i in range(random.randint(1, 3)):
            start = date.today() - timedelta(days=random.randint(365, 2000))
            end = (
                None
                if i == 0
                else start + timedelta(days=random.randint(365, 1000))
            )

            WorkExperience.objects.create(
                candidate=candidate,
                company_name=random.choice(companies),
                title=random.choice(titles),
                start_date=start,
                end_date=end,
                is_current=(i == 0),
                description='Led development of key features and mentored junior engineers.',
            )

    def add_education(self, candidate):
        """Add education to candidate."""
        universities = [
            'Stanford University',
            'MIT',
            'UC Berkeley',
            'Carnegie Mellon',
            'Harvard University',
        ]
        degrees = [
            "Bachelor's in Computer Science",
            "Master's in Computer Science",
            "Bachelor's in Software Engineering",
        ]

        start = date(2015, 9, 1)
        end = date(2019, 6, 1)

        Education.objects.create(
            candidate=candidate,
            institution=random.choice(universities),
            degree=random.choice(degrees),
            field_of_study='Computer Science',
            start_date=start,
            end_date=end,
            gpa=Decimal(str(round(random.uniform(3.0, 4.0), 2))),
        )

    def add_skills(self, candidate):
        """Add skills to candidate."""
        all_skills = [
            'Python',
            'JavaScript',
            'TypeScript',
            'React',
            'Django',
            'Node.js',
            'PostgreSQL',
            'AWS',
            'Docker',
            'Kubernetes',
            'Git',
            'REST APIs',
            'GraphQL',
            'Redis',
            'MongoDB',
        ]

        num_skills = random.randint(5, 10)
        skills = random.sample(all_skills, num_skills)

        for skill_name in skills:
            Skill.objects.get_or_create(
                candidate=candidate,
                name=skill_name,
                defaults={
                    'proficiency': random.choice(
                        ['intermediate', 'advanced', 'expert']
                    ),
                    'years_experience': random.randint(1, 8),
                },
            )

    def create_requisitions(
        self, departments, locations, job_levels, internal_users
    ):
        """Create job requisitions."""
        req_data = [
            {
                'title': 'Senior Software Engineer - Backend',
                'department': departments[0],  # Engineering
                'level': job_levels[3],  # Senior IC
                'status': 'open',
                'description': 'We are looking for an experienced backend engineer to join our team...',
            },
            {
                'title': 'Frontend Engineer',
                'department': departments[0],
                'level': job_levels[2],  # IC3
                'status': 'open',
                'description': 'Join our frontend team to build amazing user experiences...',
            },
            {
                'title': 'Product Designer',
                'department': departments[2],  # Design
                'level': job_levels[2],
                'status': 'open',
                'description': 'Looking for a creative product designer...',
            },
            {
                'title': 'Engineering Manager',
                'department': departments[0],
                'level': job_levels[5],  # Manager
                'status': 'draft',
                'description': 'Lead and grow our engineering team...',
            },
            {
                'title': 'DevOps Engineer',
                'department': departments[0],
                'level': job_levels[3],
                'status': 'on_hold',
                'description': 'Build and maintain our infrastructure...',
            },
        ]

        requisitions = []
        for idx, data in enumerate(req_data, start=1):
            req_id = f'REQ-2026-{idx:03d}'

            req, created = Requisition.objects.get_or_create(
                requisition_id=req_id,
                defaults={
                    'title': data['title'],
                    'department': data['department'],
                    'hiring_manager': internal_users[
                        1
                    ],  # Mike (Hiring Manager)
                    'recruiter': internal_users[0],  # Sarah (Recruiter)
                    'created_by': internal_users[0],  # Created by Sarah (Recruiter)
                    'status': data['status'],
                    'employment_type': 'full_time',
                    'level': data['level'],
                    'location': locations[0],  # San Francisco
                    'remote_policy': random.choice(
                        ['onsite', 'hybrid', 'remote']
                    ),
                    'salary_min': data['level'].salary_band_min,
                    'salary_max': data['level'].salary_band_max,
                    'salary_currency': 'ZAR',
                    'description': data['description'],
                    'requirements_required': {
                        'skills': ['Python', 'Django', 'PostgreSQL'],
                        'experience_years': 5,
                    },
                    'headcount': 1,
                    'filled_count': 0,
                },
            )

            if created:
                # Create default pipeline stages
                self.create_pipeline_stages(req)

            requisitions.append(req)

        return requisitions

    def create_pipeline_stages(self, requisition):
        """Create default pipeline stages for a requisition."""
        stages_data = [
            {'name': 'Applied', 'order': 1, 'stage_type': 'screening'},
            {'name': 'Phone Screen', 'order': 2, 'stage_type': 'interview'},
            {'name': 'Technical Interview', 'order': 3, 'stage_type': 'interview'},
            {'name': 'Team Interview', 'order': 4, 'stage_type': 'interview'},
            {'name': 'Offer', 'order': 5, 'stage_type': 'offer'},
            {'name': 'Hired', 'order': 6, 'stage_type': 'hired'},
        ]

        for stage_data in stages_data:
            PipelineStage.objects.get_or_create(
                requisition=requisition,
                name=stage_data['name'],
                defaults={
                    'order': stage_data['order'],
                    'stage_type': stage_data['stage_type'],
                },
            )

    def create_applications(self, candidates, requisitions):
        """Create applications from candidates to requisitions."""
        # Create applications (2-3 per open requisition)
        open_reqs = [r for r in requisitions if r.status == 'open']

        applications = []
        app_count = 1
        for req in open_reqs:
            num_apps = random.randint(2, 4)
            selected_candidates = random.sample(
                candidates, min(num_apps, len(candidates))
            )

            stages = list(req.stages.all().order_by('order'))

            for candidate in selected_candidates:
                # Check if application already exists
                if Application.objects.filter(
                    candidate=candidate, requisition=req
                ).exists():
                    continue

                app_id = f'APP-2026-{app_count:04d}'
                current_stage = random.choice(stages[:3])  # First 3 stages

                # Map stage to status
                status_map = {
                    'Applied': 'applied',
                    'Phone Screen': 'screening',
                    'Technical Interview': 'interview',
                }
                status = status_map.get(current_stage.name, 'applied')

                cover_letter = (
                    'I am very interested in this position and believe '
                    'my skills align well with the requirements.'
                )

                application = Application.objects.create(
                    application_id=app_id,
                    candidate=candidate,
                    requisition=req,
                    status=status,
                    current_stage=current_stage,
                    source=candidate.source,
                    cover_letter=cover_letter,
                    screening_responses={},
                    is_starred=(random.random() > 0.7),  # Star 30%
                )

                # Create application event
                ApplicationEvent.objects.create(
                    application=application,
                    event_type='application.created',
                    metadata={
                        'stage_id': str(current_stage.id),
                        'stage_name': current_stage.name,
                    },
                )

                applications.append(application)
                app_count += 1

        return applications

    def create_assessment_templates(self, internal_users):
        """Create assessment templates."""
        from django.utils import timezone

        templates_data = [
            {
                'name': 'Python Backend Assessment',
                'type': 'coding',
                'description': 'Technical assessment for backend Python developers',
                'instructions': (
                    'Complete the coding challenges within the time limit. '
                    'Write clean, well-documented code.'
                ),
                'duration': 90,  # 90 minutes
                'passing_score': Decimal('70.00'),
                'questions': [
                    {
                        'id': 'q1',
                        'question': 'Implement a function to reverse a linked list',
                        'type': 'code',
                        'points': 30,
                    },
                    {
                        'id': 'q2',
                        'question': 'Design a REST API for a blog system',
                        'type': 'code',
                        'points': 40,
                    },
                    {
                        'id': 'q3',
                        'question': 'Optimize this database query',
                        'type': 'code',
                        'points': 30,
                    },
                ],
                'scoring_rubric': {
                    'code_quality': {'weight': 30, 'max': 100},
                    'correctness': {'weight': 50, 'max': 100},
                    'efficiency': {'weight': 20, 'max': 100},
                },
            },
            {
                'name': 'System Design Interview',
                'type': 'technical',
                'description': 'System design assessment for senior engineers',
                'instructions': (
                    'Design a scalable system based on the requirements provided. '
                    'Consider trade-offs and justify your decisions.'
                ),
                'duration': 60,
                'passing_score': Decimal('75.00'),
                'questions': [
                    {
                        'id': 'q1',
                        'question': 'Design a URL shortening service like bit.ly',
                        'type': 'design',
                        'points': 50,
                    },
                    {
                        'id': 'q2',
                        'question': 'How would you scale this to handle 1M requests/sec?',
                        'type': 'design',
                        'points': 50,
                    },
                ],
            },
            {
                'name': 'Behavioral Assessment',
                'type': 'behavioral',
                'description': 'Evaluate cultural fit and soft skills',
                'instructions': 'Answer the following questions thoughtfully and honestly.',
                'duration': 30,
                'passing_score': None,
                'questions': [
                    {
                        'id': 'q1',
                        'question': (
                            'Describe a challenging project you worked on '
                            'and how you overcame obstacles'
                        ),
                        'type': 'text',
                        'points': 25,
                    },
                    {
                        'id': 'q2',
                        'question': 'How do you handle conflicts with team members?',
                        'type': 'text',
                        'points': 25,
                    },
                    {
                        'id': 'q3',
                        'question': 'What motivates you in your work?',
                        'type': 'text',
                        'points': 25,
                    },
                    {
                        'id': 'q4',
                        'question': 'Where do you see yourself in 5 years?',
                        'type': 'text',
                        'points': 25,
                    },
                ],
            },
            {
                'name': 'Culture Fit Assessment',
                'type': 'culture_fit',
                'description': 'Evaluate alignment with company values',
                'instructions': (
                    'Rate the following statements based on your preferences.'
                ),
                'duration': 20,
                'passing_score': None,
                'questions': [
                    {
                        'id': 'q1',
                        'question': 'I prefer working independently vs. in a team',
                        'type': 'rating',
                        'scale': 5,
                    },
                    {
                        'id': 'q2',
                        'question': 'I value work-life balance',
                        'type': 'rating',
                        'scale': 5,
                    },
                ],
            },
        ]

        templates = []
        for data in templates_data:
            template, _ = AssessmentTemplate.objects.get_or_create(
                name=data['name'],
                defaults=data,
            )
            templates.append(template)

        return templates

    def create_assessments(self, applications, templates, internal_users):
        """Create assessments for some applications."""
        from apps.assessments.services import AssessmentService

        # Assign assessments to ~50% of applications
        for application in applications[: len(applications) // 2]:
            # Pick a random template (coding or behavioral)
            template = random.choice(templates[:3])
            recruiter = internal_users[0]  # Sarah (Recruiter)

            try:
                AssessmentService.assign_assessment(
                    application=application,
                    template=template,
                    assigned_by=recruiter,
                    due_days=random.randint(3, 7),
                )
            except Exception:
                # Skip if already assigned
                pass

    def create_reference_checks(self, applications, internal_users):
        """Create reference check requests for some applications."""
        from apps.assessments.services import ReferenceCheckService

        # Create references for ~30% of applications
        for application in applications[: len(applications) // 3]:
            recruiter = internal_users[0]  # Sarah (Recruiter)

            # Create 2 reference checks per application
            references_data = [
                {
                    'name': f'{application.candidate.user.first_name} Manager',
                    'email': f'manager.{application.candidate.user.email}',
                    'phone': '+1-555-0200',
                    'company': 'Previous Company Inc',
                    'title': 'Engineering Manager',
                    'relationship': 'manager',
                },
                {
                    'name': f'{application.candidate.user.first_name} Colleague',
                    'email': f'colleague.{application.candidate.user.email}',
                    'phone': '+1-555-0201',
                    'company': 'Previous Company Inc',
                    'title': 'Senior Engineer',
                    'relationship': 'colleague',
                },
            ]

            for ref_data in references_data:
                try:
                    ReferenceCheckService.create_reference_request(
                        application=application,
                        reference_name=ref_data['name'],
                        reference_email=ref_data['email'],
                        requested_by=recruiter,
                        reference_phone=ref_data['phone'],
                        reference_company=ref_data['company'],
                        reference_title=ref_data['title'],
                        relationship=ref_data['relationship'],
                        due_days=14,
                    )
                except Exception:
                    # Skip if duplicate
                    pass

    def create_talent_pools(self, candidates, internal_users):
        """Create talent pools for proactive recruiting."""
        from apps.applications.services import TalentPoolService

        pools_data = [
            {
                'name': 'Senior Python Engineers',
                'description': 'Experienced Python developers with 5+ years',
                'is_dynamic': False,
            },
            {
                'name': 'Frontend Specialists',
                'description': 'React and TypeScript experts',
                'is_dynamic': False,
            },
            {
                'name': 'SF Bay Area Candidates',
                'description': 'Candidates in San Francisco Bay Area',
                'is_dynamic': True,
                'search_criteria': {'location': 'San Francisco', 'radius_miles': 50},
            },
        ]

        for pool_data in pools_data:
            try:
                pool = TalentPoolService.create_pool(
                    name=pool_data['name'],
                    description=pool_data['description'],
                    owner=random.choice(internal_users),
                    is_dynamic=pool_data.get('is_dynamic', False),
                    search_criteria=pool_data.get('search_criteria', {}),
                )

                # Add some random candidates to static pools
                if not pool.is_dynamic:
                    num_candidates = random.randint(3, 8)
                    pool_candidates = random.sample(
                        list(candidates),
                        min(num_candidates, len(candidates)),
                    )
                    pool.candidates.add(*pool_candidates)
            except Exception:
                # Skip if duplicate
                pass

    def create_message_threads(self, applications, internal_users, candidates):
        """Create message threads between recruiters and candidates."""
        from apps.communications.services import MessagingService

        # Select a few applications to create message threads for
        sample_applications = random.sample(
            list(applications),
            min(5, len(applications)),
        )

        for application in sample_applications:
            candidate_user = application.candidate.user
            recruiter = random.choice(internal_users).user

            # Create thread about the application
            thread = MessagingService.create_thread(
                subject=f'Regarding your application for {application.requisition.title}',
                participants=[candidate_user, recruiter],
                application=application,
                created_by=recruiter,
            )

            # Add some messages to the conversation
            messages = [
                (
                    recruiter,
                    f'Hi {candidate_user.first_name}, thank you for applying to the {application.requisition.title} position! '
                    f'I wanted to reach out and let you know that we have received your application.',
                ),
                (
                    candidate_user,
                    f'Thank you for the update! I am very excited about this opportunity. '
                    f'When can I expect to hear back about next steps?',
                ),
                (
                    recruiter,
                    f'We are currently reviewing all applications and expect to complete the initial screening by next week. '
                    f'If your qualifications match what we are looking for, we will reach out to schedule an initial interview.',
                ),
                (
                    candidate_user,
                    f'That sounds great! I look forward to hearing from you.',
                ),
            ]

            # Send the messages
            for sender, body in messages:
                MessagingService.send_message(
                    thread=thread,
                    sender=sender,
                    body=body,
                )

        # Create a general thread between recruiters (team discussion)
        if len(internal_users) >= 2:
            recruiter1 = internal_users[0].user
            recruiter2 = internal_users[1].user

            team_thread = MessagingService.create_thread(
                subject='Weekly recruiting sync',
                participants=[recruiter1, recruiter2],
                created_by=recruiter1,
            )

            team_messages = [
                (
                    recruiter1,
                    'Hey, wanted to check in on the hiring pipeline for this week. '
                    'How are your candidates progressing?',
                ),
                (
                    recruiter2,
                    'Going well! I have 3 candidates moving to the interview stage this week. '
                    'What about you?',
                ),
                (
                    recruiter1,
                    'Same here. We should coordinate schedules for the interview panels.',
                ),
            ]

            for sender, body in team_messages:
                MessagingService.send_message(
                    thread=team_thread,
                    sender=sender,
                    body=body,
                )

    def create_compliance_data(self, candidates, internal_users):
        """Create compliance-related test data."""
        from apps.compliance.models import ConsentRecord, DataRetentionPolicy
        from apps.compliance.services import GDPRService

        # Create data retention policies
        policies = [
            {
                'data_type': 'candidate_application',
                'retention_days': 730,  # 2 years
                'grace_period_days': 30,
                'is_active': True,
                'description': 'Retain candidate applications for 2 years after last update.',
            },
            {
                'data_type': 'candidate_profile',
                'retention_days': 1095,  # 3 years
                'grace_period_days': 30,
                'is_active': True,
                'description': 'Retain candidate profiles for 3 years after creation.',
            },
            {
                'data_type': 'assessment_results',
                'retention_days': 730,  # 2 years
                'grace_period_days': 30,
                'is_active': True,
                'description': 'Retain assessment results for 2 years.',
            },
            {
                'data_type': 'interview_notes',
                'retention_days': 730,  # 2 years
                'grace_period_days': 30,
                'is_active': True,
                'description': 'Retain interview notes for 2 years.',
            },
            {
                'data_type': 'communication_logs',
                'retention_days': 365,  # 1 year
                'grace_period_days': 30,
                'is_active': True,
                'description': 'Retain communication logs for 1 year.',
            },
            {
                'data_type': 'audit_logs',
                'retention_days': 2555,  # 7 years (legal requirement)
                'grace_period_days': 0,
                'is_active': True,
                'description': 'Retain audit logs for 7 years (legal requirement).',
            },
        ]

        for policy_data in policies:
            DataRetentionPolicy.objects.get_or_create(
                data_type=policy_data['data_type'],
                defaults=policy_data,
            )

        # Create consent records for candidates
        consent_types = ['data_processing', 'marketing', 'eeo_collection']

        for candidate in candidates[:5]:  # First 5 candidates
            for consent_type in consent_types:
                # Random chance of having each consent
                if random.random() > 0.3:  # 70% chance
                    GDPRService.record_consent(
                        user=candidate.user,
                        consent_type=consent_type,
                        ip_address=f'192.168.1.{random.randint(1, 254)}',
                        user_agent='Mozilla/5.0 (Test Browser)',
                    )

        # Create consent records for internal users
        for internal_user in internal_users[:3]:
            for consent_type in ['data_processing', 'marketing']:
                GDPRService.record_consent(
                    user=internal_user.user,
                    consent_type=consent_type,
                    ip_address=f'10.0.0.{random.randint(1, 254)}',
                    user_agent='Mozilla/5.0 (Internal Browser)',
                )

        # Note: We do NOT create sample EEO data as it contains sensitive information
        # EEO data should only be created by actual candidates through the proper flow

    def create_onboarding_data(self, departments, job_levels):
        """Create onboarding templates."""
        # Engineering onboarding template
        engineering_template = OnboardingTemplate.objects.create(
            name='Engineering Onboarding',
            description='Standard onboarding process for engineering hires',
            department=departments[0],  # Engineering
            job_level=None,  # Apply to all levels
            is_active=True,
            tasks=[
                {
                    'title': 'Complete I-9 Verification',
                    'description': 'Submit I-9 form with required documentation (passport, driver license, SSN card)',
                    'category': 'admin',
                    'days_offset': 0,
                    'assigned_to': 'candidate',
                },
                {
                    'title': 'Sign Employee Handbook',
                    'description': 'Review and sign the employee handbook acknowledgment',
                    'category': 'admin',
                    'days_offset': 0,
                    'assigned_to': 'candidate',
                },
                {
                    'title': 'Setup Workstation',
                    'description': 'Configure laptop, development environment, and necessary software',
                    'category': 'equipment',
                    'days_offset': 1,
                    'assigned_to': 'it',
                },
                {
                    'title': 'Create Email and Slack Accounts',
                    'description': 'Setup company email and add to relevant Slack channels',
                    'category': 'equipment',
                    'days_offset': 1,
                    'assigned_to': 'it',
                },
                {
                    'title': 'Welcome Team Meeting',
                    'description': 'Meet the team and get introduced to ongoing projects',
                    'category': 'meeting',
                    'days_offset': 1,
                    'assigned_to': 'buddy',
                },
                {
                    'title': 'Review Codebase',
                    'description': 'Clone repositories and review project structure',
                    'category': 'training',
                    'days_offset': 2,
                    'assigned_to': 'buddy',
                },
                {
                    'title': 'Security Training',
                    'description': 'Complete mandatory security awareness training',
                    'category': 'training',
                    'days_offset': 3,
                    'assigned_to': 'candidate',
                },
                {
                    'title': 'First Code Review',
                    'description': 'Complete first pull request and code review',
                    'category': 'other',
                    'days_offset': 7,
                    'assigned_to': 'candidate',
                },
            ],
            required_documents=['i9', 'w4', 'direct_deposit', 'emergency_contact'],
            forms=['equipment_preferences', 'emergency_contact'],
        )

        # Product onboarding template
        product_template = OnboardingTemplate.objects.create(
            name='Product Team Onboarding',
            description='Onboarding for product managers and designers',
            department=departments[2] if len(departments) > 2 else departments[0],  # Product
            job_level=None,
            is_active=True,
            tasks=[
                {
                    'title': 'Complete I-9 Verification',
                    'description': 'Submit I-9 form with required documentation',
                    'category': 'admin',
                    'days_offset': 0,
                    'assigned_to': 'candidate',
                },
                {
                    'title': 'Sign Employee Handbook',
                    'description': 'Review and sign employee handbook',
                    'category': 'admin',
                    'days_offset': 0,
                    'assigned_to': 'candidate',
                },
                {
                    'title': 'Setup Workstation',
                    'description': 'Configure laptop and design/product tools',
                    'category': 'equipment',
                    'days_offset': 1,
                    'assigned_to': 'it',
                },
                {
                    'title': 'Product Roadmap Overview',
                    'description': 'Review current product roadmap and priorities',
                    'category': 'training',
                    'days_offset': 1,
                    'assigned_to': 'buddy',
                },
                {
                    'title': 'Customer Journey Workshop',
                    'description': 'Learn about user personas and customer journey maps',
                    'category': 'training',
                    'days_offset': 2,
                    'assigned_to': 'buddy',
                },
                {
                    'title': 'Meet Key Stakeholders',
                    'description': 'Schedule 1:1s with engineering, sales, and customer success leads',
                    'category': 'meeting',
                    'days_offset': 3,
                    'assigned_to': 'candidate',
                },
            ],
            required_documents=['i9', 'w4', 'direct_deposit'],
            forms=['equipment_preferences', 'emergency_contact'],
        )

        # Generic template for all departments
        generic_template = OnboardingTemplate.objects.create(
            name='General Employee Onboarding',
            description='Standard onboarding for all new hires',
            department=None,  # No department = applies to all
            job_level=None,
            is_active=True,
            tasks=[
                {
                    'title': 'Complete I-9 Verification',
                    'description': 'Submit I-9 form with required documentation',
                    'category': 'admin',
                    'days_offset': 0,
                    'assigned_to': 'candidate',
                },
                {
                    'title': 'Sign Employee Handbook',
                    'description': 'Review and sign employee handbook',
                    'category': 'admin',
                    'days_offset': 0,
                    'assigned_to': 'candidate',
                },
                {
                    'title': 'HR Orientation',
                    'description': 'Company culture, benefits, policies overview',
                    'category': 'meeting',
                    'days_offset': 1,
                    'assigned_to': 'hr',
                },
                {
                    'title': 'Setup Workstation',
                    'description': 'Configure laptop and necessary software',
                    'category': 'equipment',
                    'days_offset': 1,
                    'assigned_to': 'it',
                },
            ],
            required_documents=['i9', 'w4', 'direct_deposit'],
            forms=['emergency_contact'],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Created {OnboardingTemplate.objects.count()} onboarding templates'
            )
        )

    def create_integrations(self):
        """Create sample integrations."""
        from apps.integrations.models import Integration

        # Sample integrations (inactive by default as they have no real credentials)
        integrations_data = [
            {
                'provider': 'indeed',
                'category': 'job_board',
                'name': 'Indeed US',
                'is_active': False,
                'config': '{"api_key": "sample_key", "employer_id": "12345"}',
                'sync_status': 'idle',
                'metadata': {'region': 'US'},
            },
            {
                'provider': 'linkedin',
                'category': 'job_board',
                'name': 'LinkedIn Jobs',
                'is_active': False,
                'config': '{"client_id": "sample_client_id", "client_secret": "sample_secret"}',
                'sync_status': 'idle',
                'metadata': {'api_version': 'v2'},
            },
            {
                'provider': 'glassdoor',
                'category': 'job_board',
                'name': 'Glassdoor',
                'is_active': False,
                'config': '{"partner_id": "12345", "api_key": "sample_key"}',
                'sync_status': 'idle',
                'metadata': {},
            },
            {
                'provider': 'bamboo_hr',
                'category': 'hris',
                'name': 'BambooHR',
                'is_active': False,
                'config': '{"subdomain": "company", "api_key": "sample_key"}',
                'sync_status': 'idle',
                'metadata': {},
            },
            {
                'provider': 'workday',
                'category': 'hris',
                'name': 'Workday HRIS',
                'is_active': False,
                'config': '{"tenant_url": "https://example.workday.com", "username": "user", "password": "pass"}',
                'sync_status': 'idle',
                'metadata': {},
            },
        ]

        for data in integrations_data:
            Integration.objects.get_or_create(
                provider=data['provider'],
                name=data['name'],
                defaults={
                    'category': data['category'],
                    'is_active': data['is_active'],
                    'config': data['config'],
                    'sync_status': data['sync_status'],
                    'metadata': data['metadata'],
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Created {Integration.objects.count()} integrations'
            )
        )

    def print_credentials(self):
        """Print login credentials for testing."""
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(
            self.style.SUCCESS('Test Credentials Created:')
        )
        self.stdout.write('=' * 70)
        self.stdout.write('\nSuperuser:')
        self.stdout.write('  Email: admin@hrplus.local')
        self.stdout.write('  Password: admin123')
        self.stdout.write('\nInternal Users:')
        self.stdout.write('  Email: sarah.recruiter@hrplus.local')
        self.stdout.write('  Password: password123')
        self.stdout.write('  Role: Recruiter')
        self.stdout.write('')
        self.stdout.write('  Email: mike.manager@hrplus.local')
        self.stdout.write('  Password: password123')
        self.stdout.write('  Role: Hiring Manager')
        self.stdout.write('')
        self.stdout.write('  Email: jessica.hr@hrplus.local')
        self.stdout.write('  Password: password123')
        self.stdout.write('  Role: HR Admin')
        self.stdout.write('\nCandidates:')
        self.stdout.write('  Email: john.doe@example.com')
        self.stdout.write('  Password: candidate123')
        self.stdout.write('')
        self.stdout.write('  Email: jane.smith@example.com')
        self.stdout.write('  Password: candidate123')
        self.stdout.write('=' * 70 + '\n')
