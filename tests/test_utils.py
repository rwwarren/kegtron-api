"""Tests for the kegtron.utils module."""

import pytest

from kegtron.utils import (
    calculate_drinks_remaining,
    detect_new_keg,
    detect_pour,
    estimate_pour_time_seconds,
    format_volume,
    ml_to_gallons,
    ml_to_liters,
    ml_to_oz,
    ml_to_pints,
    oz_to_ml,
)


class TestVolumeConversions:
    """Tests for volume conversion functions."""

    def test_ml_to_oz(self):
        """Test milliliters to ounces conversion."""
        assert abs(ml_to_oz(29.5735) - 1.0) < 0.001
        assert abs(ml_to_oz(354.882) - 12.0) < 0.01
        assert ml_to_oz(0) == 0

    def test_oz_to_ml(self):
        """Test ounces to milliliters conversion."""
        assert abs(oz_to_ml(1.0) - 29.5735) < 0.001
        assert abs(oz_to_ml(12.0) - 354.882) < 0.01
        assert oz_to_ml(0) == 0

    def test_ml_to_gallons(self):
        """Test milliliters to gallons conversion."""
        assert abs(ml_to_gallons(3785.41) - 1.0) < 0.001
        assert ml_to_gallons(0) == 0

    def test_ml_to_liters(self):
        """Test milliliters to liters conversion."""
        assert ml_to_liters(1000) == 1.0
        assert ml_to_liters(1500) == 1.5
        assert ml_to_liters(0) == 0

    def test_ml_to_pints(self):
        """Test milliliters to pints conversion."""
        assert abs(ml_to_pints(473.176) - 1.0) < 0.001
        assert ml_to_pints(0) == 0

    def test_round_trip_conversion(self):
        """Test that oz->ml->oz is consistent."""
        original = 12.0
        converted = ml_to_oz(oz_to_ml(original))
        assert abs(converted - original) < 0.001


class TestFormatVolume:
    """Tests for format_volume function."""

    def test_format_oz(self):
        """Test formatting as ounces."""
        assert format_volume(1000, "oz") == "33.8 oz"
        assert format_volume(1000, "oz", precision=0) == "34 oz"

    def test_format_ml(self):
        """Test formatting as milliliters."""
        assert format_volume(1000, "ml") == "1000.0 ml"
        assert format_volume(1500, "ml", precision=0) == "1500 ml"

    def test_format_liters(self):
        """Test formatting as liters."""
        assert format_volume(5000, "l") == "5.0 L"
        assert format_volume(2500, "l", precision=2) == "2.50 L"

    def test_format_gallons(self):
        """Test formatting as gallons."""
        assert format_volume(3785.41, "gal", precision=1) == "1.0 gal"

    def test_format_pints(self):
        """Test formatting as pints."""
        assert format_volume(946.352, "pint", precision=1) == "2.0 pints"

    def test_format_invalid_unit(self):
        """Test that invalid unit raises ValueError."""
        with pytest.raises(ValueError, match="Unknown unit"):
            format_volume(1000, "invalid")

    def test_format_case_insensitive(self):
        """Test that unit is case-insensitive."""
        assert format_volume(1000, "OZ") == format_volume(1000, "oz")
        assert format_volume(1000, "ML") == format_volume(1000, "ml")


class TestCalculateDrinksRemaining:
    """Tests for calculate_drinks_remaining function."""

    def test_default_drink_size(self):
        """Test with default 12oz drink size."""
        # 10000 ml / 354.882 ml = ~28 drinks
        drinks = calculate_drinks_remaining(10000)
        assert drinks == 28

    def test_pint_size(self):
        """Test with pint-sized drinks."""
        # 10000 ml / 473.176 ml = ~21 drinks
        drinks = calculate_drinks_remaining(10000, drink_size_ml=473.176)
        assert drinks == 21

    def test_zero_volume(self):
        """Test with zero remaining volume."""
        assert calculate_drinks_remaining(0) == 0

    def test_zero_drink_size(self):
        """Test with zero drink size returns 0."""
        assert calculate_drinks_remaining(1000, drink_size_ml=0) == 0

    def test_fractional_drinks_floor(self):
        """Test that partial drinks are floored."""
        # Should floor, not round
        drinks = calculate_drinks_remaining(400, drink_size_ml=354.882)
        assert drinks == 1


