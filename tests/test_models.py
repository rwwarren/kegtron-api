"""Tests for the kegtron.models module."""

import pytest

from kegtron.models import (
    KegSize,
    KegtronDevice,
    KegtronReading,
    PortState,
)


class TestKegtronReading:
    """Tests for KegtronReading dataclass."""

    @pytest.fixture
    def sample_reading(self) -> KegtronReading:
        """Create a sample reading for testing."""
        return KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=5000,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Test IPA",
        )

    def test_volume_remaining(self, sample_reading):
        """Test volume_remaining_ml calculation."""
        assert sample_reading.volume_remaining_ml == 14550

    def test_volume_remaining_empty(self):
        """Test volume_remaining when keg is empty."""
        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=19550,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Empty Keg",
        )
        assert reading.volume_remaining_ml == 0

    def test_volume_remaining_negative_clamps_to_zero(self):
        """Test that over-dispensed doesn't go negative."""
        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=20000,  # More than start
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Over Dispensed",
        )
        assert reading.volume_remaining_ml == 0

    def test_percent_remaining(self, sample_reading):
        """Test percent_remaining calculation."""
        # 14550 / 19550 * 100 = 74.42%
        assert abs(sample_reading.percent_remaining - 74.42) < 0.1

    def test_percent_remaining_full_keg(self):
        """Test percent_remaining when keg is full."""
        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=0,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Full Keg",
        )
        assert reading.percent_remaining == 100.0

    def test_percent_remaining_empty_keg(self):
        """Test percent_remaining when keg is empty."""
        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=19550,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Empty Keg",
        )
        assert reading.percent_remaining == 0.0

    def test_percent_remaining_zero_start(self):
        """Test percent_remaining handles zero start volume."""
        reading = KegtronReading(
            keg_size_ml=0,
            volume_start_ml=0,
            volume_dispensed_ml=0,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Zero",
        )
        assert reading.percent_remaining == 0.0

    def test_percent_dispensed(self, sample_reading):
        """Test percent_dispensed calculation."""
        assert abs(sample_reading.percent_dispensed - 25.58) < 0.1

    def test_is_empty_false(self, sample_reading):
        """Test is_empty when keg has beer."""
        assert sample_reading.is_empty is False

    def test_is_empty_true(self):
        """Test is_empty when keg is empty."""
        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=19550,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Empty",
        )
        assert reading.is_empty is True

    def test_is_low_false(self, sample_reading):
        """Test is_low when keg has plenty of beer (74% remaining)."""
        assert sample_reading.is_low() is False

    def test_is_low_true(self):
        """Test is_low when keg is below 15% remaining."""
        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=17000,  # ~13% remaining
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Low Keg",
        )
        assert reading.is_low() is True

    def test_is_low_custom_threshold(self, sample_reading):
        """Test is_low honors a custom threshold."""
        # sample_reading is ~74% remaining
        assert sample_reading.is_low(threshold=80.0) is True
        assert sample_reading.is_low(threshold=50.0) is False

    def test_is_low_threshold_boundary(self):
        """Test is_low is strictly less-than at the boundary."""
        reading = KegtronReading(
            keg_size_ml=100,
            volume_start_ml=100,
            volume_dispensed_ml=85,  # exactly 15% remaining
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Boundary",
        )
        # 15% is NOT below 15% threshold
        assert reading.is_low(threshold=15.0) is False
        assert reading.is_low(threshold=15.01) is True

    def test_volume_remaining_oz_empty(self):
        """Test volume_remaining_oz when keg is empty."""
        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=19550,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Empty",
        )
        assert reading.volume_remaining_oz() == 0.0

    def test_volume_remaining_gallons_empty(self):
        """Test volume_remaining_gallons when keg is empty."""
        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=19550,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Empty",
        )
        assert reading.volume_remaining_gallons() == 0.0

    def test_percent_dispensed_full(self):
        """percent_dispensed is 0 for a full keg."""
        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=0,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Full",
        )
        assert reading.percent_dispensed == 0.0

    def test_percent_dispensed_empty(self):
        """percent_dispensed is 100 for an empty keg."""
        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=19550,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Empty",
        )
        assert reading.percent_dispensed == 100.0

    def test_volume_remaining_oz(self, sample_reading):
        """Test volume_remaining_oz conversion."""
        # 14550 ml / 29.5735 = ~491.9 oz
        oz = sample_reading.volume_remaining_oz()
        assert abs(oz - 491.9) < 1

    def test_volume_remaining_gallons(self, sample_reading):
        """Test volume_remaining_gallons conversion."""
        # 14550 ml / 3785.41 = ~3.84 gal
        gal = sample_reading.volume_remaining_gallons()
        assert abs(gal - 3.84) < 0.1


