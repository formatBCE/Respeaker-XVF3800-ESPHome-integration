# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

External ESPHome components plus a reference YAML that turn a **Respeaker XVF3800 USB 4-mic array** (host board uses an ESP32-S3) into a Home Assistant voice satellite. There is no build system here — this repo is consumed by ESPHome via `external_components:` (see `config/respeaker-xvf-satellite-example.yaml` lines 1364–1392). Compilation/flashing happens in an ESPHome environment that pulls this repo by git ref.

## Layout

- `esphome/components/respeaker_xvf3800/` — main component. Talks to the XMOS XVF3800 DSP over I²C (default addr `0x2C`) using the XMOS "transport protocol" (resid + cmd + read/write bit `0x80`). Exposes:
  - hub component `RespeakerXVF3800` (`respeaker_xvf3800.{h,cpp}`, `__init__.py`)
  - sub-entities: `MuteSwitch`, `DFUVersionTextSensor`, `LEDBeamSensor` (sub-classes of ESPHome `switch`/`text_sensor`/`sensor` + `PollingComponent`)
  - DFU (firmware update) state machine for the XMOS chip itself, driven from `loop()`. Action: `respeaker_xvf3800.flash` (registered in `__init__.py`). Triggers: `on_begin`/`on_progress`/`on_end`/`on_error` under the `firmware:` key. Firmware binary is downloaded at codegen time (`download_firmware`), MD5-verified, then embedded as a `progmem_array`. The shipped `application_xvf3800_inthost-lr48-sqr-i2c-v1.0.7-release.bin` is the reference XMOS firmware.
  - `automation.h` defines the trigger templates and the `RespeakerXVF3800FlashAction`.
  - `USE_RESPEAKER_XVF3800_STATE_CALLBACK` is a codegen-defined macro — only emitted when at least one DFU automation is configured. Code touching DFU callbacks must stay inside `#ifdef`.
- `esphome/components/aic3104/` — minimal ESPHome `audio_dac` driver for the TI AIC3104 codec (I²C addr `0x18`). Header `aic3104.h` is large but the Python side is intentionally tiny.
- `config/respeaker-xvf-satellite-example.yaml` — the canonical, working satellite config (~1400 lines). It pulls **forks** of ESPHome for `i2s_audio`, `const`/`media_source`/`sendspin`, and `http_request` (see external_components block). Do not assume mainline ESPHome; behavior of those forks matters.
- `ha/` — Home Assistant script blueprints invoking the device's exposed `esphome.<device>_set_led_color` service. `f_device` selector filters on `manufacturer: formatbce`, `model: Respeaker XVF3800 Satellite` — keep that metadata stable in the YAML's `esphome.project` block or these scripts break.
- `misc/` — duplicate of one HA script; not wired into anything.

## Architectural notes worth knowing before editing

- **The component is an I²C bridge to an XMOS DSP, not the audio path.** Audio I/O goes through `i2s_audio` (forked) + `aic3104`. The XVF3800 component only configures/queries the DSP (mute, beam direction, VNR, LED ring, firmware version/DFU).
- **All XMOS reads use `cmd | 0x80`**. There is a single helper `xmos_write_bytes`; reads are open-coded with `read_register`/`read_bytes_raw`. Servicer resids and command IDs are in `respeaker_xvf3800.h` — these come from the XMOS firmware's `*_servicer.h` headers (see comments referencing `xmos/sln_voice`). When adding new commands, add the constant there, don't sprinkle magic numbers.
- **`can_proceed()` blocks ESPHome setup until firmware version is read AND either matches the embedded blob or no blob is configured.** A DFU is auto-triggered from `loop()` when versions mismatch. Don't add work that needs setup to complete before DFU finishes — it won't.
- **LED ring is 12 LEDs**, controlled via GPO servicer `LED_RING_VALUE` (resid `20`, cmd `18`). Beam direction (0–11) comes from AEC servicer (resid `33`, cmd `75`). Both are polled — `LEDBeamSensor` defaults to 500 ms, mute switch 1 s, DFU version 30 s.
- **Codegen Python (`__init__.py`) wires children to the hub via `set_parent` AND `set_<child>` on the hub.** Both directions are required; missing one silently breaks polling. When adding a new child entity follow the existing pattern (`MuteSwitch`/`DFUVersionTextSensor`/`LEDBeamSensor` are the templates).
- **`AUTO_LOAD` includes `number` and `select`** even though no such entities exist yet in code — the example YAML uses `number`/`select` platforms via lambdas calling the hub. If you remove from `AUTO_LOAD`, the example YAML will fail to compile.
- **Min ESPHome version is `2026.3.0`** (set in the example YAML). Recent commits (`Fix for new Espressif framework`, `Fix for 2026.3.0 register_action warning`) show the codebase tracks ESPHome breaking changes closely — when something looks like a workaround for a recent ESPHome change, check `git log` before "cleaning it up".

## Working in this repo

- No tests, no lint config, no CI. Validation = `esphome config <yaml>` / `esphome compile <yaml>` against a YAML that lists this repo in `external_components`. There is no way to compile components from inside this repo alone.
- To test changes locally, point an ESPHome YAML's `external_components` at a local path (`type: local`, `path: <repo>/esphome/components`) instead of the git source.
- `CODEOWNERS = ["@formatBCE"]` — single maintainer; component name `respeaker_xvf3800` and HA project name `formatbce.Respeaker XVF3800 Satellite` are referenced externally (HA blueprints) — renaming is a breaking change.
- The `.bin` at the repo root is firmware shipped to end users via the example YAML's `firmware:` URL/MD5 mechanism; bumping it requires updating both the URL/version and the MD5 in any consumer YAML.
