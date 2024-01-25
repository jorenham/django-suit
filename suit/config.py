from django.contrib.admin import ModelAdmin
from django.conf import settings
from . import VERSION

CONFIG_KEY = 'SUIT_CONFIG'


def default_config():
    return {
        'VERSION': VERSION,

        # configurable
        'ADMIN_NAME': 'Django Suit',
        'HEADER_DATE_FORMAT': 'l, jS F Y',
        'HEADER_TIME_FORMAT': 'H:i',

        # form
        'SHOW_REQUIRED_ASTERISK': True,
        'CONFIRM_UNSAVED_CHANGES': True,

        # menu
        'SEARCH_URL': '/admin/auth/user/',
        'MENU_OPEN_FIRST_CHILD': True,
        'MENU_ICONS': {
            'auth': 'icon-lock',
            'sites': 'icon-leaf',
        },
        'LIST_PER_PAGE': 20
    }


def get_config(key=None):
    default = default_config()
    config = getattr(settings, CONFIG_KEY, default)
    return config.get(key, default.get(key)) if key else config


# Reverse default actions position
ModelAdmin.actions_on_top = False
ModelAdmin.actions_on_bottom = True

# Set global list_per_page
ModelAdmin.list_per_page = get_config('LIST_PER_PAGE')
