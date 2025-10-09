# HP Vehicle Tracking - Architecture & Conventions

## 📋 Module Structure (Following hp_trucking_planning Convention)

```
hp_vehicle_tracking/
├── __init__.py                          # Module initialization (imports models, controllers, services)
├── __manifest__.py                      # Module metadata and dependencies
├── README.md                            # User documentation
├── ARCHITECTURE.md                      # This file - technical documentation
│
├── models/                              # Data models
│   ├── __init__.py
│   └── res_config_settings.py          # Settings configuration
│
├── controllers/                         # HTTP/JSON endpoints (thin layer)
│   ├── __init__.py
│   ├── zalo_gps_webhook.py            # GPS data webhook endpoint
│   └── vehicle_tracking_map.py        # Map view and API endpoints
│
├── services/                            # ✅ Business logic layer (NEW - follows manager's convention)
│   ├── __init__.py
│   └── vehicle_tracking_service.py    # Core tracking business logic
│
├── views/                               # UI definitions (XML)
│   ├── vehicle_tracking_map_views.xml # Map page template and menu
│   └── res_config_settings_views.xml  # Settings UI
│
├── security/                            # Access rights
│   └── ir.model.access.csv            # User permissions
│
└── static/                              # Frontend assets
    └── src/
        ├── js/                          # JavaScript files (auto-loaded via assets)
        └── css/                         # CSS files
```

---

## 🎯 Convention Compliance Checklist

### ✅ Follows hp_trucking_planning Conventions:
1. **✅ Service Layer Pattern**: Business logic in `services/` folder
2. **✅ Thin Controllers**: Controllers only handle HTTP/routing
3. **✅ Proper __init__.py**: Imports models, controllers, services
4. **✅ AbstractModel Services**: Using `models.AbstractModel` for services
5. **✅ Proper Logging**: Using `_logger` consistently
6. **✅ Error Handling**: UserError for business logic, logging for debugging
7. **✅ Naming Convention**: Underscore naming (vehicle_tracking_service.py)
8. **✅ Comment Style**: Clear docstrings and inline comments

### ⚠️ Differences from hp_trucking_planning:
1. **No `listeners/` folder**: Not needed for this module (no event listeners required)
2. **No `report/` folder**: No PDF reports in this module
3. **No `wizards/` folder**: No wizard dialogs in this module
4. **No `demo/` folder**: No demo data needed for tracking

---

## 🔄 Data Flow & Architecture

### **1. GPS Data Flow (Webhook)**
```
Driver (Zalo)
    ↓
CRM System
    ↓
POST /zalo/gps_location (zalo_gps_webhook.py)
    ↓
Controller validates input
    ↓
vehicle.tracking.service.create_gps_checkpoint() ← SERVICE LAYER
    ↓
Creates trucking_planning.trip_checkpoint record
    ↓
Returns success response
```

**Where Each Component is Called:**

- **Controller** (`zalo_gps_webhook.py`):
  - Called by: External CRM system via HTTP POST
  - URL: `/zalo/gps_location`
  - Auth: Public (no authentication required)
  - Responsibilities:
    - Validate HTTP request format
    - Parse JSON data
    - Validate coordinates range
    - Call service layer
    - Return HTTP response

- **Service** (`vehicle_tracking_service.create_gps_checkpoint()`):
  - Called by: `zalo_gps_webhook.py` controller
  - Parameters: `phone`, `latitude`, `longitude`
  - Responsibilities:
    - Find driver by phone number (handles format conversion)
    - Find driver's current trip (`is_current=True`)
    - Create checkpoint record
    - Return structured result
    - Handle business exceptions

---

### **2. Map Display Flow**
```
User clicks "Vehicle Tracking" → "Live Map"
    ↓
GET /vehicle_tracking/map (vehicle_tracking_map.py)
    ↓
Renders QWeb template with Leaflet.js map
    ↓
JavaScript calls JSON endpoints every 30s:
    ↓
POST /vehicle_tracking/api/driver_locations
    ↓
Controller calls service layer
    ↓
vehicle.tracking.service.get_all_active_driver_locations() ← SERVICE LAYER
    ↓
Returns JSON with driver locations
    ↓
JavaScript updates markers on map
```

