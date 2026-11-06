# klipper-adaptive-chamber-soak

> **Safety and liability notice**
>
> This software controls or influences chamber-heating behavior. Improper configuration, installation, or use may cause equipment damage, fire, personal injury, or property loss. You are solely responsible for assessing suitability, verifying all hardware and temperature limits, installing and configuring the software correctly, supervising operation, and maintaining appropriate independent safety protections. This project is provided “as is,” without warranty. To the fullest extent permitted by applicable law, the authors and contributors disclaim liability for damage, injury, loss, or claims arising from the software or its use. Do not rely on this software as a substitute for hardware safety controls or safe operating practices.

Klipper add-on that replaces a fixed chamber soak with a temperature-stability check. The core command is usable from Klipper macros, with a RatOS-specific integration described below.

## Klipper add-on

The target temperature comes from the caller, such as the slicer-driven RatOS startup macro. Timing, sensor name, and temperature tolerances can be customized in the `[chamber_equilibrium]` section of `printer.cfg`:

```ini
[chamber_equilibrium]
sensor: temperature_sensor chamber
initial_delay: 480
interval: 300
target_tolerance: 3
stability_tolerance: 3
max_wait: 5400
```

Values are in seconds for the delays and timeout, and degrees Celsius for the tolerances. Defaults give an 8-minute first sample, 5-minute intervals, a minimum temperature of target minus 3 C, a maximum 3 C change between adjacent readings, and a 90-minute fail-closed timeout. The `WAIT_CHAMBER_EQUILIBRIUM` command can also override these defaults per call using `SENSOR`, `INITIAL_DELAY`, `INTERVAL`, `TARGET_TOLERANCE`, `STABILITY_TOLERANCE`, and `MAX_WAIT`.

## RatOS-specific integration

RatOS Beacon adaptive heatsoaking is a separate bed-stability feature. `variable_beacon_adaptive_heat_soak` controls that Beacon-based bed soak. It does not turn off the chamber heater macro or replace its chamber-temperature wait. Keep the chamber macro override below to route the chamber wait through this add-on. RatOS bed heatsoaking is configured separately through `bed_heat_soak_time` and related settings.

```ini
# Adaptive Heat Soak
variable_beacon_adaptive_heat_soak: False
```

The existing `[gcode_macro RatOS]` section is usually already defined, so add only the comment and variable inside it. Do not add a duplicate section. `False` disables Beacon adaptive bed heatsoaking. Set it only if that is the desired bed-soak behavior. It does not disable the chamber equilibrium gate or the chamber heater.

## Hardware configuration

Configure the chamber temperature sensor in `printer.cfg` for the sensor actually installed to measure chamber air. Set its Klipper sensor type, MCU pin, pullup, and any other required values from the sensor and controller documentation. Then set the `[chamber_equilibrium]` `sensor` option to that configured Klipper object name. The example name `temperature_sensor chamber` is only a placeholder. Some printers also have a separate thermistor for a PTC heater. Configure the heater's own sensor and heater safety limits according to the hardware design. The chamber-air sensor used by this add-on and the heater's control sensor may be different devices.

Retain Klipper's heater temperature limits and configure `verify_heater` for the installed heater, sensor, power supply, and enclosure. Ensure every commanded preheat and printing target, including any RatOS heater offset, stays within the configured heater limit. Do not copy pin assignments, sensor types, or temperature limits from another printer without verifying that they match your hardware.

### Original author's setup notes

The original RatOS setup supplied with this project had a 150 C preheat request and an 80 C heater `max_temp`. Its integration therefore sets `variable_chamber_heater_preheating_temp: 80` and keeps that existing limit unchanged. Those values describe the author's setup only. Other installations must use their verified hardware limits and configure their RatOS preheat and offsets accordingly.

## Files and destinations

- `chamber_equilibrium.py` → Klipper `klippy/extras/chamber_equilibrium.py` on the printer host. Common RatOS path is `/home/pi/klipper/klippy/extras/`.
- `chamber_equilibrium.cfg` → printer configuration directory, commonly `~/printer_data/config/`.
- `chamber_heater_override.cfg` → reference patch for the existing RatOS `_CHAMBER_HEATER_ON` macro. This override is required to replace that macro’s blocking chamber-temperature wait with the equilibrium check. Apply the documented edits to a copy of the existing macro. Do not add a duplicate `[gcode_macro _CHAMBER_HEATER_ON]` section. Preserve RatOS fan, bed, toolhead movement, filter, post-preheat, and delayed-control code.

## Backup and install

1. In Mainsail/Fluidd, download a backup of `printer.cfg` and the RatOS chamber-heater configuration file that defines `_CHAMBER_HEATER_ON`. Also save the current `klippy.log`.
2. Upload `chamber_equilibrium.py` to `/home/pi/klipper/klippy/extras/` and `chamber_equilibrium.cfg` to `~/printer_data/config/`.
3. Include `chamber_equilibrium.cfg` from `printer.cfg` using its actual config path, for example `[include chamber_equilibrium.cfg]`. Set the sensor and timing values in that file as needed. Klipper loads the Python extra through its `[chamber_equilibrium]` section.
4. Apply the macro edits described in `chamber_heater_override.cfg` to the existing macro copy in your user config, ensuring the include order loads your customized definition in place of the RatOS definition. Config section override behavior depends on your RatOS version. Validate duplicate-section handling before restarting.
5. Configure the RatOS preheat target and heater offsets so they remain within your heater's existing Klipper `max_temp`. Do not raise the limit to accommodate an unsafe target.
6. Restart Klipper. If it fails to start, restore the backed-up configs and remove the Python extra.

## Checks

With heaters disabled and the printer cold, run `HELP WAIT_CHAMBER_EQUILIBRIUM` to confirm the command is registered. Do not run a real heater cycle until the chamber sensor configuration, heater sensor configuration, heater limit, preheat target, printing offset, and `verify_heater` values have been checked against your hardware. During supervised testing, use a low slicer chamber target within the hardware-approved range, verify the first reading is after 8 minutes, subsequent readings are 5 minutes apart, and startup errors after 90 minutes if the pass criteria are not met. Confirm bed/fan behavior and post-preheat chamber control match the original RatOS sequence.
