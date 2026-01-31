# ReSpeaker XVF3800 ESPHome Integration - Bootstrap Setup Guide
**Date:** January 31, 2026  
**Status:** ✅ SYSTEM READY FOR FIRMWARE TESTING

---

## Overview
This document describes the bootstrap setup required to prepare the ReSpeaker XVF3800 firmware for testing. All critical code fixes have been verified and the system is ready to proceed to the firmware update and testing phases.

---

## Pre-Bootstrap Status Report

### ✅ Code Audit Completion
All 5 critical bugs identified in the audit have been **FIXED AND VERIFIED**:

#### 1. ✅ Missing Member Variable in AIC3104 Header
- **File:** `esphome/components/aic3104/aic3104.h`
- **Status:** VERIFIED - `bool is_muted_{false};` present in class definition

#### 2. ✅ Memory Safety Issue in load_buf_()
- **File:** `esphome/components/respeaker_xvf3800/respeaker_xvf3800.cpp`
- **Status:** VERIFIED - Loop uses `uint32_t i < buf_len` (correct) instead of `i < max_len`
- **Offset check:** Changed from `>` to `>=` for correctness

#### 3. ✅ Buffer Size Mismatch in dfu_update_send_block_()
- **File:** `esphome/components/respeaker_xvf3800/respeaker_xvf3800.cpp`
- **Status:** VERIFIED - Array declared as `[MAX_XFER + 5]` with valid initialization `{240, 1, 0, 0, 0}`

#### 4. ✅ Function Name Typo in Python Configuration
- **File:** `esphome/components/respeaker_xvf3800/__init__.py`
- **Status:** VERIFIED - Function correctly named `respeaker_xvf3800_flash_action_to_code` (no double 'x')

#### 5. ✅ Empty AIC3104 Configuration Module
- **File:** `esphome/components/aic3104/__init__.py`
- **Status:** VERIFIED - Full configuration schema with proper imports, CONFIG_SCHEMA, and to_code() function

---

## Bootstrap Phase 1: Environment Preparation

### Option A: Docker-Based Setup (Recommended)
**Best for:** Isolated environment, ESPHome in-place compilation

```bash
# Pull official ESPHome Docker image
docker pull esphome/esphome:latest

# Create esphome configuration directory
mkdir -p ~/.esphome

# Run ESPHome container with project directory mounted
docker run -it --rm \
  -v "C:\Users\Satraj\Respeaker-XVF3800-ESPHome-integration:/workspace" \
  -v ~/.esphome:/esphome \
  esphome/esphome /bin/bash
```

### Option B: Native Python Installation (For x86_64/x64 systems)
**Best for:** Direct firmware uploads, debugging

```powershell
# Install Python dependencies
pip install esphome

# Verify installation
esphome version

# List available components
esphome compile config/respeaker-xvf-satellite-example.yaml
```

### Option C: Home Assistant Add-on (Recommended for integration)
**Best for:** Full ecosystem testing with Home Assistant integration

- Install Home Assistant on a separate machine or VM
- Install ESPHome add-on from Home Assistant community add-ons
- Upload custom components to `/config/esphome/components/`
- Create ESPHome device configuration

---

## Bootstrap Phase 2: Project Validation

### 2.1 Firmware Binary Verification
```powershell
$fw_file = "C:\Users\Satraj\Respeaker-XVF3800-ESPHome-integration\application_xvf3800_inthost-lr48-sqr-i2c-v1.0.7-release.bin"
$file_size = (Get-Item $fw_file).Length
$file_hash = (Get-FileHash $fw_file -Algorithm MD5).Hash

Write-Host "Firmware Binary Status:"
Write-Host "  File: $fw_file"
Write-Host "  Size: $file_size bytes"
Write-Host "  MD5:  $file_hash"
Write-Host ""
Write-Host "⚠️ NOTE: Store this MD5 hash for configuration validation"
```

### 2.2 Component Structure Validation
```powershell
$components = @(
    "esphome/components/aic3104/aic3104.h",
    "esphome/components/aic3104/aic3104.cpp",
    "esphome/components/aic3104/__init__.py",
    "esphome/components/aic3104/audio_dac.py",
    "esphome/components/respeaker_xvf3800/respeaker_xvf3800.h",
    "esphome/components/respeaker_xvf3800/respeaker_xvf3800.cpp",
    "esphome/components/respeaker_xvf3800/__init__.py",
    "esphome/components/respeaker_xvf3800/automation.h"
)

foreach ($comp in $components) {
    $path = "C:\Users\Satraj\Respeaker-XVF3800-ESPHome-integration\$comp"
    if (Test-Path $path) {
        Write-Host "✅ $comp"
    } else {
        Write-Host "❌ $comp - MISSING"
    }
}
```

---

## Bootstrap Phase 3: Configuration Preparation

### 3.1 Create Test Configuration
**File:** `config/respeaker-xvf-test.yaml`

