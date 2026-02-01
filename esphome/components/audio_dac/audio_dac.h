#pragma once

#include "esphome/core/component.h"

namespace esphome {
namespace audio_dac {

class AudioDac : public Component {
 public:
  virtual bool set_mute_on() = 0;
  virtual bool set_mute_off() = 0;
  virtual bool set_volume(float volume) = 0;

  virtual bool is_muted() = 0;
  virtual float volume() = 0;
};

}  // namespace audio_dac
}  // namespace esphome
