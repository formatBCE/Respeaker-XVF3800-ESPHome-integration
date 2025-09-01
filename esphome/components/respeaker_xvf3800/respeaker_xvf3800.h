#pragma once

#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/components/text_sensor/text_sensor.h"
#include "esphome/components/i2c/i2c.h"
#include "esphome/components/switch/switch.h"
#include "esphome/components/number/number.h"
#include "esphome/components/select/select.h"
#include "esphome/core/automation.h"
#include "esphome/core/component.h"
#include "esphome/core/defines.h"
#include "esphome/core/hal.h"

namespace esphome {
namespace respeaker_xvf3800 {

// Forward-declare the main component class
class RespeakerXVF3800;

static const uint8_t REGISTER_CHANNEL_1_STAGE = 0x40;

// Configuration servicer resource IDs
static const uint8_t DFU_CONTROLLER_SERVICER_RESID = 240;
static const uint8_t CONFIGURATION_SERVICER_RESID = 241;
static const uint8_t CONFIGURATION_COMMAND_READ_BIT = 0x80;
static const uint8_t DFU_COMMAND_READ_BIT = 0x80;

static const uint16_t DFU_TIMEOUT_MS = 4000;
static const uint16_t MAX_XFER = 128;  // maximum number of bytes we can transfer per block

// Original XVF3800 constants
const uint8_t GPO_SERVICER_RESID = 20;
const uint8_t GPO_SERVICER_RESID_GPO_READ_VALUES = 0;
const uint8_t GPO_SERVICER_RESID_GPO_WRITE_VALUE = 1;
const uint8_t GPO_SERVICER_RESID_LED_RING_VALUE = 18;
const uint8_t GPO_GPO_READ_NUM_BYTES = 5;
const uint8_t IO_CONFIG_SERVICER_RESID = 36;
const uint8_t IO_CONFIG_SERVICER_RESID_GPI_READ_VALUES = 0;
const uint8_t IO_CONFIG_SERVICER_RESID_GPI_VALUE_ALL = 6;

// LED Control Constants
const uint8_t GPO_SERVICER_RESID_LED_EFFECT = 12;
const uint8_t GPO_SERVICER_RESID_LED_BRIGHTNESS = 13;
const uint8_t GPO_SERVICER_RESID_LED_SPEED = 15;
const uint8_t GPO_SERVICER_RESID_LED_COLOR = 16;

const uint8_t RESID_LED = 0x0C;
const uint8_t RESID_DFU_VERSION = 0xFE;
const uint8_t I2C_COMMAND_READ_BIT = 0x80;

enum TransportProtocolReturnCode : uint8_t {
  CTRL_DONE = 0,
  CTRL_WAIT = 1,
  CTRL_INVALID = 3,
};

enum RespeakerXVF3800UpdaterStatus : uint8_t {
  UPDATE_OK,
  UPDATE_COMMUNICATION_ERROR,
  UPDATE_READ_VERSION_ERROR,
  UPDATE_TIMEOUT,
  UPDATE_FAILED,
  UPDATE_BAD_STATE,
  UPDATE_IN_PROGRESS,
  UPDATE_REBOOT_PENDING,
  UPDATE_VERIFY_NEW_VERSION,
};

// Configuration enums from the XMOS firmware's src/configuration/configuration_servicer.h
enum ConfCommands : uint8_t {
  CONFIGURATION_SERVICER_RESID_VNR_VALUE = 0x00,
};

// DFU enums from https://github.com/xmos/sln_voice/blob/develop/examples/ffva/src/dfu_int/dfu_state_machine.h
enum DfuIntAltSetting : uint8_t {
  DFU_INT_ALTERNATE_FACTORY,
  DFU_INT_ALTERNATE_UPGRADE,
};

enum DfuIntState : uint8_t {
  DFU_INT_APP_IDLE,    // unused
  DFU_INT_APP_DETACH,  // unused
  DFU_INT_DFU_IDLE,
  DFU_INT_DFU_DNLOAD_SYNC,
  DFU_INT_DFU_DNBUSY,
  DFU_INT_DFU_DNLOAD_IDLE,
  DFU_INT_DFU_MANIFEST_SYNC,
  DFU_INT_DFU_MANIFEST,
  DFU_INT_DFU_MANIFEST_WAIT_RESET,
  DFU_INT_DFU_UPLOAD_IDLE,
  DFU_INT_DFU_ERROR,
};

enum DfuIntStatus : uint8_t {
  DFU_INT_DFU_STATUS_OK,
  DFU_INT_DFU_STATUS_ERR_TARGET,
  DFU_INT_DFU_STATUS_ERR_FILE,
  DFU_INT_DFU_STATUS_ERR_WRITE,
  DFU_INT_DFU_STATUS_ERR_ERASE,
  DFU_INT_DFU_STATUS_ERR_CHECK_ERASED,
  DFU_INT_DFU_STATUS_ERR_PROG,
  DFU_INT_DFU_STATUS_ERR_VERIFY,
  DFU_INT_DFU_STATUS_ERR_ADDRESS,
  DFU_INT_DFU_STATUS_ERR_NOTDONE,
  DFU_INT_DFU_STATUS_ERR_FIRMWARE,
  DFU_INT_DFU_STATUS_ERR_VENDOR,
  DFU_INT_DFU_STATUS_ERR_USBR,
  DFU_INT_DFU_STATUS_ERR_POR,
  DFU_INT_DFU_STATUS_ERR_UNKNOWN,
  DFU_INT_DFU_STATUS_ERR_STALLEDPKT,
};

enum DfuCommands : uint8_t {
  DFU_CONTROLLER_SERVICER_RESID_DFU_DETACH = 0,
  DFU_CONTROLLER_SERVICER_RESID_DFU_DNLOAD = 1,
  DFU_CONTROLLER_SERVICER_RESID_DFU_UPLOAD = 2,
  DFU_CONTROLLER_SERVICER_RESID_DFU_GETSTATUS = 3,
  DFU_CONTROLLER_SERVICER_RESID_DFU_CLRSTATUS = 4,
  DFU_CONTROLLER_SERVICER_RESID_DFU_GETSTATE = 5,
  DFU_CONTROLLER_SERVICER_RESID_DFU_ABORT = 6,
  DFU_CONTROLLER_SERVICER_RESID_DFU_SETALTERNATE = 64,
  DFU_CONTROLLER_SERVICER_RESID_DFU_TRANSFERBLOCK = 65,
  DFU_CONTROLLER_SERVICER_RESID_DFU_GETVERSION = 88,
  DFU_CONTROLLER_SERVICER_RESID_DFU_REBOOT = 89,
};

enum DFUAutomationState {
  DFU_COMPLETE = 0,
  DFU_START,
  DFU_IN_PROGRESS,
  DFU_ERROR,
};

// --- Component Classes ---

// MuteSwitch class that handles the mute functionality
class MuteSwitch : public switch_::Switch, public PollingComponent {
 public:
  void set_parent(RespeakerXVF3800 *parent) {
    parent_ = parent;
    ESP_LOGD("respeaker_xvf3800", "MuteSwitch parent set to %p", parent);
  }
  void setup() override;
  void write_state(bool state) override;
  void update() override;
  void dump_config() override;

