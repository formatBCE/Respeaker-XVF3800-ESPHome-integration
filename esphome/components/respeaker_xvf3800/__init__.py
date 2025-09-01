import hashlib
from pathlib import Path
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation, core, external_files
from esphome.components import i2c, switch, text_sensor, light, number, select
from esphome.const import (
    CONF_ID, 
    CONF_ON_ERROR,
    CONF_RAW_DATA_ID,
    CONF_TRIGGER_ID,
    CONF_URL,
    CONF_VERSION
)
from esphome.core import HexInt

# Dependency declarations
DEPENDENCIES = ["i2c"]
AUTO_LOAD = ["switch", "text_sensor", "number", "select"]
CODEOWNERS = ["@your_github_username"]  # Replace with your GitHub username

# Configuration keys
CONF_MUTE_SWITCH = "mute_switch"
CONF_DFU_VERSION = "dfu_version"
CONF_LED_EFFECT = "led_effect"
CONF_LED_SPEED = "led_speed"
CONF_LED_BRIGHTNESS = "led_brightness"
CONF_LED_RED = "led_red"
CONF_LED_GREEN = "led_green"
CONF_LED_BLUE = "led_blue"
CONF_FIRMWARE = "firmware"
CONF_MD5 = "md5"
CONF_ON_BEGIN = "on_begin"
CONF_ON_END = "on_end"
CONF_ON_PROGRESS = "on_progress"

DOMAIN = "respeaker_xvf3800"

# Create a namespace for the component
respeaker_xvf3800_ns = cg.esphome_ns.namespace('respeaker_xvf3800')
RespeakerXVF3800 = respeaker_xvf3800_ns.class_('RespeakerXVF3800', cg.Component, i2c.I2CDevice)
RespeakerXVF3800FlashAction = respeaker_xvf3800_ns.class_("RespeakerXVF3800FlashAction", automation.Action)

MuteSwitch = respeaker_xvf3800_ns.class_('MuteSwitch', switch.Switch, cg.PollingComponent)
DFUVersionTextSensor = respeaker_xvf3800_ns.class_('DFUVersionTextSensor', text_sensor.TextSensor, cg.PollingComponent)
LEDEffectSelect = respeaker_xvf3800_ns.class_('LEDEffectSelect', select.Select, cg.Component)
LEDSpeedNumber = respeaker_xvf3800_ns.class_('LEDSpeedNumber', number.Number, cg.Component)
LEDBrightnessNumber = respeaker_xvf3800_ns.class_('LEDBrightnessNumber', number.Number, cg.Component)
LEDRedNumber = respeaker_xvf3800_ns.class_('LEDRedNumber', number.Number, cg.Component)
LEDGreenNumber = respeaker_xvf3800_ns.class_('LEDGreenNumber', number.Number, cg.Component)
LEDBlueNumber = respeaker_xvf3800_ns.class_('LEDBlueNumber', number.Number, cg.Component)

DFUEndTrigger = respeaker_xvf3800_ns.class_("DFUEndTrigger", automation.Trigger.template())
DFUErrorTrigger = respeaker_xvf3800_ns.class_("DFUErrorTrigger", automation.Trigger.template())
DFUProgressTrigger = respeaker_xvf3800_ns.class_(
    "DFUProgressTrigger", automation.Trigger.template()
)
DFUStartTrigger = respeaker_xvf3800_ns.class_("DFUStartTrigger", automation.Trigger.template())


def _compute_local_file_path(url: str) -> Path:
    h = hashlib.new("sha256")
    h.update(url.encode())
    key = h.hexdigest()[:8]
    base_dir = external_files.compute_local_file_dir(DOMAIN)
    return base_dir / key


def download_firmware(config):
    url = config[CONF_URL]
    path = _compute_local_file_path(url)
    external_files.download_content(url, path)

    try:
        with open(path, "r+b") as f:
            firmware_bin = f.read()
    except FileNotFoundError as e:
        raise cv.Invalid(f"Could not open firmware file {path}: {e}") from e

    firmware_bin_md5 = hashlib.md5(firmware_bin).hexdigest()
    if firmware_bin_md5 != config[CONF_MD5]:
        raise cv.Invalid(f"{CONF_MD5} is not consistent with file contents")

    return config

# LED Effect options (0-4 as per actual device capabilities)
LED_EFFECTS = [
    "Off",           # 0 - turned off
    "Breath",        # 1 - breath effect
    "Rainbow",       # 2 - rainbow effect
    "Solid",         # 3 - solid color
    "Direction"      # 4 - direction of arrival
]

