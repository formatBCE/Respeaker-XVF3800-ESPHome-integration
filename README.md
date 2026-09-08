# reSpeaker XVF3800 — ESPHome voice satellite

ESPHome components and configuration packages that make a
[reSpeaker XVF3800 USB 4-Mic Array](https://github.com/respeaker/reSpeaker_XVF3800_USB_4MIC_ARRAY)
into a Home Assistant voice satellite.

The board has three parts. This project drives all of them:

| Part | Function | Component |
| --- | --- | --- |
| ESP32-S3 | Host. Runs ESPHome. | ESPHome core |
| XMOS XVF3800 | Audio DSP. Beam forming, mute, LED ring. | `respeaker_xvf3800` |
| TLV320AIC3104 | Audio codec. | `aic3104` |

> **Warning:** This project is under development. Use it at your own risk.
> Test reports are welcome.

---

## What you get

The device gives these entities to Home Assistant:

| Entity | Type | Function |
| --- | --- | --- |
| Microphone Mute | switch | Mutes the microphone array in the DSP |
| Mute-unmute sound | switch | Plays a sound when you mute the microphone |
| Wake sound | switch | Plays a sound when the wake word starts the pipeline |
| Beam lock | switch | Locks the microphone beam during one utterance |
| Alarm on | switch | Turns the alarm clock on |
| Alarm time | datetime | Sets the alarm time |
| Alarm action | select | Selects what the alarm does |
| Wake word sensitivity | select | Sets the wake word threshold |
| LED Ring Color Preset | select | Selects the LED ring colour |
| LED Ring | light | Sets the LED ring colour, the brightness and the idle effect |
| Firmware Version | text sensor | Shows the XMOS DSP firmware version |
| Current device time | text sensor | Shows the device clock |
| Next timer, Next timer name | sensor, text sensor | Show the first active timer |
| Media Player | media player | Plays announcements and media |
| Restart, Factory Reset | button | Restart and factory reset |

The **LED Ring** light controls the 12-LED ring. Read
[LED effects](#led-effects) for more information.

---

## Requirements

- ESPHome **2026.6.0** or later.
- Home Assistant with the ESPHome integration.
- A reSpeaker XVF3800 USB 4-Mic Array board.
- A USB-C cable and a computer that can flash the board.

This project needs a **patched `i2s_audio` component**. The standard ESPHome
component does not work with this board. The `base.yaml` package gets the patch
from a fork. You do not need to install it yourself.

---

## Install

### 1. Make the secrets file

Copy `config/secrets.yaml.example` to `config/secrets.yaml`. Set your own values.

```yaml
wifi_ssid: "YOUR_WIFI_NAME"
wifi_password: "YOUR_WIFI_PASSWORD"
ota_password: "YOUR_OTA_PASSWORD"
api_key: "YOUR_BASE64_API_ENCRYPTION_KEY"
```

Make a new API key at the [ESPHome API page](https://esphome.io/components/api.html).
Keep `secrets.yaml` out of version control.

### 2. Make the device configuration

Create a file for your device. The packages give all the other configuration.

```yaml
substitutions:
  name: respeaker-xvf3800-assistant
  friendly_name: reSpeaker XVF3800 Assistant
  respeaker_ref: main

packages:
  respeaker:
    url: https://github.com/formatBCE/Respeaker-XVF3800-ESPHome-integration
    ref: ${respeaker_ref}
    refresh: 1d
    files:
      - packages/base.yaml
      - packages/hardware.yaml
      - packages/voice-assistant.yaml
      - packages/leds.yaml
      - packages/timers-alarm.yaml

# A remote package cannot read secrets, so the credentials go here.
# ESPHome joins these blocks with the blocks in the packages.
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

api:
  encryption:
    key: !secret api_key

ota:
  - platform: esphome
    id: ota_esphome
    password: !secret ota_password
```

`config/respeaker-xvf-satellite-example.yaml` holds this same configuration.

### 3. Build and flash

Connect the board with USB. Then run:

```bash
esphome run config/respeaker-xvf-satellite-example.yaml
```

The first build takes several minutes, because ESPHome compiles the ESP-IDF
framework. Later builds are much faster.

### 4. Add the device to Home Assistant

Home Assistant finds the device automatically. Give it the API key from your
`secrets.yaml` file.

---

## Configuration

Set any of these substitutions in your own configuration. Your value always
wins, because a substitution in the main configuration overrides the same
substitution in a package.

| Substitution | Default | Function |
| --- | --- | --- |
| `name` | `respeaker-xvf3800-assistant` | ESPHome node name |
| `friendly_name` | `reSpeaker XVF3800 Assistant` | Display name |
| `respeaker_ref` | `main` | Ref for the packages, the components, and the firmware |
| `i2s_audio_ref` | `respeaker_microphone` | Ref for the patched `i2s_audio` fork |
| `hidden_ssid` | `"false"` | Set this to `"true"` for a hidden network |
| `log_level` | `INFO` | Logger level |
| `voice_assist_*_phase_id` | `1` to `11` | Phase constants for the LED ring |
| `*_sound_file` | Voice PE sound URLs | URL of each notification sound |

**Caution:** All substitutions share one namespace. A name that you set in your
configuration replaces that name in every package.

---

## Change the configuration

The packages merge into your configuration. They do not replace it.

**Change a setting.** Set the substitution:

```yaml
substitutions:
  log_level: DEBUG
```

**Add an entity.** Declare it. Lists join together:

```yaml
sensor:
  - platform: uptime
    name: "Uptime"
```

**Add steps to a script.** Use `!extend`. The new steps go after the existing
steps:

```yaml
script:
  - id: !extend control_leds
    then:
      - logger.log: "LEDs updated"
```

**Delete an entity.** Use `!remove`:

```yaml
button:
  - id: !remove restart_button
```

**Delete a whole component.** Use `!remove` on the key:

```yaml
debug: !remove
```

**Replace a script.** Delete the old script. Then add a new script with a
**different** id. You cannot delete an id and add the same id in one
configuration.

**Caution:** Do not delete a whole package file. Read
[Package layout](#package-layout) first.

---

## Pin a version

`main` gets new commits at any time. Pin the device to one version for a stable
build. Set `respeaker_ref` to a tag or a commit:

```yaml
substitutions:
  respeaker_ref: 67f4afe
```

One substitution controls three things: the YAML packages, the C++ components,
and the DSP firmware. So the YAML and the firmware always match. If you pin only
the `packages:` block, ESPHome takes the YAML from your tag but the C++ from
`main`. That mismatch is difficult to find.

**Note:** `esp32.framework.version` is `recommended`, so a new ESPHome release
can still change the ESP-IDF version. A pinned `respeaker_ref` does not give a
fully reproducible build.

---

## Package layout

| Package | Contents |
| --- | --- |
| `base.yaml` | `esphome`, `esp32`, `psram`, `logger`, `network`, `wifi`, `api`, `i2c`, `debug`, `external_components` |
| `hardware.yaml` | `i2s_audio`, `microphone`, `speaker`, `audio_dac`, `respeaker_xvf3800` with the DFU firmware |
| `voice-assistant.yaml` | `micro_wake_word`, `voice_assistant`, `media_player`, `media_source`, `audio_file` |
| `leds.yaml` | LED globals, the animation interval, the effect scripts, the colour preset |
| `timers-alarm.yaml` | `time`, `datetime`, the alarm and timer entities, the timer scripts |

**Caution:** Include all five packages. They are separate files for maintenance,
but they are not independent. The `leds.yaml` package reads entities from
`hardware.yaml`, `voice-assistant.yaml`, and `timers-alarm.yaml`. The
`control_leds` script runs from `wifi`, `api`, `on_boot`, and 12 voice assistant
triggers. If you remove one file, the build fails.

To change one part, use `!extend` or `!remove`. Do not delete a package.

---

## First boot and firmware update

The `respeaker_xvf3800` component holds a copy of the XMOS DSP firmware. At boot
the component reads the version from the chip. ESPHome waits at startup until
this read is complete.

If the version on the chip is different from the version in the build, call the
`respeaker_xvf3800.flash` action. The component then sends the firmware in
128-byte blocks. The update does not block the main loop. The `on_begin`,
`on_progress`, `on_end`, and `on_error` triggers report the progress.

To change the firmware version, change three things together:

1. The `.bin` file in the repository root.
2. The `version` value in `packages/hardware.yaml`.
3. The `md5` value in `packages/hardware.yaml`.

The build fails if the MD5 sum does not agree with the file.

---

## Home Assistant setup

### LED colour script

Import `ha/change_color_script.yaml` as a Home Assistant script. The script
selects the device and sets the LED ring colour.

### API actions

The device gives four actions to Home Assistant:

| Action | Parameters | Function |
| --- | --- | --- |
| `set_led_color` | `red`, `green`, `blue` | Sets the LED ring colour |
| `start_va` | none | Starts the voice pipeline |
| `stop_va` | none | Stops the voice pipeline |
| `set_time_zone` | `posix_time_zone` | Sets the device time zone |

Call `set_time_zone` one time after you add the device. The device saves the
value and restores it at the next boot.

### Events

The device sends three events to Home Assistant. Use them as automation
triggers.

| Event | Data | Sent when |
| --- | --- | --- |
| `esphome.wake_word_detected` | `wake_word` | The device detects a wake word |
| `esphome.stt_text` | `text` | Speech to text gives a result |
| `esphome.tts_uri` | `uri` | Text to speech gives a response URL |

### Play the response on an external speaker

You can trigger an automation on `esphome.tts_uri` and send the `uri` to another
speaker, for example a Sonos. This works, but you must know three limits first.

Set the conversation agent to ask no follow-up questions. An external speaker
gives no echo signal to the XVF3800 canceller. If the agent sets
`continue_conversation`, the microphone stays open, and the device can hear its
own response as a new command.

The local media player still gets the same URL. It downloads the audio and it
decodes the audio a second time. To stop this path, add
`voice_assistant: media_player: !remove` to your configuration. To hide the
entity from Home Assistant, set `internal: true` on `external_media_player`.

The stop word gets its timing from the **local** announcement state. So the stop
word can start late, or stop early, when the audio plays on an external speaker.

---

## LED effects

The ring has 12 RGB LEDs. The DSP controls them over I2C. The driver writes the
ring as one 12-entry array.

All animation is in YAML, in `packages/leds.yaml`:

1. A 50 ms interval reads the `current_led_effect` global.
2. The interval calls one `update_*_effect` script.
3. The `control_leds` script decides which effect the device state needs.

To add an effect, add a script and add a branch in the interval. Do not change
the C++ component.

The `update_rainbow_effect` script works, but no `control_leds_*` script selects
it. Call `led_set_effect` to use it.

### The LED Ring light

The **LED Ring** light is an ESPHome `rgb` light. The ring is not an addressable
output, so the light does not write the LEDs. The light writes the animation
engine instead.

The light owns the idle look. If you turn the light on, the ring shows the light
colour and the light effect while the satellite waits for the wake word. If you
turn the light off, the ring stays dark. The voice, timer and error animations
always come first.

The light is the one authority for the ring colour and the ring level:

- The light colour is also the accent colour of every animation.
- The light brightness is the master level of every animation. The level stays
  the same when you turn the light off, so the voice animations keep the last
  level.
- The `LED Ring Color Preset` select and the `set_led_color` action write the
  light. The light then writes the colour globals.

The light gives these effects to Home Assistant:

| Effect | Animation |
| --- | --- |
| None | A steady ring |
| Breathe | The ring fades in and out |
| Twinkle | Single LEDs fade in and out |
| Comet CW | A comet turns clockwise |
| Comet CCW | A comet turns counterclockwise |

The light keeps the largest colour component at full, and moves the level to the
brightness axis. The hue stays the same. So `set_led_color` with `(128, 64, 0)`
reads back as `(255, 128, 0)` at half brightness.

A volume change or a mute change shows the volume for 2 seconds. The light
returns after that.

### Beam direction

The DSP reports the direction of the voice. The `update_led_beam_effect` script
shows this direction on the ring. When the wake word starts the pipeline, the
device locks the beam to the current direction. The device releases the beam at
the end of the pipeline. So the ring stays on the speaker during one utterance.

The **Beam lock** switch turns this behaviour on and off. Beam lock reads the
direction from the `led_beam_sensor` poll. Keep that poll on, or beam lock has
no direction to use.

---

## Develop the components

The packages get the C++ components from GitHub, so a new checkout builds the
**published** code and not your working tree.

To build your local changes, change the `external_components` block in
`packages/base.yaml`:

```yaml
external_components:
  - source:
      type: local
      path: esphome/components
    components: [respeaker_xvf3800, aic3104]
```

Do not commit this change.

To test a change to the packages, include them from disk:

```yaml
packages:
  base: !include ../packages/base.yaml
  hardware: !include ../packages/hardware.yaml
  voice_assistant: !include ../packages/voice-assistant.yaml
  leds: !include ../packages/leds.yaml
  timers_alarm: !include ../packages/timers-alarm.yaml
```

Useful commands:

```bash
esphome config config/...yaml    # validate the merged configuration
esphome compile config/...yaml   # build the firmware and check the C++
esphome logs config/...yaml      # read the device logs
esphome clean config/...yaml     # clean after a component or firmware change
```

Run `esphome clean` after you change the component Python code or the firmware
file.

---

## Troubleshooting

**The I2C scan does not find address 0x2C.** Check the board power. The XMOS DSP
needs about two seconds to boot. The component waits for this.

**The startup stops at the firmware version read.** The DSP does not answer.
Power the board off and on. Then read the logs at `DEBUG` level.

**There is no audio.** Check that the `aic3104` codec is at address 0x18 in the
I2C scan. Check that the media player volume is not zero.

**The wake word does not start the pipeline.** Check that the microphone is not
muted. Lower the value of the **Wake word sensitivity** select.

**The build uses old package files.** ESPHome caches a remote package for the
`refresh` time. Set `refresh: 0s` while you test.

**The response plays many seconds late.** Home Assistant sends the text to
speech audio while the engine still makes it. So a slow engine gives a slow
download. Test with a static audio file on the same host. If the static file is
fast, the cause is the engine. Use a local text to speech engine to make the
delay smaller.

**The LED ring stays off.** The `control_leds` script did not run. Check the
connection to Home Assistant, because the LED state follows the API state.

---

## Known issues

1. The board has no buttons. So you can only stop a timer or a response when you
   say "stop". You cannot start the pipeline by hand.
2. There is no hardware volume control. Only the software volume works.

---

## Credits

- [formatBCE](https://github.com/formatBCE) — components and configuration.
- The XMOS control protocol follows Respeaker's `xvf_host.py`.
- The notification sounds come from the
  [Home Assistant Voice PE](https://github.com/esphome/home-assistant-voice-pe) project.
