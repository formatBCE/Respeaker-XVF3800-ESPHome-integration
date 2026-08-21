# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

External ESPHome components plus an example device config that turn a **Respeaker XVF3800 USB 4-Mic Array** board (ESP32-S3 host + XMOS XVF3800 DSP + TLV320AIC3104 codec) into a Home Assistant voice satellite. There is no application to run here — the deliverables are consumed by ESPHome as `external_components`.

Layout:
- `esphome/components/respeaker_xvf3800/` — I2C driver for the XMOS DSP (mute, LED ring, beam direction, beam lock, DFU firmware update).
- `esphome/components/aic3104/` — `audio_dac` platform for the TLV320AIC3104 codec.
- `packages/` — the ESPHome packages consumers pull over `packages:`. This is the source of truth for device config: `base.yaml` (core/network/api/external_components), `hardware.yaml` (I2S, speaker, DSP, codec, DFU), `voice-assistant.yaml` (mWW, pipeline, media player), `leds.yaml` (all LED effect scripts), `timers-alarm.yaml` (time, alarm, timers).
- `config/respeaker-xvf-satellite-example.yaml` — thin (~47 line) consumer example. It only sets substitutions and the secret-bearing `wifi:`/`api:`/`ota:` blocks.
- `application_xvf3800_inthost-lr48-sqr-i2c-v1.0.7-release.bin` — XMOS firmware image, served over raw GitHub URL and flashed by the component's DFU code.
- `ha/` — Home Assistant script snippet that calls the device's `set_led_color` API action.

## Commands

There are no tests, no linters, and no CI. Everything goes through the ESPHome CLI:

```bash
esphome config config/respeaker-xvf-satellite-example.yaml    # validate YAML + component schemas
esphome compile config/respeaker-xvf-satellite-example.yaml   # build firmware (C++ errors surface here)
esphome run config/respeaker-xvf-satellite-example.yaml       # build + upload + logs
esphome logs config/respeaker-xvf-satellite-example.yaml
esphome clean config/respeaker-xvf-satellite-example.yaml     # after changing component Python or firmware bin
```

`esphome config` is the fast feedback loop for `__init__.py` changes; `esphome compile` is the only check for the C++.

The example config needs a `secrets.yaml` next to it (`wifi_ssid`, `wifi_password`, `ota_password`, `api_key`); see `config/secrets.yaml.example`. Keep local-only files in `local/` — it is gitignored.

### Testing changes before they are pushed

Both the packages and `external_components` resolve from GitHub `@main`, so a fresh checkout validates the *published* code, not the working tree.

To test **package** edits, use a local harness that `!include`s them (this is how the split was verified):

```yaml
# local/test-merge.yaml  — local/ is gitignored
packages:
  base: !include ../packages/base.yaml
  hardware: !include ../packages/hardware.yaml
  voice_assistant: !include ../packages/voice-assistant.yaml
  leds: !include ../packages/leds.yaml
  timers_alarm: !include ../packages/timers-alarm.yaml
```

Then `esphome config local/test-merge.yaml`. Relative-include resolution is the same locally and from the git cache, so this is a faithful dry run.

To test **C++** edits, temporarily switch `external_components` in `packages/base.yaml` to `source: {type: local, path: esphome/components}`. Do not commit that switch.

The refs are parameterised: `${respeaker_ref}` drives the packages, the C++ components, and the DFU firmware URL together. Keep them in lockstep.

The config also pins a **fork** of ESPHome's `i2s_audio` (`formatBCE/esphome@respeaker_microphone`). The stock component does not work with this board.

## Architecture

### Hub and children

`RespeakerXVF3800` (`respeaker_xvf3800.h/.cpp`) is an `i2c::I2CDevice` hub at address `0x2C`. It owns three optional `PollingComponent` children — `MuteSwitch`, `DFUVersionTextSensor`, `LEDBeamSensor` — each of which holds a back-pointer set in `to_code()` and does nothing but call a hub method in `update()`. Add new entities the same way: declare the class in `__init__.py`, add an optional schema key, create it and wire both directions in `to_code()`.

`AUTO_LOAD` lists `number` and `select` although the component defines no such platforms; the example config uses template `number`/`select` entities instead.

### XMOS control protocol

All DSP access is `(resid, cmd, payload)` over I2C, mirroring Respeaker's `xvf_host.py`. Writes go through `xmos_write_bytes()`. Reads set the high bit (`0x80`) on the command byte, then read `1 + n` bytes where byte 0 is a `TransportProtocolReturnCode`. Only `CTRL_DONE` means the payload is valid; `CTRL_WAIT` and `SERVICER_COMMAND_RETRY` (`0x40`) are normal transient answers and must be retried, not logged as errors. Resource IDs and command numbers are named constants at the top of the header — take new ones from `xvf_host.py` and record the source in a comment, as the existing constants do.

### Beam direction and beam lock

The DSP reports four azimuth slots (radians) from `AEC_SERVICER_RESID`/cmd 75: beam 1, beam 2, free-running, auto-select. `read_led_beam_direction()` normally reads slot 3 (auto-select) and maps it to one of 12 LED positions. `lock_beam()` captures the current azimuth, writes it to the fixed-beam registers, enables fixed-beam mode, and flips `beam_locked_` so subsequent reads follow slot 0 instead. The example config calls `lock_beam()` on wake word and `unlock_beam()` when the pipeline ends, so the LED ring stays pointed at the speaker during an utterance.

### DFU firmware update

`__init__.py` downloads the firmware at *build* time, checks its MD5, and embeds it as a PROGMEM array. `can_proceed()` blocks ESPHome startup until the on-chip version is read; if it does not match the embedded version, the `respeaker_xvf3800.flash` action drives a non-blocking state machine in `loop()` that sends 128-byte blocks. Progress and errors reach YAML through `on_begin`/`on_progress`/`on_end`/`on_error` triggers, compiled in only when `USE_RESPEAKER_XVF3800_STATE_CALLBACK` is defined. Bumping the bundled firmware means updating the binary, the `version`, and the `md5` in `packages/hardware.yaml` together.

### LED ring

The ring is 12 RGB LEDs written as one 12-entry `uint32_t` array through `set_led_ring()`; there is no ESPHome `light` component. All animation lives in YAML, now in `packages/leds.yaml`: a 50 ms `interval` dispatches on the `current_led_effect` global to one of the `update_*_effect` scripts, and `control_leds` decides which effect the current device state calls for. Add an effect by adding a script plus a branch in that interval — not by touching C++.
