import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation
from esphome.components import i2c, sensor, switch, text_sensor
from esphome.const import (
    CONF_ADDRESS,
    CONF_ID,
    CONF_ICON,
    CONF_NAME,
    CONF_TRIGGER_ID,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_UPDATE_INTERVAL,
    CONF_ACCURACY_DECIMALS,
)

CONF_PROCESSING_TIMEOUT = "processing_timeout"
CONF_MUTE_SWITCH = "mute_switch"
CONF_DFU_VERSION = "dfu_version"
CONF_LED_BEAM_SENSOR = "led_beam_sensor"
CONF_FIRMWARE = "firmware"
CONF_URL = "url"
CONF_VERSION = "version"
CONF_MD5 = "md5"
CONF_ON_BEGIN = "on_begin"
CONF_ON_PROGRESS = "on_progress"
CONF_ON_END = "on_end"
CONF_ON_ERROR = "on_error"

respeaker_xvf3800_ns = cg.esphome_ns.namespace("respeaker_xvf3800")
RespeakerXVF3800Component = respeaker_xvf3800_ns.class_(
    "RespeakerXVF3800Component", cg.Component, i2c.I2CDevice
)
RespeakerXVF3800MuteSwitch = respeaker_xvf3800_ns.class_(
    "RespeakerXVF3800MuteSwitch", switch.Switch, cg.Component
)
RespeakerXVF3800OnBeginTrigger = respeaker_xvf3800_ns.class_(
    "RespeakerXVF3800OnBeginTrigger", automation.Trigger.template()
)
RespeakerXVF3800OnProgressTrigger = respeaker_xvf3800_ns.class_(
    "RespeakerXVF3800OnProgressTrigger", automation.Trigger.template(cg.float_)
)
RespeakerXVF3800OnEndTrigger = respeaker_xvf3800_ns.class_(
    "RespeakerXVF3800OnEndTrigger", automation.Trigger.template()
)
RespeakerXVF3800OnErrorTrigger = respeaker_xvf3800_ns.class_(
    "RespeakerXVF3800OnErrorTrigger", automation.Trigger.template(cg.int_)
)

FIRMWARE_SCHEMA = cv.Schema(
    {
        cv.Optional(CONF_URL): cv.url,
        cv.Optional(CONF_VERSION): cv.string,
        cv.Optional(CONF_MD5): cv.string,
        cv.Optional(CONF_ON_BEGIN): automation.validate_automation(
            {
                cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(
                    RespeakerXVF3800OnBeginTrigger
                )
            }
        ),
        cv.Optional(CONF_ON_PROGRESS): automation.validate_automation(
            {
                cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(
                    RespeakerXVF3800OnProgressTrigger
                )
            }
        ),
        cv.Optional(CONF_ON_END): automation.validate_automation(
            {
                cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(
                    RespeakerXVF3800OnEndTrigger
                )
            }
        ),
        cv.Optional(CONF_ON_ERROR): automation.validate_automation(
            {
                cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(
                    RespeakerXVF3800OnErrorTrigger
                )
            }
        ),
    }
)

MUTE_SWITCH_SCHEMA = switch.SWITCH_SCHEMA.extend(
    {
        cv.GenerateID(): cv.declare_id(RespeakerXVF3800MuteSwitch),
        cv.Optional(CONF_UPDATE_INTERVAL): cv.positive_time_period_milliseconds,
    }
)

DFU_VERSION_SCHEMA = text_sensor.TEXT_SENSOR_SCHEMA.extend(
    {
        cv.Optional(CONF_ICON): cv.icon,
        cv.Optional(CONF_NAME): cv.string,
        cv.Optional(CONF_UPDATE_INTERVAL): cv.positive_time_period_milliseconds,
    }
)

LED_BEAM_SENSOR_SCHEMA = sensor.SENSOR_SCHEMA.extend(
    {
        cv.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        cv.Optional(CONF_ACCURACY_DECIMALS): cv.int_,
        cv.Optional(CONF_UPDATE_INTERVAL): cv.positive_time_period_milliseconds,
    }
)

CONFIG_SCHEMA = (
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(RespeakerXVF3800Component),
            cv.Optional(CONF_PROCESSING_TIMEOUT): cv.positive_time_period_milliseconds,
            cv.Optional(CONF_MUTE_SWITCH): MUTE_SWITCH_SCHEMA,
            cv.Optional(CONF_DFU_VERSION): DFU_VERSION_SCHEMA,
            cv.Optional(CONF_LED_BEAM_SENSOR): LED_BEAM_SENSOR_SCHEMA,
            cv.Optional(CONF_FIRMWARE): FIRMWARE_SCHEMA,
        }
    )
    .extend(i2c.i2c_device_schema(0x2C))
    .extend(cv.COMPONENT_SCHEMA)
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)

    if CONF_PROCESSING_TIMEOUT in config:
        cg.add(
            var.set_processing_timeout(config[CONF_PROCESSING_TIMEOUT].total_milliseconds)
        )

    if CONF_MUTE_SWITCH in config:
        mute_switch = cg.new_Pvariable(config[CONF_MUTE_SWITCH][CONF_ID])
        await cg.register_component(mute_switch, config[CONF_MUTE_SWITCH])
        await switch.register_switch(mute_switch, config[CONF_MUTE_SWITCH])
        cg.add(mute_switch.set_parent(var))
        cg.add(var.set_mute_switch(mute_switch))

    if CONF_DFU_VERSION in config:
        dfu_version = await text_sensor.new_text_sensor(config[CONF_DFU_VERSION])
        cg.add(var.set_dfu_version(dfu_version))

    if CONF_LED_BEAM_SENSOR in config:
        led_beam_sensor = await sensor.new_sensor(config[CONF_LED_BEAM_SENSOR])
        cg.add(var.set_led_beam_sensor(led_beam_sensor))

    firmware = config.get(CONF_FIRMWARE)
    if firmware:
        if CONF_ON_BEGIN in firmware:
            for entry in firmware[CONF_ON_BEGIN]:
                trigger = cg.new_Pvariable(entry[CONF_TRIGGER_ID])
                cg.add(var.add_on_begin_trigger(trigger))
                await automation.build_automation(trigger, [], entry)

        if CONF_ON_PROGRESS in firmware:
            for entry in firmware[CONF_ON_PROGRESS]:
                trigger = cg.new_Pvariable(entry[CONF_TRIGGER_ID])
                cg.add(var.add_on_progress_trigger(trigger))
                await automation.build_automation(trigger, [(cg.float_, "x")], entry)

        if CONF_ON_END in firmware:
            for entry in firmware[CONF_ON_END]:
                trigger = cg.new_Pvariable(entry[CONF_TRIGGER_ID])
                cg.add(var.add_on_end_trigger(trigger))
                await automation.build_automation(trigger, [], entry)

        if CONF_ON_ERROR in firmware:
            for entry in firmware[CONF_ON_ERROR]:
                trigger = cg.new_Pvariable(entry[CONF_TRIGGER_ID])
                cg.add(var.add_on_error_trigger(trigger))
                await automation.build_automation(trigger, [(cg.int_, "x")], entry)
