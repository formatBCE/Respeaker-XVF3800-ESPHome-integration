import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import audio_dac, i2c
from esphome.const import CONF_ID

aic3104_ns = cg.esphome_ns.namespace("aic3104")
AIC3104AudioDac = aic3104_ns.class_(
    "AIC3104AudioDac", cg.Component, i2c.I2CDevice, audio_dac.AudioDac
)

CONFIG_SCHEMA = (
    audio_dac.AUDIO_DAC_SCHEMA.extend(
        {
            cv.GenerateID(): cv.declare_id(AIC3104AudioDac),
        }
    )
    .extend(i2c.i2c_device_schema(0x18))
    .extend(cv.COMPONENT_SCHEMA)
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)
    await audio_dac.register_audio_dac(var, config)
