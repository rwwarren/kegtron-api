"""
Data models for Kegtron devices.

This module provides dataclasses representing Kegtron device data
parsed from BLE manufacturer advertisements.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class PortState(IntEnum):
    """
    Kegtron port state values.

    Indicates the current operational state of a Kegtron port.
    """
    DISABLED = 0
    ENABLED = 1
    UNKNOWN_2 = 2
    UNKNOWN_3 = 3


@dataclass
class KegtronReading:
    """
    Represents a single reading from a Kegtron device.

    This data is parsed from the BLE manufacturer data broadcast
    by Kegtron devices (manufacturer ID 0xFFFF).

    Attributes:
        keg_size_ml: The configured keg size in milliliters.
        volume_start_ml: The starting volume when the keg was tapped, in milliliters.
        volume_dispensed_ml: Total volume dispensed from this keg, in milliliters.
        port_count: Number of ports on this Kegtron device (1 or 2).
        port_index: Index of this port (0 or 1 for dual-port devices).
        port_state: Current state of this port (see PortState enum).
        beer_name: Name/label configured for this port (up to 20 characters).

    Example:
        >>> reading = KegtronReading(
        ...     keg_size_ml=19550,
        ...     volume_start_ml=19550,
        ...     volume_dispensed_ml=5000,
        ...     port_count=1,
        ...     port_index=0,
        ...     port_state=PortState.ENABLED,
        ...     beer_name="IPA"
        ... )
        >>> reading.volume_remaining_ml
        14550
        >>> reading.percent_remaining
        74.42...
    """
    keg_size_ml: int
    volume_start_ml: int
    volume_dispensed_ml: int
    port_count: int
    port_index: int
    port_state: PortState
    beer_name: str

    @property
    def volume_remaining_ml(self) -> int:
        """Calculate the remaining volume in milliliters."""
        return max(0, self.volume_start_ml - self.volume_dispensed_ml)

    @property
    def percent_remaining(self) -> float:
        """Calculate the percentage of beer remaining in the keg."""
        if self.volume_start_ml <= 0:
            return 0.0
        return (self.volume_remaining_ml / self.volume_start_ml) * 100

    @property
    def percent_dispensed(self) -> float:
        """Calculate the percentage of beer that has been dispensed."""
        return 100.0 - self.percent_remaining

    @property
    def is_empty(self) -> bool:
        """Check if the keg is empty (0% remaining)."""
        return self.volume_remaining_ml <= 0

    @property
    def is_low(self, threshold: float = 15.0) -> bool:
        """Check if the keg is running low (below threshold %)."""
        return self.percent_remaining < threshold

    def volume_remaining_oz(self) -> float:
        """Get the remaining volume in fluid ounces."""
        return self.volume_remaining_ml / 29.5735

    def volume_remaining_gallons(self) -> float:
        """Get the remaining volume in gallons."""
        return self.volume_remaining_ml / 3785.41


@dataclass
class KegtronDevice:
    """
    Represents a discovered Kegtron BLE device.

    Combines the BLE device information with the parsed reading data.

    Attributes:
        device_id: The unique device identifier extracted from the device name
            (e.g., "F1EDC6" from "Kegtron F1EDC6").
        device_name: The full BLE device name (e.g., "Kegtron F1EDC6").
        ble_address: The BLE address/UUID of the device.
        reading: The parsed Kegtron reading data.

    Example:
        >>> device = KegtronDevice(
        ...     device_id="F1EDC6",
        ...     device_name="Kegtron F1EDC6",
        ...     ble_address="D7C00968-5CCB-5205-B250-9E1972F841ED",
        ...     reading=reading
        ... )
        >>> device.device_id
        'F1EDC6'
    """
    device_id: str
    device_name: str
    ble_address: str
    reading: KegtronReading

    def to_dict(self) -> dict:
        """
        Convert the device data to a dictionary.

        Useful for serialization or API responses.

        Returns:
            Dictionary containing all device and reading data.
        """
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "ble_address": self.ble_address,
            "keg_size_ml": self.reading.keg_size_ml,
            "volume_start_ml": self.reading.volume_start_ml,
            "volume_dispensed_ml": self.reading.volume_dispensed_ml,
            "volume_remaining_ml": self.reading.volume_remaining_ml,
            "percent_remaining": self.reading.percent_remaining,
            "port_count": self.reading.port_count,
            "port_index": self.reading.port_index,
            "port_state": self.reading.port_state,
            "beer_name": self.reading.beer_name,
        }


# Common keg sizes in milliliters
class KegSize:
    """
    Common keg sizes in milliliters.

    Use these constants when configuring keg sizes or for reference.

    Example:
        >>> KegSize.SIXTH_BARREL
        19550
        >>> KegSize.to_gallons(KegSize.HALF_BARREL)
        15.5
    """
    MINI_KEG = 5000          # 5L / 1.32 gal
    CORNELIUS = 18927        # 5 gal
    SIXTH_BARREL = 19550     # 5.16 gal (1/6 bbl)
    QUARTER_BARREL = 29337   # 7.75 gal (1/4 bbl / pony keg)
    SLIM_QUARTER = 29337     # 7.75 gal (tall quarter)
    HALF_BARREL = 58674      # 15.5 gal (1/2 bbl / full size)

    @staticmethod
    def to_gallons(ml: int) -> float:
        """Convert milliliters to gallons."""
        return ml / 3785.41

    @staticmethod
    def to_liters(ml: int) -> float:
        """Convert milliliters to liters."""
        return ml / 1000.0
