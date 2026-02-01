#pragma once

#include "esphome/core/component.h"
#include "esphome/components/i2c/i2c.h"
#include "esphome/components/audio_dac/audio_dac.h"

namespace esphome {
namespace aic3104 {

class AIC3104AudioDac : public Component, public i2c::I2CDevice, public audio_dac::AudioDac {
 public:
  void setup() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA; }
};

}  // namespace aic3104
}  // namespace esphome
