"""
Test-specific Django settings for HR-Plus.
Uses SQLite for fast test execution without external dependencies.
"""

from .base import *  # noqa: F401, F403

DEBUG = False

# Use SQLite for tests (fast, no external dependencies)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use in-memory cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Use database-backed sessions (SQLite compatible)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Disable throttling in tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []  # noqa: F405
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}  # noqa: F405

# Faster password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Console email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Field encryption key for tests (django-fernet-encrypted-fields)
FIELD_ENCRYPTION_KEY = 'test-encryption-key-do-not-use-in-production-32b!'
SALT_KEY = FIELD_ENCRYPTION_KEY  # Required by encrypted_fields

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {},
    'root': {'level': 'CRITICAL'},
}

# Disable Elasticsearch during tests
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'localhost:9200',
    },
}
ELASTICSEARCH_DSL_AUTOSYNC = False
ELASTICSEARCH_DSL_AUTO_REFRESH = False
