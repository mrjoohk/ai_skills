# Examples: Sim Physics Auditor

## Test Prompt 1: Units and Coordinate Frame Consistency Audit
```
"Audit src/sensor/imu_processor.py. Check whether all variables
 have explicit units and verify there is no mixing of deg/rad.
 Output a PASS/WARN/FAIL checklist. Propose minimal code changes
 (diff) if issues are found."
```

**Expected output:**
- PASS/WARN/FAIL checklist (including path::symbol per item)
- Proposed fix diffs

---

## Test Prompt 2: Signal Processing Nyquist Condition Verification
```
"Verify the Nyquist condition and bandwidth-resolution relationship
 for the following parameters: sample rate fs=1000Hz, max signal
 frequency f_max=450Hz, FIR filter cutoff fc=400Hz.
 Provide a PASS/WARN/FAIL checklist and recommend a verification
 experiment."
```

**Expected output:**
- Nyquist condition verification results
- Parameter sweep plan (fs variation range)

---

## Test Prompt 3: Control Loop Numerical Stability Verification
```
"Audit the 50Hz control loop in src/control/pid_controller.py.
 Check the numerical integrator method, saturation handling, and
 stability conditions. Propose step response and saturation test
 experiments."
```

**Expected output:**
- Stability checklist
- Recommended verification experiments (step response, saturation test)
- Acceptance thresholds (overshoot <= X%, settling time <= Y sec)

---

## Test Prompt 4: Cross-Language Porting Equation Equivalence Verification
```
"Verify equation equivalence between Python and C++ implementations:
 Python: src/sim/dynamics.py::integrate()
 C++:    src/sim/dynamics.cpp::integrate()
 Establish a verification plan to ensure numerical error <= 1e-6
 for identical inputs."
```

**Expected output:**
- Equation correspondence list (Python symbol ↔ C++ symbol)
- Numerical equivalence verification test plan
- Acceptance threshold (error <= 1e-6)
