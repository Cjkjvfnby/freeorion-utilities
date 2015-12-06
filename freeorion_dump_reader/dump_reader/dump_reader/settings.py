"""
Django settings for dump_reader project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'b7etm355#tf7t#s$-%s%%gv3x%#$gd&ewkwoj2rr&mrhc35ris'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'reader'
)

REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
}


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)

ROOT_URLCONF = 'dump_reader.urls'

WSGI_APPLICATION = 'dump_reader.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = False

USE_L10N = False

USE_TZ = False


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {'debug': True}
    },
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

try:
    from user_settings import *
except ImportError:
    print 'Settings file user_settings.py is missed. Use user_settings_sample.py as template.'
    exit(1)