class TestDetectPour:
    """Tests for detect_pour function."""

    def test_detect_normal_pour(self):
        """Test detecting a normal pour."""
        result = detect_pour(5100, 5000)
        assert result == 100

    def test_detect_large_pour(self):
        """Test detecting a large pour."""
        result = detect_pour(6000, 5000)
        assert result == 1000

    def test_below_threshold(self):
        """Test that small changes below threshold return None."""
        result = detect_pour(5010, 5000, min_pour_ml=30)
        assert result is None

    def test_no_change(self):
        """Test that no change returns None."""
        result = detect_pour(5000, 5000)
        assert result is None

    def test_decrease_returns_none(self):
        """Test that a decrease (new keg) returns None."""
        result = detect_pour(5000, 5100)
        assert result is None

    def test_custom_threshold(self):
        """Test with custom threshold."""
        # 20ml pour with 10ml threshold should detect
        result = detect_pour(5020, 5000, min_pour_ml=10)
        assert result == 20

        # 20ml pour with 50ml threshold should not detect
        result = detect_pour(5020, 5000, min_pour_ml=50)
        assert result is None


class TestDetectNewKeg:
    """Tests for detect_new_keg function."""

    def test_detect_start_volume_change(self):
        """Test detecting new keg by start volume change."""
        result = detect_new_keg(
            current_start_ml=19550,
            previous_start_ml=18927,
            current_dispensed_ml=0,
            previous_dispensed_ml=5000,
        )
        assert result is True

    def test_detect_dispensed_reset(self):
        """Test detecting new keg by dispensed reset."""
        result = detect_new_keg(
            current_start_ml=19550,
            previous_start_ml=19550,
            current_dispensed_ml=100,
            previous_dispensed_ml=5000,
        )
        assert result is True

    def test_normal_pour_not_new_keg(self):
        """Test that normal pour doesn't trigger new keg detection."""
        result = detect_new_keg(
            current_start_ml=19550,
            previous_start_ml=19550,
            current_dispensed_ml=5100,
            previous_dispensed_ml=5000,
        )
        assert result is False

    def test_no_change_not_new_keg(self):
        """Test that no change doesn't trigger new keg detection."""
        result = detect_new_keg(
            current_start_ml=19550,
            previous_start_ml=19550,
            current_dispensed_ml=5000,
            previous_dispensed_ml=5000,
        )
        assert result is False

    def test_custom_reset_threshold(self):
        """Test with custom reset threshold."""
        # 500ml drop with 1000ml threshold should NOT detect
        result = detect_new_keg(
            current_start_ml=19550,
            previous_start_ml=19550,
            current_dispensed_ml=4500,
            previous_dispensed_ml=5000,
            reset_threshold_ml=1000,
        )
        assert result is False

        # 500ml drop with 100ml threshold SHOULD detect
        result = detect_new_keg(
            current_start_ml=19550,
            previous_start_ml=19550,
            current_dispensed_ml=4500,
            previous_dispensed_ml=5000,
            reset_threshold_ml=100,
        )
        assert result is True


class TestEstimatePourTimeSeconds:
    """Tests for estimate_pour_time_seconds function."""

    def test_12oz_pour(self):
        """Test estimating time for 12oz pour."""
        # 354.882 ml at ~59.15 ml/s = ~6 seconds
        time = estimate_pour_time_seconds(354.882)
        assert abs(time - 6.0) < 0.5

    def test_pint_pour(self):
        """Test estimating time for pint pour."""
        # 473.176 ml at ~59.15 ml/s = ~8 seconds
        time = estimate_pour_time_seconds(473.176)
        assert abs(time - 8.0) < 0.5

    def test_zero_volume(self):
        """Test with zero volume."""
        assert estimate_pour_time_seconds(0) == 0

    def test_zero_flow_rate(self):
        """Test with zero flow rate returns 0."""
        assert estimate_pour_time_seconds(1000, flow_rate_ml_per_sec=0) == 0

    def test_custom_flow_rate(self):
        """Test with custom flow rate."""
        # 100ml at 10 ml/s = 10 seconds
        time = estimate_pour_time_seconds(100, flow_rate_ml_per_sec=10)
        assert time == 10.0