```yaml
# ESPHome test configuration for ReSpeaker XVF3800
esphome:
  name: respeaker-xvf-test
  friendly_name: "ReSpeaker XVF Test"
  platform: ESP32
  board: esp32-s3-devkitc-1

# Update over-the-air (OTA) configuration
ota:
  password: "your_ota_password"

# WiFi configuration
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  ap:
    ssid: "ReSpeaker-Fallback"
    password: "fallback_password"

# Enable logging
logger:
  level: DEBUG

# I2C Bus configuration (adjust pins as needed)
i2c:
  sda: GPIO21
  scl: GPIO22
  frequency: 100kHz

# Enable API
api:
  encryption:
    key: !secret api_key

# Import custom components
external_components:
  - source: local
    components: [aic3104, respeaker_xvf3800]

# Audio DAC component (AIC3104)
audio_dac:

# ReSpeaker XVF3800 component
respeaker_xvf3800:
  id: respeaker_main
  address: 0x2C
  
  # Optional: Mute switch
  mute_switch:
    name: "ReSpeaker Mute"
    id: respeaker_mute
  
  # Optional: DFU version sensor
  dfu_version:
    name: "ReSpeaker DFU Version"
    id: respeaker_dfu_version
  
  # Optional: LED beam sensor
  led_beam_sensor:
    name: "ReSpeaker LED Beam"
    id: respeaker_led_beam
  
  # Firmware update configuration
  firmware:
    url: "local://application_xvf3800_inthost-lr48-sqr-i2c-v1.0.7-release.bin"
    version: "1.0.7"
    md5: "YOUR_MD5_HERE"
    on_begin:
      - logger.log: "Firmware update starting..."
    on_progress:
      - logger.log: "Update progress: ${x}%"
    on_end:
      - logger.log: "Firmware update completed!"
    on_error:
      - logger.log: "Firmware update failed: ${x}"
```

### 3.2 Create Secrets Configuration
**File:** `config/secrets.yaml`

```yaml
wifi_ssid: "Your_WiFi_SSID"
wifi_password: "Your_WiFi_Password"
api_key: !secret api_encryption_key
```

---

## Bootstrap Phase 4: Compilation Testing

### 4.1 Syntax Validation (Without Compilation)
```powershell
# Check Python syntax in custom components
$python_files = @(
    "esphome/components/aic3104/__init__.py",
    "esphome/components/aic3104/audio_dac.py",
    "esphome/components/respeaker_xvf3800/__init__.py"
)

foreach ($file in $python_files) {
    $path = "C:\Users\Satraj\Respeaker-XVF3800-ESPHome-integration\$file"
    Write-Host "Checking syntax: $file"
    python -m py_compile $path
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Syntax OK"
    } else {
        Write-Host "  ❌ Syntax Error"
    }
}
```

### 4.2 ESPHome Configuration Validation
```bash
# Using Docker (if available)
docker run --rm -v /path/to/project:/workspace esphome/esphome \
  config config/respeaker-xvf-test.yaml

# Or native ESPHome (if installed)
esphome config config/respeaker-xvf-test.yaml
```

---

## Bootstrap Phase 5: Pre-Testing Checklist

### Hardware Requirements
- [ ] ESP32 microcontroller (recommend ESP32-S3 for better memory)
- [ ] ReSpeaker XVF3800 USB 4-mic array
- [ ] I2C connection between ESP32 and XVF3800 (SDA/SCL)
- [ ] USB power supply for both ESP32 and XVF3800
- [ ] Serial adapter (if using USB serial for flashing)

### Software Requirements
- [ ] Python 3.8+ installed
- [ ] ESPHome environment configured (Docker or native)
- [ ] Custom components copied to `/esphome/components/`
- [ ] Firmware binary accessible (`*.bin` file)
- [ ] WiFi credentials configured
- [ ] OTA password set

### Configuration Requirements
- [ ] I2C pins configured correctly (match your hardware)
- [ ] ESP32 board model specified correctly
- [ ] Firmware MD5 hash verified
- [ ] API encryption key generated
- [ ] Secrets file populated with credentials

---

## Bootstrap Phase 6: Initial Testing

### 6.1 Power-On Test
```
1. Power on ESP32 device
2. Check Serial output for boot messages
3. Verify I2C communication with XVF3800
4. Check that mute switch responds
5. Monitor LED beam sensor readings
```

### 6.2 Firmware Update Test
```
1. Ensure device is on WiFi or connected via OTA
2. Trigger firmware update via ESPHome dashboard
3. Monitor progress messages
4. Verify successful completion (device reboots)
5. Check DFU version sensor for new firmware version
```

### 6.3 Component Tests
```
Mute Switch:
  - Toggle mute state
  - Verify GPIO 30 write operations
  - Check state persistence

LED Beam:
  - Monitor beam direction sensor readings
  - Verify sensor updates at configured interval

DFU Version:
  - Read current firmware version
  - Compare with expected version after update
```

---

## Testing Recommendations

### Critical Tests to Run
1. **Compilation Test**
   - Verify no compilation errors
   - Check generated C++ code