 protected:
  RespeakerXVF3800 *parent_{nullptr};
};

// DFUVersionTextSensor class to read the firmware version
class DFUVersionTextSensor : public text_sensor::TextSensor, public PollingComponent {
 public:
  void set_parent(RespeakerXVF3800 *parent) { parent_ = parent; }
  void setup() override;
  void update() override;
  void dump_config() override;

 protected:
  RespeakerXVF3800 *parent_{nullptr};
};

// Simple LED switch to turn LEDs on/off
class LEDSwitch : public switch_::Switch, public Component {
 public:
  void set_parent(RespeakerXVF3800 *parent) { parent_ = parent; }
  void setup() override;
  void write_state(bool state) override;
  void dump_config() override;

 protected:
  RespeakerXVF3800 *parent_{nullptr};
};

// LED Effect Select class to choose LED effects 1-10
class LEDEffectSelect : public select::Select, public Component {
 public:
  void set_parent(RespeakerXVF3800 *parent) { parent_ = parent; }
  void setup() override;
  void control(const std::string &value) override;
  void dump_config() override;

 protected:
  RespeakerXVF3800 *parent_{nullptr};
};

// LED Speed Number class to control LED animation speed
class LEDSpeedNumber : public number::Number, public Component {
 public:
  void set_parent(RespeakerXVF3800 *parent) { parent_ = parent; }
  void setup() override;
  void control(float value) override;
  void dump_config() override;