# Define the configuration schema for the component
CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(RespeakerXVF3800),
    cv.Optional(CONF_MUTE_SWITCH): switch.switch_schema(
        MuteSwitch,
        icon="mdi:microphone-off",
    ).extend(cv.polling_component_schema("1s")),
    cv.Optional(CONF_DFU_VERSION): text_sensor.text_sensor_schema(
        DFUVersionTextSensor,
        icon="mdi:chip",
    ).extend(cv.polling_component_schema("30s")),
    cv.Optional(CONF_LED_EFFECT): select.select_schema(
        LEDEffectSelect,
        icon="mdi:led-strip-variant",
    ).extend(cv.COMPONENT_SCHEMA),
    cv.Optional(CONF_LED_SPEED): number.number_schema(
        LEDSpeedNumber,
        icon="mdi:speedometer",
    ).extend(cv.COMPONENT_SCHEMA),
    cv.Optional(CONF_LED_BRIGHTNESS): number.number_schema(
        LEDBrightnessNumber,
        icon="mdi:brightness-6",
    ).extend(cv.COMPONENT_SCHEMA),
    cv.Optional(CONF_LED_RED): number.number_schema(
        LEDRedNumber,
        icon="mdi:palette",
    ).extend(cv.COMPONENT_SCHEMA),
    cv.Optional(CONF_LED_GREEN): number.number_schema(
        LEDGreenNumber,
        icon="mdi:palette",
    ).extend(cv.COMPONENT_SCHEMA),
    cv.Optional(CONF_LED_BLUE): number.number_schema(
        LEDBlueNumber,
        icon="mdi:palette",
    ).extend(cv.COMPONENT_SCHEMA),
    cv.GenerateID(CONF_RAW_DATA_ID): cv.declare_id(cg.uint8),
    cv.Optional(CONF_FIRMWARE): cv.All(
                {
                    cv.Required(CONF_URL): cv.url,
                    cv.Required(CONF_VERSION): cv.version_number,
                    cv.Required(CONF_MD5): cv.All(cv.string, cv.Length(min=32, max=32)),
                    cv.Optional(CONF_ON_BEGIN): automation.validate_automation(
                        {
                            cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(
                                DFUStartTrigger
                            ),
                        }
                    ),
                    cv.Optional(CONF_ON_END): automation.validate_automation(
                        {
                            cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(
                                DFUEndTrigger
                            ),
                        }
                    ),
                    cv.Optional(CONF_ON_ERROR): automation.validate_automation(
                        {
                            cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(
                                DFUErrorTrigger
                            ),
                        }
                    ),
                    cv.Optional(CONF_ON_PROGRESS): automation.validate_automation(
                        {
                            cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(
                                DFUProgressTrigger
                            ),
                        }
                    ),
                },
                download_firmware,
            ),
}).extend(cv.COMPONENT_SCHEMA).extend(i2c.i2c_device_schema(0x2C))


OTA_RESPEAKER_XVF3800_FLASH_ACTION_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.use_id(RespeakerXVF3800),
    }
)


@automation.register_action(
    "respeaker_xvf3800.flash",
    RespeakerXVF3800FlashAction,
    OTA_RESPEAKER_XVF3800_FLASH_ACTION_SCHEMA,
)
async def respeaker_xxvf3800_flash_action_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)

    return var

