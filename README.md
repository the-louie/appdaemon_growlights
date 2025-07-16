# Grow Lights Control for Home Assistant AppDaemon

Copyright (c) 2025 the_louie

An AppDaemon app for Home Assistant that automatically controls growth lights based on UV index readings and seasonal time schedules.

## Features

- **Seasonal Time Control**: Different operating hours for summer (June-August) and other months
- **UV Index Monitoring**: Automatically turns off lights when UV index is 5 or above
- **Multiple Switch Support**: Control multiple growth light switches simultaneously
- **Robust Error Handling**: Comprehensive logging and error recovery
- **Configurable Parameters**: All thresholds and sensors configurable via YAML

## Time Schedules

- **Summer Months (June-August)**: 06:00 to 18:00
- **Other Months**: 09:00 to 15:00

## UV Index Logic

- Lights are **ON** during active hours when UV index is below 5
- Lights are **OFF** during active hours when UV index is 5 or above
- Lights are **OFF** outside of active hours regardless of UV index
- If UV sensor is unavailable, lights remain ON during active hours

## Installation

1. Copy `i1_growlights.py` to your AppDaemon `apps` directory
2. Add the configuration to your `apps.yaml` or include the `config.yaml` file
3. Restart AppDaemon

## Configuration

```yaml
grow_lights:
  module: i1_growlights
  class: GrowLights

  # Time-based configuration
  off_season_start: "09:00"
  off_season_end: "15:00"
  on_season_start: "06:00"
  on_season_end: "18:00"

  # UV index configuration
  uv_index_sensor: "sensor.ecowitt_uv"
  uv_index_threshold: 5

  # Growth light switches to control
  switches:
    - switch.vaxtlampa
    - switch.vaxtlampa_fonster_vast
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `uv_index_sensor` | string | required | Home Assistant entity ID of UV index sensor |
| `uv_index_threshold` | number | 5 | UV index threshold for turning off lights |
| `switches` | list | required | List of switch entity IDs to control |
| `off_season_start` | time | "09:00" | Start time for non-summer months |
| `off_season_end` | time | "15:00" | End time for non-summer months |
| `on_season_start` | time | "06:00" | Start time for summer months |
| `on_season_end` | time | "18:00" | End time for summer months |

## Operation

The app runs the following checks every 10 minutes **only during active hours**:

1. Determines current season (summer vs other months)
2. Checks if current time is within active hours
3. Reads UV index from configured sensor
4. Controls lights based on time and UV index conditions

**Performance Optimizations:**
- Time strings are parsed once at startup for efficiency
- UV checks are skipped outside of active hours
- Minimal state tracking to reduce memory usage

## Logging

The app provides comprehensive logging at different levels:

- **INFO**: Light state changes and important events
- **WARNING**: UV sensor unavailability
- **ERROR**: Configuration or operational errors
- **DEBUG**: Detailed state information

## Error Handling

- Graceful handling of sensor unavailability
- Configuration validation on startup
- Exception logging with line numbers
- Fallback behavior when sensors are unavailable

## Requirements

- Home Assistant with AppDaemon
- UV index sensor (e.g., Ecowitt weather station)
- Growth light switches or relays

## License

This project is licensed under the BSD 2-Clause License - see the [LICENSE](LICENSE) file for details.