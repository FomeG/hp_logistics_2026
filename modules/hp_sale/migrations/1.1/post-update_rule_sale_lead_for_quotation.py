from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    rule = env.ref('sale.sale_order_see_all', raise_if_not_found=False)
    if rule:
        rule.write({
            'name': 'Rule Sale Order  For Sale Lead',
            'domain_force': "['|', ('user_id','=',user.id), ('department_id','in', user.employee_ids.department_id.ids)]"
        })
