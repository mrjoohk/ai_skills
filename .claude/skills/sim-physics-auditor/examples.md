# Examples: Sim Physics Auditor

## Test Prompt 1: SAR Parameter Consistency
"Given fc=9.65GHz, B=300MHz, v=100m/s, look=45deg, assess PRF and Doppler constraints for stripmap mode. Output PASS/WARN/FAIL checklist."

## Test Prompt 2: Unit Consistency
"Audit `src/sar/geometry.py` for units and frames. Flag any deg/rad ambiguity and propose minimal code changes."

## Test Prompt 3: Dynamics Stability
"For a 120Hz control loop, check numerical integration stability assumptions and propose validation experiments (step response, saturation)."

## Expected Output
- checklist
- sweep plan
- plots path conventions
