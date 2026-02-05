"""
Kegtron - Python API for Kegtron BLE keg monitoring devices.

This library provides tools to discover and read data from Kegtron
devices via Bluetooth Low Energy (BLE).

Quick Start:
    >>> import asyncio
    >>> from kegtron import scan_devices
    >>>
    >>> async def main():
    ...     devices = await scan_devices(timeout=10)
    ...     for device in devices:
    ...         print(f"{device.reading.beer_name}: {device.reading.percent_remaining:.1f}%")
    ...
    >>> asyncio.run(main())

For parsing raw BLE data:
    >>> from kegtron import parse_manufacturer_data
    >>> reading = parse_manufacturer_data(raw_bytes)
    >>> print(reading.volume_remaining_ml)

See the module documentation for more details:
    - kegtron.scanner: BLE scanning functions
    - kegtron.parser: Data parsing functions
    - kegtron.models: Data classes
    - kegtron.utils: Helper utilities
"""

__version__ = "0.1.0"

# Main scanning functions
from .scanner import (
    scan_devices,
    scan_device,
    KegtronScanner,
)

# Parser functions
from .parser import (
    parse_manufacturer_data,
    extract_device_id,
    is_kegtron_device,
    has_kegtron_data,
    ParseError,
    KEGTRON_MANUFACTURER_ID,
)

# Data models
from .models import (
    KegtronReading,
    KegtronDevice,
    PortState,
    KegSize,
)

# Utility functions
from .utils import (
    ml_to_oz,
    oz_to_ml,
    ml_to_gallons,
    ml_to_liters,
    ml_to_pints,
    format_volume,
    calculate_drinks_remaining,
    detect_pour,
    detect_new_keg,
    estimate_pour_time_seconds,
)

__all__ = [
    # Version
    "__version__",
    # Scanner
    "scan_devices",
    "scan_device",
    "KegtronScanner",
    # Parser
    "parse_manufacturer_data",
    "extract_device_id",
    "is_kegtron_device",
    "has_kegtron_data",
    "ParseError",
    "KEGTRON_MANUFACTURER_ID",
    # Models
    "KegtronReading",
    "KegtronDevice",
    "PortState",
    "KegSize",
    # Utils
    "ml_to_oz",
    "oz_to_ml",
    "ml_to_gallons",
    "ml_to_liters",
    "ml_to_pints",
    "format_volume",
    "calculate_drinks_remaining",
    "detect_pour",
    "detect_new_keg",
    "estimate_pour_time_seconds",
]
