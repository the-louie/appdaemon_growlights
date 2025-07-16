"""
Grow Lights Control App for Home Assistant AppDaemon

This app controls growth lights based on UV index readings and seasonal time schedules.
During summer months (June-August), lights are active from 06:00 to 18:00.
During other months, lights are active from 09:00 to 15:00.
Lights are turned off when UV index is 5 or above during active hours.

Copyright (c) 2025 the_louie
"""

import appdaemon.plugins.hass.hassapi as hass
import datetime
from typing import Optional


class GrowLights(hass.Hass):
    """
    AppDaemon app for controlling growth lights based on UV index and time schedules.

    The app monitors UV index sensor readings and controls growth light switches
    according to seasonal schedules and UV index thresholds.
    """

    def initialize(self) -> None:
        """Initialize the grow lights control app."""
        try:
            # Get configuration parameters
            self.uv_sensor = self.args.get("uv_index_sensor")
            self.uv_threshold = self.args.get("uv_index_threshold", 5)
            self.switches = self.args.get("switches", [])

            # Time configuration
            self.off_season_start = self.args.get("off_season_start", "09:00")
            self.off_season_end = self.args.get("off_season_end", "15:00")
            self.on_season_start = self.args.get("on_season_start", "06:00")
            self.on_season_end = self.args.get("on_season_end", "18:00")

            # Validate configuration
            if not self.uv_sensor:
                self.log("Error: UV index sensor not configured", level="ERROR")
                return

            if not self.switches:
                self.log("Error: No switches configured", level="ERROR")
                return

            # Parse time strings once for efficiency
            self._parse_time_configs()

            # Schedule initial check
            self.run_in(self.check_conditions, 0)

            # Schedule periodic UV index checks (every 10 minutes) only during active hours
            self.run_every(self.check_conditions, "now", 10 * 60)

            # Schedule daily time range updates
            self.run_daily(self.update_time_ranges, "00:01")

            self.log("Grow Lights app initialized successfully", level="INFO")

        except Exception as e:
            self.log(f"Error initializing Grow Lights app: {str(e)}", level="ERROR")

    def _parse_time_configs(self) -> None:
        """Parse time configuration strings once for efficiency."""
        try:
            self.off_season_start_time = datetime.datetime.strptime(self.off_season_start, "%H:%M").time()
            self.off_season_end_time = datetime.datetime.strptime(self.off_season_end, "%H:%M").time()
            self.on_season_start_time = datetime.datetime.strptime(self.on_season_start, "%H:%M").time()
            self.on_season_end_time = datetime.datetime.strptime(self.on_season_end, "%H:%M").time()
        except ValueError as e:
            self.log(f"Error parsing time configuration: {str(e)}", level="ERROR")
            raise

    def is_summer_season(self) -> bool:
        """
        Determine if current date is in summer season (June-August).

        Returns:
            bool: True if current month is June, July, or August
        """
        try:
            current_month = datetime.datetime.now().month
            return 6 <= current_month <= 8
        except Exception as e:
            self.log(f"Error determining season: {str(e)}", level="ERROR")
            return False

    def is_active_time(self) -> bool:
        """
        Check if current time is within active hours based on season.

        Returns:
            bool: True if current time is within active hours
        """
        try:
            current_time = datetime.datetime.now().time()

            if self.is_summer_season():
                return self.on_season_start_time <= current_time <= self.on_season_end_time
            else:
                return self.off_season_start_time <= current_time <= self.off_season_end_time

        except Exception as e:
            self.log(f"Error checking active time: {str(e)}", level="ERROR")
            return False

    def get_uv_index(self) -> Optional[float]:
        """
        Get current UV index from sensor.

        Returns:
            Optional[float]: Current UV index value or None if unavailable
        """
        try:
            uv_state = self.get_state(self.uv_sensor)
            if uv_state is not None and uv_state != "unavailable":
                return float(uv_state)
            else:
                self.log(f"UV sensor {self.uv_sensor} is unavailable", level="WARNING")
                return None
        except (ValueError, TypeError) as e:
            self.log(f"Error parsing UV index value: {str(e)}", level="ERROR")
            return None
        except Exception as e:
            self.log(f"Error getting UV index: {str(e)}", level="ERROR")
            return None

    def control_lights(self, turn_on: bool) -> None:
        """
        Control all configured growth light switches.

        Args:
            turn_on (bool): True to turn lights on, False to turn off
        """
        try:
            action = "on" if turn_on else "off"
            self.log(f"Turning lights {action}", level="INFO")

            for switch in self.switches:
                try:
                    self.turn_on(switch) if turn_on else self.turn_off(switch)
                    self.log(f"Set {switch} to {action}", level="DEBUG")
                except Exception as e:
                    self.log(f"Error controlling switch {switch}: {str(e)}", level="ERROR")

        except Exception as e:
            self.log(f"Error controlling lights: {str(e)}", level="ERROR")

    def check_conditions(self, kwargs) -> None:
        """
        Main function to check conditions and control lights.
        Called every 10 minutes and on initialization.
        """
        try:
            # Return early if outside active hours
            if not self.is_active_time():
                self.log("Skipping UV check - outside active hours", level="DEBUG")
                return

            # Get current UV index
            uv_index = self.get_uv_index()
            if uv_index is None:
                self.log("Error: UV index is None", level="ERROR")
                return

            # Check current state of first switch to determine if lights are currently on
            current_state = None
            if self.switches:
                current_state = self.get_state(self.switches[0])

            if uv_index >= self.uv_threshold and current_state == "off":
                self.log(f"Lights remain off - {uv_index} > {self.uv_threshold}", level="DEBUG")
                return
            elif uv_index < self.uv_threshold and current_state == "on":
                self.log(f"Lights remain on - {uv_index} < {self.uv_threshold}", level="DEBUG")
                return

            # Control lights if state needs to change
            self.control_lights(current_state == "on")

        except Exception as e:
            self.log(f"Error in check_conditions: {str(e)}", level="ERROR")

    def update_time_ranges(self, kwargs) -> None:
        """
        Update time ranges based on current season.
        Called daily at 00:01 to handle season changes.
        """
        try:
            is_summer = self.is_summer_season()
            season_name = "summer" if is_summer else "winter"

            if is_summer:
                start_time = self.on_season_start
                end_time = self.on_season_end
            else:
                start_time = self.off_season_start
                end_time = self.off_season_end

            self.log(f"Updated to {season_name} schedule: {start_time} - {end_time}", level="INFO")

        except Exception as e:
            self.log(f"Error updating time ranges: {str(e)}", level="ERROR")
