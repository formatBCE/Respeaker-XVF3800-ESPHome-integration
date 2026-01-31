import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import i2c, audio_dac
from esphome.const import CONF_ID

DEPENDENCIES = ["i2c", "audio_dac"]
AUTO_LOAD = []

aic3104_ns = cg.esphome_ns.namespace("aic3104")
AIC3104 = aic3104_ns.class_("AIC3104", audio_dac.AudioDac, cg.Component, i2c.I2CDevice)

CONFIG_SCHEMA = cv.All(
    audio_dac.AUDIO_DAC_SCHEMA.extend(
        {
            cv.GenerateID(): cv.declare_id(AIC3104),
        }
    ).extend(cv.COMPONENT_SCHEMA).extend(i2c.i2c_device_schema(0x18))
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)
    await audio_dac.register_audio_dac(var, config)
