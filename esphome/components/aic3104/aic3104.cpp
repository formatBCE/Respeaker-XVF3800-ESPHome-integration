#include "aic3104.h"

#include "esphome/core/defines.h"
#include "esphome/core/helpers.h"
#include "esphome/core/log.h"

namespace esphome {
namespace aic3104 {

static const char *const TAG = "aic3104";

#define ERROR_CHECK(err, msg) \
  if (!(err)) { \
    ESP_LOGE(TAG, msg); \
    this->mark_failed(); \
    return; \
  }

void AIC3104::setup() {
  // Set register page to 0
  ERROR_CHECK(this->write_byte(AIC3104_PAGE_CTRL, 0x00), "Set page 0 failed");
  // Initiate SW reset (PLL is powered off as part of reset)
  ERROR_CHECK(this->write_byte(AIC3104_SW_RST, 0x01), "Software reset failed");
  
  // *** Program clock settings ***
  // Default is CODEC_CLKIN is from MCLK pin. Don't need to change this.
  // MDAC*NDAC*FOSR*48Khz = mClk (24.576 MHz when the XMOS is expecting 48kHz audio)
  // (See page 51 of https://www.ti.com/lit/ml/slaa557/slaa557.pdf)
  // We do need MDAC*DOSR/32 >= the resource compute level for the processing block
  // So here 2*128/32 = 8, which is adequate for basic processing

  // Power up NDAC and set to 2
  ERROR_CHECK(this->write_byte(AIC3104_NDAC, 0x82), "Set NDAC failed");
  // Power up MDAC and set to 2
  ERROR_CHECK(this->write_byte(AIC3104_MDAC, 0x82), "Set MDAC failed");
  // Program DOSR = 128
  ERROR_CHECK(this->write_byte(AIC3104_DOSR, 0x80), "Set DOSR failed");
  // Set Audio Interface Config: I2S, 32 bits, DOUT always driving
  ERROR_CHECK(this->write_byte(AIC3104_CODEC_IF, 0x30), "Set CODEC_IF failed");
  // For I2S Firmware only, set SCLK/MFP3 pin as Audio Data In
  ERROR_CHECK(this->write_byte(AIC3104_SCLK_MFP3, 0x02), "Set SCLK/MFP3 failed");
  ERROR_CHECK(this->write_byte(AIC3104_AUDIO_IF_4, 0x01), "Set AUDIO_IF_4 failed");
  ERROR_CHECK(this->write_byte(AIC3104_AUDIO_IF_5, 0x01), "Set AUDIO_IF_5 failed");
  
  // Note: AIC3104 doesn't have the advanced processing blocks of AIC3204
  // Skip DAC signal processing block configuration as it uses simpler architecture

  // *** Select Page 1 ***
  ERROR_CHECK(this->write_byte(AIC3104_PAGE_CTRL, 0x01), "Set page 1 failed");
  // Enable the internal AVDD_LDO:
  ERROR_CHECK(this->write_byte(AIC3104_LDO_CTRL, 0x09), "Set LDO_CTRL failed");
  // *** Program Analog Blocks ***
  // Disable Internal Crude AVdd in presence of external AVdd supply or before powering up internal AVdd LDO
  ERROR_CHECK(this->write_byte(AIC3104_PWR_CFG, 0x08), "Set PWR_CFG failed");
  // Enable Master Analog Power Control
  ERROR_CHECK(this->write_byte(AIC3104_LDO_CTRL, 0x01), "Set LDO_CTRL failed");
  // Page 125: Common mode control register, set d6 to 1 to make the full chip common mode = 0.75 v
  // We are using the internal AVdd regulator with a nominal output of 1.72 V (see LDO_CTRL_REGISTER on page 123)
  ERROR_CHECK(this->write_byte(AIC3104_CM_CTRL, 0x40), "Set CM_CTRL failed");
  // *** Set PowerTune Modes ***
  // Set the Left & Right DAC PowerTune mode to PTM_P3/4. Use Class-AB driver.
  ERROR_CHECK(this->write_byte(AIC3104_PLAY_CFG1, 0x00), "Set PLAY_CFG1 failed");
  ERROR_CHECK(this->write_byte(AIC3104_PLAY_CFG2, 0x00), "Set PLAY_CFG2 failed");
  // Set the REF charging time to 40ms
  ERROR_CHECK(this->write_byte(AIC3104_REF_STARTUP, 0x01), "Set REF_STARTUP failed");
  // HP soft stepping settings for optimal pop performance at power up
  // Rpop used is 6k with N = 6 and soft step = 20usec. This should work with 47uF coupling
  // capacitor. Can try N=5,6 or 7 time constants as well. Trade-off delay vs "pop" sound.
  ERROR_CHECK(this->write_byte(AIC3104_HP_START, 0x25), "Set HP_START failed");
  // Route Left DAC to HPL
  ERROR_CHECK(this->write_byte(AIC3104_HPL_ROUTE, 0x08), "Set HPL_ROUTE failed");
  // Route Right DAC to HPR
  ERROR_CHECK(this->write_byte(AIC3104_HPR_ROUTE, 0x08), "Set HPR_ROUTE failed");
  // Route Left DAC to LOL
  ERROR_CHECK(this->write_byte(AIC3104_LOL_ROUTE, 0x08), "Set LOL_ROUTE failed");
  // Route Right DAC to LOR
  ERROR_CHECK(this->write_byte(AIC3104_LOR_ROUTE, 0x08), "Set LOR_ROUTE failed");

  // Unmute HPL and set gain to -2dB 
  ERROR_CHECK(this->write_byte(AIC3104_HPL_GAIN, 0x3e), "Set HPL_GAIN failed");
  // Unmute HPR and set gain to -2dB 
  ERROR_CHECK(this->write_byte(AIC3104_HPR_GAIN, 0x3e), "Set HPR_GAIN failed");
  // Unmute LOL and set gain to 0dB
  ERROR_CHECK(this->write_byte(AIC3104_LOL_DRV_GAIN, 0x00), "Set LOL_DRV_GAIN failed");
  // Unmute LOR and set gain to 0dB
  ERROR_CHECK(this->write_byte(AIC3104_LOR_DRV_GAIN, 0x00), "Set LOR_DRV_GAIN failed");

  // Power up HPL and HPR, LOL and LOR drivers
  ERROR_CHECK(this->write_byte(AIC3104_OP_PWR_CTRL, 0x3C), "Set OP_PWR_CTRL failed");

  // Wait for 2.5 sec for soft stepping to take effect before attempting power-up
  this->set_timeout(2500, [this]() {
    // *** Power Up DAC ***
    // Select Page 0
    ERROR_CHECK(this->write_byte(AIC3104_PAGE_CTRL, 0x00), "Set PAGE_CTRL failed");
    // Power up the Left and Right DAC Channels. Route Left data to Left DAC and Right data to Right DAC.
    // DAC Vol control soft step 1 step per DAC word clock.
    // Note: AIC3104 uses simpler configuration without advanced auto-mute features
    ERROR_CHECK(this->write_byte(AIC3104_DAC_CH_SET1, 0xd4), "Set DAC_CH_SET1 failed");
    // Set left and right DAC digital volume control
    ERROR_CHECK(this->write_volume_(), "Set volume failed");
    // Unmute left and right channels
    ERROR_CHECK(this->write_mute_(), "Set mute failed");
  });
}

void AIC3104::dump_config() {
  ESP_LOGCONFIG(TAG, "AIC3104:");
  LOG_I2C_DEVICE(this);

  if (this->is_failed()) {
    ESP_LOGE(TAG, ESP_LOG_MSG_COMM_FAIL);
  }
}

bool AIC3104::set_mute_off() {
  this->is_muted_ = false;
  return this->write_mute_();
}

bool AIC3104::set_mute_on() {
  this->is_muted_ = true;
  return this->write_mute_();
}

bool AIC3104::set_volume(float volume) {
  this->volume_ = clamp<float>(volume, 0.0, 1.0);
  ESP_LOGD(TAG, "AIC3104 set_volume called: %.2f", this->volume_);
  bool result = this->write_volume_();
  ESP_LOGD(TAG, "AIC3104 write_volume result: %s", result ? "SUCCESS" : "FAILED");
  return result;
}

bool AIC3104::is_muted() { return this->is_muted_; }

float AIC3104::volume() { return this->volume_; }

bool AIC3104::write_mute_() {
  // XVF3800/AIC3104 mute control - setting volume to maximum attenuation
  // Based on Seeed Studio approach
  uint8_t mute_value = this->is_muted_ ? 0x48 : ((1.0f - this->volume_) * 0x48); // 0x48 = max attenuation/mute
  
  if (!this->write_byte(AIC3104_PAGE_CTRL, 0x00) || 
      !this->write_byte(AIC3104_LEFT_DAC_VOLUME, mute_value) ||
      !this->write_byte(AIC3104_RIGHT_DAC_VOLUME, mute_value)) {
    ESP_LOGE(TAG, "Writing mute failed");
    return false;
  }
  
  ESP_LOGVV(TAG, "Mute %s (volume=0x%.2x)", this->is_muted_ ? "ON" : "OFF", mute_value);
  return true;
}

bool AIC3104::write_volume_() {
  ESP_LOGD(TAG, "write_volume_() called - volume: %.2f", this->volume_);
  
  // Simplified: Only control DAC volume like Seeed Studio example
  // Let XVF3800 firmware handle analog stages
  
  if (!this->write_byte(AIC3104_PAGE_CTRL, 0x00)) {
    ESP_LOGE(TAG, "Failed to set page 0");
    return false;
  }
  
  // Map volume 0.0-1.0 to DAC range 0x48-0x00 (inverted)
  // 0x00 = 0dB (loudest), 0x48 = -72dB (quietest)
  uint8_t dac_val = (uint8_t)((1.0f - this->volume_) * 0x48);
  dac_val = clamp<uint8_t>(dac_val, 0x00, 0x48);
  
  ESP_LOGD(TAG, "Writing DAC volume: 0x%.2x (%.1fdB attenuation) to registers 0x2B/0x2C", 
           dac_val, -(float)dac_val);
  
  if (!this->write_byte(AIC3104_LEFT_DAC_VOLUME, dac_val) ||
      !this->write_byte(AIC3104_RIGHT_DAC_VOLUME, dac_val)) {
    ESP_LOGE(TAG, "Writing DAC volume failed");
    return false;
  }
  
  ESP_LOGD(TAG, "Volume %.1f%% → DAC: 0x%.2x (%.1fdB attenuation) - SUCCESS", 
           this->volume_ * 100.0f, dac_val, -(float)dac_val);
  
  return true;
}

}  // namespace aic3104
}  // namespace esphome
