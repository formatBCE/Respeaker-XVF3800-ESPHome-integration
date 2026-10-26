import esphome.codegen as cg
from esphome.components import audio, microphone
import esphome.config_validation as cv
from esphome.const import (
    CONF_BITS_PER_SAMPLE,
    CONF_CHANNELS,
    CONF_ID,
    CONF_MICROPHONE,
)

from .. import respeaker_xvf3800_ns

AUTO_LOAD = ["audio"]
DEPENDENCIES = ["microphone"]

# The XVF3800 processes at 16 kHz and its I2S master firmware outputs 48 kHz.
SOURCE_SAMPLE_RATE = 48000
SAMPLE_RATE = 16000

DecimatingMicrophone = respeaker_xvf3800_ns.class_(
    "DecimatingMicrophone", cg.Component, microphone.Microphone
)


def _set_stream_limits(config):
    # Only the sample rate changes; the bits and channels are those selected from the source microphone
    source = config[CONF_MICROPHONE]
    audio.set_stream_limits(
        min_bits_per_sample=source[CONF_BITS_PER_SAMPLE],
        max_bits_per_sample=source[CONF_BITS_PER_SAMPLE],
        min_channels=len(source[CONF_CHANNELS]),
        max_channels=len(source[CONF_CHANNELS]),
        min_sample_rate=SAMPLE_RATE,
        max_sample_rate=SAMPLE_RATE,
    )(config)
    return config


CONFIG_SCHEMA = cv.All(
    microphone.MICROPHONE_SCHEMA.extend(
        {
            cv.GenerateID(): cv.declare_id(DecimatingMicrophone),
            cv.Required(CONF_MICROPHONE): microphone.microphone_source_schema(
                min_bits_per_sample=16,
                max_bits_per_sample=32,
                min_channels=1,
                max_channels=2,
            ),
        }
    ).extend(cv.COMPONENT_SCHEMA),
    _set_stream_limits,
)

FINAL_VALIDATE_SCHEMA = cv.Schema(
    {
        cv.Required(CONF_MICROPHONE): microphone.final_validate_microphone_source_schema(
            "respeaker_xvf3800", sample_rate=SOURCE_SAMPLE_RATE
        ),
    },
    extra=cv.ALLOW_EXTRA,
)


async def to_code(config):
    mic_source = await microphone.microphone_source_to_code(config[CONF_MICROPHONE])
    var = cg.new_Pvariable(config[CONF_ID], mic_source)
    await cg.register_component(var, config)
    await microphone.register_microphone(var, config)
