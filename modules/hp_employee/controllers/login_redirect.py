from odoo import http
from odoo.http import request

class HpEmployeeRedirect(http.Controller):

    @http.route(['/web', '/odoo'], type='http', auth='user')
    def redirect_by_department(self, **kw):
        user = request.env.user
        employee = user.sudo().employee_id
        department = employee.department_id if employee else False

        redirect_url = '/odoo/discuss'

        redirect_map = {
            'trucking': 'hp_trucking_planning.action_trucking_dashboard',
            'pricing': 'hp_freight_purchase.freight_purchase_booking_action',
        }

        if department and department.department_type_id:
            code = department.department_type_id.code.lower()
            xml_id = redirect_map.get(code)
            if xml_id:
                action = request.env.ref(xml_id, raise_if_not_found=False)
                if action:
                    redirect_url = f"/odoo/action-{action.id}"

        return request.redirect(redirect_url)
