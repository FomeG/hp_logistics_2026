
class planning_service:
    _name = "trucking_planning.plan.service"

    def __init__(self, env):
        self.env = env

    def remove_vehicle_driver_by_vehicle_and_date_plan(self, vehicle_id, date_plan, exclude_plan_id):
        plans = self.env['trucking_planning.plan'].search([
            ('id', '!=', exclude_plan_id),
            ('status', '!=', 'cancel'),
            ('vehicle_id', '=', vehicle_id),
            ('date', '=', date_plan),
        ])

        if plans:
            plans.write({
                'vehicle_id': False,
                'driver_id': False,
            })

            self.env['trucking_planning.plan.line'].search([
                ('plan_id', 'in', plans.ids) 
            ]).write({
                'truck_id': False,
                'driver_id': False,
            })

