"""
Parser for Kegtron BLE manufacturer data.

This module provides functions to parse the raw BLE manufacturer data
broadcast by Kegtron devices into structured Python objects.

The Kegtron manufacturer data format (27 bytes):
    - Bytes 0-1: Keg size (ml), big-endian uint16
    - Bytes 2-3: Volume start (ml), big-endian uint16
    - Bytes 4-5: Volume dispensed (ml), big-endian uint16
    - Byte 6: Port state byte
        - Bits 6-7: Port count (0-3)
        - Bits 4-5: Port index (0-3)
        - Bits 0-1: Port state (0-3)
    - Bytes 7-26: Beer name (20 bytes, UTF-8, null-padded)
"""

import re
from typing import Optional

from .models import KegtronReading, PortState


# Kegtron uses manufacturer ID 0xFFFF for their BLE advertisements
KEGTRON_MANUFACTURER_ID = 0xFFFF

# Expected length of Kegtron manufacturer data
KEGTRON_DATA_LENGTH = 27


class ParseError(Exception):
    """Raised when parsing Kegtron data fails."""
    pass


def parse_manufacturer_data(data: bytes) -> KegtronReading:
    """
    Parse Kegtron BLE manufacturer data into a KegtronReading.

    Kegtron devices broadcast their status via BLE manufacturer-specific
    data using manufacturer ID 0xFFFF. This function parses that raw
    byte data into a structured KegtronReading object.

    Args:
        data: Raw manufacturer data bytes (must be exactly 27 bytes).

    Returns:
        KegtronReading object containing the parsed data.

    Raises:
        ParseError: If the data length is incorrect or parsing fails.

    Example:
        >>> # Example raw data (27 bytes)
        >>> raw_data = bytes([
        ...     0x4C, 0x6E,  # keg_size_ml = 19566
        ...     0x4C, 0x6E,  # volume_start_ml = 19566
        ...     0x13, 0x88,  # volume_dispensed_ml = 5000
        ...     0x41,        # port_state_byte (1 port, index 0, enabled)
        ...     # Beer name: "Kolsch" + null padding
        ...     0x4B, 0x6F, 0x6C, 0x73, 0x63, 0x68, 0x00, 0x00,
        ...     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        ...     0x00, 0x00, 0x00, 0x00
        ... ])
        >>> reading = parse_manufacturer_data(raw_data)
        >>> reading.beer_name
        'Kolsch'
    """
    if len(data) != KEGTRON_DATA_LENGTH:
        raise ParseError(
            f"Invalid data length: expected {KEGTRON_DATA_LENGTH} bytes, "
            f"got {len(data)} bytes"
        )

    try:
        # Parse volume fields (big-endian uint16)
        keg_size_ml = int.from_bytes(data[0:2], byteorder='big')
        volume_start_ml = int.from_bytes(data[2:4], byteorder='big')
        volume_dispensed_ml = int.from_bytes(data[4:6], byteorder='big')

        # Parse port state byte
        port_state_byte = data[6]
        port_count = (port_state_byte >> 6) & 0b11
        port_index = (port_state_byte >> 4) & 0b11
        port_state_value = port_state_byte & 0b11

        # Parse beer name (null-terminated UTF-8 string)
        beer_name = data[7:27].decode('utf-8', errors='replace').rstrip('\x00')

        return KegtronReading(
            keg_size_ml=keg_size_ml,
            volume_start_ml=volume_start_ml,
            volume_dispensed_ml=volume_dispensed_ml,
            port_count=port_count,
            port_index=port_index,
            port_state=PortState(port_state_value),
            beer_name=beer_name,
        )
    except Exception as e:
        raise ParseError(f"Failed to parse manufacturer data: {e}") from e


def extract_device_id(device_name: str) -> Optional[str]:
    """
    Extract the device ID from a Kegtron device name.

    Kegtron devices have names in the format "Kegtron XXXXXX" where
    XXXXXX is a 6-character hexadecimal device ID.

    Args:
        device_name: The BLE device name (e.g., "Kegtron F1EDC6").

    Returns:
        The extracted device ID in uppercase (e.g., "F1EDC6"),
        or None if the name doesn't match the expected format.

    Example:
        >>> extract_device_id("Kegtron F1EDC6")
        'F1EDC6'
        >>> extract_device_id("kegtron abc123")
        'ABC123'
        >>> extract_device_id("Some Other Device")
        None
    """
    if not device_name:
        return None

    match = re.search(r'Kegtron\s+([A-Fa-f0-9]+)', device_name, re.IGNORECASE)
    return match.group(1).upper() if match else None


def is_kegtron_device(device_name: Optional[str]) -> bool:
    """
    Check if a BLE device name indicates a Kegtron device.

    Args:
        device_name: The BLE device name to check.

    Returns:
        True if the device name contains "Kegtron", False otherwise.

    Example:
        >>> is_kegtron_device("Kegtron F1EDC6")
        True
        >>> is_kegtron_device("kegtron ABC123")
        True
        >>> is_kegtron_device("Some Other Device")
        False
        >>> is_kegtron_device(None)
        False
    """
    if not device_name:
        return False
    return "kegtron" in device_name.lower()


def has_kegtron_data(manufacturer_data: dict) -> bool:
    """
    Check if BLE manufacturer data contains Kegtron data.

    Args:
        manufacturer_data: Dictionary of manufacturer ID to data bytes
            from BLE advertisement.

    Returns:
        True if Kegtron manufacturer data (ID 0xFFFF) is present.

    Example:
        >>> has_kegtron_data({0xFFFF: b'...'})
        True
        >>> has_kegtron_data({0x004C: b'...'})  # Apple
        False
    """
    return KEGTRON_MANUFACTURER_ID in manufacturer_data