class TestKegtronDevice:
    """Tests for KegtronDevice dataclass."""

    @pytest.fixture
    def sample_device(self) -> KegtronDevice:
        """Create a sample device for testing."""
        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=5000,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Test IPA",
        )
        return KegtronDevice(
            device_id="F1EDC6",
            device_name="Kegtron F1EDC6",
            ble_address="D7C00968-5CCB-5205-B250-9E1972F841ED",
            reading=reading,
        )

    def test_device_attributes(self, sample_device):
        """Test device attributes are set correctly."""
        assert sample_device.device_id == "F1EDC6"
        assert sample_device.device_name == "Kegtron F1EDC6"
        assert sample_device.ble_address == "D7C00968-5CCB-5205-B250-9E1972F841ED"
        assert sample_device.reading.beer_name == "Test IPA"

    def test_to_dict(self, sample_device):
        """Test to_dict serialization."""
        data = sample_device.to_dict()

        assert data["device_id"] == "F1EDC6"
        assert data["device_name"] == "Kegtron F1EDC6"
        assert data["ble_address"] == "D7C00968-5CCB-5205-B250-9E1972F841ED"
        assert data["keg_size_ml"] == 19550
        assert data["volume_start_ml"] == 19550
        assert data["volume_dispensed_ml"] == 5000
        assert data["volume_remaining_ml"] == 14550
        assert data["beer_name"] == "Test IPA"
        assert data["port_count"] == 1
        assert data["port_index"] == 0
        assert data["port_state"] == PortState.ENABLED
        assert abs(data["percent_remaining"] - 74.42) < 0.1

    def test_to_dict_is_json_serializable(self, sample_device):
        """to_dict output must be safe to json.dumps (port_state is IntEnum)."""
        import json
        # Should not raise - IntEnum serializes via its int value
        encoded = json.dumps(sample_device.to_dict())
        decoded = json.loads(encoded)
        assert decoded["port_state"] == 1


class TestPortState:
    """Tests for PortState enum."""

    def test_port_state_values(self):
        """Test PortState enum values."""
        assert PortState.DISABLED == 0
        assert PortState.ENABLED == 1
        assert PortState.UNKNOWN_2 == 2
        assert PortState.UNKNOWN_3 == 3

    def test_port_state_from_int(self):
        """Test creating PortState from int."""
        assert PortState(0) == PortState.DISABLED
        assert PortState(1) == PortState.ENABLED
        assert PortState(2) == PortState.UNKNOWN_2
        assert PortState(3) == PortState.UNKNOWN_3

    def test_port_state_invalid_value(self):
        """PortState raises for out-of-range ints."""
        with pytest.raises(ValueError):
            PortState(4)


class TestKegSize:
    """Tests for KegSize constants."""

    def test_keg_size_values(self):
        """Test KegSize constant values."""
        assert KegSize.MINI_KEG == 5000
        assert KegSize.CORNELIUS == 18927
        assert KegSize.SIXTH_BARREL == 19550
        assert KegSize.QUARTER_BARREL == 29337
        assert KegSize.SLIM_QUARTER == 29337
        assert KegSize.HALF_BARREL == 58674

    def test_to_gallons(self):
        """Test KegSize.to_gallons conversion across sizes."""
        assert abs(KegSize.to_gallons(KegSize.HALF_BARREL) - 15.5) < 0.1
        assert abs(KegSize.to_gallons(KegSize.QUARTER_BARREL) - 7.75) < 0.1
        assert abs(KegSize.to_gallons(KegSize.SIXTH_BARREL) - 5.16) < 0.1
        assert abs(KegSize.to_gallons(KegSize.CORNELIUS) - 5.0) < 0.1
        assert KegSize.to_gallons(0) == 0.0

    def test_to_liters(self):
        """Test KegSize.to_liters conversion across sizes."""
        assert abs(KegSize.to_liters(KegSize.MINI_KEG) - 5.0) < 0.01
        assert abs(KegSize.to_liters(KegSize.HALF_BARREL) - 58.674) < 0.01
        assert KegSize.to_liters(0) == 0.0
