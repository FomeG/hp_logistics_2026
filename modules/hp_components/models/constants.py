class VehicleEngineType:
    SMALL = 'small_engine'
    BIG = 'big_engine'

class VehicleModel:
    TRUCK = 'truck'
    TRAILER = 'trailer'

class VehicleModelCategory:
    TRUCK = 'truck'
    TRAILER = 'trailer'

class VehicleTag:
    RENTED = 'rented'
    ENGINE_SMALL = 'small_engine'
    ENGINE_BIG = 'big_engine'

class PartnerMainTypeCode:
    DRIVER = 'driver'
    CLIENT = 'client'

class PlanStatus:
    DRAFT = 'draft'
    CONFIRMED = 'confirmed'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    CANCEL = 'cancel'

class PlanLineStatus:
    HPL_REJECT = 'hpl_reject'
    CLIENT_CANCEL = 'client_cancel'
    CHECKING = 'checking'
    TRANSFER = 'transfer'
    RENTED = 'rented'

class TripStatus:
    DRAFT = 'draft'
    ON_ROUTE = 'on_route'
    STOPPED = 'stopped'
    DONE = 'done'
    CANCELLED = 'cancelled'

