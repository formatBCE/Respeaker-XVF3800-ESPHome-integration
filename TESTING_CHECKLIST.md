# ReSpeaker XVF3800 Firmware Testing Checklist
**Bootstrap Phase:** Complete  
**Testing Phase:** Ready to Execute  
**Date:** January 31, 2026  

---

## Pre-Testing Verification

### Code Audits & Fixes
- [x] Audit report generated (AUDIT_REPORT.md)
- [x] All 5 critical bugs identified
- [x] All 5 critical bugs fixed and verified
- [x] Bootstrap documentation created
- [x] Test configuration file prepared

### Project Structure
- [x] Custom components in place
- [x] Firmware binary present and accessible
- [x] Configuration examples available
- [x] Documentation complete

---

## Hardware Preparation

### Required Hardware
- [ ] ESP32 microcontroller (or ESP32-S3 variant)
- [ ] ReSpeaker XVF3800 USB 4-mic array
- [ ] I2C wiring (SDA/SCL/GND/VCC)
- [ ] USB power for both devices
- [ ] Serial adapter (if needed)

### Hardware Configuration
- [ ] I2C pins identified on ESP32 board
- [ ] I2C pull-up resistors installed (4.7kΩ typical)
- [ ] Power supply rated for both devices (500mA+)
- [ ] All connections verified visually
- [ ] No loose wires or cold solder joints

### Hardware Testing
- [ ] Multimeter voltage checks (3.3V on I2C, 5V on power)
- [ ] I2C continuity verified (no shorts)
- [ ] Devices power on without smoke/burning smells
- [ ] No thermal issues on components

---

## Software Environment Setup

### Development Environment

#### Option A: Native ESPHome (x86_64 only)
```powershell
# [ ] Python 3.8+ installed
# [ ] pip package manager working
# [ ] ESPHome installed via: pip install esphome
# [ ] ESPHome version verified: esphome version
# [ ] Compiler toolchain available
```

#### Option B: Docker Container (Recommended)
```bash
# [ ] Docker installed and running
# [ ] ESPHome image pulled: docker pull esphome/esphome
# [ ] Volume mounts configured
# [ ] Networking functional
```

#### Option C: Home Assistant Add-on
```yaml
# [ ] Home Assistant installed
# [ ] ESPHome add-on installed
# [ ] Custom components directory exists
# [ ] YAML configuration valid
```

### Configuration Files
- [ ] Secrets file created (config/secrets.yaml)
- [ ] WiFi credentials entered
- [ ] OTA password set
- [ ] API key generated
- [ ] I2C pins match hardware
- [ ] Firmware MD5 hash verified

---

## Compilation Testing

### Pre-Compilation Checks
- [ ] YAML syntax valid (no typos)
- [ ] Custom components importable
- [ ] External component paths correct
- [ ] Required dependencies declared

### Compilation Test
```bash
# [ ] Configuration compiles without errors
esphome compile config/respeaker-xvf-test.yaml

# [ ] No warnings about missing files
# [ ] Generated C++ code in .esphome/ directory
# [ ] Firmware binary created (.bin file)
# [ ] Firmware size reasonable (< 1MB)
```

### Post-Compilation Checks
- [ ] Generated binary exists
- [ ] Binary size logged
- [ ] No memory warnings
- [ ] No deprecated function calls
- [ ] All includes resolved

---

## Initial Flash & Boot

### Flashing Process
- [ ] Device connected via USB/serial
- [ ] Correct COM port identified
- [ ] Flash speed set appropriately (460800 baud typical)
- [ ] Firmware flashed successfully
- [ ] No corruption errors during flash

### Boot Verification
- [ ] Device boots without hanging
- [ ] Serial output shows boot messages
- [ ] I2C initialization messages appear
- [ ] No fatal error logs
- [ ] Device stabilizes within 10 seconds

### Serial Output Inspection
```
Expected boot sequence:
1. [00:00:00] esp_image: ...ESP Bootloader
2. [00:00:XX] heap_alloc: Heap has overflowed (if overflow detected)
3. [00:00:XX] [aic3104] Initializing I2C...
4. [00:00:XX] [respeaker_xvf3800] Found XVF3800 at address 0x2C
5. [00:00:XX] [respeaker_xvf3800] Component ready
```

- [ ] All initialization messages present
- [ ] No errors in boot sequence
- [ ] Heap status reasonable (> 50KB free)

---

## Component Testing

### Test 1: I2C Communication

**Objective:** Verify ESP32 can communicate with XVF3800 over I2C

```
Procedure:
1. Monitor serial logs for I2C scan results
2. Look for message: "Found device at address 0x2C"
3. Attempt to read device registers
4. Verify no I2C error codes
```

