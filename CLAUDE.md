# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

External ESPHome components plus an example device config that turn a **Respeaker XVF3800 USB 4-Mic Array** board (ESP32-S3 host + XMOS XVF3800 DSP + TLV320AIC3104 codec) into a Home Assistant voice satellite. There is no application to run here — the deliverables are consumed by ESPHome as `external_components`.

Layout:
- `esphome/components/respeaker_xvf3800/` — I2C driver for the XMOS DSP (mute, LED ring, beam direction, beam lock, DFU firmware update), plus the `microphone` platform that decimates the 48 kHz DSP output to 16 kHz.
- `esphome/components/aic3104/` — `audio_dac` platform for the TLV320AIC3104 codec.
- `packages/` — the ESPHome packages consumers pull over `packages:`. Users list all five files, so keep every path. `base.yaml` holds the voice satellite core as a nested remote package (`satellite_core`: Respeaker-Lite-ESPHome-integration `packages/core/{base,voice-assistant,media-player,timers-alarm}.yaml` at `${respeaker_lite_ref}`; `controls.yaml` is left out because the buttons belong to the XMOS chip), plus identity, esp32, psram, i2c, the logger level, Wi-Fi tuning, `set_led_color`, and `external_components`. The other files only add the XVF3800 parts to the core: `hardware.yaml` (I2S, speaker, DSP, codec, DFU), `voice-assistant.yaml` (beam lock, mWW gain 1, media player volume range and volume display via `!extend external_media_player`), `leds.yaml` (all LED effect scripts), `timers-alarm.yaml` (the timer-tick LED animation only).
- The core is shared with Respeaker Lite and Koala. Change boot, network, voice pipeline, media player, timer, alarm, snooze, or sound behavior in the Lite repository, release it, and bump `respeaker_lite_ref` here. The core merges first: a scalar here wins, an action list here (for example `voice_assistant: on_end:`) runs after the core's actions, and `- id: !extend <id>` merges into a core item. The core runs the `wake_word_start_hook` script after a wake word starts the voice assistant; `voice-assistant.yaml` extends it with `lock_beam()`. The IDs the core expects from a device are listed in the header of Lite's `packages/core/base.yaml`.
- `config/respeaker-xvf-satellite-example.yaml` — thin (~47 line) consumer example. It only sets substitutions and the secret-bearing `wifi:`/`api:`/`ota:` blocks.
- `config/common/respeaker-xvf-satellite-base.yaml` — all five packages as local `!include`s, no credentials and no provisioning. The factory config includes it, and an adopted device imports it at the release tag (same role as Koala's `koala-base.yaml`).
- `config/respeaker-xvf-satellite-factory.yaml` — factory configuration without credentials: the base file, Improv over BLE (`improv_ble`, authorizer: `mute_button`) and serial, BLE off while Wi-Fi is up, `dashboard_import` of the base file at `${respeaker_ref}`. The `ota: http_request` and `update:` blocks stay commented out on purpose: the release workflow builds this file with ewt-gen, which adds them. Do not uncomment them in a commit.
- `respeaker_xvf3800_i2s_master_v1.0.9_48k.bin` — XMOS firmware image (Seeed I2S master, 48 kHz), served over raw GitHub URL and flashed by the component's DFU code.
- Sounds: there is no `sounds/` directory here. The core gets the Opus sounds from Respeaker-Lite-ESPHome-integration `sounds/` at `${satellite_core_ref}` (equal to `${respeaker_lite_ref}`). Both media player pipelines are `format: FLAC`, so a new MP3 or WAV sound adds that decoder back.
- `ha/` — Home Assistant script snippet that calls the device's `set_led_color` API action.

## Commands

There are no tests and no linters. The only CI is `.github/workflows/release.yaml`, which builds and publishes releases. Everything goes through the ESPHome CLI:

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

The example config gets the packages from GitHub at `${respeaker_ref}`, `external_components` resolve from GitHub too, and `packages/base.yaml` always gets the core from GitHub at `${respeaker_lite_ref}`. So a fresh checkout validates the *published* code, not the working tree.

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

To test **core** edits, or XVF edits that need an unreleased core, check out Respeaker-Lite-ESPHome-integration next to this repository and temporarily replace the `satellite_core` package in `packages/base.yaml` with four `!include ../../Respeaker-Lite-ESPHome-integration/packages/core/<file>.yaml` entries. Do not commit that switch. To verify a refactor, diff the merged `esphome config` output before and after.

To test **C++** edits, temporarily switch `external_components` in `packages/base.yaml` to `source: {type: local, path: esphome/components}`. Do not commit that switch.

The refs are parameterised: `${respeaker_ref}` drives the packages, the C++ components, and the DFU firmware URL together. Keep them in lockstep. Its default in `packages/base.yaml` is the current release tag, not `main`. `${respeaker_lite_ref}` (a Lite release tag, set in `packages/base.yaml`) selects the core, the sounds, and the `kenobi` and `snooze` models. The Lite tag must exist before an XVF release: the release workflow checks it, and the core at that tag must have every ID that the XVF packages `!extend`.

Releases use plain CalVer tags without a `v`, for example `2026.9.1`. To release, set the new version in four places in one commit: `esphome.project.version` and the `respeaker_ref` default in `packages/base.yaml`, and `respeaker_ref` in `config/respeaker-xvf-satellite-example.yaml` and `config/respeaker-xvf-satellite-factory.yaml`. Push to `main`. `.github/workflows/release.yaml` then works like Koala's: `prepare` checks that the tag does not exist and that all three `respeaker_ref` values equal the version; `build` installs the pinned `ESPHOME_VERSION`, points the factory config's `respeaker_ref` at the commit SHA (the C++, the XMOS image and the sounds load from this repo at that ref, and the tag does not exist yet), and runs the pinned `ewt-gen`, whose `--import-url` still pins adopted devices to the tag; `publish-pages` deploys the web installer and `manifest.json` to `https://formatbce.github.io/Respeaker-XVF3800-ESPHome-integration` (factory devices update from it); `release` creates the tag and the GitHub release with the binaries, only after Pages succeeded. Pages must use "GitHub Actions" as its source. There is no `ota/` mirror, unlike Koala: no device uses an older update URL. A push without a new version does nothing. Do not tag by hand.

`i2s_audio` is the stock ESPHome component. The microphones run at 48 kHz (`i2s_mics_raw`), the same clock as the speaker. The `respeaker_xvf3800` microphone platform (`microphone/decimating_microphone.*`) makes `i2s_mics` at 16 kHz by keeping 1 frame of 3, with no filter. This is exact because the DSP processes at 16 kHz, so the 48 kHz stream has no content above 8 kHz. Do not switch back to the stock `resampler` microphone: with esp-audio-libs 4.0.1 and 16 taps it cuts 4 kHz by 2 dB, 6 kHz by 8 dB and 7.5 kHz by 17 dB (two pre-filter biquads at 6.7 kHz, not configurable; 128 taps still lose 6 dB at 7 kHz), which degrades the wake word and STT (issue #69). This needs ESPHome 2026.10.0 (`min_version`, and `ESPHOME_VERSION` in the release workflow). It replaces the patched `i2s_audio` from `formatBCE/esphome@respeaker_microphone`, which did the same decimation inside the driver.

## Architecture

### Hub and children

`RespeakerXVF3800` (`respeaker_xvf3800.h/.cpp`) is an `i2c::I2CDevice` hub at address `0x2C`. It owns three optional `PollingComponent` children — `MuteSwitch`, `DFUVersionTextSensor`, `LEDBeamSensor` — each of which holds a back-pointer set in `to_code()` and does nothing but call a hub method in `update()`. Add new entities the same way: declare the class in `__init__.py`, add an optional schema key, create it and wire both directions in `to_code()`.

`AUTO_LOAD` lists `number` and `select` although the component defines no such platforms; the example config uses template `number`/`select` entities instead.

### XMOS control protocol

All DSP access is `(resid, cmd, payload)` over I2C, mirroring Respeaker's `xvf_host.py`. Writes go through `xmos_write_bytes()`. Reads set the high bit (`0x80`) on the command byte, then read `1 + n` bytes where byte 0 is a `TransportProtocolReturnCode`. Only `CTRL_DONE` means the payload is valid; `CTRL_WAIT` and `SERVICER_COMMAND_RETRY` (`0x40`) are normal transient answers and must be retried, not logged as errors. Resource IDs and command numbers are named constants at the top of the header — take new ones from `xvf_host.py` and record the source in a comment, as the existing constants do.

### Beam direction and beam lock

The DSP reports four azimuth slots (radians) from `AEC_SERVICER_RESID`/cmd 75: beam 1, beam 2, free-running, auto-select. `read_led_beam_direction()` normally reads slot 3 (auto-select) and maps it to one of 12 LED positions. `lock_beam()` captures the current azimuth, writes it to the fixed-beam registers, enables fixed-beam mode, and flips `beam_locked_` so subsequent reads follow slot 0 instead. `packages/voice-assistant.yaml` calls `lock_beam()` from the core's `wake_word_start_hook` (if the `Beam lock` switch is on) and `unlock_beam()` on STT VAD end and when the pipeline ends, so the LED ring stays pointed at the speaker during an utterance.

### DFU firmware update

`__init__.py` downloads the firmware at *build* time, checks its MD5, and embeds it as a PROGMEM array. `can_proceed()` blocks ESPHome startup until the on-chip version is read and matches, or the component fails; on a mismatch `setup()` starts the update itself (`start_dfu_update()`, the same path as the `respeaker_xvf3800.flash` action), a non-blocking state machine in `loop()` that sends 128-byte blocks. `packages/hardware.yaml` reports the result in the `dsp_status` text sensor (`OK`, `Update failed` from `on_error`, `No response` when the component failed without a DFU error), set by an `on_boot` handler that runs after the component can proceed. Progress and errors reach YAML through `on_begin`/`on_progress`/`on_end`/`on_error` triggers, compiled in only when `USE_RESPEAKER_XVF3800_STATE_CALLBACK` is defined. Bumping the bundled firmware means updating the binary, the `version`, and the `md5` in `packages/hardware.yaml` together.

### LED ring

The ring is 12 RGB LEDs written as one 12-entry `uint32_t` array through `set_led_ring()`. All animation lives in YAML, now in `packages/leds.yaml`: a 50 ms `interval` dispatches on the `current_led_effect` global to one of the `update_*_effect` scripts, and `control_leds` decides which effect the current device state calls for. Add an effect by adding a script plus a branch in that interval — not by touching C++.

`set_led_ring()` picks the command from the version read off the chip: `LED_RING_COLOR` is cmd 19 from XMOS firmware 1.0.8 on, cmd 18 before (1.0.8 swapped it with `DOA_VALUE`). `dfu_get_version_()` invalidates the cached frame, so the next frame goes out with the right command.

### Timers, alarm, and snooze

`timer_ringing` (internal switch) is the single ring path for HA timers and the alarm: `on_turn_on` enables the `stop` model (and `snooze` if `snooze_enabled`), starts the repeating ring and the `ring_timeout` script (15 min, `mode: restart`); `on_turn_off` stops that script and disables both models. Keep the timeout in a script: a `delay` inside `on_turn_on` keeps running after turn-off (ESPHome runs re-triggered automation delays in parallel) and cuts a later ring short.

"Snooze" (model by @dlarkinsPonderosa, kept in Respeaker-Lite-ESPHome-integration `microwakeword/models/v2/` with kenobi, loaded at `${respeaker_lite_ref}`) is handled in the ringing branch of `on_wake_word_detected`, matched by the model's `wake_word` string. `snooze_ring` stores an epoch deadline in the restored `snooze_until` global (0 = none) and turns the ring off; a 1 s `interval` turns `timer_ringing` on at the deadline, and drops a deadline that is more than 15 min old (device was off). Without a valid clock, "Snooze" is ignored and the ring continues. The `stop` model stays off during the snooze window on purpose, so a false "Stop" cannot lose a wake-up; `Cancel snooze`, turning `alarm_on` off, setting `alarm_time`, or turning `snooze_enabled` off clear the deadline; the `alarm_on` case is detected in the 1 s interval. All of this lives in Lite's `packages/core/timers-alarm.yaml` and `packages/core/voice-assistant.yaml`; this repository only adds the timer-tick LED animation. Any other wake word while ringing only stops the ring, as on the Voice PE.

### Mute button

The DSP keeps its built-in mute action: a press toggles mute in the DSP, and `MuteSwitch` sees it on its 1 s poll. `MuteButtonBinarySensor` (`mute_button`, 50 ms poll) only reads the button through `GPI_VALUE_ALL` (IO config servicer, resid 36, cmd 6, bit 0). The bit is low while pressed on firmware 1.0.9 (measured), despite `xvf_host.py` calling it active-referenced; the DSP toggles mute on the press edge. `packages/hardware.yaml` uses it for the Voice PE factory reset hold (10 s warning, 22 s confirm, reset on release; at 10 s it toggles `mic_mute_switch` back, so a hold never changes mute). The `factory_reset_phase` global (0 none, 1 warning, 2 confirmed) is an input of `control_leds` and wins over every state except a failed DSP: orange breathe, then solid red. The factory config uses the sensor as the Improv authorizer. Do not set `MUTE_FUNCTION_ENABLE` to 0: the hardware mute must keep working when the ESP misbehaves.

The ring is not an addressable output, so the `LED Ring` light (`led_ring_light`, `platform: rgb`) does not write the LEDs; it drives the animation engine. It needs three template `output`s only because `platform: rgb` demands them — they are deliberately stubs, because that platform premultiplies colour by brightness and the engine needs the two apart. The light's `on_state` reads `remote_values` instead, and is the **single writer** of `user_led_ring_color_{r,g,b}`, `user_led_ring_brightness` (a plain global, not a `number`), `user_idle_effect` and `user_idle_speed`. Everything that used to write those globals — the `user_led_color_preset` select and the `set_led_color` API action — now calls `id(led_ring_light).make_call()` instead, and the values flow back out through `on_state`. Effect names map to engine strings in exactly one place, that `on_state` lambda; the four `lambda` light effects have empty bodies and exist only to populate Home Assistant's effect list.

The light owns the **idle** branch of `control_leds` only; every other device state still wins. Because `control_leds` early-returns when none of its cached inputs changed, a light change sets the `led_force_update` global to demand a repaint.
