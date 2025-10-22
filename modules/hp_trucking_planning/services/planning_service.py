from odoo import fields
from odoo.addons.hp_components.models import constants

class planning_service:
    _name = "trucking_planning.plan.service"

    def __init__(self, env):
        self.env = env

    def remove_vehicle_driver_by_vehicle_and_date_plan(self, vehicle_id, date_plan, exclude_trip_id):
        trips = self.env['trucking_planning.trip'].search([
            ('id', '!=', exclude_trip_id),
            ('status', 'not in', [constants.TripStatus.CANCELLED]),
            ('truck_id', '=', vehicle_id),
            ('plan_date', '=', date_plan),
        ])

        if trips:
            trips.write({
                'truck_id': False,
                'driver_id': False,
            })

    def update_trip_statuses(self, status):
        now = fields.Datetime.now()
        today = fields.Date.today()

        match status:
            case constants.TripStatus.CANCELLED:
                domain = [
                    ('truck_id', '=', False),
                    '|', '|',
                        ('goods_cut_off', '<', now),
                        ('plan_date', '<', today),
                        ('plan_estimate_time_departure', '<', now),
                    ('status', '!=', constants.TripStatus.CANCELLED),
                ]

            case constants.TripStatus.DONE:
                domain = [
                    ('truck_id', '!=', False),
                    '|', '|',
                        ('goods_cut_off', '<', now),
                        ('plan_date', '<', today),
                        ('plan_estimate_time_arrival', '<', now),
                    ('status', '!=', constants.TripStatus.DONE),
                ]
            case _:
                return False

        system_user = self.env.ref('base.user_root')
        trips = self.env['trucking_planning.trip'].search(domain)
        if trips:
            trips.with_user(system_user).write({
                'status': status
            })
        
        return True