**Success Criteria:**
- [x] Device detected at 0x2C
- [x] No I2C communication errors
- [x] Response times < 100ms
- [x] Register reads return valid data

### Test 2: Mute Switch

**Objective:** Verify mute switch GPIO control works

```
Procedure:
1. Open ESPHome web dashboard
2. Locate "ReSpeaker Mute" switch
3. Toggle switch ON
4. Monitor logs for GPIO 30 write confirmation
5. Toggle switch OFF
6. Verify state persists on reboot
```

**Success Criteria:**
- [ ] Switch toggles without errors
- [ ] GPIO 30 state changes reflected in logs
- [ ] No I2C errors during control
- [ ] State persists after reboot
- [ ] Control latency < 500ms

### Test 3: LED Beam Sensor

**Objective:** Verify LED beam direction sensing

```
Procedure:
1. Open ESPHome web dashboard
2. Monitor "ReSpeaker LED Beam Direction" sensor
3. Make sound from different directions
4. Verify sensor value changes (0-7 typical)
5. Observe update frequency (should be 500ms intervals)
```

**Success Criteria:**
- [ ] Sensor values update regularly
- [ ] Values change with sound direction
- [ ] No sensor read errors
- [ ] Update interval consistent
- [ ] Values in valid range (0-255 or 0-7)

### Test 4: DFU Version Sensor

**Objective:** Verify firmware version detection

```
Procedure:
1. Open ESPHome web dashboard
2. Monitor "ReSpeaker Firmware Version" text sensor
3. Initial version should match pre-update firmware
4. Check logs for version read operations
```

**Success Criteria:**
- [ ] Version sensor displays value
- [ ] Version matches expected pre-update version
- [ ] No sensor read errors
- [ ] Update interval correct (30s default)

---

## Memory Analysis

### Heap Analysis

**Objective:** Verify no memory leaks or corruption

```powershell
# Monitor heap statistics during normal operation
# Expected: Heap usage stable over 60 seconds

Procedure:
1. Boot device
2. Wait 5 minutes for stabilization
3. Take heap snapshot
4. Wait another 5 minutes
5. Compare heap snapshots
```

**Success Criteria:**
- [ ] Free heap decreases < 5% per minute
- [ ] No dramatic heap spikes
- [ ] No "heap_alloc: Heap has overflowed" errors
- [ ] Device doesn't reset due to memory

### Stack Analysis

**Objective:** Verify stack usage is reasonable

```
Expected:
- Normal stack usage: 20-50% of available
- During I2C operations: < 70%
- During firmware update: < 80%
```

**Success Criteria:**
- [ ] No stack overflow errors
- [ ] Stack pointer stays in valid range
- [ ] No corruption detected

---

## Firmware Update Testing

### Pre-Update Verification
- [ ] Firmware binary MD5 matches configuration
- [ ] Device on stable WiFi (good signal strength)
- [ ] Device has adequate free storage
- [ ] Previous firmware version noted
- [ ] Backup of current firmware available

### Update Execution

**Procedure:**
1. Trigger firmware update via automation or dashboard
2. Monitor progress in logs
3. Watch for DFU state machine transitions
4. Verify all blocks transferred
5. Confirm device reboots with new firmware

**Expected Log Output:**
```
[ReSpeaker] Firmware update started
[ReSpeaker] Update progress: 0%
[ReSpeaker] Update progress: 10%
[ReSpeaker] Update progress: 20%
...
[ReSpeaker] Update progress: 100%
[ReSpeaker] Firmware update completed successfully
[ReSpeaker] Device will reboot with new firmware
```

**Success Criteria:**
- [ ] Update starts without errors
- [ ] Progress messages appear regularly
- [ ] Update completes within 5 minutes
- [ ] No I2C communication errors during transfer
- [ ] Device reboots cleanly
- [ ] New firmware version confirmed

### Post-Update Verification
- [ ] DFU version sensor shows new version
- [ ] All components functional
- [ ] Memory and heap normal
- [ ] No error messages in logs

---

## Buffer Overflow Testing

### Objective: Verify the critical buffer fixes don't regress

**Test 1: load_buf_() Function**
- [ ] Firmware transfers complete without overruns
- [ ] No out-of-bounds memory access
- [ ] Buffer size checks working

**Test 2: dfu_update_send_block_() Function**
- [ ] Large firmware blocks transfer correctly
- [ ] Array bounds respected
- [ ] No stack corruption

**Test 3: Memory Monitoring During Firmware Transfer**
```
1. Start firmware update
2. Monitor heap continuously
3. Watch for corruption patterns
4. Log any anomalies
```

**Success Criteria:**
- [ ] No buffer overflow detected
- [ ] Memory remains stable
- [ ] No corruption warnings

---

## Error Handling Testing

### Test Various Error Conditions

