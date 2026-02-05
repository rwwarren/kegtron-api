# Kegtron Python API

[![Tests](https://github.com/rwwarren/kegtron-api/actions/workflows/tests.yml/badge.svg)](https://github.com/rwwarren/kegtron-api/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/rwwarren/kegtron-api/branch/main/graph/badge.svg)](https://codecov.io/gh/rwwarren/kegtron-api)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library for interacting with [Kegtron](https://kegtron.com/) BLE keg monitoring devices.

## Features

- Discover Kegtron devices via Bluetooth Low Energy (BLE)
- Parse device broadcast data to get keg status
- Calculate remaining volume, percentage, and drinks left
- Detect pours and new keg events
- Unit conversion utilities (ml, oz, gallons, liters, pints)

## Installation

```bash
pip install kegtron
```

Or install from source:

```bash
git clone https://github.com/rwwarren/kegtron-api.git
cd kegtron-api
pip install -e .
```

## Requirements

- Python 3.9+
- macOS, Linux, or Windows with Bluetooth support
- Bluetooth permissions granted to your application

### Platform Notes

- **macOS**: Your terminal or Python app needs Bluetooth permission in System Settings → Privacy & Security → Bluetooth
- **Linux**: Requires `bluez` and appropriate permissions (typically via the `bluetooth` group)
- **Windows**: Requires Windows 10+ with Bluetooth enabled

## Quick Start

### Scanning for Devices

```python
import asyncio
from kegtron import scan_devices

async def main():
    # Scan for 10 seconds
    devices = await scan_devices(timeout=10)

    for device in devices:
        print(f"Device: {device.device_id}")
        print(f"  Beer: {device.reading.beer_name}")
        print(f"  Remaining: {device.reading.percent_remaining:.1f}%")
        print(f"  Volume: {device.reading.volume_remaining_ml} ml")

asyncio.run(main())
```

### Scanning for a Specific Device

```python
from kegtron import scan_device

async def main():
    device = await scan_device("F1EDC6", timeout=10)

    if device:
        print(f"Found {device.reading.beer_name}!")
        print(f"{device.reading.percent_remaining:.1f}% remaining")
    else:
        print("Device not found")

asyncio.run(main())
```

### Parsing Raw BLE Data

If you're handling BLE scanning yourself, you can parse the manufacturer data directly:

```python
from kegtron import parse_manufacturer_data, KEGTRON_MANUFACTURER_ID

# In your BLE callback
def handle_advertisement(device, advertisement_data):
    if KEGTRON_MANUFACTURER_ID in advertisement_data.manufacturer_data:
        raw_data = advertisement_data.manufacturer_data[KEGTRON_MANUFACTURER_ID]
        reading = parse_manufacturer_data(raw_data)

        print(f"Beer: {reading.beer_name}")
        print(f"Dispensed: {reading.volume_dispensed_ml} ml")
        print(f"Remaining: {reading.percent_remaining:.1f}%")
```

### Using the Scanner Class

For continuous monitoring with callbacks:

```python
from kegtron import KegtronScanner, KegtronDevice

scanner = KegtronScanner()

@scanner.on_device_found
def handle_device(device: KegtronDevice):
    print(f"Found: {device.device_id} - {device.reading.beer_name}")
    print(f"  {device.reading.percent_remaining:.1f}% remaining")

async def main():
    while True:
        await scanner.scan(timeout=10)
        await asyncio.sleep(60)  # Scan every minute

asyncio.run(main())
```

### Utility Functions

```python
from kegtron import (
    ml_to_oz,
    format_volume,
    calculate_drinks_remaining,
    detect_pour,
    detect_new_keg,
)

# Volume conversions
remaining_ml = 14550
print(f"{ml_to_oz(remaining_ml):.1f} oz remaining")
print(format_volume(remaining_ml, "oz"))  # "491.9 oz"
print(format_volume(remaining_ml, "gal")) # "3.8 gal"

# Calculate drinks
drinks = calculate_drinks_remaining(remaining_ml)
print(f"{drinks} 12oz drinks remaining")

pints = calculate_drinks_remaining(remaining_ml, drink_size_ml=473.176)
print(f"{pints} pints remaining")

# Detect pours
pour_amount = detect_pour(current_dispensed=5100, previous_dispensed=5000)
if pour_amount:
    print(f"Pour detected: {pour_amount} ml")

# Detect new keg
is_new = detect_new_keg(
    current_start_ml=19550,
    previous_start_ml=18927,
    current_dispensed_ml=0,
    previous_dispensed_ml=5000,
)
if is_new:
    print("New keg detected!")
```

## API Reference

### Scanner Module

#### `scan_devices(timeout=10.0, device_id=None) -> List[KegtronDevice]`

Scan for Kegtron devices.

- `timeout`: Scan duration in seconds (default: 10)
- `device_id`: Optional filter for specific device
- Returns: List of discovered devices

#### `scan_device(device_id, timeout=10.0) -> Optional[KegtronDevice]`

Scan for a specific device by ID.

#### `KegtronScanner`

Stateful scanner with callback support.

### Parser Module

#### `parse_manufacturer_data(data: bytes) -> KegtronReading`

Parse 27-byte Kegtron manufacturer data.

#### `extract_device_id(device_name: str) -> Optional[str]`

Extract device ID from name (e.g., "Kegtron F1EDC6" → "F1EDC6").

#### `is_kegtron_device(device_name: str) -> bool`

Check if device name indicates a Kegtron device.

### Models

#### `KegtronReading`

Parsed data from a Kegtron device:

- `keg_size_ml`: Configured keg size
- `volume_start_ml`: Starting volume when tapped
- `volume_dispensed_ml`: Total volume dispensed
- `port_count`: Number of ports (1 or 2)
- `port_index`: This port's index (0 or 1)
- `port_state`: Port state (PortState enum)
- `beer_name`: Configured beer name (up to 20 chars)
- `volume_remaining_ml`: Calculated remaining volume
- `percent_remaining`: Calculated percentage remaining

#### `KegtronDevice`

Discovered device with reading:

- `device_id`: Unique ID (e.g., "F1EDC6")
- `device_name`: Full BLE name
- `ble_address`: BLE address/UUID
- `reading`: KegtronReading object

#### `KegSize`

Common keg size constants in ml:

- `MINI_KEG`: 5000 (5L)
- `CORNELIUS`: 18927 (5 gal)
- `SIXTH_BARREL`: 19550 (5.16 gal)
- `QUARTER_BARREL`: 29337 (7.75 gal)
- `HALF_BARREL`: 58674 (15.5 gal)

### Utils Module

Volume conversion:
- `ml_to_oz(ml)`, `oz_to_ml(oz)`
- `ml_to_gallons(ml)`, `ml_to_liters(ml)`, `ml_to_pints(ml)`
- `format_volume(ml, unit, precision=1)`

Calculations:
- `calculate_drinks_remaining(volume_ml, drink_size_ml=354.882)`
- `detect_pour(current, previous, min_pour_ml=30)`
- `detect_new_keg(current_start, previous_start, current_dispensed, previous_dispensed)`
- `estimate_pour_time_seconds(volume_ml, flow_rate_ml_per_sec=59.15)`

## Development

### Setup

```bash
git clone https://github.com/rwwarren/kegtron-api.git
cd kegtron-api
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=kegtron --cov-report=html
```

## Data Format

Kegtron devices broadcast manufacturer-specific data (ID: 0xFFFF) in the following 27-byte format:

| Bytes | Field | Type | Description |
|-------|-------|------|-------------|
| 0-1 | keg_size | uint16 BE | Configured keg size in ml |
| 2-3 | volume_start | uint16 BE | Starting volume in ml |
| 4-5 | volume_dispensed | uint16 BE | Total dispensed in ml |
| 6 | port_state | uint8 | Port count, index, and state |
| 7-26 | beer_name | char[20] | UTF-8 null-padded string |

Port state byte layout:
- Bits 6-7: Port count (0-3)
- Bits 4-5: Port index (0-3)
- Bits 0-1: Port state (0=disabled, 1=enabled)

Source: https://kegtron.com/docs/Gen1BLEMessageFormat.pdf (Also in [Gen1BLEMessageFormat.pdf](Gen1BLEMessageFormat.pdf)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Kegtron](https://kegtron.com/) for making great keg monitoring hardware
- [bleak](https://github.com/hbldh/bleak) for cross-platform BLE support
