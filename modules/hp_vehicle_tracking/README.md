# HP Vehicle Tracking Module

## Overview
The HP Vehicle Tracking module provides real-time GPS tracking for vehicles in the trucking planning system. It displays driver locations on an interactive map using OpenStreetMap and Leaflet.js.

## Features

### 🗺️ Live Map Display
- Interactive OpenStreetMap integration
- Real-time vehicle location tracking
- Color-coded markers based on data freshness:
  - 🟢 **Green**: Updated within last 30 minutes
  - 🟡 **Yellow**: Updated 30-60 minutes ago
  - 🔴 **Red**: Updated more than 1 hour ago

### 📊 Dashboard Statistics
- Total active trips
- Fresh location count (< 30 mins)
- Stale location count (> 1 hour)

### 🔄 Auto-Refresh
- Configurable auto-refresh interval (default: 30 seconds)
- Manual refresh option
- Toggle auto-refresh on/off

### 🔍 Search & Filter
- Search by driver name
- Search by vehicle name
- Search by trip code
- Real-time search with marker highlighting

### 📍 GPS Checkpoint Integration
- Receives GPS data via Zalo webhook from CRM system
- Stores checkpoint data in `trucking_planning.trip_checkpoint` model
- Shows only latest location per driver (from their current trip)

## Installation

1. Copy the module to your Odoo addons directory
2. Update the app list in Odoo
3. Install the "HP Vehicle Tracking" module
4. The module depends on `hp_trucking_planning`

## Configuration

Go to **Settings → Vehicle Tracking** to configure:

- **Auto-refresh Interval**: How often the map updates (default: 30 seconds)
- **Stale Threshold**: When to consider location data stale (default: 60 minutes)
- **Default Map Center**: Latitude and longitude for map initialization (default: Hanoi)
- **Default Zoom Level**: Initial zoom level (default: 10)

## Usage

### Accessing the Map
Navigate to **Vehicle Tracking → Live Map** from the main menu.

### Map Interface
- **Header**: Shows real-time statistics
- **Controls**: Search box, refresh button, auto-refresh toggle
- **Map**: Interactive map with vehicle markers

### Marker Information
Click any marker to see:
- Driver name
- Trip code
- Vehicle name and plate
- Container number (if applicable)
- Driver phone
- Last update time
- Status (fresh/stale/old)

### GPS Data Flow
1. Driver shares location via Zalo
2. CRM system processes the location
3. CRM sends data to webhook: `/zalo/gps_location`
4. Odoo creates checkpoint for driver's current trip
5. Map displays latest location

## API Endpoints

### Webhook for GPS Data
- **URL**: `/zalo/gps_location`
- **Method**: POST
- **Auth**: Public
- **Body**:
```json
{
  "error": false,
  "message": "success",
  "data": {
    "phone": "84325749486",
    "longitude": "105.74044561",
    "latitude": "21.00421426"
  }
}
```

### Get Driver Locations
- **URL**: `/vehicle_tracking/api/driver_locations`
- **Method**: POST (JSON-RPC)
- **Auth**: User
- **Returns**: Array of driver locations with latest GPS data

### Get Trip Route
- **URL**: `/vehicle_tracking/api/trip_route/<trip_id>`
- **Method**: POST (JSON-RPC)
- **Auth**: User
- **Returns**: All checkpoints for a trip (for route history)

### Get Statistics
- **URL**: `/vehicle_tracking/api/stats`
- **Method**: POST (JSON-RPC)
- **Auth**: User
- **Returns**: Dashboard statistics

## Technical Details

### Dependencies
- `base`
- `web`
- `hp_trucking_planning`

### External Libraries
- **Leaflet.js v1.9.4**: JavaScript library for interactive maps
- **OpenStreetMap**: Free map tiles

### Data Model
The module uses the existing `trucking_planning.trip_checkpoint` model from `hp_trucking_planning`:
- `trip_id`: Many2one to trip
- `latitude`: GPS latitude
- `longitude`: GPS longitude
- `create_date`: Timestamp of checkpoint

### Map Logic
- Shows **one marker per driver** (not per trip)
- Displays **latest checkpoint** from driver's current trip (`is_current=True`)
- Only shows trips that are not cancelled or done
- Auto-refreshes every 30 seconds (configurable)

## Permissions
- All logged-in users can view the map (read-only access)
- No create/write/delete permissions required for viewing

## Future Enhancements (Roadmap)
- ✅ Show route history (all checkpoints for a trip)
- ✅ Playback feature (animate trip over time)
- ✅ Geofencing (alerts when vehicle enters/exits areas)
- ✅ ETA prediction based on current location
- ✅ Mobile app for continuous GPS tracking

## Support
For issues or questions, contact HP Logistics development team.

## License
LGPL-3

## Version
1.0.0