**Where Each Component is Called:**

- **Controller** (`vehicle_tracking_map.py`):
  - `vehicle_tracking_map_view()`:
    - Called by: User navigation (menu click)
    - URL: `/vehicle_tracking/map`
    - Auth: User (logged-in users only)
    - Returns: HTML page with map
  
  - `get_driver_locations()`:
    - Called by: JavaScript (auto-refresh every 30s)
    - URL: `/vehicle_tracking/api/driver_locations`
    - Type: JSON-RPC
    - Auth: User
    - Returns: Array of driver locations
  
  - `get_trip_route()`:
    - Called by: JavaScript (when user clicks marker - future feature)
    - URL: `/vehicle_tracking/api/trip_route/<trip_id>`
    - Type: JSON-RPC
    - Auth: User
    - Returns: Array of all checkpoints for a trip
  
  - `get_tracking_stats()`:
    - Called by: JavaScript (map page load & refresh)
    - URL: `/vehicle_tracking/api/stats`
    - Type: JSON-RPC
    - Auth: User
    - Returns: Dashboard statistics

- **Service** (`vehicle_tracking_service`):
  - `get_all_active_driver_locations()`:
    - Called by: `get_driver_locations()` controller
    - Responsibilities:
      - Find all trips with `is_current=True`
      - For each trip, get latest checkpoint
      - Calculate time difference and status
      - Return formatted location data
  
  - `get_trip_route_history()`:
    - Called by: `get_trip_route()` controller
    - Parameters: `trip_id`
    - Responsibilities:
      - Get all checkpoints for trip (ordered by time)
      - Format for map polyline display
  
  - `get_tracking_statistics()`:
    - Called by: `get_tracking_stats()` controller
    - Responsibilities:
      - Count active trips
      - Calculate fresh vs stale locations
      - Return dashboard stats

---

## 🏗️ Why Service Layer? (Manager's Convention)

### **Benefits of Service Layer Pattern:**

1. **Separation of Concerns**:
   - Controllers: HTTP/routing only
   - Services: Business logic
   - Models: Data persistence

2. **Reusability**:
   - Services can be called from:
     - Controllers (HTTP endpoints)
     - Scheduled actions (cron jobs)
     - Other models (via `self.env['vehicle.tracking.service']`)
     - RPC calls
     - Unit tests

3. **Maintainability**:
   - Business logic in one place
   - Easy to test services independently
   - Clear responsibility boundaries

4. **Consistency**:
   - Same pattern as `hp_trucking_planning`
   - Easy for team to understand
   - Follows Odoo best practices

### **Example: How to Call Service from Other Modules**

```python
# From any model or controller:
tracking_service = self.env['vehicle.tracking.service']

# Create GPS checkpoint
result = tracking_service.create_gps_checkpoint(
    phone='0965774192',
    latitude=21.0285,
    longitude=105.8542
)

# Get driver location
location = tracking_service.get_driver_latest_location(driver_id)

# Get all locations
all_locations = tracking_service.get_all_active_driver_locations()

# Get trip route
route = tracking_service.get_trip_route_history(trip_id)

# Get statistics
stats = tracking_service.get_tracking_statistics()
```

---

## 📊 Service Methods Reference

### `vehicle.tracking.service` Methods:

| Method | Called By | Parameters | Returns | Purpose |
|--------|-----------|------------|---------|---------|
| `create_gps_checkpoint()` | `zalo_gps_webhook.py` | phone, lat, lng | dict (checkpoint info) | Process GPS webhook |
| `get_driver_latest_location()` | Internal helper | driver_id | dict (location) | Get single driver location |
| `get_all_active_driver_locations()` | `vehicle_tracking_map.py` | - | list[dict] | Get all driver locations |
| `get_trip_route_history()` | `vehicle_tracking_map.py` | trip_id | list[dict] | Get all checkpoints for trip |
| `get_tracking_statistics()` | `vehicle_tracking_map.py` | - | dict (stats) | Get dashboard statistics |
| `_find_driver_by_phone()` | Internal helper | phone | driver record | Find driver (handles formats) |

