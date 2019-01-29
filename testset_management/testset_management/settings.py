"""
Django settings for testset_management project.

Generated by 'django-admin startproject' using Django 2.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
from .loader import load_credential
# import django
# django.setup()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'm_34b6v^6e!ceooy($*az(xw4n3cz+1ds_!y_2$g0nw$#k#v%='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
#
# import django
# django.setup()
# Application definition

INSTALLED_APPS = [
    'storages',
    'testset',
    'source',
    'hangul_qalculator',
    'picture_boxing',
    'handwritten',
    'training',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'qanda',
    'rest_framework',
    'django_filters',


]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'testset_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'testset_management.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'testset.cluster-cvy8leytggjq.ap-northeast-2.rds.amazonaws.com',
        'NAME': os.getenv('DATABASE_NAME', 'expr_testset'),
        'USER': 'root',
        'PASSWORD': load_credential('DATABASE_PASSWORD', ""),
        'PORT': '3306',
    },
    'qanda': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': load_credential('PROD_QANDA_DATABASE_HOST', ""),
        'USER': load_credential('PROD_QANDA_DATABASE_USER', ""),
        'PASSWORD': load_credential('PROD_QANDA_DATABASE_PASSWORD', ""),
        'NAME': load_credential('PROD_QANDA_DATABASE_NAME', ""),
    },
    'qanda_readonly': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': load_credential('PROD_QANDA_READONLY_DATABASE_HOST', ""),
        'USER': load_credential('PROD_QANDA_READONLY_DATABASE_USER', ""),
        'PASSWORD': load_credential('PROD_QANDA_READONLY_DATABASE_PASSWORD', ""),
        'NAME': load_credential('PROD_QANDA_READONLY_DATABASE_NAME', ""),
    },
}

DATABASE_ROUTERS = [
    'qanda.routers.QandaRouter',
]

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = []


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True



DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = load_credential("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = load_credential("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = 'testset-storage'
AWS_S3_REGION_NAME = 'ap-northeast-2'
AWS_S3_HOST = 's3.%s.amazonaws.com' % AWS_S3_REGION_NAME
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
STATIC_LOCATION = 'static'
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATIC_LOCATION)
STATICFILES_STORAGE = 'testset_management.custom_storages.StaticStorage'
MEDIA_LOCATION = 'media'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIA_LOCATION)

# REST FRAMEWORK CONFIGURATION

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 300
}

# END REST FRAMEWORK CONFIGURATION