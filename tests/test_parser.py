"""Tests for the kegtron.parser module."""

import pytest

from kegtron.parser import (
    KEGTRON_DATA_LENGTH,
    KEGTRON_MANUFACTURER_ID,
    ParseError,
    extract_device_id,
    has_kegtron_data,
    is_kegtron_device,
    parse_manufacturer_data,
)
from kegtron.models import PortState


def create_test_data(
    keg_size_ml: int = 19550,
    volume_start_ml: int = 19550,
    volume_dispensed_ml: int = 5000,
    port_count: int = 1,
    port_index: int = 0,
    port_state: int = 1,
    beer_name: str = "Kolsch",
) -> bytes:
    """Create test manufacturer data bytes."""
    data = bytearray(27)

    # Keg size (big-endian)
    data[0:2] = keg_size_ml.to_bytes(2, byteorder='big')

    # Volume start (big-endian)
    data[2:4] = volume_start_ml.to_bytes(2, byteorder='big')

    # Volume dispensed (big-endian)
    data[4:6] = volume_dispensed_ml.to_bytes(2, byteorder='big')

    # Port state byte
    port_state_byte = ((port_count & 0b11) << 6) | ((port_index & 0b11) << 4) | (port_state & 0b11)
    data[6] = port_state_byte

    # Beer name (null-padded)
    name_bytes = beer_name.encode('utf-8')[:20]
    data[7:7 + len(name_bytes)] = name_bytes

    return bytes(data)


class TestParseManufacturerData:
    """Tests for parse_manufacturer_data function."""

    def test_parse_valid_data(self):
        """Test parsing valid manufacturer data."""
        data = create_test_data(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=5000,
            beer_name="Test IPA",
        )

        reading = parse_manufacturer_data(data)

        assert reading.keg_size_ml == 19550
        assert reading.volume_start_ml == 19550
        assert reading.volume_dispensed_ml == 5000
        assert reading.beer_name == "Test IPA"
        assert reading.port_count == 1
        assert reading.port_index == 0
        assert reading.port_state == PortState.ENABLED

    def test_parse_different_keg_sizes(self):
        """Test parsing different keg sizes."""
        # Half barrel
        data = create_test_data(keg_size_ml=58674)
        reading = parse_manufacturer_data(data)
        assert reading.keg_size_ml == 58674

        # Cornelius
        data = create_test_data(keg_size_ml=18927)
        reading = parse_manufacturer_data(data)
        assert reading.keg_size_ml == 18927

    def test_parse_port_states(self):
        """Test parsing different port states."""
        for state_val in [0, 1, 2, 3]:
            data = create_test_data(port_state=state_val)
            reading = parse_manufacturer_data(data)
            assert reading.port_state == PortState(state_val)

    def test_parse_dual_port_device(self):
        """Test parsing data from dual-port devices."""
        # Port 0
        data = create_test_data(port_count=2, port_index=0)
        reading = parse_manufacturer_data(data)
        assert reading.port_count == 2
        assert reading.port_index == 0

        # Port 1
        data = create_test_data(port_count=2, port_index=1)
        reading = parse_manufacturer_data(data)
        assert reading.port_count == 2
        assert reading.port_index == 1

    def test_parse_empty_beer_name(self):
        """Test parsing with empty beer name."""
        data = create_test_data(beer_name="")
        reading = parse_manufacturer_data(data)
        assert reading.beer_name == ""

    def test_parse_max_length_beer_name(self):
        """Test parsing with maximum length beer name."""
        long_name = "A" * 20
        data = create_test_data(beer_name=long_name)
        reading = parse_manufacturer_data(data)
        assert reading.beer_name == long_name

    def test_parse_invalid_length_short(self):
        """Test that short data raises ParseError."""
        data = bytes(10)
        with pytest.raises(ParseError, match="Invalid data length"):
            parse_manufacturer_data(data)

    def test_parse_invalid_length_long(self):
        """Test that long data raises ParseError."""
        data = bytes(30)
        with pytest.raises(ParseError, match="Invalid data length"):
            parse_manufacturer_data(data)

    def test_parse_empty_data(self):
        """Test that empty data raises ParseError."""
        with pytest.raises(ParseError, match="Invalid data length"):
            parse_manufacturer_data(bytes())


class TestExtractDeviceId:
    """Tests for extract_device_id function."""

    def test_extract_valid_id(self):
        """Test extracting ID from valid device name."""
        assert extract_device_id("Kegtron F1EDC6") == "F1EDC6"
        assert extract_device_id("Kegtron ABC123") == "ABC123"

    def test_extract_lowercase(self):
        """Test extracting ID with lowercase input."""
        assert extract_device_id("kegtron abc123") == "ABC123"
        assert extract_device_id("KEGTRON f1edc6") == "F1EDC6"

    def test_extract_mixed_case(self):
        """Test extracting ID with mixed case."""
        assert extract_device_id("KeGtRoN AbC123") == "ABC123"

    def test_extract_with_extra_spaces(self):
        """Test extracting ID with extra whitespace."""
        assert extract_device_id("Kegtron  F1EDC6") == "F1EDC6"
        assert extract_device_id("Kegtron   ABC123") == "ABC123"

    def test_extract_invalid_name(self):
        """Test that invalid names return None."""
        assert extract_device_id("Some Other Device") is None
        assert extract_device_id("") is None
        assert extract_device_id("Kegtron") is None

    def test_extract_none_input(self):
        """Test that None input returns None."""
        assert extract_device_id(None) is None


class TestIsKegtronDevice:
    """Tests for is_kegtron_device function."""

    def test_valid_device_names(self):
        """Test that Kegtron names return True."""
        assert is_kegtron_device("Kegtron F1EDC6") is True
        assert is_kegtron_device("kegtron ABC123") is True
        assert is_kegtron_device("KEGTRON XYZ789") is True

    def test_invalid_device_names(self):
        """Test that non-Kegtron names return False."""
        assert is_kegtron_device("Some Other Device") is False
        assert is_kegtron_device("iPhone") is False
        assert is_kegtron_device("") is False

    def test_none_input(self):
        """Test that None returns False."""
        assert is_kegtron_device(None) is False


class TestHasKegtronData:
    """Tests for has_kegtron_data function."""

    def test_has_kegtron_manufacturer_id(self):
        """Test detection of Kegtron manufacturer ID."""
        assert has_kegtron_data({KEGTRON_MANUFACTURER_ID: b"data"}) is True

    def test_no_kegtron_manufacturer_id(self):
        """Test absence of Kegtron manufacturer ID."""
        assert has_kegtron_data({0x004C: b"apple_data"}) is False
        assert has_kegtron_data({}) is False

    def test_multiple_manufacturer_ids(self):
        """Test with multiple manufacturer IDs including Kegtron."""
        data = {
            0x004C: b"apple",
            KEGTRON_MANUFACTURER_ID: b"kegtron",
            0x0001: b"other",
        }
        assert has_kegtron_data(data) is True
