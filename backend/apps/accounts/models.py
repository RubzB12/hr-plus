"""User and authentication models for HR-Plus."""

import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import BaseModel, TimestampedModel


class User(AbstractUser):
    """Custom user model using email as the primary identifier."""

    email = models.EmailField(unique=True)
    is_internal = models.BooleanField(
        default=False,
        help_text='Designates whether this user is an internal staff member.',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'accounts_user'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email


class Permission(BaseModel):
    """Granular permission for RBAC system."""

    MODULE_CHOICES = [
        ('accounts', 'Accounts'),
        ('candidates', 'Candidates'),
        ('jobs', 'Jobs'),
        ('applications', 'Applications'),
        ('interviews', 'Interviews'),
        ('assessments', 'Assessments'),
        ('offers', 'Offers'),
        ('onboarding', 'Onboarding'),
        ('communications', 'Communications'),
        ('analytics', 'Analytics'),
        ('integrations', 'Integrations'),
        ('compliance', 'Compliance'),
    ]

    ACTION_CHOICES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
    ]

    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    class Meta:
        db_table = 'accounts_permission'
        ordering = ['module', 'action']

    def __str__(self):
        return self.codename


class Role(BaseModel):
    """RBAC role with associated permissions."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False,
        help_text='System roles cannot be deleted.',
    )
    permissions = models.ManyToManyField(
        Permission,
        related_name='roles',
        blank=True,
    )

    class Meta:
        db_table = 'accounts_role'
        ordering = ['name']

    def __str__(self):
        return self.name


class InternalUser(BaseModel):
    """Profile for internal staff members (recruiters, hiring managers, etc.)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='internal_profile',
    )
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(
        'Department',
        on_delete=models.PROTECT,
        related_name='members',
        null=True,
        blank=True,
    )
    team = models.ForeignKey(
        'Team',
        on_delete=models.SET_NULL,
        related_name='members',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
    )
    roles = models.ManyToManyField(
        Role,
        related_name='internal_users',
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    sso_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='External SSO identifier.',
    )
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'accounts_internal_user'
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.employee_id})'

    def has_role(self, role_name: str) -> bool:
        return self.roles.filter(name=role_name).exists()

    def has_module_permission(self, module: str, action: str) -> bool:
        return self.roles.filter(
            permissions__module=module,
            permissions__action=action,
        ).exists()

    @property
    def all_permissions(self) -> set:
        return set(
            self.roles.values_list(
                'permissions__codename', flat=True
            ).distinct()
        )


class CandidateProfile(BaseModel):
    """Profile for external candidates."""

    WORK_AUTH_CHOICES = [
        ('citizen', 'Citizen'),
        ('permanent_resident', 'Permanent Resident'),
        ('visa_holder', 'Visa Holder'),
        ('requires_sponsorship', 'Requires Sponsorship'),
        ('other', 'Other'),
    ]

    JOB_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('temporary', 'Temporary'),
        ('internship', 'Internship'),
    ]

    SOURCE_CHOICES = [
        ('direct', 'Direct'),
        ('linkedin', 'LinkedIn'),
        ('indeed', 'Indeed'),
        ('referral', 'Referral'),
        ('career_site', 'Career Site'),
        ('job_board', 'Job Board'),
        ('agency', 'Agency'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='candidate_profile',
    )
    phone = models.CharField(max_length=20, blank=True)
    location_city = models.CharField(max_length=100, blank=True)
    location_country = models.CharField(max_length=100, blank=True)
    work_authorization = models.CharField(
        max_length=30,
        choices=WORK_AUTH_CHOICES,
        blank=True,
    )
    resume_file = models.FileField(
        upload_to='resumes/%Y/%m/',
        null=True,
        blank=True,
    )
    resume_parsed = models.JSONField(
        null=True,
        blank=True,
        help_text='Structured data parsed from resume.',
    )
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    preferred_salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    preferred_salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    preferred_job_types = models.JSONField(
        default=list,
        blank=True,
        help_text='List of preferred job types.',
    )
    profile_completeness = models.IntegerField(default=0)
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='direct',
    )

    class Meta:
        db_table = 'accounts_candidate_profile'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.get_full_name()} (Candidate)'

    def calculate_completeness(self) -> int:
        """Calculate profile completeness as a percentage."""
        fields_to_check = [
            bool(self.user.first_name),
            bool(self.user.last_name),
            bool(self.phone),
            bool(self.location_city),
            bool(self.location_country),
            bool(self.work_authorization),
            bool(self.resume_file),
            bool(self.linkedin_url or self.portfolio_url),
        ]
        total = len(fields_to_check)
        completed = sum(fields_to_check)
        return round((completed / total) * 100) if total else 0


class WorkExperience(BaseModel):
    """Candidate work experience entry."""

    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='experiences',
    )
    company_name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'accounts_work_experience'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.title} at {self.company_name}'


class Education(BaseModel):
    """Candidate education entry."""

    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='education',
    )
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'accounts_education'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.degree} from {self.institution}'


class Skill(TimestampedModel):
    """Candidate skill entry."""

    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='skills',
    )
    name = models.CharField(max_length=100)
    proficiency = models.CharField(
        max_length=20,
        choices=PROFICIENCY_CHOICES,
        blank=True,
    )
    years_experience = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'accounts_skill'
        ordering = ['name']
        unique_together = [['candidate', 'name']]

    def __str__(self):
        return self.name


class Department(BaseModel):
    """Organizational department with optional hierarchy."""

    name = models.CharField(max_length=200, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
    )
    head = models.ForeignKey(
        InternalUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'accounts_department'
        ordering = ['name']

    def __str__(self):
        return self.name


class Team(BaseModel):
    """Team within a department."""

    name = models.CharField(max_length=200)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='teams',
    )
    lead = models.ForeignKey(
        InternalUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_teams',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'accounts_team'
        ordering = ['department__name', 'name']
        unique_together = [['name', 'department']]

    def __str__(self):
        return f'{self.name} ({self.department.name})'


class Location(BaseModel):
    """Office location."""

    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    is_remote = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'accounts_location'
        ordering = ['country', 'city']

    def __str__(self):
        return self.name


class JobLevel(BaseModel):
    """Job level / grade within the organization."""

    name = models.CharField(max_length=100, unique=True)
    level_number = models.IntegerField(unique=True)
    salary_band_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    salary_band_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'accounts_job_level'
        ordering = ['level_number']

    def __str__(self):
        return f'{self.name} (L{self.level_number})'
