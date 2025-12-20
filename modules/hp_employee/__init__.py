from . import models
from . import services
from . import controllers
from . import listeners

from .models.override_base_access import override_base_hr_access_rights


def post_init_hook(env):
    """Hook to run after module installation"""
    override_base_hr_access_rights(env)