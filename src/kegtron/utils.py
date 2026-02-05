"""
Utility functions for working with Kegtron data.

This module provides helper functions for common operations like
unit conversion, pour detection, and data formatting.
"""

from typing import Optional


# Conversion constants
ML_PER_OZ = 29.5735
ML_PER_GALLON = 3785.41
ML_PER_LITER = 1000.0
ML_PER_PINT = 473.176


def ml_to_oz(ml: float) -> float:
    """
    Convert milliliters to fluid ounces.

    Args:
        ml: Volume in milliliters.

    Returns:
        Volume in fluid ounces.

    Example:
        >>> ml_to_oz(1000)
        33.814...
    """
    return ml / ML_PER_OZ


def oz_to_ml(oz: float) -> float:
    """
    Convert fluid ounces to milliliters.

    Args:
        oz: Volume in fluid ounces.

    Returns:
        Volume in milliliters.

    Example:
        >>> oz_to_ml(12)
        354.882
    """
    return oz * ML_PER_OZ


def ml_to_gallons(ml: float) -> float:
    """
    Convert milliliters to gallons.

    Args:
        ml: Volume in milliliters.

    Returns:
        Volume in gallons.

    Example:
        >>> ml_to_gallons(3785.41)
        1.0
    """
    return ml / ML_PER_GALLON


def ml_to_liters(ml: float) -> float:
    """
    Convert milliliters to liters.

    Args:
        ml: Volume in milliliters.

    Returns:
        Volume in liters.

    Example:
        >>> ml_to_liters(1500)
        1.5
    """
    return ml / ML_PER_LITER


def ml_to_pints(ml: float) -> float:
    """
    Convert milliliters to pints.

    Args:
        ml: Volume in milliliters.

    Returns:
        Volume in pints.

    Example:
        >>> ml_to_pints(473.176)
        1.0
    """
    return ml / ML_PER_PINT


def calculate_drinks_remaining(
    volume_ml: float,
    drink_size_ml: float = 354.882,  # 12 oz default
) -> int:
    """
    Calculate the number of drinks remaining.

    Args:
        volume_ml: Remaining volume in milliliters.
        drink_size_ml: Size of one drink in milliliters.
            Default is 354.882 ml (12 oz).

    Returns:
        Number of full drinks remaining.

    Example:
        >>> calculate_drinks_remaining(10000)  # ~28 12oz drinks
        28
        >>> calculate_drinks_remaining(10000, drink_size_ml=473.176)  # pints
        21
    """
    if drink_size_ml <= 0:
        return 0
    return int(volume_ml / drink_size_ml)


def format_volume(
    ml: float,
    unit: str = "oz",
    precision: int = 1,
) -> str:
    """
    Format a volume for display.

    Args:
        ml: Volume in milliliters.
        unit: Target unit ("oz", "ml", "l", "gal", "pint").
        precision: Decimal places to show.

    Returns:
        Formatted string with unit suffix.

    Example:
        >>> format_volume(1000, "oz")
        '33.8 oz'
        >>> format_volume(5000, "l")
        '5.0 L'
    """
    converters = {
        "oz": (ml_to_oz, "oz"),
        "ml": (lambda x: x, "ml"),
        "l": (ml_to_liters, "L"),
        "gal": (ml_to_gallons, "gal"),
        "pint": (ml_to_pints, "pints"),
    }

    if unit.lower() not in converters:
        raise ValueError(f"Unknown unit: {unit}. Use one of: {list(converters.keys())}")

    converter, suffix = converters[unit.lower()]
    value = converter(ml)
    return f"{value:.{precision}f} {suffix}"


def detect_pour(
    current_dispensed_ml: int,
    previous_dispensed_ml: int,
    min_pour_ml: int = 30,
) -> Optional[int]:
    """
    Detect if a pour occurred between two readings.

    A pour is detected when the dispensed volume increases by at
    least the minimum pour threshold.

    Args:
        current_dispensed_ml: Current volume dispensed reading.
        previous_dispensed_ml: Previous volume dispensed reading.
        min_pour_ml: Minimum volume increase to count as a pour.
            Default is 30ml (~1 oz) to filter out noise.

    Returns:
        The pour amount in ml if a pour was detected, None otherwise.

    Example:
        >>> detect_pour(5100, 5000)
        100
        >>> detect_pour(5010, 5000)  # Below threshold
        None
        >>> detect_pour(5000, 5100)  # Decrease (new keg?)
        None
    """
    diff = current_dispensed_ml - previous_dispensed_ml
    if diff >= min_pour_ml:
        return diff
    return None


def detect_new_keg(
    current_start_ml: int,
    previous_start_ml: int,
    current_dispensed_ml: int,
    previous_dispensed_ml: int,
    reset_threshold_ml: int = 1000,
) -> bool:
    """
    Detect if a new keg has been tapped.

    A new keg is detected when either:
    1. The volume_start_ml changes (different keg size/fill)
    2. The volume_dispensed drops significantly (keg was reset)

    Args:
        current_start_ml: Current volume start reading.
        previous_start_ml: Previous volume start reading.
        current_dispensed_ml: Current volume dispensed reading.
        previous_dispensed_ml: Previous volume dispensed reading.
        reset_threshold_ml: Minimum decrease in dispensed to detect reset.

    Returns:
        True if a new keg was detected, False otherwise.

    Example:
        >>> # Start volume changed
        >>> detect_new_keg(19550, 18927, 0, 5000)
        True
        >>> # Dispensed dropped significantly
        >>> detect_new_keg(19550, 19550, 100, 5000)
        True
        >>> # Normal pour
        >>> detect_new_keg(19550, 19550, 5100, 5000)
        False
    """
    # Check if volume_start changed
    if current_start_ml != previous_start_ml:
        return True

    # Check if dispensed dropped significantly (reset)
    if previous_dispensed_ml - current_dispensed_ml > reset_threshold_ml:
        return True

    return False


def estimate_pour_time_seconds(volume_ml: float, flow_rate_ml_per_sec: float = 59.15) -> float:
    """
    Estimate the time to pour a given volume.

    Args:
        volume_ml: Volume to pour in milliliters.
        flow_rate_ml_per_sec: Pour rate in ml/second.
            Default is ~59.15 ml/s (2 oz/second).

    Returns:
        Estimated pour time in seconds.

    Example:
        >>> estimate_pour_time_seconds(354.882)  # 12 oz
        6.0...
    """
    if flow_rate_ml_per_sec <= 0:
        return 0.0
    return volume_ml / flow_rate_ml_per_sec
