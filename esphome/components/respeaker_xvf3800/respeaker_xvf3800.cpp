#include "respeaker_xvf3800.h"

namespace esphome {
namespace respeaker_xvf3800 {

static const char *const TAG = "respeaker_xvf3800";

void RespeakerXVF3800MuteSwitch::write_state(bool state) {
  this->publish_state(state);
}

void RespeakerXVF3800Component::setup() {
  ESP_LOGCONFIG(TAG, "Setting up ReSpeaker XVF3800 (stub component)...");
  if (this->dfu_version_ != nullptr) {
    this->dfu_version_->publish_state("unknown");
  }
}

void RespeakerXVF3800Component::dump_config() {
  ESP_LOGCONFIG(TAG, "ReSpeaker XVF3800:");
  LOG_I2C_DEVICE(this);
  ESP_LOGCONFIG(TAG, "  Processing timeout: %ums", this->processing_timeout_ms_);
  if (this->mute_switch_ != nullptr) {
    ESP_LOGCONFIG(TAG, "  Mute switch enabled");
  }
  if (this->dfu_version_ != nullptr) {
    ESP_LOGCONFIG(TAG, "  DFU version sensor enabled");
  }
  if (this->led_beam_sensor_ != nullptr) {
    ESP_LOGCONFIG(TAG, "  LED beam sensor enabled");
  }
}

}  // namespace respeaker_xvf3800
}  // namespace esphome
