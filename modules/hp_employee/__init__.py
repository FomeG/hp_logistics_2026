from . import models
from . import services
from . import controllers
from . import listeners


def uninstall_hook(env):
    try:
        menu = env.ref('hr.menu_hr_department_kanban', raise_if_not_found=False)
        if menu:
            menu.active = True
    except Exception:
        pass