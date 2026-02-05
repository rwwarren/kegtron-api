"""
BLE scanner for discovering Kegtron devices.

This module provides async functions to scan for Kegtron BLE devices
and retrieve their current status.

Requirements:
    - macOS: Bluetooth permission must be granted to the running application
    - Linux: Bluetooth must be enabled and accessible
    - Windows: Bluetooth must be enabled

Example:
    >>> import asyncio
    >>> from kegtron import scan_devices
    >>>
    >>> async def main():
    ...     devices = await scan_devices(timeout=10)
    ...     for device in devices:
    ...         print(f"{device.device_id}: {device.reading.beer_name}")
    ...         print(f"  {device.reading.percent_remaining:.1f}% remaining")
    ...
    >>> asyncio.run(main())
"""

import asyncio
import logging
from typing import List, Optional

from bleak import BleakScanner

from .models import KegtronDevice
from .parser import (
    KEGTRON_MANUFACTURER_ID,
    ParseError,
    extract_device_id,
    is_kegtron_device,
    parse_manufacturer_data,
)

logger = logging.getLogger(__name__)


async def scan_devices(
    timeout: float = 10.0,
    *,
    device_id: Optional[str] = None,
) -> List[KegtronDevice]:
    """
    Scan for Kegtron BLE devices.

    Performs a BLE scan for the specified duration and returns all
    discovered Kegtron devices with their current readings.

    Args:
        timeout: How long to scan in seconds. Longer timeouts increase
            the chance of discovering devices with weak signals.
            Default is 10 seconds.
        device_id: Optional device ID to filter for. If specified, only
            devices matching this ID will be returned.

    Returns:
        List of KegtronDevice objects for all discovered devices.
        Returns an empty list if no devices are found.

    Raises:
        BleakError: If Bluetooth is not available or not authorized.

    Example:
        >>> devices = await scan_devices(timeout=10)
        >>> for device in devices:
        ...     print(f"{device.device_id}: {device.reading.percent_remaining:.1f}%")

        >>> # Scan for a specific device
        >>> devices = await scan_devices(device_id="F1EDC6")
    """
    devices_found: List[KegtronDevice] = []

    logger.debug(f"Starting BLE scan (timeout={timeout}s)")

    async with BleakScanner() as scanner:
        await asyncio.sleep(timeout)

    discovered = scanner.discovered_devices_and_advertisement_data

    for address, (ble_device, adv_data) in discovered.items():
        if not is_kegtron_device(ble_device.name):
            continue

        if KEGTRON_MANUFACTURER_ID not in adv_data.manufacturer_data:
            logger.debug(f"Kegtron device {ble_device.name} has no manufacturer data")
            continue

        raw_data = adv_data.manufacturer_data[KEGTRON_MANUFACTURER_ID]

        try:
            reading = parse_manufacturer_data(raw_data)
        except ParseError as e:
            logger.warning(f"Failed to parse data from {ble_device.name}: {e}")
            continue

        dev_id = extract_device_id(ble_device.name)
        if not dev_id:
            logger.warning(f"Could not extract device ID from {ble_device.name}")
            continue

        # Filter by device_id if specified
        if device_id and dev_id.upper() != device_id.upper():
            continue

        device = KegtronDevice(
            device_id=dev_id,
            device_name=ble_device.name,
            ble_address=address,
            reading=reading,
        )
        devices_found.append(device)
        logger.debug(f"Found device: {device.device_id} ({device.reading.beer_name})")

    logger.debug(f"Scan complete: found {len(devices_found)} device(s)")
    return devices_found


async def scan_device(
    device_id: str,
    timeout: float = 10.0,
) -> Optional[KegtronDevice]:
    """
    Scan for a specific Kegtron device by ID.

    Convenience function to find a single device. Equivalent to
    calling scan_devices() with a device_id filter.

    Args:
        device_id: The device ID to search for (e.g., "F1EDC6").
        timeout: How long to scan in seconds.

    Returns:
        KegtronDevice if found, None otherwise.

    Example:
        >>> device = await scan_device("F1EDC6")
        >>> if device:
        ...     print(f"Found! {device.reading.percent_remaining:.1f}% remaining")
        ... else:
        ...     print("Device not found")
    """
    devices = await scan_devices(timeout=timeout, device_id=device_id)
    return devices[0] if devices else None


class KegtronScanner:
    """
    A reusable scanner for monitoring Kegtron devices.

    This class provides a stateful interface for scanning devices,
    with callbacks for device discovery and updates.

    Example:
        >>> scanner = KegtronScanner()
        >>>
        >>> @scanner.on_device_found
        >>> def handle_device(device: KegtronDevice):
        ...     print(f"Found: {device.device_id}")
        ...
        >>> await scanner.scan(timeout=30)
    """

    def __init__(self):
        self._callbacks: List[callable] = []
        self._last_readings: dict = {}

    def on_device_found(self, callback: callable) -> callable:
        """
        Register a callback for when a device is discovered.

        The callback will be called with a KegtronDevice argument
        each time a device is found during scanning.

        Args:
            callback: Function to call with KegtronDevice argument.

        Returns:
            The callback function (for use as a decorator).
        """
        self._callbacks.append(callback)
        return callback

    async def scan(self, timeout: float = 10.0) -> List[KegtronDevice]:
        """
        Perform a scan and trigger callbacks for discovered devices.

        Args:
            timeout: How long to scan in seconds.

        Returns:
            List of discovered KegtronDevice objects.
        """
        devices = await scan_devices(timeout=timeout)

        for device in devices:
            for callback in self._callbacks:
                try:
                    callback(device)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

            self._last_readings[device.device_id] = device

        return devices

    def get_last_reading(self, device_id: str) -> Optional[KegtronDevice]:
        """
        Get the last known reading for a device.

        Args:
            device_id: The device ID to look up.

        Returns:
            The last KegtronDevice reading, or None if never seen.
        """
        return self._last_readings.get(device_id.upper())

    @property
    def known_devices(self) -> List[str]:
        """List of device IDs that have been discovered."""
        return list(self._last_readings.keys())
