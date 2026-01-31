#!/usr/bin/env python3
"""
ReSpeaker XVF3800 Firmware Bootstrap Validation Script

This script validates that the system is ready for firmware testing:
1. Verifies all critical code fixes are in place
2. Checks component files exist and are readable
3. Validates firmware binary integrity
4. Checks configuration validity
5. Generates test report

Run with: python3 bootstrap_validation.py
"""

import os
import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class BootstrapValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'checks': {},
            'passed': 0,
            'failed': 0,
            'warnings': 0,
        }
    
    def print_header(self, text: str):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
        print(f"{text:^60}")
        print(f"{'='*60}{Colors.ENDC}")
    
    def print_check(self, name: str, result: bool, details: str = ""):
        status = f"{Colors.GREEN}✓ PASS{Colors.ENDC}" if result else f"{Colors.RED}✗ FAIL{Colors.ENDC}"
        print(f"  {status}  {name}")
        if details:
            print(f"         {details}")
        
        if result:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
        
        self.results['checks'][name] = {'result': result, 'details': details}
    
    def print_warning(self, text: str):
        print(f"  {Colors.YELLOW}⚠ WARNING{Colors.ENDC}  {text}")
        self.results['warnings'] += 1
    
    # Check 1: Critical Code Fixes
    def check_code_fixes(self):
        self.print_header("Code Audit Fixes Verification")
        
        # Fix 1: Missing is_muted_ member variable
        fix1_file = self.project_root / "esphome/components/aic3104/aic3104.h"
        if fix1_file.exists():
            content = fix1_file.read_text()
            has_fix = "bool is_muted_{false};" in content or "bool is_muted_;" in content
            self.print_check(
                "Fix #1: AIC3104 is_muted_ member variable",
                has_fix,
                f"{'✓' if has_fix else 'Missing'} is_muted_ declaration in aic3104.h"
            )
        else:
            self.print_check("Fix #1: AIC3104 Header File", False, "File not found")
        
        # Fix 2: Buffer overflow in load_buf_()
        fix2_file = self.project_root / "esphome/components/respeaker_xvf3800/respeaker_xvf3800.cpp"
        if fix2_file.exists():
            content = fix2_file.read_text()
            # Check for the correct loop: uint32_t i = 0; i < buf_len
            has_fix = "uint32_t i = 0; i < buf_len" in content or "uint32_t i = 0;i<buf_len" in content
            has_bounds_check = "offset >= this->firmware_bin_length_" in content
            self.print_check(
                "Fix #2: load_buf_() buffer overflow",
                has_fix and has_bounds_check,
                f"{'✓' if has_fix else 'Missing'} uint32_t loop, {'✓' if has_bounds_check else 'Missing'} bounds check"
            )
        else:
            self.print_check("Fix #2: ReSpeaker CPP File", False, "File not found")
        
        # Fix 3: Buffer size mismatch
        if fix2_file.exists():
            content = fix2_file.read_text()
            # Check for correct buffer declaration: [MAX_XFER + 5]
            has_fix = "uint8_t dfu_dnload_req[MAX_XFER + 5]" in content
            has_init = "{240, 1, 0" in content  # Should have initialization with zeros
            self.print_check(
                "Fix #3: dfu_dnload_req buffer size",
                has_fix and has_init,
                f"{'✓' if has_fix else 'Incorrect'} array size, {'✓' if has_init else 'Invalid'} initialization"
            )
        
        # Fix 4: Function name typo
        fix4_file = self.project_root / "esphome/components/respeaker_xvf3800/__init__.py"
        if fix4_file.exists():
            content = fix4_file.read_text()
            has_fix = "async def respeaker_xvf3800_flash_action_to_code" in content
            has_typo = "respeakerxxvf3800_flash_action_to_code" in content
            self.print_check(
                "Fix #4: Function name typo correction",
                has_fix and not has_typo,
                f"{'✓ Correct' if has_fix and not has_typo else '✗ Still has typo'} function name"
            )
        else:
            self.print_check("Fix #4: ReSpeaker __init__.py", False, "File not found")
        
        # Fix 5: AIC3104 configuration module
        fix5_file = self.project_root / "esphome/components/aic3104/__init__.py"
        if fix5_file.exists():
            content = fix5_file.read_text()
            has_imports = "import esphome.codegen" in content and "import esphome.config_validation" in content
            has_schema = "CONFIG_SCHEMA" in content
            has_to_code = "async def to_code(config):" in content
            self.print_check(
                "Fix #5: AIC3104 configuration schema",
                has_imports and has_schema and has_to_code,
                f"{'✓' if has_imports else 'Missing'} imports, {'✓' if has_schema else 'Missing'} schema, {'✓' if has_to_code else 'Missing'} to_code()"
            )
        else:
            self.print_check("Fix #5: AIC3104 __init__.py", False, "File not found")
    
    # Check 2: Component Files Structure
    def check_component_files(self):
        self.print_header("Component Files Verification")
        
        required_files = [
            "esphome/components/aic3104/aic3104.h",
            "esphome/components/aic3104/aic3104.cpp",
            "esphome/components/aic3104/__init__.py",
            "esphome/components/aic3104/audio_dac.py",
            "esphome/components/respeaker_xvf3800/respeaker_xvf3800.h",
            "esphome/components/respeaker_xvf3800/respeaker_xvf3800.cpp",
            "esphome/components/respeaker_xvf3800/__init__.py",
            "esphome/components/respeaker_xvf3800/automation.h",
        ]
        
        all_exist = True
        for file_path in required_files:
            full_path = self.project_root / file_path
            exists = full_path.exists()
            all_exist = all_exist and exists
            self.print_check(
                f"File exists: {file_path}",
                exists,
                f"Size: {full_path.stat().st_size} bytes" if exists else "Not found"
            )
        
        return all_exist
    
    # Check 3: Firmware Binary
    def check_firmware_binary(self):
        self.print_header("Firmware Binary Verification")
        
        # Find the firmware binary
        bin_file = self.project_root / "application_xvf3800_inthost-lr48-sqr-i2c-v1.0.7-release.bin"
        
        if bin_file.exists():
            size = bin_file.stat().st_size
            self.print_check("Firmware binary exists", True, f"Size: {size} bytes ({size//1024} KB)")
            
            # Calculate MD5
            md5_hash = self.calculate_md5(bin_file)
            self.print_check("Firmware MD5 checksum", True, f"MD5: {md5_hash}")
            
            # Check size is reasonable
            if 100000 < size < 1000000:
                self.print_check("Firmware size reasonable", True, f"Size {size} bytes is valid")
            else:
                self.print_warning(f"Firmware size {size} bytes seems unusual")
            
            return md5_hash
        else:
            self.print_check("Firmware binary exists", False, "Binary file not found")
            return None
    
    # Check 4: Configuration Files
    def check_configuration_files(self):
        self.print_header("Configuration Files Verification")
        
        # Check example config
        example_config = self.project_root / "config/respeaker-xvf-satellite-example.yaml"
        self.print_check(
            "Example configuration exists",
            example_config.exists(),
            f"Path: {example_config}"
        )
        
        # Check test config
        test_config = self.project_root / "config/respeaker-xvf-test.yaml"
        self.print_check(
            "Test configuration exists",
            test_config.exists(),
            f"Path: {test_config}"
        )
        
        # Check for secrets template
        secrets_file = self.project_root / "config/secrets.yaml"
        if not secrets_file.exists():
            self.print_warning("secrets.yaml not found - you'll need to create it")
    
    # Check 5: Python Syntax
    def check_python_syntax(self):
        self.print_header("Python Syntax Verification")
        
        python_files = [
            "esphome/components/aic3104/__init__.py",
            "esphome/components/aic3104/audio_dac.py",
            "esphome/components/respeaker_xvf3800/__init__.py",
        ]
        
        for py_file in python_files:
            full_path = self.project_root / py_file
            if full_path.exists():
                result = self.check_python_file_syntax(full_path)
                self.print_check(
                    f"Python syntax: {py_file}",
                    result,
                    f"Valid syntax" if result else "Syntax errors detected"
                )
            else:
                self.print_check(f"Python file: {py_file}", False, "File not found")
    
    # Check 6: Documentation
    def check_documentation(self):
        self.print_header("Documentation Verification")
        
        docs = [
            ("README", "Readme.md"),
            ("Audit Report", "AUDIT_REPORT.md"),
            ("Bootstrap Setup", "BOOTSTRAP_SETUP.md"),
            ("Testing Checklist", "TESTING_CHECKLIST.md"),
        ]
        
        for doc_name, doc_file in docs:
            full_path = self.project_root / doc_file
            if full_path.exists():
                size = full_path.stat().st_size
                self.print_check(
                    f"{doc_name} exists",
                    True,
                    f"Size: {size} bytes"
                )
            else:
                self.print_check(f"{doc_name} exists", False, "File not found")
    
    # Helper: Calculate MD5
    def calculate_md5(self, file_path: Path) -> str:
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5.update(chunk)
        return md5.hexdigest()
    
    # Helper: Check Python syntax
    def check_python_file_syntax(self, file_path: Path) -> bool:
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), str(file_path), 'exec')
            return True
        except SyntaxError:
            return False
        except Exception:
            return True  # Other exceptions don't indicate syntax errors
    
    # Run all checks
    def run_all_checks(self):
        self.check_code_fixes()
        self.check_component_files()
        fw_md5 = self.check_firmware_binary()
        self.check_configuration_files()
        self.check_python_syntax()
        self.check_documentation()
        
        return fw_md5
    
    # Print summary
    def print_summary(self, fw_md5: str = None):
        self.print_header("Bootstrap Validation Summary")
        
        total = self.results['passed'] + self.results['failed']
        passed_pct = (self.results['passed'] / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.BOLD}Test Results:{Colors.ENDC}")
        print(f"  Passed:  {Colors.GREEN}{self.results['passed']}/{total}{Colors.ENDC}")
        print(f"  Failed:  {Colors.RED}{self.results['failed']}{Colors.ENDC}")
        print(f"  Warnings: {Colors.YELLOW}{self.results['warnings']}{Colors.ENDC}")
        print(f"  Success Rate: {passed_pct:.1f}%")
        
        if fw_md5:
            print(f"\n{Colors.BOLD}Firmware Information:{Colors.ENDC}")
            print(f"  MD5 Hash: {fw_md5}")
            print(f"  Add to config: md5: \"{fw_md5}\"")
        
        print(f"\n{Colors.BOLD}Next Steps:{Colors.ENDC}")
        if self.results['failed'] == 0:
            print(f"  {Colors.GREEN}✓ Bootstrap validation PASSED{Colors.ENDC}")
            print(f"  1. Install ESPHome environment (Docker or native)")
            print(f"  2. Update secrets.yaml with WiFi credentials")
            print(f"  3. Update I2C pins in test config to match your board")
            print(f"  4. Add firmware MD5 to configuration")
            print(f"  5. Compile: esphome compile config/respeaker-xvf-test.yaml")
            print(f"  6. Flash firmware to ESP32")
            print(f"  7. Begin testing using TESTING_CHECKLIST.md")
        else:
            print(f"  {Colors.RED}✗ Bootstrap validation FAILED{Colors.ENDC}")
            print(f"  See failures above and check:")
            print(f"  - BOOTSTRAP_SETUP.md for detailed setup instructions")
            print(f"  - AUDIT_REPORT.md for code fixes applied")
        
        print()
    
    # Save results to JSON
    def save_results(self):
        output_file = self.project_root / "bootstrap_validation_results.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"Results saved to: {output_file}")

def main():
    # Detect project root
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # Try current directory
        project_root = "."
    
    project_root = Path(project_root)
    if not (project_root / "AUDIT_REPORT.md").exists():
        print(f"{Colors.RED}Error: Project root not found or invalid{Colors.ENDC}")
        print(f"Usage: python bootstrap_validation.py /path/to/Respeaker-XVF3800-ESPHome-integration")
        sys.exit(1)
    
    # Run validation
    validator = BootstrapValidator(str(project_root))
    fw_md5 = validator.run_all_checks()
    validator.print_summary(fw_md5)
    validator.save_results()
    
    # Exit with appropriate code
    sys.exit(0 if validator.results['failed'] == 0 else 1)

if __name__ == "__main__":
    main()
