from odoo import http
from odoo.http import request


class TruckingDashboardController(http.Controller):

    def _get_dashboard(self, month=None, year=None):
        # Đảm bảo month và year được convert sang string nếu cần
        if month:
            month = str(month)
        if year:
            year = str(year)

        # Gọi model service
        dashboard_model = request.env['trucking.dashboard']
        dashboard_data = dashboard_model.get_dashboard_data(month, year)

        return dashboard_data

    @http.route('/trucking/dashboard', type='http', auth='user', website=True)
    def trucking_dashboard(self, month=None, year=None, **kw):
        """Route chính cho dashboard web"""
        dashboard_data = self._get_dashboard(month, year)

        # Lấy ID actions (nếu tồn tại, tránh lỗi ref)
        action_trip_analysis_id = request.env.ref('hp_trucking_planning.action_trip_analysis', raise_if_not_found=False)
        action_trip_on_route_id = request.env.ref('hp_trucking_planning.action_trip_on_route', raise_if_not_found=False)
        action_new_plans_from_cs_id = request.env.ref('hp_trucking_planning.action_new_plans_from_cs',raise_if_not_found=False)
        action_pending_plans_id = request.env.ref('hp_trucking_planning.action_pending_plans', raise_if_not_found=False)

        # Render template QWeb với dữ liệu
        return request.render('hp_trucking_planning.trucking_dashboard_template', {
            'dashboard_data': dashboard_data,
            'month': month or dashboard_data.get('filter_month'),
            'year': year or dashboard_data.get('filter_year'),
            'action_trip_analysis_id': action_trip_analysis_id.id if action_trip_analysis_id else False,
            'action_trip_on_route_id': action_trip_on_route_id.id if action_trip_on_route_id else False,
            'action_new_plans_from_cs_id': action_new_plans_from_cs_id.id if action_new_plans_from_cs_id else False,
            'action_pending_plans_id': action_pending_plans_id.id if action_pending_plans_id else False
        })

    @http.route('/trucking/dashboard/filter', type='json', auth='user', website=True, methods=['POST'])
    def filter_dashboard(self, month, year, **kw):
        """Xử lý filter động qua AJAX"""
        dashboard_data = self._get_dashboard(month, year)
        # Return JSON data thay vì render template
        return {
            'success': True,
            'data': dashboard_data
        }