#pragma once

#include "esphome/components/microphone/microphone.h"
#include "esphome/components/microphone/microphone_source.h"
#include "esphome/core/component.h"

#include <vector>

namespace esphome {
namespace respeaker_xvf3800 {

/// Converts the 48 kHz XVF3800 output to 16 kHz by keeping one frame of three, without a filter.
/// The DSP processes at 16 kHz, so the 48 kHz stream has no content above 8 kHz and nothing aliases.
/// A low-pass filter would only cut the 4-8 kHz band that the wake word and STT use.
class DecimatingMicrophone : public Component, public microphone::Microphone {
 public:
  explicit DecimatingMicrophone(microphone::MicrophoneSource *source) : source_(source) {}

  void setup() override;
  void loop() override;
  void dump_config() override;

  void start() override;
  void stop() override;

 protected:
  /// Source microphone task only.
  void process_audio_(const std::vector<uint8_t> &data);

  microphone::MicrophoneSource *source_;
  // Reused for every chunk so decimation does not allocate after the first chunks
  std::vector<uint8_t> output_buffer_;
  // Index of the next kept frame in the next chunk; chunks need not be a multiple of three frames
  uint8_t phase_{0};
  uint8_t active_listeners_{0};
};

}  // namespace respeaker_xvf3800
}  // namespace esphome