 protected:
  RespeakerXVF3800 *parent_{nullptr};
};

// LED Brightness Number class to control LED brightness
class LEDBrightnessNumber : public number::Number, public Component {
 public:
  void set_parent(RespeakerXVF3800 *parent) { parent_ = parent; }
  void setup() override;
  void control(float value) override;
  void dump_config() override;

 protected:
  RespeakerXVF3800 *parent_{nullptr};
};

// LED Color Numbers for RGB control (separate R, G, B numbers)
class LEDRedNumber : public number::Number, public Component {
 public:
  void set_parent(RespeakerXVF3800 *parent) { parent_ = parent; }
  void setup() override;
  void control(float value) override;
  void dump_config() override;

 protected:
  RespeakerXVF3800 *parent_{nullptr};
};

class LEDGreenNumber : public number::Number, public Component {
 public:
  void set_parent(RespeakerXVF3800 *parent) { parent_ = parent; }
  void setup() override;
  void control(float value) override;
  void dump_config() override;

 protected:
  RespeakerXVF3800 *parent_{nullptr};
};

class LEDBlueNumber : public number::Number, public Component {
 public:
  void set_parent(RespeakerXVF3800 *parent) { parent_ = parent; }
  void setup() override;
  void control(float value) override;
  void dump_config() override;

 protected:
  RespeakerXVF3800 *parent_{nullptr};
};

// --- Main Hub Class ---

class RespeakerXVF3800 : public i2c::I2CDevice, public Component {
 public:
  void setup() override;
  bool can_proceed() override {
    return this->is_failed() || (this->version_read_() && (this->versions_match_() || !this->firmware_bin_is_valid_()));
  }
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::HARDWARE - 1; }
  void loop() override;

#ifdef USE_RESPEAKER_XVF3800_STATE_CALLBACK
  void add_on_state_callback(std::function<void(DFUAutomationState, float, RespeakerXVF3800UpdaterStatus)> &&callback) {
    this->state_callback_.add(std::move(callback));
  }
#endif

  void set_reset_pin(GPIOPin *reset_pin) { reset_pin_ = reset_pin; }

  void set_firmware_bin(const uint8_t *data, const uint32_t len) {
    this->firmware_bin_ = data;
    this->firmware_bin_length_ = len;
  }

  void mute_speaker();
  void unmute_speaker();

  void set_mute_state(binary_sensor::BinarySensor* mute_state) {
    this->mute_state_ = mute_state;
  }

  void set_firmware_version(text_sensor::TextSensor* firmware_version) {
    this->firmware_version_ = firmware_version;
  }
  
  void set_firmware_version(uint8_t major, uint8_t minor, uint8_t patch) {
    this->firmware_bin_version_major_ = major;
    this->firmware_bin_version_minor_ = minor;
    this->firmware_bin_version_patch_ = patch;
  }

  void start_dfu_update();
  uint8_t read_vnr();

  // Public methods for child components
  bool read_gpo_values(uint8_t *buffer, uint8_t *status);
  bool read_gpio_status(uint32_t *gpio_status);
  bool read_mute_status();
  void write_mute_status(bool value);
  
  // Original LED method (for backward compatibility)
  void control_leds(uint8_t mode, uint8_t r, uint8_t g, uint8_t b);
  
  // Extended LED methods based on Seeed documentation
  void set_led_effect(uint8_t effect);
  void set_led_color(uint32_t color);
  void set_led_speed(uint8_t speed);
  void set_led_brightness(uint8_t brightness);
  
