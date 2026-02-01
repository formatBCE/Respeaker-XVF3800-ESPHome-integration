#pragma once

#include <vector>

#include "esphome/core/component.h"
#include "esphome/core/log.h"
#include "esphome/components/automation/automation.h"
#include "esphome/components/i2c/i2c.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/switch/switch.h"
#include "esphome/components/text_sensor/text_sensor.h"

namespace esphome {
namespace respeaker_xvf3800 {

class RespeakerXVF3800Component;

class RespeakerXVF3800MuteSwitch : public switch_::Switch, public Component {
 public:
  void set_parent(RespeakerXVF3800Component *parent) { this->parent_ = parent; }

 protected:
  void write_state(bool state) override;

  RespeakerXVF3800Component *parent_{nullptr};
};

class RespeakerXVF3800Component : public Component, public i2c::I2CDevice {
 public:
  void set_processing_timeout(uint32_t processing_timeout_ms) {
    this->processing_timeout_ms_ = processing_timeout_ms;
  }
  void set_mute_switch(RespeakerXVF3800MuteSwitch *mute_switch) { this->mute_switch_ = mute_switch; }
  void set_dfu_version(text_sensor::TextSensor *dfu_version) { this->dfu_version_ = dfu_version; }
  void set_led_beam_sensor(sensor::Sensor *led_beam_sensor) { this->led_beam_sensor_ = led_beam_sensor; }

  void add_on_begin_trigger(Trigger<> *trigger) { this->on_begin_triggers_.push_back(trigger); }
  void add_on_progress_trigger(Trigger<float> *trigger) { this->on_progress_triggers_.push_back(trigger); }
  void add_on_end_trigger(Trigger<> *trigger) { this->on_end_triggers_.push_back(trigger); }
  void add_on_error_trigger(Trigger<int> *trigger) { this->on_error_triggers_.push_back(trigger); }

  void setup() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA; }

 protected:
  uint32_t processing_timeout_ms_{0};
  RespeakerXVF3800MuteSwitch *mute_switch_{nullptr};
  text_sensor::TextSensor *dfu_version_{nullptr};
  sensor::Sensor *led_beam_sensor_{nullptr};
  std::vector<Trigger<> *> on_begin_triggers_{};
  std::vector<Trigger<float> *> on_progress_triggers_{};
  std::vector<Trigger<> *> on_end_triggers_{};
  std::vector<Trigger<int> *> on_error_triggers_{};
};

}  // namespace respeaker_xvf3800
}  // namespace esphome
