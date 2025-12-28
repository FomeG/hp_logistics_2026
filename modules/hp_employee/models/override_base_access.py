from odoo import api, SUPERUSER_ID

# để ghi đè các quyền truy cập mặc định của module HR
# sinh ra file này vì hiện tại nhiều phòng ban đang sử dụng module HR mặc định, khiến việc thay đổi quyền truy cập trở nên phức tạp
# vd nhân viên pricing vẫn có thể thấy được nút New ở department hoặc employee dù accessrights phần create đã tắt
def override_base_hr_access_rights(env):
    """
    Override base hr module access rules to remove create permission from hr.group_hr_user.
    Only our custom hp_employee.group_hr_user should have create permission.
    """


    # Find and update hr.employee access rule for hr.group_hr_user
    employee_access = env.ref('hr.access_hr_employee_user', raise_if_not_found=False)
    if employee_access:
        employee_access.sudo().write({
            'perm_read': True,
            'perm_write': False,
            'perm_create': False,
            'perm_unlink': False,
        })

    # Find and update hr.department access rule for hr.group_hr_user
    department_access = env.ref('hr.access_hr_department_user', raise_if_not_found=False)
    if department_access:
        department_access.sudo().write({
            'perm_read': True,
            'perm_write': False,
            'perm_create': False,
            'perm_unlink': False,
        })
