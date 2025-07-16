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
import traceback


class GrowLights(hass.Hass):
    """AppDaemon app for controlling growth lights based on UV index and time schedules."""

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
            try:
                self.off_season_start_time = datetime.datetime.strptime(self.off_season_start, "%H:%M").time()
                self.off_season_end_time = datetime.datetime.strptime(self.off_season_end, "%H:%M").time()
                self.on_season_start_time = datetime.datetime.strptime(self.on_season_start, "%H:%M").time()
                self.on_season_end_time = datetime.datetime.strptime(self.on_season_end, "%H:%M").time()
            except ValueError as e:
                self.log(f"Error parsing time configuration: {str(e)} (line {traceback.extract_stack()[-1].lineno})", level="ERROR")
                raise

            # Schedule initial check
            self.run_in(self.check_conditions, 0)

            # Schedule periodic UV index checks (every 10 minutes)
            self.run_every(self.check_conditions, "now", 10 * 60)

            self.log("Grow Lights app initialized successfully", level="INFO")

        except Exception as e:
            self.log(f"Error initializing Grow Lights app: {str(e)} (line {traceback.extract_stack()[-1].lineno})", level="ERROR")

    def control_lights(self, turn_on: bool) -> None:
        """Control all configured growth light switches."""
        try:
            action = "on" if turn_on else "off"
            self.log(f"Turning lights {action}", level="INFO")

            for switch in self.switches:
                try:
                    self.turn_on(switch) if turn_on else self.turn_off(switch)
                except Exception as e:
                    self.log(f"Error controlling switch {switch}: {str(e)} (line {traceback.extract_stack()[-1].lineno})", level="ERROR")

        except Exception as e:
            self.log(f"Error controlling lights: {str(e)} (line {traceback.extract_stack()[-1].lineno})", level="ERROR")

    def check_conditions(self, kwargs) -> None:
        """Main function to check conditions and control lights."""
        try:
            # Get current time and month once (needed for active hours check)
            now = datetime.datetime.now()
            current_time = now.time()
            current_month = now.month

            # Check if we're in active hours (most likely to exit early)
            is_summer = 6 <= current_month <= 8
            is_active = (self.on_season_start_time <= current_time <= self.on_season_end_time) if is_summer else (self.off_season_start_time <= current_time <= self.off_season_end_time)

            # Get current state (needed for both active and inactive logic)
            current_state = self.get_state(self.switches[0])
            if current_state is None:
                return

            # If outside active hours, ensure lights are OFF
            if not is_active:
                if current_state == "on":
                    self.control_lights(False)
                return

            # We're in active hours - get UV index (most expensive operation)
            try:
                uv_state = self.get_state(self.uv_sensor)
                uv_index = float(uv_state) if uv_state is not None and uv_state != "unavailable" else None
            except (ValueError, TypeError) as e:
                self.log(f"Error parsing UV index value: {str(e)} (line {traceback.extract_stack()[-1].lineno})", level="ERROR")
                uv_index = None

            # Determine desired state based on UV index
            should_be_on = uv_index is None or uv_index < self.uv_threshold

            # Return early if no state change needed
            if (should_be_on and current_state == "on") or (not should_be_on and current_state == "off"):
                return

            # Control lights
            self.control_lights(should_be_on)

        except Exception as e:
            self.log(f"Error in check_conditions: {str(e)} (line {traceback.extract_stack()[-1].lineno})", level="ERROR")