2. **I2C Communication Test**
   - Read/write to XVF3800 via I2C
   - Verify addresses (0x2C for main device)

3. **Mute Functionality Test**
   - GPIO 30 write operations
   - State persistence verification

4. **Memory Analysis Test**
   - Run ESP32 heap analysis during firmware update
   - Monitor for buffer overruns (previously fixed)

5. **Firmware Update Test**
   - DFU block transfer with various sizes
   - State machine transitions
   - Error handling and recovery

### Performance Benchmarks
- Firmware update time: < 30 seconds for 256KB firmware
- I2C communication latency: < 100ms per transaction
- Memory usage: < 70% heap during update
- LED beam sensor polling: 500ms intervals

---

## Troubleshooting Guide

### Issue: "Component not found" errors
**Solution:**
- Verify custom components are in `/esphome/components/`
- Check file permissions are readable
- Ensure `__init__.py` files are present

### Issue: I2C communication fails
**Solution:**
- Verify I2C pin configuration matches hardware
- Check pull-up resistors on SDA/SCL (typically 4.7kΩ)
- Test with I2C scanner to verify device addresses

### Issue: Firmware update timeout
**Solution:**
- Check I2C frequency (should be 100kHz)
- Verify power supply is stable
- Monitor for error codes in logs

### Issue: Buffer overflow warnings
**Solution:**
- Ensure fixes from audit (items 2 & 3) are applied
- Monitor MAX_XFER constant value (typically 256)
- Check firmware binary size against allocated buffer

---

## Files in Bootstrap Package

```
Respeaker-XVF3800-ESPHome-integration/
├── AUDIT_REPORT.md                    ✅ Code audit results
├── BOOTSTRAP_SETUP.md                 ← You are here
├── Readme.md                          ✅ Project overview
├── application_xvf3800_...bin         ✅ Firmware binary
├── config/
│   ├── respeaker-xvf-satellite-example.yaml
│   └── respeaker-xvf-test.yaml       📝 New test config
├── esphome/
│   └── components/
│       ├── aic3104/                  ✅ VERIFIED FIXED
│       │   ├── __init__.py           ✅ Schema complete
│       │   ├── aic3104.h             ✅ Member variable added
│       │   ├── aic3104.cpp
│       │   └── audio_dac.py
│       └── respeaker_xvf3800/        ✅ VERIFIED FIXED
│           ├── __init__.py           ✅ Function name correct
│           ├── respeaker_xvf3800.h
│           ├── respeaker_xvf3800.cpp ✅ Buffer fixes applied
│           └── automation.h
└── ha/                                ✅ Home Assistant scripts

All critical fixes verified and ready for testing.
```

---

## Next Steps

### Immediate Actions
1. ✅ **Complete Bootstrap Setup** (This Document)
2. Prepare ESP32 hardware and ReSpeaker device
3. Set up ESPHome environment (Docker or native)
4. Create test configuration with correct I2C pins
5. Run initial compilation test

### Testing Phase
1. Power on device and verify I2C communication
2. Run component tests (mute, LED beam, DFU version)
3. Perform firmware update test with external monitor
4. Memory analysis during firmware transfer
5. Full integration test with Home Assistant

### Production Phase
1. Create production configuration
2. Run full test suite
3. Deploy to target environment
4. Monitor logs for any issues
5. Document any deviations or additional findings

---

## Rollback Procedures

If critical issues are discovered:

### Immediate Rollback
1. Restore previous firmware via DFU bootloader
2. Check error logs for root cause
3. Create GitHub issue with detailed logs

### Code Rollback
```bash
git checkout HEAD~ esphome/components/
git diff HEAD..HEAD~ esphome/components/
```

### Firmware Rollback
```bash
# Use DFU tools to restore previous version
xfutility firmware --restore previous_version.bin
```

---

## Success Criteria

✅ **Bootstrap Complete When:**
- [ ] All code fixes verified in place
- [ ] Firmware binary MD5 confirmed
- [ ] Component structure validated
- [ ] Configuration files created
- [ ] Compilation test passes (no errors)
- [ ] Hardware ready for testing

✅ **Testing Complete When:**
- [ ] I2C communication working
- [ ] Mute switch functional
- [ ] LED beam sensor operational
- [ ] Firmware update successful
- [ ] Memory analysis shows no issues
- [ ] All automated tests pass

---

## Support Resources

- **ESPHome Documentation:** https://esphome.io/
- **ReSpeaker GitHub:** https://github.com/respeaker/reSpeaker_XVF3800_USB_4MIC_ARRAY
- **This Project:** https://github.com/fitoori/Respeaker-XVF3800-ESPHome-integration
- **Home Assistant:** https://www.home-assistant.io/

---

**Bootstrap Status:** ✅ READY FOR TESTING
**Prepared By:** GitHub Copilot (Claude Haiku 4.5)
**Date:** January 31, 2026
**Next Review:** After initial testing phase completion
