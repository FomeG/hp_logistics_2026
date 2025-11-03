import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TripAccessController(http.Controller):
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
                return request.not_found("Không tìm thấy chuyến đi hợp lệ.")

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

                return request.render('http_routing.403', status=403)

            checkpoint_count = len(trip.checkpoint_ids)
            if checkpoint_count == 0:
                _logger.warning(f"Trip {trip.id} has no checkpoints")
                return request.not_found(
                    "Chuyến đi này chưa có dữ liệu GPS.<br><br>"
                    "📍 GPS tracking sẽ khả dụng khi chuyến đi bắt đầu và tài xế gửi vị trí."
                )

            start_location = trip.actual_source_location_id or trip.plan_goods_pickup_location_id
            if not start_location:
                _logger.warning(f"Trip {trip.id} has no start location")
                return request.not_found(
                    "Chuyến đi này chưa có thông tin điểm đi.<br><br>"
                    "📍 Vui lòng liên hệ để cập nhật thông tin."
                )

            dest_location = trip.actual_destination_location_id or trip.plan_goods_delivery_location_id
            if not dest_location:
                _logger.warning(f"Trip {trip.id} has no destination location")
                return request.not_found(
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
                return request.not_found("Không có dữ liệu định vị cho chuyến đi này.")

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
            return request.render('http_routing.500', status=500)

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