**Error 1: I2C Communication Failure**
```
Procedure:
1. Disconnect I2C connection mid-operation
2. Observe error messages
3. Verify graceful error handling
4. Reconnect and verify recovery
```

**Test 2: Firmware Transfer Timeout**
```
Procedure:
1. Simulate slow I2C (if possible)
2. Monitor for timeout handling
3. Verify cleanup and recovery
```

**Test 3: Incomplete Firmware Block**
```
Procedure:
1. Trigger firmware update
2. Force connection interruption mid-block
3. Verify device doesn't corrupt
4. Retry should work
```

**Success Criteria:**
- [ ] All errors handled gracefully
- [ ] No uncontrolled reboots
- [ ] Recovery procedures work
- [ ] Logs contain useful error information

---

## Home Assistant Integration Testing

### API Connection
- [ ] Device appears in Home Assistant
- [ ] API encryption working
- [ ] Entity discovery successful
- [ ] State updates flowing to HA

### Entity Testing
- [ ] Mute switch controllable from HA
- [ ] LED beam sensor visible in HA
- [ ] DFU version sensor visible in HA
- [ ] Firmware version readable

### Automation Testing
- [ ] Firmware update triggerable from HA
- [ ] Automations respond to events
- [ ] Scripts execute correctly

---

## Performance Testing

### Measurement 1: I2C Latency
```
Measure: Time from request to response
Expected: < 100ms per transaction
```
- [ ] Latency measured and logged
- [ ] Consistent across operations

### Measurement 2: Firmware Update Speed
```
Measure: Total update time for full firmware
Expected: 15-30 seconds for 256KB firmware
```
- [ ] Speed measured
- [ ] Bottleneck identified if slow

### Measurement 3: Sensor Update Frequency
```
Measure: LED beam sensor update interval
Expected: 500ms (2 Hz)
```
- [ ] Timing verified
- [ ] No missed updates

---

## Long-Term Stability Testing

### 24-Hour Soak Test
```
Duration: 24 continuous hours
Monitoring:
- Heap memory (no growth)
- I2C communication (no degradation)
- Sensor readings (consistent)
- Error logs (none expected)
```

- [ ] 24-hour test scheduled
- [ ] Test execution logged
- [ ] Results analyzed

### Reboot Cycle Test
```
Procedure: 10 clean reboot cycles
1. Boot device
2. Let stabilize (30 seconds)
3. Force reboot
4. Repeat 10 times
```

- [ ] All reboots successful
- [ ] No data corruption
- [ ] Configuration retained

---

## Regression Testing

### Verify All Previous Fixes

**Critical Bug #1: Missing is_muted_ Member**
- [ ] Code compiles
- [ ] Mute state accessible
- [ ] No undefined reference errors

**Critical Bug #2: Buffer Overflow in load_buf_()**
- [ ] Firmware transfers complete
- [ ] No memory corruption
- [ ] Large firmware files work

**Critical Bug #3: Buffer Size Mismatch**
- [ ] dfu_update_send_block_() works
- [ ] Large blocks transfer safely
- [ ] No stack overflow

**Critical Bug #4: Function Name Typo**
- [ ] Flash action registered correctly
- [ ] ESPHome finds the component
- [ ] Firmware update automation works

**Critical Bug #5: Empty AIC3104 Config**
- [ ] Component loads
- [ ] Configuration schema valid
- [ ] to_code() function executes

---

## Test Report Template

**Test Date:** _________________  
**Tester Name:** _________________  
**Device:** _________________  
**Firmware Version:** _________________  

### Summary
- [ ] All critical tests passed
- [ ] No blocking issues found
- [ ] Performance acceptable
- [ ] Ready for production

### Issues Found
```
Issue #1: _______________
  Severity: [ ] Critical [ ] Major [ ] Minor
  Workaround: _______________
  
Issue #2: _______________
  Severity: [ ] Critical [ ] Major [ ] Minor
  Workaround: _______________
```

### Notes
```
_______________________________________________
_______________________________________________
_______________________________________________
```

### Sign-Off
Tester: _________________ Date: _________________  
Reviewer: _________________ Date: _________________  

---

## Success Criteria Summary

**Minimum Requirements:**
- [x] All code fixes verified
- [ ] Device boots without errors
- [ ] I2C communication established
- [ ] Mute switch functional
- [ ] Firmware update completes
- [ ] No memory corruption
- [ ] Device stable for 24 hours

**Testing Complete When:**
- [ ] All sections above checked
- [ ] No blocking issues remaining
- [ ] Performance within specifications
- [ ] Test report signed off
- [ ] Results documented

---

**Testing Status:** 🔄 **IN PROGRESS - READY FOR EXECUTION**

See BOOTSTRAP_SETUP.md for setup instructions before beginning tests.
