"""Tests for the kegtron.scanner module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from kegtron.scanner import (
    KegtronScanner,
    scan_device,
    scan_devices,
)
from kegtron.models import KegtronDevice, KegtronReading, PortState
from kegtron.parser import KEGTRON_MANUFACTURER_ID


def create_mock_manufacturer_data(
    keg_size_ml: int = 19550,
    volume_start_ml: int = 19550,
    volume_dispensed_ml: int = 5000,
    port_count: int = 1,
    port_index: int = 0,
    port_state: int = 1,
    beer_name: str = "Test IPA",
) -> bytes:
    """Create mock manufacturer data bytes."""
    data = bytearray(27)
    data[0:2] = keg_size_ml.to_bytes(2, byteorder='big')
    data[2:4] = volume_start_ml.to_bytes(2, byteorder='big')
    data[4:6] = volume_dispensed_ml.to_bytes(2, byteorder='big')
    port_state_byte = ((port_count & 0b11) << 6) | ((port_index & 0b11) << 4) | (port_state & 0b11)
    data[6] = port_state_byte
    name_bytes = beer_name.encode('utf-8')[:20]
    data[7:7 + len(name_bytes)] = name_bytes
    return bytes(data)


def create_mock_ble_device(name: str = "Kegtron F1EDC6"):
    """Create a mock BLE device."""
    device = MagicMock()
    device.name = name
    return device


def create_mock_adv_data(manufacturer_data: dict = None):
    """Create mock advertisement data."""
    adv = MagicMock()
    adv.manufacturer_data = manufacturer_data or {}
    return adv


class TestScanDevices:
    """Tests for scan_devices function."""

    @pytest.mark.asyncio
    async def test_scan_no_devices(self):
        """Test scanning when no devices are found."""
        mock_scanner = MagicMock()
        mock_scanner.discovered_devices_and_advertisement_data = {}

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_bleak.return_value.__aenter__ = AsyncMock(return_value=mock_scanner)
            mock_bleak.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value.discovered_devices_and_advertisement_data = {}

            devices = await scan_devices(timeout=0.01)

            assert devices == []

    @pytest.mark.asyncio
    async def test_scan_finds_kegtron_device(self):
        """Test scanning finds a Kegtron device."""
        mock_ble_device = create_mock_ble_device("Kegtron F1EDC6")
        mock_adv_data = create_mock_adv_data({
            KEGTRON_MANUFACTURER_ID: create_mock_manufacturer_data(beer_name="Kolsch")
        })

        discovered = {
            "AA:BB:CC:DD:EE:FF": (mock_ble_device, mock_adv_data)
        }

        mock_scanner = MagicMock()
        mock_scanner.discovered_devices_and_advertisement_data = discovered

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            # Make the scanner's discovered_devices available after context
            mock_bleak.return_value.discovered_devices_and_advertisement_data = discovered

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                # Patch at module level to access after context manager
                with patch.object(mock_scanner, 'discovered_devices_and_advertisement_data', discovered):
                    devices = await scan_devices(timeout=0.01)

        assert len(devices) == 1
        assert devices[0].device_id == "F1EDC6"
        assert devices[0].reading.beer_name == "Kolsch"
        assert devices[0].ble_address == "AA:BB:CC:DD:EE:FF"

    @pytest.mark.asyncio
    async def test_scan_filters_non_kegtron_devices(self):
        """Test that non-Kegtron devices are filtered out."""
        mock_kegtron = create_mock_ble_device("Kegtron ABC123")
        mock_other = create_mock_ble_device("iPhone")

        mock_kegtron_adv = create_mock_adv_data({
            KEGTRON_MANUFACTURER_ID: create_mock_manufacturer_data()
        })
        mock_other_adv = create_mock_adv_data({0x004C: b"apple_data"})

        discovered = {
            "11:22:33:44:55:66": (mock_kegtron, mock_kegtron_adv),
            "AA:BB:CC:DD:EE:FF": (mock_other, mock_other_adv),
        }

        mock_scanner = MagicMock()
        mock_scanner.discovered_devices_and_advertisement_data = discovered

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                devices = await scan_devices(timeout=0.01)

        assert len(devices) == 1
        assert devices[0].device_id == "ABC123"

    @pytest.mark.asyncio
    async def test_scan_filters_by_device_id(self):
        """Test filtering by specific device ID."""
        mock_device1 = create_mock_ble_device("Kegtron ABC123")
        mock_device2 = create_mock_ble_device("Kegtron DEF456")

        mock_adv1 = create_mock_adv_data({
            KEGTRON_MANUFACTURER_ID: create_mock_manufacturer_data(beer_name="IPA")
        })
        mock_adv2 = create_mock_adv_data({
            KEGTRON_MANUFACTURER_ID: create_mock_manufacturer_data(beer_name="Lager")
        })

        discovered = {
            "11:22:33:44:55:66": (mock_device1, mock_adv1),
            "AA:BB:CC:DD:EE:FF": (mock_device2, mock_adv2),
        }

        mock_scanner = MagicMock()
        mock_scanner.discovered_devices_and_advertisement_data = discovered

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                devices = await scan_devices(timeout=0.01, device_id="DEF456")

        assert len(devices) == 1
        assert devices[0].device_id == "DEF456"
        assert devices[0].reading.beer_name == "Lager"

    @pytest.mark.asyncio
    async def test_scan_filter_case_insensitive(self):
        """Test device ID filter is case insensitive."""
        mock_device = create_mock_ble_device("Kegtron ABC123")
        mock_adv = create_mock_adv_data({
            KEGTRON_MANUFACTURER_ID: create_mock_manufacturer_data()
        })

        discovered = {"11:22:33:44:55:66": (mock_device, mock_adv)}

        mock_scanner = MagicMock()
        mock_scanner.discovered_devices_and_advertisement_data = discovered

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                devices = await scan_devices(timeout=0.01, device_id="abc123")

        assert len(devices) == 1

    @pytest.mark.asyncio
    async def test_scan_skips_device_without_manufacturer_data(self):
        """Test devices without manufacturer data are skipped."""
        mock_device = create_mock_ble_device("Kegtron F1EDC6")
        mock_adv = create_mock_adv_data({})  # No manufacturer data

        discovered = {"11:22:33:44:55:66": (mock_device, mock_adv)}

        mock_scanner = MagicMock()
        mock_scanner.discovered_devices_and_advertisement_data = discovered

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                devices = await scan_devices(timeout=0.01)

        assert len(devices) == 0

    @pytest.mark.asyncio
    async def test_scan_skips_invalid_manufacturer_data(self):
        """Test devices with invalid manufacturer data are skipped."""
        mock_device = create_mock_ble_device("Kegtron F1EDC6")
        mock_adv = create_mock_adv_data({
            KEGTRON_MANUFACTURER_ID: b"short"  # Invalid length
        })

        discovered = {"11:22:33:44:55:66": (mock_device, mock_adv)}

        mock_scanner = MagicMock()
        mock_scanner.discovered_devices_and_advertisement_data = discovered

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                devices = await scan_devices(timeout=0.01)

        assert len(devices) == 0

    @pytest.mark.asyncio
    async def test_scan_skips_device_without_valid_id(self):
        """Test devices without extractable ID are skipped."""
        mock_device = create_mock_ble_device("Kegtron")  # No ID in name
        mock_adv = create_mock_adv_data({
            KEGTRON_MANUFACTURER_ID: create_mock_manufacturer_data()
        })

        discovered = {"11:22:33:44:55:66": (mock_device, mock_adv)}

        mock_scanner = MagicMock()
        mock_scanner.discovered_devices_and_advertisement_data = discovered

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                devices = await scan_devices(timeout=0.01)

        assert len(devices) == 0


class TestScanDevice:
    """Tests for scan_device function."""

    @pytest.mark.asyncio
    async def test_scan_device_found(self):
        """Test scan_device returns device when found."""
        mock_device = create_mock_ble_device("Kegtron F1EDC6")
        mock_adv = create_mock_adv_data({
            KEGTRON_MANUFACTURER_ID: create_mock_manufacturer_data(beer_name="Stout")
        })

        discovered = {"11:22:33:44:55:66": (mock_device, mock_adv)}

        mock_scanner = MagicMock()
        mock_scanner.discovered_devices_and_advertisement_data = discovered

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                device = await scan_device("F1EDC6", timeout=0.01)

        assert device is not None
        assert device.device_id == "F1EDC6"
        assert device.reading.beer_name == "Stout"

    @pytest.mark.asyncio
    async def test_scan_device_not_found(self):
        """Test scan_device returns None when device not found."""
        mock_scanner = MagicMock()
        mock_scanner.discovered_devices_and_advertisement_data = {}

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                device = await scan_device("NOTFOUND", timeout=0.01)

        assert device is None


class TestKegtronScanner:
    """Tests for KegtronScanner class."""

    def test_init(self):
        """Test scanner initialization."""
        scanner = KegtronScanner()
        assert scanner._callbacks == []
        assert scanner._last_readings == {}
        assert scanner.known_devices == []

    def test_on_device_found_decorator(self):
        """Test on_device_found as decorator."""
        scanner = KegtronScanner()

        @scanner.on_device_found
        def my_callback(device):
            pass

        assert len(scanner._callbacks) == 1
        assert scanner._callbacks[0] == my_callback

    def test_on_device_found_multiple_callbacks(self):
        """Test registering multiple callbacks."""
        scanner = KegtronScanner()

        def callback1(device):
            pass

        def callback2(device):
            pass

        scanner.on_device_found(callback1)
        scanner.on_device_found(callback2)

        assert len(scanner._callbacks) == 2

    @pytest.mark.asyncio
    async def test_scan_triggers_callbacks(self):
        """Test that scan triggers registered callbacks."""
        scanner = KegtronScanner()
        callback_results = []

        @scanner.on_device_found
        def my_callback(device):
            callback_results.append(device.device_id)

        mock_device = create_mock_ble_device("Kegtron ABC123")
        mock_adv = create_mock_adv_data({
            KEGTRON_MANUFACTURER_ID: create_mock_manufacturer_data()
        })

        discovered = {"11:22:33:44:55:66": (mock_device, mock_adv)}

        mock_scanner_obj = MagicMock()
        mock_scanner_obj.discovered_devices_and_advertisement_data = discovered

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner_obj)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                await scanner.scan(timeout=0.01)

        assert len(callback_results) == 1
        assert callback_results[0] == "ABC123"

    @pytest.mark.asyncio
    async def test_scan_handles_callback_exception(self):
        """Test that callback exceptions don't break scanning."""
        scanner = KegtronScanner()

        @scanner.on_device_found
        def bad_callback(device):
            raise ValueError("Callback error!")

        mock_device = create_mock_ble_device("Kegtron ABC123")
        mock_adv = create_mock_adv_data({
            KEGTRON_MANUFACTURER_ID: create_mock_manufacturer_data()
        })

        discovered = {"11:22:33:44:55:66": (mock_device, mock_adv)}

        mock_scanner_obj = MagicMock()
        mock_scanner_obj.discovered_devices_and_advertisement_data = discovered

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner_obj)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                # Should not raise despite callback error
                devices = await scanner.scan(timeout=0.01)

        assert len(devices) == 1

    @pytest.mark.asyncio
    async def test_scan_updates_last_readings(self):
        """Test that scan updates last readings."""
        scanner = KegtronScanner()

        mock_device = create_mock_ble_device("Kegtron A1B2C3")
        mock_adv = create_mock_adv_data({
            KEGTRON_MANUFACTURER_ID: create_mock_manufacturer_data(beer_name="Porter")
        })

        discovered = {"11:22:33:44:55:66": (mock_device, mock_adv)}

        mock_scanner_obj = MagicMock()
        mock_scanner_obj.discovered_devices_and_advertisement_data = discovered

        with patch('kegtron.scanner.BleakScanner') as mock_bleak:
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_scanner_obj)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_bleak.return_value = mock_context

            with patch('kegtron.scanner.asyncio.sleep', new_callable=AsyncMock):
                await scanner.scan(timeout=0.01)

        assert "A1B2C3" in scanner.known_devices

    def test_get_last_reading_exists(self):
        """Test get_last_reading when device was seen."""
        scanner = KegtronScanner()

        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=5000,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Test",
        )
        device = KegtronDevice(
            device_id="ABC123",
            device_name="Kegtron ABC123",
            ble_address="11:22:33:44:55:66",
            reading=reading,
        )
        scanner._last_readings["ABC123"] = device

        result = scanner.get_last_reading("ABC123")
        assert result is not None
        assert result.device_id == "ABC123"

    def test_get_last_reading_case_insensitive(self):
        """Test get_last_reading is case insensitive."""
        scanner = KegtronScanner()

        reading = KegtronReading(
            keg_size_ml=19550,
            volume_start_ml=19550,
            volume_dispensed_ml=5000,
            port_count=1,
            port_index=0,
            port_state=PortState.ENABLED,
            beer_name="Test",
        )
        device = KegtronDevice(
            device_id="ABC123",
            device_name="Kegtron ABC123",
            ble_address="11:22:33:44:55:66",
            reading=reading,
        )
        scanner._last_readings["ABC123"] = device

        # Should find with lowercase
        result = scanner.get_last_reading("abc123")
        assert result is not None

    def test_get_last_reading_not_found(self):
        """Test get_last_reading returns None for unknown device."""
        scanner = KegtronScanner()
        result = scanner.get_last_reading("UNKNOWN")
        assert result is None

    def test_known_devices_empty(self):
        """Test known_devices when no devices seen."""
        scanner = KegtronScanner()
        assert scanner.known_devices == []

    def test_known_devices_with_devices(self):
        """Test known_devices returns all seen device IDs."""
        scanner = KegtronScanner()
        scanner._last_readings["ABC123"] = MagicMock()
        scanner._last_readings["DEF456"] = MagicMock()

        known = scanner.known_devices
        assert len(known) == 2
        assert "ABC123" in known
        assert "DEF456" in known
