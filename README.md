# klipper-adaptive-chamber-soak

Klipper add-on for adaptive chamber heat soaking, including a RatOS integration patch.

## RatOS package

This package adds a chamber stability gate to startup. It samples 8 minutes after the wait begins, then every 5 minutes. It passes only when the chamber is at least target minus 3 C and the absolute change from the previous five-minute sample is at most 3 C. A 90-minute timeout raises an error and stops startup.

## Important hardware checks before enabling

Your supplied RatOS macro requests a 150 C chamber-heater preheat, while the supplied Klipper heater `max_temp` is 80 C. This package explicitly ignores the 150 C request and sets `variable_chamber_heater_preheating_temp: 80`, retaining the existing 80 C `max_temp`. Klipper rejects heater targets above `max_temp`. The printing target plus RatOS heating offset must also stay at or below 80 C or Klipper will reject it. The 80 C limit itself still needs to match the heater, sensor, wiring, and chamber materials' manufacturer ratings before enabling heat.

The supplied snippets do not include the chamber heater section or verify_heater values, so this package cannot safely rewrite those values. Restore conservative `verify_heater` settings appropriate to the installed hardware and follow Klipper/RatOS documentation. The duplicate PF4 thermistor must be resolved by confirming which physical sensor is wired to PF4 and keeping exactly one active pin assignment. Do not change sensor type or pin based on guesswork.

## Files and destinations

- `chamber_equilibrium.py` → Klipper `klippy/extras/chamber_equilibrium.py` on the printer host. Common RatOS path is `/home/pi/klipper/klippy/extras/`.
- `chamber_equilibrium.cfg` → printer configuration directory, commonly `~/printer_data/config/`.
- `chamber_heater_override.cfg` → reference patch for the existing RatOS `_CHAMBER_HEATER_ON` macro. Apply the two documented edits to a copy of the existing macro. Do not add a duplicate `[gcode_macro _CHAMBER_HEATER_ON]` section. Preserve RatOS fan, bed, toolhead movement, filter, post-preheat, and delayed-control code.

## Backup and install

1. In Mainsail/Fluidd, download a backup of `printer.cfg` and the RatOS chamber-heater configuration file that defines `_CHAMBER_HEATER_ON`. Also save the current `klippy.log`.
2. Upload `chamber_equilibrium.py` to `/home/pi/klipper/klippy/extras/` and the cfg to `~/printer_data/config/`.
3. Add `[chamber_equilibrium]` to `printer.cfg` and add ` [include chamber_equilibrium.cfg]` only if your RatOS setup supports that section loading arrangement. Klipper extras are normally loaded by a `[chamber_equilibrium]` config section. Include the local file using its actual absolute config path if needed.
4. Apply the macro edits described in `chamber_heater_override.cfg` to the existing macro copy in your user config, ensuring the include order loads your customized definition in place of the RatOS definition. Config section override behavior depends on your RatOS version. Validate duplicate-section handling before restarting.
5. In the `[gcode_macro RatOS]` settings override, set `variable_chamber_heater_preheating_temp: 80`. This disregards the old 150 C request. Keep the heater `max_temp: 80` unchanged. Resolve the printing offset and duplicate PF4 as described above before using chamber heat.
6. Restart Klipper. If it fails to start, restore the backed-up configs and remove the Python extra.

## Checks

With heaters disabled and the printer cold, run `HELP WAIT_CHAMBER_EQUILIBRIUM` to confirm the command is registered. Do not run a real heater cycle until the heater limit, preheat target, printing offset, verify_heater values, and PF4 sensor assignment have been checked. During supervised testing, use a low slicer chamber target within the hardware-approved range, verify the first reading is after 8 minutes, subsequent readings are 5 minutes apart, and startup errors after 90 minutes if the pass criteria are not met. Confirm bed/fan behavior and post-preheat chamber control match the original RatOS sequence.
