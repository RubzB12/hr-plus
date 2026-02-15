"""Serializers for accounts app."""

from django.contrib.auth import authenticate, password_validation
from rest_framework import serializers

from .models import (
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
    User,
    WorkExperience,
)


class UserSerializer(serializers.ModelSerializer):
    """Read-only user serializer for nested representations."""

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_internal', 'date_joined']
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    """Candidate registration serializer."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    """Login serializer."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs['email'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')
        attrs['user'] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request password reset."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirm password reset with token."""

    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=10)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'codename', 'name', 'module', 'action']
        read_only_fields = ['id']


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        source='permissions',
        required=False,
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'is_system', 'permissions', 'permission_ids']
        read_only_fields = ['id', 'is_system']


class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = [
            'id', 'company_name', 'title', 'start_date', 'end_date',
            'is_current', 'description', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            'id', 'institution', 'degree', 'field_of_study',
            'start_date', 'end_date', 'gpa', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'proficiency', 'years_experience']
        read_only_fields = ['id']


class CandidateProfileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for candidate lists (e.g., talent pools)."""

    user_name = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'user_name', 'user_email', 'location_city',
            'location_country', 'work_authorization',
            'profile_completeness', 'created_at',
        ]
        read_only_fields = fields

    def get_user_name(self, obj):
        return obj.user.get_full_name()


class CandidateProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    completeness = serializers.SerializerMethodField()
    experiences = WorkExperienceSerializer(many=True, read_only=True)
    education = EducationSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'user', 'phone', 'location_city', 'location_country',
            'work_authorization', 'resume_file', 'resume_parsed',
            'linkedin_url', 'portfolio_url', 'preferred_salary_min',
            'preferred_salary_max', 'preferred_job_types',
            'profile_completeness', 'source', 'completeness',
            'experiences', 'education', 'skills',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'resume_parsed', 'profile_completeness', 'created_at', 'updated_at']

    def get_completeness(self, obj):
        return obj.calculate_completeness()


class CandidateProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for candidates updating their own profile."""

    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)

    class Meta:
        model = CandidateProfile
        fields = [
            'first_name', 'last_name', 'phone', 'location_city',
            'location_country', 'work_authorization', 'resume_file',
            'linkedin_url', 'portfolio_url', 'preferred_salary_min',
            'preferred_salary_max', 'preferred_job_types', 'source',
        ]

    def update(self, instance, validated_data):
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)
        if first_name is not None:
            instance.user.first_name = first_name
        if last_name is not None:
            instance.user.last_name = last_name
        if first_name is not None or last_name is not None:
            instance.user.save(update_fields=['first_name', 'last_name'])
        return super().update(instance, validated_data)


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'parent', 'head', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'department', 'lead', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'city', 'country', 'address', 'is_remote', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class JobLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobLevel
        fields = ['id', 'name', 'level_number', 'salary_band_min', 'salary_band_max', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class InternalUserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for InternalUser in list views."""

    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = InternalUser
        fields = ['id', 'user_name', 'email', 'employee_id', 'title']


class InternalUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    roles = RoleSerializer(many=True, read_only=True)
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        many=True,
        write_only=True,
        source='roles',
        required=False,
    )

    class Meta:
        model = InternalUser
        fields = [
            'id', 'user', 'employee_id', 'department', 'team',
            'title', 'manager', 'roles', 'role_ids', 'is_active',
            'sso_id', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class MeSerializer(serializers.ModelSerializer):
    """Serializer for the /auth/me/ endpoint — returns full user context."""

    internal_profile = InternalUserSerializer(read_only=True)
    candidate_profile = CandidateProfileSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'is_internal',
            'date_joined', 'internal_profile', 'candidate_profile', 'permissions',
        ]
        read_only_fields = fields

    def get_permissions(self, obj):
        if obj.is_internal and hasattr(obj, 'internal_profile'):
            return list(obj.internal_profile.all_permissions)
        return []
