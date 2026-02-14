"""
Development-specific Django settings for HR-Plus.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Additional dev apps
INSTALLED_APPS += [  # noqa: F405
    'django_extensions',
    'debug_toolbar',
]

# Debug toolbar middleware (after all other middleware)
MIDDLEWARE += [  # noqa: F405
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Debug toolbar
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Session cookie — not secure in dev (no HTTPS)
SESSION_COOKIE_SECURE = False

# CSRF cookie — not secure in dev
CSRF_COOKIE_SECURE = False

# Use console email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Use local file storage in development
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# S3 endpoint for MinIO in local development
AWS_S3_ENDPOINT_URL = 'http://localhost:9000'

# Disable throttling in development
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []  # noqa: F405
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}  # noqa: F405

# Use SQLite for local development (no Docker required)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

# Field encryption key for development
FIELD_ENCRYPTION_KEY = 'dev-encryption-key-do-not-use-in-production-32b!'
SALT_KEY = FIELD_ENCRYPTION_KEY  # Required by encrypted_fields

# Disable features that require external services
CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously
CELERY_TASK_EAGER_PROPAGATES = True