  // Individual LED ring control (12 LEDs)
  void set_led_ring(uint32_t *rgb_array);
  
  std::string read_dfu_version();

  // Setters for child components
  void set_mute_switch(MuteSwitch *mute_switch) { mute_switch_ = mute_switch; }
  void set_dfu_version_sensor(DFUVersionTextSensor *dfu_version_sensor) { dfu_version_sensor_ = dfu_version_sensor; }
  void set_led_effect_select(LEDEffectSelect *led_effect_select) { led_effect_select_ = led_effect_select; }
  void set_led_speed_number(LEDSpeedNumber *led_speed_number) { led_speed_number_ = led_speed_number; }
  void set_led_brightness_number(LEDBrightnessNumber *led_brightness_number) { led_brightness_number_ = led_brightness_number; }
  void set_led_red_number(LEDRedNumber *led_red_number) { led_red_number_ = led_red_number; }
  void set_led_green_number(LEDGreenNumber *led_green_number) { led_green_number_ = led_green_number; }
  void set_led_blue_number(LEDBlueNumber *led_blue_number) { led_blue_number_ = led_blue_number; }
  
  // Store current RGB values for color mixing
  uint8_t current_red_{255};
  uint8_t current_green_{255}; 
  uint8_t current_blue_{255};
  
  // Helper to update color from current RGB values
  void update_led_color();

 protected:
#ifdef USE_RESPEAKER_XVF3800_STATE_CALLBACK
  CallbackManager<void(DFUAutomationState, float, RespeakerXVF3800UpdaterStatus)> state_callback_{};
#endif
  RespeakerXVF3800UpdaterStatus dfu_update_send_block_();
  uint32_t load_buf_(uint8_t *buf, const uint8_t max_len, const uint32_t offset);
  bool firmware_bin_is_valid_() { return this->firmware_bin_ != nullptr && this->firmware_bin_length_; }
  bool version_read_();
  bool versions_match_();

  bool dfu_get_status_();
  bool dfu_get_version_();
  bool dfu_reboot_();
  bool dfu_set_alternate_();
  bool dfu_check_if_ready_();

  GPIOPin *reset_pin_{nullptr};
  binary_sensor::BinarySensor *mute_state_{nullptr};
  text_sensor::TextSensor *firmware_version_{nullptr};

  bool get_firmware_version_();

  uint8_t dfu_state_{0};
  uint8_t dfu_status_{0};
  uint32_t dfu_status_next_req_delay_{0};

  uint8_t const *firmware_bin_{nullptr};
  uint32_t firmware_bin_length_{0};
  uint8_t firmware_bin_version_major_{0};
  uint8_t firmware_bin_version_minor_{0};
  uint8_t firmware_bin_version_patch_{0};

  uint8_t firmware_version_major_{0};
  uint8_t firmware_version_minor_{0};
  uint8_t firmware_version_patch_{0};

  uint32_t bytes_written_{0};
  uint32_t last_progress_{0};
  uint32_t last_ready_{0};
  uint32_t status_last_read_ms_{0};
  uint32_t update_start_time_{0};
  RespeakerXVF3800UpdaterStatus dfu_update_status_{UPDATE_OK};

  // Child components
  MuteSwitch *mute_switch_{nullptr};
  DFUVersionTextSensor *dfu_version_sensor_{nullptr};
  LEDEffectSelect *led_effect_select_{nullptr};
  LEDSpeedNumber *led_speed_number_{nullptr};
  LEDBrightnessNumber *led_brightness_number_{nullptr};
  LEDRedNumber *led_red_number_{nullptr};
  LEDGreenNumber *led_green_number_{nullptr};
  LEDBlueNumber *led_blue_number_{nullptr};
  
  // Helper method for XMOS communication
  void xmos_write_bytes(uint8_t resid, uint8_t cmd, uint8_t *value, uint8_t write_byte_num);
};

}  // namespace respeaker_xvf3800
}  // namespace esphome
