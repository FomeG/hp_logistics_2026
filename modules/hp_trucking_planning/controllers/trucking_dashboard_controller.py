from odoo import http
from odoo.http import request


class TruckingDashboardController(http.Controller):

    @http.route('/trucking/dashboard', type='http', auth='user', website=True)
    def trucking_dashboard(self, month=None, year=None, **kw):
        """Route chính cho dashboard web"""
        # Đảm bảo month và year được convert sang string nếu cần
        if month:
            month = str(month)
        if year:
            year = str(year)

        # Lấy dữ liệu từ model với month và year từ URL parameters
        dashboard_data = request.env['trucking.dashboard'].get_dashboard_data(month, year)

        # Lấy ID actions (nếu tồn tại, tránh lỗi ref)
        action_trip_analysis_id = request.env.ref('hp_trucking_planning.action_trip_analysis', raise_if_not_found=False)
        action_trip_on_route_id = request.env.ref('hp_trucking_planning.action_trip_on_route', raise_if_not_found=False)

        # Render template QWeb với dữ liệu
        return request.render('hp_trucking_planning.trucking_dashboard_template', {
            'dashboard_data': dashboard_data,
            'month': month or dashboard_data.get('filter_month'),
            'year': year or dashboard_data.get('filter_year'),
            'action_trip_analysis_id': action_trip_analysis_id.id if action_trip_analysis_id else False,
            'action_trip_on_route_id': action_trip_on_route_id.id if action_trip_on_route_id else False,
        })

    @http.route('/trucking/dashboard/filter', type='json', auth='user', website=True, methods=['POST'])
    def filter_dashboard(self, month, year, **kw):
        """Xử lý filter động qua AJAX"""
        # Convert sang string để đảm bảo consistency
        month = str(month) if month else None
        year = str(year) if year else None

        dashboard_data = request.env['trucking.dashboard'].get_dashboard_data(month, year)

        # Return JSON data thay vì render template
        return {
            'success': True,
            'data': dashboard_data
        }