---

## 🔐 Security Model

```csv
# ir.model.access.csv
access_vehicle_tracking_all_users,vehicle_tracking.all_users,base.model_res_users,base.group_user,1,0,0,0
```

- **Read access**: All logged-in users (`base.group_user`)
- **No write/create/delete**: Map is read-only
- **Webhook**: Public access (no auth required)

---

## ⚙️ Settings Configuration

**Location**: Settings → Vehicle Tracking

- `vehicle_tracking_auto_refresh_interval`: Auto-refresh interval (seconds)
- `vehicle_tracking_stale_threshold`: Stale location threshold (minutes)
- `vehicle_tracking_default_map_center_lat`: Default map latitude
- `vehicle_tracking_default_map_center_lng`: Default map longitude
- `vehicle_tracking_default_zoom_level`: Default zoom level (1-19)

**Access**: `res.config.settings` model extension

---

## 🚀 Deployment Checklist

### Before Installing:
1. ✅ Ensure `hp_trucking_planning` is installed
2. ✅ Update Odoo addons path
3. ✅ Restart Odoo server

### After Installing:
1. ✅ Go to Settings → Vehicle Tracking (configure map settings)
2. ✅ Go to Vehicle Tracking → Live Map (verify map loads)
3. ✅ Test webhook: `POST /zalo/gps_location` with sample data
4. ✅ Verify checkpoints are created
5. ✅ Verify map shows driver locations

---

## 🧪 Testing Service Layer

```python
# In Odoo shell or unit tests:

# Test GPS checkpoint creation
service = self.env['vehicle.tracking.service']
result = service.create_gps_checkpoint(
    phone='0965774192',
    latitude=21.0285,
    longitude=105.8542
)
print(result)  # Should show checkpoint_id, trip_id, etc.

# Test getting locations
locations = service.get_all_active_driver_locations()
print(f"Found {len(locations)} active drivers")

# Test statistics
stats = service.get_tracking_statistics()
print(f"Active: {stats['active_trips']}, Fresh: {stats['fresh_locations']}")
```

---

## 📝 Future Enhancements (Following Same Pattern)

### Add New Service Methods:
```python
# In vehicle_tracking_service.py

@api.model
def get_drivers_near_location(self, latitude, longitude, radius_km):
    """Find all drivers within radius of a location"""
    pass

@api.model
def calculate_driver_eta(self, driver_id, destination_lat, destination_lng):
    """Calculate estimated time of arrival for driver"""
    pass

@api.model
def get_driver_route_summary(self, driver_id, date_from, date_to):
    """Get summary of driver's routes for a period"""
    pass
```

### Add New Controllers:
```python
# In vehicle_tracking_map.py

@http.route('/vehicle_tracking/api/nearby_drivers', type='json', auth='user')
def get_nearby_drivers(self, latitude, longitude, radius, **kwargs):
    tracking_service = request.env['vehicle.tracking.service']
    drivers = tracking_service.get_drivers_near_location(latitude, longitude, radius)
    return {'success': True, 'drivers': drivers}
```

---

## ✅ Compliance Summary

This module **fully follows** the `hp_trucking_planning` conventions:

1. ✅ **Service Layer**: All business logic in `services/`
2. ✅ **Thin Controllers**: Controllers delegate to services
3. ✅ **AbstractModel**: Services use `models.AbstractModel`
4. ✅ **Proper Imports**: `__init__.py` imports services
5. ✅ **Error Handling**: `UserError` for business logic
6. ✅ **Logging**: Consistent `_logger` usage
7. ✅ **Documentation**: Clear docstrings everywhere
8. ✅ **Naming**: Underscore convention throughout

**Ready for production deployment!** 🚀


