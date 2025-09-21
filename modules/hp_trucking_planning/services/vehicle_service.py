

class VehicleService:
    _name = "vehicle.service"

    VEHICLE_MODEL_TYPE_TRUCK = 'truck'
    VEHICLE_MODEL_TYPE_TRAILER = 'trailer'

    VEHICLE_ENGINE_TYPE_SMALL = 'small'
    VEHICLE_ENGINE_TYPE_BIG = 'big'

    def __init__(self, env):
        self.env = env
