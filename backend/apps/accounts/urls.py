"""URL routing for accounts app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'users', views.InternalUserViewSet, basename='internal-user')
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'teams', views.TeamViewSet, basename='team')
router.register(r'locations', views.LocationViewSet, basename='location')
router.register(r'job-levels', views.JobLevelViewSet, basename='job-level')
router.register(r'roles', views.RoleViewSet, basename='role')

# Candidate data routers
candidate_router = DefaultRouter()
candidate_router.register(r'experiences', views.WorkExperienceViewSet, basename='candidate-experience')
candidate_router.register(r'education', views.EducationViewSet, basename='candidate-education')
candidate_router.register(r'skills', views.SkillViewSet, basename='candidate-skill')

# Auth endpoints
auth_urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='auth-register'),
    path('login/', views.LoginView.as_view(), name='auth-login'),
    path('logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('me/', views.MeView.as_view(), name='auth-me'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='auth-password-reset'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
]

# Candidate endpoints
candidate_urlpatterns = [
    path('profile/', views.CandidateProfileView.as_view(), name='candidate-profile'),
    path('resume/', views.ResumeUploadView.as_view(), name='candidate-resume-upload'),
    path('', include(candidate_router.urls)),
]

urlpatterns = [
    path('auth/', include(auth_urlpatterns)),
    path('candidates/', include(candidate_urlpatterns)),
    path('internal/', include(router.urls)),
]
