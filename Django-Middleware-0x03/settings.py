# In the MIDDLEWARE list, add these two lines:
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # ADD THESE TWO CUSTOM MIDDLEWARES:
    'chats.middleware.RestrictAccessByTimeMiddleware',
    'chats.middleware.RequestLoggingMiddleware',
    'chats.middleware.OffensiveLanguageMiddleware',
    'chats.middleware.RolePermissionMiddleware',
]
# Add this logging configuration at the end of settings.py:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'request_formatter': {
            'format': '{asctime} - User: {user} - Path: {path}',
        },
    },
    'handlers': {
        'request_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'requests.log',
            'formatter': 'request_formatter',
        },
    },
    'loggers': {
        'request_logger': {
            'handlers': ['request_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
# Add cache configuration for rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Cache timeout (optional, defaults are fine)
CACHE_MIDDLEWARE_SECONDS = 300