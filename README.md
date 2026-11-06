# klipper-adaptive-chamber-soak

> **Safety and liability notice**
>
> This software controls or influences chamber-heating behavior. Improper configuration, installation, or use may cause equipment damage, fire, personal injury, or property loss. You are solely responsible for assessing suitability, verifying all hardware and temperature limits, installing and configuring the software correctly, supervising operation, and maintaining appropriate independent safety protections. This project is provided “as is,” without warranty. To the fullest extent permitted by applicable law, the authors and contributors disclaim liability for damage, injury, loss, or claims arising from the software or its use. Do not rely on this software as a substitute for hardware safety controls or safe operating practices.

Klipper add-on that replaces a fixed chamber soak with a temperature-stability check. Integrate it by calling its command from the startup macro that currently performs your chamber soak.

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

Time below is measured from when `WAIT_CHAMBER_EQUILIBRIUM` starts. With the default settings, the add-on behaves as follows:

| Elapsed time | Reading and decision |
| --- | --- |
| 8 minutes | Record the first chamber reading as the baseline. |
| 13 minutes | Record a new reading. Compare it with the 8-minute reading and check both pass conditions. |
| Every 5 minutes afterward | Compare the latest reading with the immediately previous reading and check both pass conditions again. |
| 90-minute timeout | If the pass conditions have not both been met, stop startup with an error. |

The chamber passes when its latest reading is no more than 3 C below the requested target and the absolute change since the previous reading is no more than 3 C. Both conditions must pass in the same comparison. The 8-minute reading establishes the baseline, so the earliest pass is at 13 minutes. Timing and tolerances use the `[chamber_equilibrium]` settings above. The `WAIT_CHAMBER_EQUILIBRIUM` command can override them per call using `SENSOR`, `INITIAL_DELAY`, `INTERVAL`, `TARGET_TOLERANCE`, `STABILITY_TOLERANCE`, and `MAX_WAIT`.

## Startup macro integration

The Python add-on registers `WAIT_CHAMBER_EQUILIBRIUM`. Your printer's startup macro must call it with the slicer chamber target and the configured chamber-air sensor. Replace the fixed chamber wait or soak step with a call in this form:

```gcode
WAIT_CHAMBER_EQUILIBRIUM TARGET=<slicer chamber target> SENSOR="<chamber sensor object>"
```

### RatOS heatsoak setting

For your RatOS V-Core 4 setup, add this variable to the existing `[gcode_macro RatOS]` section in `printer.cfg` to disable RatOS adaptive heatsoaking:

```ini
variable_beacon_adaptive_heat_soak: False
```

If `[gcode_macro RatOS]` already exists, add only this variable to that section. Do not create a duplicate section. This RatOS setting does not call the chamber add-on. Your startup macro still needs to call `WAIT_CHAMBER_EQUILIBRIUM` as shown above. Preserve existing heater, fan, movement, and post-preheat controls when changing startup macros.

## Hardware configuration

Configure the chamber temperature sensor in `printer.cfg` for the sensor actually installed to measure chamber air. Set its Klipper sensor type, MCU pin, pullup, and any other required values from the sensor and controller documentation. Then set the `[chamber_equilibrium]` `sensor` option to that configured Klipper object name. The example name `temperature_sensor chamber` is only a placeholder. Some printers also have a separate thermistor for a PTC heater. Configure the heater's own sensor and heater safety limits according to the hardware design. The chamber-air sensor used by this add-on and the heater's control sensor may be different devices.

Retain Klipper's heater temperature limits and configure `verify_heater` for the installed heater, sensor, power supply, and enclosure. Ensure every commanded preheat and printing target, including any RatOS heater offset, stays within the configured heater limit. Do not copy pin assignments, sensor types, or temperature limits from another printer without verifying that they match your hardware.

### Original author's setup notes

The original RatOS setup supplied with this project had a 150 C preheat request and an 80 C heater `max_temp`. Its integration therefore sets `variable_chamber_heater_preheating_temp: 80` and keeps that existing limit unchanged. Those values describe the author's setup only. Other installations must use their verified hardware limits and configure their RatOS preheat and offsets accordingly.

## Files and destinations

- `chamber_equilibrium.py` → Klipper `klippy/extras/chamber_equilibrium.py` on the printer host. Common RatOS path is `/home/pi/klipper/klippy/extras/`.
- `chamber_equilibrium.cfg` → printer configuration directory, commonly `~/printer_data/config/`.

## Backup and install

1. In Mainsail/Fluidd, back up `printer.cfg` and any file containing your startup or chamber-soak macro. Also save the current `klippy.log`.
2. Upload `chamber_equilibrium.py` to `/home/pi/klipper/klippy/extras/` and `chamber_equilibrium.cfg` to `~/printer_data/config/`.
3. Include `chamber_equilibrium.cfg` from `printer.cfg` using its actual config path, for example `[include chamber_equilibrium.cfg]`. Set the sensor and timing values in that file as needed. Klipper loads the Python extra through its `[chamber_equilibrium]` section.
4. In your startup macro, replace the existing chamber soak wait with `WAIT_CHAMBER_EQUILIBRIUM`, passing the slicer target and your configured chamber sensor. Use your firmware's supported macro override method. Do not create a duplicate macro section unless your configuration system supports merging it.
5. Configure heater targets and offsets so they remain within your heater's existing Klipper `max_temp`. Do not raise the limit to accommodate an unsafe target.
6. Restart Klipper. If it fails to start, restore the backed-up configs and remove the Python extra.

## Checks

With heaters disabled and the printer cold, run `HELP WAIT_CHAMBER_EQUILIBRIUM` to confirm the command is registered. Do not run a real heater cycle until the chamber sensor configuration, heater sensor configuration, heater limit, preheat target, printing offset, and `verify_heater` values have been checked against your hardware. During supervised testing, use a low slicer chamber target within the hardware-approved range, verify the first reading is after 8 minutes, subsequent readings are 5 minutes apart, and startup errors after 90 minutes if the pass criteria are not met. Confirm bed/fan behavior and post-preheat chamber control match the original RatOS sequence.
