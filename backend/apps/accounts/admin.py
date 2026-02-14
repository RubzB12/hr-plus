"""Admin configuration for accounts app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

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


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_internal', 'is_active', 'date_joined']
    list_filter = ['is_internal', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('HR-Plus', {'fields': ('is_internal',)}),
    )


@admin.register(InternalUser)
class InternalUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'title', 'department', 'is_active']
    list_filter = ['is_active', 'department']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'employee_id']
    raw_id_fields = ['user', 'manager']
    filter_horizontal = ['roles']


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location_city', 'location_country', 'source', 'profile_completeness']
    list_filter = ['source', 'work_authorization']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_system']
    list_filter = ['is_system']
    filter_horizontal = ['permissions']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['codename', 'name', 'module', 'action']
    list_filter = ['module', 'action']
    search_fields = ['codename', 'name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active']
    list_filter = ['is_active']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'is_active']
    list_filter = ['department', 'is_active']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'country', 'is_remote', 'is_active']
    list_filter = ['country', 'is_remote', 'is_active']


@admin.register(JobLevel)
class JobLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'level_number', 'salary_band_min', 'salary_band_max']
    ordering = ['level_number']


admin.site.register(WorkExperience)
admin.site.register(Education)
admin.site.register(Skill)
