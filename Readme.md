# ESPHome components and example config for [Respeaker XVF3800](https://github.com/respeaker/reSpeaker_XVF3800_USB_4MIC_ARRAY)

## _ATTENTION! Under development, use on your own risk!_
## Testing appreciated.

## Overview
This repository provides custom ESPHome components, an example configuration, and helper scripts for running a Respeaker XVF3800 USB 4-mic array as a Home Assistant voice satellite. The goal is to make the XVF3800 usable over I2C with ESPHome, including firmware management and some device state exposure.

## What's included
- **ESPHome components**
  - `respeaker_xvf3800`: I2C control of the XVF3800, including mute, DFU firmware update helpers, and LED beam direction telemetry.
  - `aic3104`: Minimal I2C Audio DAC component stub for the on-board codec.
- **Example ESPHome config**
  - `config/respeaker-xvf-satellite-example.yaml`
- **Home Assistant scripts**
  - `ha/change_color_script.yaml` and `misc/set_color_script.yaml` for LED ring color control
- **Firmware artifact**
  - `application_xvf3800_inthost-lr48-sqr-i2c-v1.0.7-release.bin`

## Known issues
1. There's no buttons, so no way to stop timer or response except saying "stop", and no way to start pipeline manually.
2. No volume controls besides the software one (similar to Respeaker Lite Voice Kit).
3. No exposed light (LED is controlled via I2C).
4. ...?

## Quick start
1. Review the example YAML in `config/respeaker-xvf-satellite-example.yaml` and copy the relevant sections into your ESPHome device configuration.
2. Ensure the XVF3800 is wired to the ESP32 I2C bus (SDA/SCL) and powered correctly.
3. Optionally include the firmware block in the config to perform DFU updates from the bundled `.bin` file.
4. Use the HA scripts in `ha/` or `misc/` to drive LED color changes once the device is online.

If you test changes or have success reports, please open an issue or PR with your findings.
