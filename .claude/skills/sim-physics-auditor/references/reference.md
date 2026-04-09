# Reference: Physics Audit Checklist

## Common Units and Coordinate System Checklist

### Units
- [ ] All variables have explicit units
- [ ] Unit conversions (deg↔rad, m↔km, Hz↔kHz, etc.) are handled explicitly
- [ ] Input and output units are documented in function signature or comments

### Coordinate Frames
- [ ] Coordinate frame is declared (e.g., ENU, NED, body, world, image)
- [ ] Coordinate frame transformation points are explicitly marked
- [ ] Angles: consistency maintained (no mixing of deg/rad)

---

## Domain-Specific Additional Checks

### Signal Processing
- [ ] Sample rate fs and Nyquist condition (fs >= 2 × f_max) are satisfied
- [ ] Bandwidth (B) and resolution relationship verified
- [ ] Windowing and filtering assumptions are explicit

### Dynamics / Control
- [ ] Time step dt and control period are explicit
- [ ] Numerical integrator method (RK4, Euler, etc.) and stability conditions verified
- [ ] State saturation and boundary handling logic exists

### Optics / Imaging
- [ ] Focal length, field of view (FOV), pixel size unit consistency
- [ ] Coordinate origin (image vs sensor vs world) is explicit

### Thermal / Fluid
- [ ] Temperature units (K vs °C) consistency
- [ ] Boundary and initial conditions are explicit

---

## Verification Output Format

### Checklist Results Table
```
| Item | Status | Suspected Location (path::symbol) | Notes |
|------|:----:|----------------------|------|
| Unit consistency      | PASS/WARN/FAIL | ... | ... |
| Coordinate frame declaration | PASS/WARN/FAIL | ... | ... |
| Nyquist condition  | PASS/WARN/FAIL | ... | ... |
| Numerical stability | PASS/WARN/FAIL | ... | ... |
```

### Parameter Sweep Table
```
| Parameter | Range | Steps | Expected Output Change | Results Path |
|---------|------|--------|--------------|---------|
```

### Acceptance Thresholds
```
- Unit errors:   0 (no FAIL items)
- Numerical error:   <= eps (vs. analytical solution or reference case)
- Stability margin: maintain bounded state within specified conditions
```

---

## Result Storage Paths
- `reports/physics/checklist_<timestamp>.md`
- `reports/physics/sweep_<parameter>_<timestamp>.csv`
- `reports/physics/plots/`
