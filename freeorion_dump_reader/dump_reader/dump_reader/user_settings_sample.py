# Copy this as user_settings.py
DUMP_FOLDER = ''
PROJECT_FOLDER = ''  # path to  freeorion/default/ repository folder, required to read research icons
STATICFILES_DIRS = [PROJECT_FOLDER]

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'freeorion',
        # The following settings are not used with sqlite3:
        'USER': 'freeorion',
        'PASSWORD': 'freeorion',
        'HOST': 'localhost',
        'PORT': '5432',
        'ATOMIC_REQUESTS': True
    }
}