# This function is called by ESPHome to generate the C++ code for the component
async def to_code(config):
    # Create the main hub component
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)
        
    # Set up mute switch if configured
    if CONF_MUTE_SWITCH in config:
        mute_switch = cg.new_Pvariable(config[CONF_MUTE_SWITCH][CONF_ID])
        await cg.register_component(mute_switch, config[CONF_MUTE_SWITCH])
        await switch.register_switch(mute_switch, config[CONF_MUTE_SWITCH])
        cg.add(var.set_mute_switch(mute_switch))
        cg.add(mute_switch.set_parent(var))
        
    # Set up DFU version sensor if configured
    if CONF_DFU_VERSION in config:
        dfu_sensor = cg.new_Pvariable(config[CONF_DFU_VERSION][CONF_ID])
        await cg.register_component(dfu_sensor, config[CONF_DFU_VERSION])
        await text_sensor.register_text_sensor(dfu_sensor, config[CONF_DFU_VERSION])
        cg.add(var.set_dfu_version_sensor(dfu_sensor))
        cg.add(dfu_sensor.set_parent(var))
        
    # Set up LED effect select if configured
    if CONF_LED_EFFECT in config:
        led_effect_select = cg.new_Pvariable(config[CONF_LED_EFFECT][CONF_ID])
        await cg.register_component(led_effect_select, config[CONF_LED_EFFECT])
        await select.register_select(led_effect_select, config[CONF_LED_EFFECT], options=LED_EFFECTS)
        cg.add(var.set_led_effect_select(led_effect_select))
        cg.add(led_effect_select.set_parent(var))
        
    # Set up LED speed number if configured
    if CONF_LED_SPEED in config:
        led_speed_number = cg.new_Pvariable(config[CONF_LED_SPEED][CONF_ID])
        await cg.register_component(led_speed_number, config[CONF_LED_SPEED])
        await number.register_number(
            led_speed_number, 
            config[CONF_LED_SPEED], 
            min_value=1, 
            max_value=10, 
            step=1
        )
        cg.add(var.set_led_speed_number(led_speed_number))
        cg.add(led_speed_number.set_parent(var))
        
    # Set up LED brightness number if configured
    if CONF_LED_BRIGHTNESS in config:
        led_brightness_number = cg.new_Pvariable(config[CONF_LED_BRIGHTNESS][CONF_ID])
        await cg.register_component(led_brightness_number, config[CONF_LED_BRIGHTNESS])
        await number.register_number(
            led_brightness_number, 
            config[CONF_LED_BRIGHTNESS], 
            min_value=0, 
            max_value=255, 
            step=1
        )
        cg.add(var.set_led_brightness_number(led_brightness_number))
        cg.add(led_brightness_number.set_parent(var))
        
    # Set up LED color numbers if configured
    if CONF_LED_RED in config:
        led_red_number = cg.new_Pvariable(config[CONF_LED_RED][CONF_ID])
        await cg.register_component(led_red_number, config[CONF_LED_RED])
        await number.register_number(
            led_red_number, 
            config[CONF_LED_RED], 
            min_value=0, 
            max_value=255, 
            step=1
        )
        cg.add(var.set_led_red_number(led_red_number))
        cg.add(led_red_number.set_parent(var))
        
    if CONF_LED_GREEN in config:
        led_green_number = cg.new_Pvariable(config[CONF_LED_GREEN][CONF_ID])
        await cg.register_component(led_green_number, config[CONF_LED_GREEN])
        await number.register_number(
            led_green_number, 
            config[CONF_LED_GREEN], 
            min_value=0, 
            max_value=255, 
            step=1
        )
        cg.add(var.set_led_green_number(led_green_number))
        cg.add(led_green_number.set_parent(var))
        
    if CONF_LED_BLUE in config:
        led_blue_number = cg.new_Pvariable(config[CONF_LED_BLUE][CONF_ID])
        await cg.register_component(led_blue_number, config[CONF_LED_BLUE])
        await number.register_number(
            led_blue_number, 
            config[CONF_LED_BLUE], 
            min_value=0, 
            max_value=255, 
            step=1
        )
        cg.add(var.set_led_blue_number(led_blue_number))
        cg.add(led_blue_number.set_parent(var))

    if config_fw := config.get(CONF_FIRMWARE):
        firmware_version = config_fw[CONF_VERSION].split(".")
        path = _compute_local_file_path(config_fw[CONF_URL])

        try:
            with open(path, "r+b") as f:
                firmware_bin = f.read()
        except FileNotFoundError as e:
            raise core.EsphomeError(f"Could not open firmware file {path}: {e}")

        # Convert retrieved binary file to an array of ints
        rhs = [HexInt(x) for x in firmware_bin]
        # Create an array which will reside in program memory and set the pointer to it
        firmware_bin_arr = cg.progmem_array(config[CONF_RAW_DATA_ID], rhs)
        cg.add(var.set_firmware_bin(firmware_bin_arr, len(rhs)))
        cg.add(
            var.set_firmware_version(
                int(firmware_version[0]),
                int(firmware_version[1]),
                int(firmware_version[2]),
            )
        )

        use_state_callback = False
        for conf in config_fw.get(CONF_ON_BEGIN, []):
            trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID], var)
            await automation.build_automation(trigger, [], conf)
            use_state_callback = True
        for conf in config_fw.get(CONF_ON_PROGRESS, []):
            trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID], var)
            await automation.build_automation(trigger, [(float, "x")], conf)
            use_state_callback = True
        for conf in config_fw.get(CONF_ON_END, []):
            trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID], var)
            await automation.build_automation(trigger, [], conf)
            use_state_callback = True
        for conf in config_fw.get(CONF_ON_ERROR, []):
            trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID], var)
            await automation.build_automation(trigger, [(cg.uint8, "x")], conf)
            use_state_callback = True
        if use_state_callback:
            cg.add_define("USE_RESPEAKER_XVF3800_STATE_CALLBACK")
