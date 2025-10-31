import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SimpleTripAccessController(http.Controller):
    """Controller show map với trip data - Portal user"""

    @http.route('/trip/view/<string:token>', type='http', auth='public', website=True)
    def view_trip_public(self, token, **kwargs):
        """
        ✅ Hiển thị Public Trip Map - CHỈ KHI:
        1. Token hợp lệ
        2. Có GPS checkpoints
        3. Có start + destination location

        URL: /trip/view/{token}
        """
        try:
            _logger.info(f"=== Public trip view: token={token[:10]}...")

            Trip = request.env['trucking_planning.trip'].sudo()
            trip = Trip.search([('access_token', '=', token)], limit=1)

            if not trip:
                _logger.warning(f"Trip not found for token: {token[:10]}...")
                return self._render_error("Không tìm thấy chuyến đi hợp lệ.")

            if not trip.is_token_valid(token):
                _logger.warning(f"Invalid/expired token for trip {trip.id}")

                # ✅ Nếu token match nhưng expired → auto refresh và redirect
                if trip.access_token == token and \
                        trip.access_token_expires and \
                        trip.access_token_expires < request.env['odoo'].fields.Datetime.now():
                    _logger.info(f"Token expired for trip {trip.id}, refreshing...")

                    # Refresh token
                    trip.refresh_access_token()

                    # Redirect to new URL
                    new_url = trip.get_public_url()
                    _logger.info(f"Redirecting to new URL: {new_url}")

                    return request.redirect(new_url)

                return self._render_error("Liên kết đã hết hạn hoặc không hợp lệ.")

            checkpoint_count = len(trip.checkpoint_ids)
            if checkpoint_count == 0:
                _logger.warning(f"Trip {trip.id} has no checkpoints")
                return self._render_error(
                    "Chuyến đi này chưa có dữ liệu GPS.<br><br>"
                    "📍 GPS tracking sẽ khả dụng khi chuyến đi bắt đầu và tài xế gửi vị trí."
                )

            start_location = trip.actual_source_location_id or trip.plan_goods_pickup_location_id
            if not start_location:
                _logger.warning(f"Trip {trip.id} has no start location")
                return self._render_error(
                    "Chuyến đi này chưa có thông tin điểm đi.<br><br>"
                    "📍 Vui lòng liên hệ để cập nhật thông tin."
                )

            dest_location = trip.actual_destination_location_id or trip.plan_goods_delivery_location_id
            if not dest_location:
                _logger.warning(f"Trip {trip.id} has no destination location")
                return self._render_error(
                    "Chuyến đi này chưa có thông tin điểm đến.<br><br>"
                    "📍 Vui lòng liên hệ để cập nhật thông tin."
                )

            _logger.info(f"Trip {trip.id} validation passed: {checkpoint_count} checkpoints, "
                         f"start={start_location.name}, dest={dest_location.name}")

            if request.env.user._is_public():
                portal_user = self._get_portal_user()
                if portal_user:
                    request.update_env(user=portal_user.id)
                    _logger.info(f"Auto login portal user: {portal_user.login}")

            tracking_service = request.env['vehicle.tracking.service'].sudo()

            trip_data = tracking_service.get_trip_location_data(trip.id)
            route_points = tracking_service.get_trip_route_history(trip.id)

            if not trip_data:
                return self._render_error("Không có dữ liệu định vị cho chuyến đi này.")

            if not route_points:
                _logger.warning(f"Trip {trip.id} has no route history")
                # Không block - vẫn cho xem map với checkpoint hiện tại
                route_points = []

            _logger.info(f"Rendering map: trip_id={trip.id}, route_points={len(route_points)}")

            return request.render('hp_vehicle_tracking.trip_public_map_template', {
                'trip_data': trip_data,
                'trip': trip,
                'route_points': route_points,
            })

        except Exception as e:
            _logger.error(f"Controller error: {e}", exc_info=True)
            return self._render_error(f"Lỗi hệ thống: {str(e)}")

    def _get_portal_user(self):
        """Lấy hoặc tạo portal user cho viewing"""
        try:
            user = request.env['res.users'].sudo().search([
                ('login', '=', 'trip_portal_viewer')
            ], limit=1)

            if not user:
                _logger.info("Creating portal user 'trip_portal_viewer'")
                portal_group = request.env.ref('base.group_portal')
                partner = request.env['res.partner'].sudo().create({
                    'name': 'Trip Portal Viewer',
                    'email': 'tripportal@system.local',
                })
                user = request.env['res.users'].sudo().create({
                    'login': 'trip_portal_viewer',
                    'password': 'portal123',
                    'partner_id': partner.id,
                    'groups_id': [(6, 0, [portal_group.id])],
                })
                _logger.info(f"Portal user created: {user.login}")

            return user
        except Exception as e:
            _logger.error(f"Error creating portal user: {e}", exc_info=True)
            return None

    def _render_error(self, message):
        """Render simple error page"""
        return request.make_response(
            f'''
            <!DOCTYPE html>
            <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Thông Báo</title>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }}
                        .error-container {{
                            background: white;
                            padding: 50px;
                            border-radius: 15px;
                            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                            text-align: center;
                            max-width: 500px;
                        }}
                        .error-icon {{ 
                            font-size: 70px; 
                            margin-bottom: 20px;
                            animation: pulse 2s ease-in-out infinite;
                        }}
                        @keyframes pulse {{
                            0%, 100% {{ transform: scale(1); }}
                            50% {{ transform: scale(1.1); }}
                        }}
                        .error-title {{ 
                            color: #333; 
                            font-size: 24px; 
                            margin: 20px 0;
                            font-weight: 600;
                        }}
                        .error-message {{ 
                            color: #666; 
                            font-size: 16px; 
                            line-height: 1.8;
                            margin: 20px 0;
                        }}
                        .footer {{
                            margin-top: 30px;
                            padding-top: 20px;
                            border-top: 1px solid #eee;
                            color: #999;
                            font-size: 13px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <div class="error-icon">📍</div>
                        <h1 class="error-title">Không Thể Hiển Thị Bản Đồ</h1>
                        <div class="error-message">{message}</div>
                        <div class="footer">
                            HP Logistics - Vehicle Tracking System
                        </div>
                    </div>
                </body>
            </html>
            ''',
            status=403
        )