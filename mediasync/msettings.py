"""
Mediasync configuration.
"""
from django.conf import settings

JS_MIMETYPES = (
    "application/javascript",
    "text/javascript", # obsolete, see RFC 4329
)
CSS_MIMETYPES = (
    "text/css",
)
TYPES_TO_COMPRESS = (
    "application/json",
    "application/xml",
    "text/html",
    "text/plain",
    "text/xml",
) + JS_MIMETYPES + CSS_MIMETYPES

DEFAULT_PROCESSORS = (
    'mediasync.processors.css_minifier',
    'mediasync.processors.js_minifier',
)

__settings_dict = getattr(settings, 'MEDIASYNC', {})

BACKEND = __settings_dict.get("BACKEND", None)
CSS_PATH = __settings_dict.get("CSS_PATH", "")
JS_PATH = __settings_dict.get("JS_PATH", "")
JOINED = __settings_dict.get("JOINED", {})
SERVE_REMOTE = __settings_dict.get("SERVE_REMOTE", False)
EMULATE_COMBO = __settings_dict.get("EMULATE_COMBO", False)
DOCTYPE = __settings_dict.get("DOCTYPE", "xhtml")
URL_PROCESSOR = __settings_dict.get("URL_PROCESSOR", lambda x: x)
CACHE_BUSTER = __settings_dict.get("CACHE_BUSTER", None)
USE_SSL = __settings_dict.get("USE_SSL", None)
EXPIRATION_DAYS = __settings_dict.get("EXPIRATION_DAYS", 365)
MEDIA_ROOT = __settings_dict.get('MEDIA_ROOT', getattr(settings, 'MEDIA_ROOT', ''))
MEDIA_URL = __settings_dict.get('MEDIA_URL', getattr(settings, 'MEDIA_URL', ''))
PROCESSORS = __settings_dict.get("PROCESSORS", DEFAULT_PROCESSORS)

"""
S3 Backend Settings
"""
AWS_KEY = __settings_dict.get("AWS_KEY", None)
AWS_SECRET = __settings_dict.get("AWS_SECRET", None)
AWS_BUCKET = __settings_dict.get('AWS_BUCKET', None)
AWS_PREFIX = __settings_dict.get('AWS_PREFIX', '').strip('/')
AWS_BUCKET_CNAME = __settings_dict.get('AWS_BUCKET_CNAME', False)

"""
Cloud Files Settings
"""
CLOUDFILES_CONTAINER = __settings_dict.get('CLOUDFILES_CONTAINER', None)
CLOUDFILES_USERNAME = __settings_dict.get("CLOUDFILES_USERNAME", None)
CLOUDFILES_KEY = __settings_dict.get("CLOUDFILES_KEY", None)
