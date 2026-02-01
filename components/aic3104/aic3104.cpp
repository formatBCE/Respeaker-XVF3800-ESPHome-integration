#include "aic3104.h"
#include "esphome/core/log.h"

namespace esphome {
namespace aic3104 {

static const char *const TAG = "aic3104";

void AIC3104AudioDac::setup() {
  ESP_LOGCONFIG(TAG, "Setting up AIC3104 Audio DAC (stub component)...");
}

void AIC3104AudioDac::dump_config() {
  ESP_LOGCONFIG(TAG, "AIC3104 Audio DAC:");
  LOG_I2C_DEVICE(this);
}

}  // namespace aic3104
}  // namespace esphome
