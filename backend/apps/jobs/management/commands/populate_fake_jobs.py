"""Management command to populate fake jobs for testing the public frontend."""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import (
    Department,
    InternalUser,
    JobLevel,
    Location,
    Role,
    Team,
    User,
)
from apps.jobs.models import PipelineStage, Requisition


class Command(BaseCommand):
    help = 'Populate database with fake jobs for testing public frontend'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=15,
            help='Number of jobs to create (default: 15)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing jobs before creating new ones',
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        # Disable Elasticsearch autosync for this command
        from django.conf import settings
        original_autosync = getattr(settings, 'ELASTICSEARCH_DSL_AUTOSYNC', True)
        settings.ELASTICSEARCH_DSL_AUTOSYNC = False

        self.stdout.write(
            self.style.WARNING(
                'Elasticsearch autosync disabled for this operation'
            )
        )

        try:
            with transaction.atomic():
                if clear:
                    self.stdout.write('Clearing existing jobs...')
                    Requisition.objects.all().delete()

                self.stdout.write('Creating foundational data...')
                departments = self._create_departments()
                locations = self._create_locations()
                job_levels = self._create_job_levels()
                internal_users = self._create_internal_users(departments)

                self.stdout.write(f'Creating {count} fake jobs...')
                jobs_created = self._create_jobs(
                    count,
                    departments,
                    locations,
                    job_levels,
                    internal_users,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created {jobs_created} jobs!'
                    )
                )
        finally:
            # Restore original autosync setting
            settings.ELASTICSEARCH_DSL_AUTOSYNC = original_autosync

    def _create_departments(self):
        """Create departments if they don't exist."""
        dept_data = [
            'Engineering',
            'Product',
            'Design',
            'Sales',
            'Marketing',
            'Customer Success',
            'Human Resources',
            'Finance',
            'Operations',
            'Data & Analytics',
        ]

        departments = []
        for name in dept_data:
            dept, created = Department.objects.get_or_create(
                name=name,
                defaults={'is_active': True},
            )
            departments.append(dept)
            if created:
                self.stdout.write(f'  Created department: {name}')

        return departments

    def _create_locations(self):
        """Create office locations if they don't exist."""
        location_data = [
            {
                'name': 'San Francisco HQ',
                'city': 'San Francisco',
                'country': 'United States',
                'is_remote': False,
            },
            {
                'name': 'New York Office',
                'city': 'New York',
                'country': 'United States',
                'is_remote': False,
            },
            {
                'name': 'London Office',
                'city': 'London',
                'country': 'United Kingdom',
                'is_remote': False,
            },
            {
                'name': 'Berlin Office',
                'city': 'Berlin',
                'country': 'Germany',
                'is_remote': False,
            },
            {
                'name': 'Remote - US',
                'city': 'Remote',
                'country': 'United States',
                'is_remote': True,
            },
            {
                'name': 'Remote - Europe',
                'city': 'Remote',
                'country': 'Europe',
                'is_remote': True,
            },
        ]

        locations = []
        for loc_data in location_data:
            loc, created = Location.objects.get_or_create(
                name=loc_data['name'],
                defaults=loc_data,
            )
            locations.append(loc)
            if created:
                self.stdout.write(f'  Created location: {loc_data["name"]}')

        return locations

    def _create_job_levels(self):
        """Create job levels if they don't exist."""
        level_data = [
            {'name': 'Entry Level', 'level_number': 1},
            {'name': 'Junior', 'level_number': 2},
            {'name': 'Mid-Level', 'level_number': 3},
            {'name': 'Senior', 'level_number': 4},
            {'name': 'Staff', 'level_number': 5},
            {'name': 'Principal', 'level_number': 6},
            {'name': 'Director', 'level_number': 7},
            {'name': 'Senior Director', 'level_number': 8},
            {'name': 'VP', 'level_number': 9},
        ]

        job_levels = []
        for level in level_data:
            jl, created = JobLevel.objects.get_or_create(
                level_number=level['level_number'],
                defaults=level,
            )
            job_levels.append(jl)
            if created:
                self.stdout.write(f'  Created job level: {level["name"]}')

        return job_levels

    def _create_internal_users(self, departments):
        """Create internal users if they don't exist, or return existing ones."""
        # Check if we already have internal users
        existing_users = InternalUser.objects.all()
        if existing_users.count() >= 2:
            self.stdout.write(
                f'  Using {existing_users.count()} existing internal users'
            )
            return list(existing_users[:4])

        # Create a recruiter role
        recruiter_role, _ = Role.objects.get_or_create(
            name='Recruiter',
            defaults={
                'description': 'Recruiting staff',
                'is_system': True,
            },
        )

        # Create test users for hiring managers and recruiters
        users_data = [
            {
                'email': 'sarah.chen@company.com',
                'first_name': 'Sarah',
                'last_name': 'Chen',
                'employee_id': 'EMP001',
                'title': 'VP of Engineering',
                'department_idx': 0,  # Engineering
            },
            {
                'email': 'michael.brown@company.com',
                'first_name': 'Michael',
                'last_name': 'Brown',
                'employee_id': 'EMP002',
                'title': 'Director of Product',
                'department_idx': 1,  # Product
            },
            {
                'email': 'jennifer.wilson@company.com',
                'first_name': 'Jennifer',
                'last_name': 'Wilson',
                'employee_id': 'EMP003',
                'title': 'Head of Design',
                'department_idx': 2,  # Design
            },
            {
                'email': 'recruiter@company.com',
                'first_name': 'Alex',
                'last_name': 'Recruiter',
                'employee_id': 'REC001',
                'title': 'Senior Technical Recruiter',
                'department_idx': 6,  # HR
            },
        ]

        internal_users = []
        for user_data in users_data:
            user, user_created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'username': user_data['email'].split('@')[0],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_internal': True,
                    'is_active': True,
                },
            )

            if user_created:
                user.set_password('password123')
                user.save()

            # Try to get existing internal user first
            try:
                internal_user = InternalUser.objects.get(user=user)
                iu_created = False
            except InternalUser.DoesNotExist:
                internal_user = InternalUser.objects.create(
                    user=user,
                    employee_id=user_data['employee_id'],
                    title=user_data['title'],
                    department=departments[user_data['department_idx']],
                    is_active=True,
                )
                iu_created = True

            if iu_created and user_data['employee_id'].startswith('REC'):
                internal_user.roles.add(recruiter_role)

            internal_users.append(internal_user)

            if user_created or iu_created:
                self.stdout.write(
                    f'  Created user: {user.get_full_name()}'
                )

        return internal_users

    def _create_jobs(
        self, count, departments, locations, job_levels, internal_users
    ):
        """Create fake job requisitions."""
        # Get the current count of requisitions to avoid ID conflicts
        existing_count = Requisition.objects.count()
        start_idx = existing_count + 1

        # Sample job titles by department
        job_titles = {
            'Engineering': [
                'Senior Software Engineer',
                'Frontend Developer',
                'Backend Engineer',
                'Full Stack Developer',
                'DevOps Engineer',
                'Mobile Developer (iOS)',
                'Mobile Developer (Android)',
                'Staff Software Engineer',
                'Engineering Manager',
                'Principal Engineer',
                'Security Engineer',
                'Data Engineer',
                'Machine Learning Engineer',
                'QA Engineer',
                'Site Reliability Engineer',
            ],
            'Product': [
                'Senior Product Manager',
                'Product Manager',
                'Associate Product Manager',
                'Technical Product Manager',
                'Product Owner',
                'Director of Product',
            ],
            'Design': [
                'Senior Product Designer',
                'UX Designer',
                'UI Designer',
                'UX Researcher',
                'Design Systems Designer',
                'Brand Designer',
            ],
            'Sales': [
                'Account Executive',
                'Sales Development Representative',
                'Enterprise Account Executive',
                'Sales Engineer',
                'VP of Sales',
            ],
            'Marketing': [
                'Content Marketing Manager',
                'Growth Marketing Manager',
                'Digital Marketing Specialist',
                'Product Marketing Manager',
                'Marketing Operations Manager',
            ],
            'Customer Success': [
                'Customer Success Manager',
                'Senior Customer Success Manager',
                'Implementation Specialist',
                'Technical Account Manager',
            ],
            'Data & Analytics': [
                'Data Analyst',
                'Senior Data Scientist',
                'Analytics Engineer',
                'Business Intelligence Analyst',
            ],
        }

        job_descriptions = {
            'Software Engineer': '''
We're looking for a talented Software Engineer to join our growing engineering team. You'll work on building scalable, reliable systems that power our platform used by thousands of customers worldwide.

**What you'll do:**
- Design, develop, and maintain high-quality software solutions
- Collaborate with cross-functional teams to define and ship new features
- Write clean, maintainable, and well-tested code
- Participate in code reviews and contribute to engineering best practices
- Debug and resolve production issues
- Mentor junior engineers and contribute to team growth

**What we're looking for:**
- Strong problem-solving skills and attention to detail
- Experience building scalable web applications
- Solid understanding of software engineering principles
- Excellent communication and collaboration skills
- Passion for learning and continuous improvement
            '''.strip(),
            'Product Manager': '''
We're seeking a Product Manager to drive the strategy and execution of our product initiatives. You'll work closely with engineering, design, and business teams to build products that delight our customers.

**What you'll do:**
- Define product vision, strategy, and roadmap
- Gather and prioritize product requirements from customers and stakeholders
- Work closely with engineering and design to deliver high-quality products
- Analyze product metrics and user feedback to drive improvements
- Communicate product plans and progress to stakeholders
- Make data-driven decisions to optimize product performance

**What we're looking for:**
- Strong analytical and problem-solving skills
- Experience shipping successful products
- Excellent communication and presentation skills
- Ability to balance user needs with business goals
- Technical background is a plus
            '''.strip(),
            'Designer': '''
We're looking for a creative Designer to join our design team. You'll help shape the user experience of our products and create beautiful, intuitive interfaces that our users love.

**What you'll do:**
- Design end-to-end user experiences for web and mobile products
- Create wireframes, prototypes, and high-fidelity designs
- Collaborate with product managers and engineers to bring designs to life
- Conduct user research and usability testing
- Contribute to and maintain our design system
- Advocate for user-centered design principles

**What we're looking for:**
- Strong portfolio demonstrating your design work
- Proficiency with design tools (Figma, Sketch, etc.)
- Understanding of UX principles and best practices
- Excellent visual design skills
- Strong communication and collaboration abilities
            '''.strip(),
            'Marketing': '''
We're looking for a Marketing professional to help us grow our brand and reach new customers. You'll develop and execute marketing strategies that drive awareness, engagement, and conversion.

**What you'll do:**
- Develop and execute marketing campaigns across multiple channels
- Create compelling content that resonates with our target audience
- Analyze campaign performance and optimize for results
- Collaborate with sales, product, and design teams
- Manage marketing budget and vendor relationships
- Stay up-to-date with marketing trends and best practices

**What we're looking for:**
- Proven experience in marketing or related field
- Strong writing and communication skills
- Analytical mindset with attention to detail
- Experience with marketing tools and platforms
- Creative thinking and problem-solving abilities
            '''.strip(),
            'Sales': '''
We're seeking a sales professional to help us expand our customer base and drive revenue growth. You'll be responsible for identifying opportunities, building relationships, and closing deals.

**What you'll do:**
- Identify and qualify new sales opportunities
- Build and maintain relationships with prospects and customers
- Conduct product demonstrations and presentations
- Negotiate contracts and close deals
- Collaborate with customer success team for smooth onboarding
- Meet and exceed sales targets

**What we're looking for:**
- Proven track record in sales
- Excellent communication and presentation skills
- Strong relationship-building abilities
- Self-motivated with a results-driven approach
- Experience with CRM systems
- Knowledge of the industry is a plus
            '''.strip(),
        }

        requisitions_created = 0
        for i in range(count):
            # Select department and get corresponding job titles
            dept = departments[i % len(departments)]
            dept_jobs = job_titles.get(dept.name, ['Specialist'])

            title = dept_jobs[i % len(dept_jobs)]

            # Determine employment type
            employment_types = [
                'full_time',
                'full_time',
                'full_time',
                'full_time',
                'contract',
            ]
            employment_type = employment_types[i % len(employment_types)]

            # Determine remote policy
            remote_policies = [
                'onsite',
                'hybrid',
                'hybrid',
                'remote',
                'remote',
            ]
            remote_policy = remote_policies[i % len(remote_policies)]

            # Select location
            if remote_policy == 'remote':
                location = [
                    loc for loc in locations if loc.is_remote
                ][i % 2]
            else:
                location = [
                    loc for loc in locations if not loc.is_remote
                ][i % 4]

            # Determine level
            level_idx = min(i % 6, len(job_levels) - 1)
            level = job_levels[level_idx]

            # Salary based on level (in ZAR)
            salary_ranges = {
                1: (1080000, 1440000),   # ~R1.08M - R1.44M
                2: (1440000, 1980000),   # ~R1.44M - R1.98M
                3: (1980000, 2700000),   # ~R1.98M - R2.7M
                4: (2700000, 3600000),   # ~R2.7M - R3.6M
                5: (3600000, 4500000),   # ~R3.6M - R4.5M
                6: (4500000, 5400000),   # ~R4.5M - R5.4M
            }
            salary_min, salary_max = salary_ranges.get(
                level.level_number, (1800000, 2700000)
            )

            # Requirements
            requirements_required = [
                f'{level.level_number + 2}+ years of professional experience',
                'Bachelor\'s degree in related field or equivalent experience',
                'Strong problem-solving and analytical skills',
                'Excellent communication skills',
                'Ability to work in a fast-paced environment',
            ]

            requirements_preferred = [
                'Experience in a startup environment',
                'Previous experience in similar role',
                'Familiarity with agile methodologies',
                'Open source contributions',
            ]

            # Screening questions
            screening_questions = [
                {
                    'id': 1,
                    'question': 'How many years of relevant experience do you have?',
                    'type': 'number',
                    'required': True,
                },
                {
                    'id': 2,
                    'question': 'Are you legally authorized to work in this location?',
                    'type': 'boolean',
                    'required': True,
                },
                {
                    'id': 3,
                    'question': 'What is your expected salary range?',
                    'type': 'text',
                    'required': False,
                },
                {
                    'id': 4,
                    'question': 'When can you start?',
                    'type': 'date',
                    'required': True,
                },
            ]

            # Select hiring manager and recruiter
            hiring_manager = internal_users[0]  # Default to first user
            recruiter = internal_users[-1]  # Last user is recruiter

            # Determine description
            description_key = 'Software Engineer'
            if 'Engineer' in title or 'Developer' in title:
                description_key = 'Software Engineer'
            elif 'Product' in title:
                description_key = 'Product Manager'
            elif 'Design' in title or 'UX' in title or 'UI' in title:
                description_key = 'Designer'
            elif 'Marketing' in title:
                description_key = 'Marketing'
            elif 'Sales' in title or 'Account' in title:
                description_key = 'Sales'

            description = job_descriptions.get(
                description_key,
                job_descriptions['Software Engineer'],
            )

            # Create requisition ID
            year = timezone.now().year
            requisition_id = f'REQ-{year}-{(start_idx + i):03d}'

            # Create requisition
            requisition = Requisition.objects.create(
                requisition_id=requisition_id,
                title=title,
                department=dept,
                hiring_manager=hiring_manager,
                recruiter=recruiter,
                status='open',
                employment_type=employment_type,
                level=level,
                location=location,
                remote_policy=remote_policy,
                salary_min=Decimal(str(salary_min)),
                salary_max=Decimal(str(salary_max)),
                salary_currency='ZAR',
                description=description,
                requirements_required=requirements_required,
                requirements_preferred=requirements_preferred,
                screening_questions=screening_questions,
                headcount=1,
                filled_count=0,
                target_fill_date=timezone.now().date() + timedelta(days=60),
                opened_at=timezone.now() - timedelta(days=i),
                published_at=timezone.now() - timedelta(days=i),
                created_by=recruiter,
            )

            # Create default pipeline stages
            default_stages = [
                {'name': 'Applied', 'stage_type': 'application', 'order': 0},
                {'name': 'Screening', 'stage_type': 'screening', 'order': 1},
                {
                    'name': 'Phone Interview',
                    'stage_type': 'phone_screen',
                    'order': 2,
                },
                {
                    'name': 'Technical Interview',
                    'stage_type': 'interview',
                    'order': 3,
                },
                {
                    'name': 'Final Interview',
                    'stage_type': 'interview',
                    'order': 4,
                },
                {'name': 'Offer', 'stage_type': 'offer', 'order': 5},
                {'name': 'Hired', 'stage_type': 'hired', 'order': 6},
            ]

            for stage_data in default_stages:
                PipelineStage.objects.create(
                    requisition=requisition,
                    **stage_data,
                )

            requisitions_created += 1

            if (i + 1) % 5 == 0:
                self.stdout.write(f'  Created {i + 1}/{count} jobs...')

        return requisitions_created
