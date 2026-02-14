"""Management command to seed database with test data."""

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
from apps.applications.models import Application, ApplicationEvent
from apps.jobs.models import PipelineStage, Requisition

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
            teams = self.create_teams(departments, internal_users)

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
            self.create_applications(candidates, requisitions)

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully seeded database with test data!'
            )
        )
        self.print_credentials()

    def clear_data(self):
        """Clear existing test data."""
        Application.objects.all().delete()
        Requisition.objects.all().delete()
        CandidateProfile.objects.all().delete()
        InternalUser.objects.all().delete()
        Team.objects.all().delete()
        Department.objects.all().delete()
        Location.objects.all().delete()
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
        # Create superuser
        superuser, created = User.objects.get_or_create(
            email='admin@hrplus.local',
            defaults={
                'username': 'admin',
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
            Skill.objects.create(
                candidate=candidate,
                name=skill_name,
                proficiency=random.choice(
                    ['intermediate', 'advanced', 'expert']
                ),
                years_experience=random.randint(1, 8),
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
                    'salary_currency': 'USD',
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

                application = Application.objects.create(
                    application_id=app_id,
                    candidate=candidate,
                    requisition=req,
                    status=status,
                    current_stage=current_stage,
                    source=candidate.source,
                    cover_letter='I am very interested in this position and believe my skills align well with the requirements.',
                    screening_responses={},
                    is_starred=(random.random() > 0.7),  # Star 30% of applications
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

                app_count += 1

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
