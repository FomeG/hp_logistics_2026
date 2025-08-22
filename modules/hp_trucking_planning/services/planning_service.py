
class planning_service:
    _name = "trucking_planning.plan.service"

    def __init__(self, env):
        self.env = env

    def remove_vehicle_driver_by_vehicle_and_date_plan(self, vehicle_id, date_plan, exclude_trip_id):
        trips = self.env['trucking_planning.trip'].search([
            ('id', '!=', exclude_trip_id),
            ('status', 'not in', ['cancelled']),
            ('truck_id', '=', vehicle_id),
            ('plan_date', '=', date_plan),
        ])

        if trips:
            trips.write({
                'truck_id': False,
                'driver_id': False,
            })
