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
    SHIPPING_LINE = 'shipping_line'

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

class BookingStatus:
    DRAFT = 'draft'
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    SHIPPED = 'shipped'
    CANCELLED = 'cancelled'
    EXPIRED = 'expired'

class SellingWeekState:
    INCOMING = 'incoming'
    CURRENT = 'current'
    PAST = 'past'

class ServiceType:
    IMPORT = 'import'
    EXPORT = 'export'
    DOMESTIC = 'domestic'
    OTHER = 'other'
    SELECT_OPTIONS = [
        (IMPORT, 'Import'),
        (EXPORT, 'Export'),
        (DOMESTIC, 'Domestic'),
        (OTHER, 'Other'),
    ]

# class ProductCategoryServiceType:
#     IMPORT = 'import'
#     EXPORT = 'export'
#     DOMESTIC = 'domestic'
#     OTHER = 'other'
#     OVERSEA = 'oversea'
#     LAND = 'land'
#     SELECT_OPTIONS = [
#         (IMPORT, 'Import'),
#         (EXPORT, 'Export'),
#         (DOMESTIC, 'Domestic'),
#         (OVERSEA, 'Oversea'),
#         (LAND, 'Land'),
#         (OTHER, 'Other'),
#     ]

class ProductTagName:
    IMPORT = 'Import'
    EXPORT = 'Export'
    DOMESTIC = 'Domestic'
    LAND = 'Land'
    OVERSEA = 'Oversea'

DEFAULT_NORMAL_PRODUCT_TAGS = [
    ProductTagName.DOMESTIC,
    ProductTagName.LAND,
    ProductTagName.OVERSEA
]

SERVICE_TYPE_TO_TAG_MAP = {
    ServiceType.IMPORT: [ProductTagName.IMPORT],
    ServiceType.EXPORT: [ProductTagName.EXPORT],
    ServiceType.OTHER: [ProductTagName.IMPORT, ProductTagName.EXPORT],
    ServiceType.DOMESTIC: [ProductTagName.DOMESTIC],
}

SERVICE_TYPE_PRICELIST_MAP = {
    ServiceType.IMPORT: 'hp_sale.pricelist_import_hp',
    ServiceType.EXPORT: 'hp_sale.pricelist_export_hp',
    # Khi là Other hoặc Domestic, mặc định dùng bảng Nhập (Bảng này được cấu hình chứa đủ cả giá Xuất)
    ServiceType.OTHER: 'hp_sale.pricelist_import_hp',
    ServiceType.DOMESTIC: 'hp_sale.pricelist_import_hp',
}

class SaleOrderState:
    DRAFT = 'draft' #quotation
    ACTIVE = 'active'
    SENT_TO_CLIENT = 'sent_to_client'
    REVIEW = 'review'
    REQUEST_TO_APPROVAL = 'request_to_approval'
    REQUEST_BOOKING = 'request_booking'
    DENIED = 'denied'
    READY = 'ready' 
    SALE = 'sale' #convert from quotation to sale order
    DONE = 'done'
    CANCELLED = 'cancelled'
    SELECT_OPTIONS = [
        (DRAFT, 'Draft'),
        (ACTIVE, 'Active'),
        (SENT_TO_CLIENT, 'Sent to Client'),
        (REVIEW, 'Review'),
        (REQUEST_TO_APPROVAL, 'Request to Approval'),
        (REQUEST_BOOKING, 'Request Booking'),
        (DENIED, 'DENIED'),
        (READY, 'Ready'),
        (SALE, 'Sale'),
        (DONE, 'Done'),
        (CANCELLED, 'Cancelled'),
    ]
    FORBIDDEN_STATES = {
        REQUEST_TO_APPROVAL,
        REQUEST_BOOKING,
        DENIED,
        READY,
        SALE,
        CANCELLED,
    }

class CsOrderState:
    DRAFT = 'draft'
    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    CANCELLED = 'cancelled'
    SELECT_OPTIONS = [
        (DRAFT,'Draft'),
        (OPEN,'Open'),
        (IN_PROGRESS,'In Progress'),
        (DONE,'Done'),
        (CANCELLED,'Cancelled')
    ]

class DeliveryTerms:
    CY_CY = 'cy_cy'
    CY_DOOR = 'cy_door'
    DOOR_CY = 'door_cy'
    DOOR_DOOR = 'door_door'
    SELECT_OPTIONS = [
        (CY_CY, 'CY to CY'),
        (CY_DOOR, 'CY to Door'),
        (DOOR_CY, 'Door to CY'),
        (DOOR_DOOR, 'Door to Door'),
    ]

