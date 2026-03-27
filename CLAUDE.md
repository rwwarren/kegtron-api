# kegtron-api

Python library for parsing Kegtron BLE keg monitoring device broadcasts and scanning for devices via Bluetooth Low Energy.

## Stack

- Python 3.9+, async/await throughout
- `bleak` for cross-platform BLE scanning
- `pytest` + `pytest-asyncio` (asyncio_mode = "auto") for tests
- `ruff` for linting
- `hatchling` build backend

## Tests

```bash
pip install -e ".[dev]"
pytest
pytest --cov=kegtron --cov-report=html  # with coverage
```

All async tests use `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` needed.

## Lint

```bash
ruff check src/ tests/
```

## Project conventions

- **BLE scanning is async** — all public scanner API is `async def`. Do not block the event loop.
- **Parser is pure/sync** — `parse_manufacturer_data()` takes raw bytes and returns a `KegtronReading`. No I/O, no side effects. Keep it that way.
- **27-byte wire format** — Kegtron Gen1 manufacturer data (ID `0xFFFF`) is fixed at 27 bytes. See `Gen1BLEMessageFormat.pdf` for the spec. The parser must validate length before unpacking.
- **`bleak` mocking in tests** — BLE hardware is not available in CI. Scanner tests mock `bleak.BleakScanner`. Keep mocks in `tests/test_scanner.py`, not in helpers.
- **No linter config in pyproject.toml** — ruff runs with defaults against `src/` and `tests/`.

See `~/CLAUDE.md` for global conventions.
