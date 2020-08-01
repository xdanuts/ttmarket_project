from djangottmarket.settings.base import *

DEBUG = True

STATICFILES = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_ROOT = os.path.join(BASE_DIR, 'static', 'media')