class ShippingInstructions:
    FREIGHT_CHARGE_COLLECT = 'collect'
    FREIGHT_CHARGE_PREPAID = 'prepaid'
    FREIGHT_CHARGE_SELECT_OPTIONS = [
        (FREIGHT_CHARGE_COLLECT, 'Collect'),
        (FREIGHT_CHARGE_PREPAID, 'Prepaid'),
    ]

class BL:
    MBL = 'mbl'
    HBL = 'hbl'
    SELECT_OPTIONS = [
        (MBL, 'Master BL'),
        (HBL, 'House BL'),
    ]

class PreAlertState:
    DRAFT = 'draft'
    READY = 'ready_to_send'
    SENT = 'sent'
    RECEIVED = 'received_by_agent'
    SELECT_OPTIONS = [
        (DRAFT, 'Draft'),
        (READY, 'Ready To Send'),
        (SENT, 'Sent'),
        (RECEIVED, 'Received by Agent'),
    ]

class TransportMode:
    SEA = 'sea'
    TRUCK = 'truck'
    SELECT_OPTIONS = [
        (SEA, 'Sea'),
        (TRUCK, 'Truck'),
    ]
class RouteLevel:
    DOMESTIC = 'domestic'
    INTERNATIONAL = 'international'
    CROSS_BORDER = 'cross_border'
    SELECT_OPTIONS = [
        (DOMESTIC, 'Domestic'),
        (INTERNATIONAL, 'International'),
        (CROSS_BORDER, 'Cross Border'),
    ]

class LocationType:
    CONTAINER_PICKUP = 'container_pickup'
    CONTAINER_DELIVERY = 'container_delivery'
    PORT = 'port'
    DEPOT = 'depot'
    WAREHOUSE = 'warehouse'
    FACTORY = 'factory'
    GOODS_PICKUP = 'goods_pickup'
    GOODS_DELIVERY = 'goods_delivery'
    TRUCK_ROAD = 'truck_road'
    OTHER = 'other'
    CITY = 'city'
    SELECT_OPTIONS = [
        (CONTAINER_PICKUP, 'Container Pickup'),
        (CONTAINER_DELIVERY, 'Container Delivery'),
        (PORT, 'Port'),
        (TRUCK_ROAD, 'Truck Road'),
        (DEPOT, 'Depot'),
        (WAREHOUSE, 'Warehouse'),
        (FACTORY, 'Factory'),
        (GOODS_PICKUP, 'Goods Pickup'),
        (GOODS_DELIVERY, 'Goods Delivery'),
        (CITY, 'City'),
        (OTHER, 'Other'),
    ]
    TYPES_4_SEA_ROUTE = {PORT}
    TYPES_4_TRUCK_ROUTE = {TRUCK_ROAD}

class ProductTemplateType:
    SEA_FREIGHT = 'sea_freight'
    TRUCK_FREIGHT = 'truck_freight'
    CUSTOM = 'custom'
    SERVICES = 'services'
    SELECT_OPTIONS = [
        (SEA_FREIGHT, 'Sea Freight'),
        (TRUCK_FREIGHT, 'Truck Freight'),
        (SERVICES, 'Services'),
        (CUSTOM, 'Custom'),
    ]

class DepartmentTypeCode:
    SALE = 'sale'
    TRUCKING = 'trucking'
    PRICING = 'pricing'
    CS = 'cs'

class LocationSource:
    MANUAL = 'manual'
    IMPORTED = 'imported'
    SELECT_OPTIONS = [
        (MANUAL, 'Manual'),
        (IMPORTED, 'Imported'),
    ]

class ShippingDocumentType:
    Delivery_Order = 'delivery_order'
    Arrival_Notice = 'arrival_notice'
    SELECT_OPTIONS = [
        (Delivery_Order, 'Delivery Order'),
        (Arrival_Notice, 'Arrival Notice'),
    ]

class ShippingDocumentState:
    DRAFT = 'draft' #quotation
    CONFIRMED = 'confirmed'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    SELECT_OPTIONS = [
        (DRAFT, 'Draft'),
        (CONFIRMED, 'Confirmed'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
    ]

class WorkShiftType:
    FIXED = 'fixed'
    FLEXIBLE = 'flexible'

class SurChargeType:
    SEA_FREIGHT = 'sea_freight'
    SELECT_OPTIONS = [
        (SEA_FREIGHT, 'sea_freight')
    ]

class PriceRequestState:
    OPEN = 'open'
    DONE = 'done'
    CANCELLED = 'cancelled'
    SELECT_OPTIONS = [
        (OPEN, 'Open'),
        (DONE, 'Done'),
        (CANCELLED, 'Cancelled'),
    ]
class VoyageMode:
    DIRECT='direct'
    TRANSIT='transit'
    OTHER='other'
    SELECT_OPTIONS = [
        (DIRECT,'Direct'),
        (TRANSIT,'Transit'),
        (OTHER,'Other')
    ]