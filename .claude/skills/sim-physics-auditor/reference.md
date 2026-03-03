# Reference: Physics Audit Checklist

## Units & Frames
- Every variable has a unit
- Coordinate frames are declared (ENU/NED/body)
- Angles: deg/rad conversions are explicit

## SAR Checks
- Bandwidth B vs range resolution: ΔR ~ c/(2B) (as applicable)
- PRF vs Doppler bandwidth: PRF sufficiently covers expected Doppler span
- Sampling assumptions stated (stripmap/spotlight specifics)
- Windowing assumptions declared

## Dynamics/Control Checks
- timestep dt and control rate declared (e.g., 120 Hz)
- stability checks (bounded states, saturation handling)
- numeric integrator assumptions (RK4/Euler/etc.)

## Validation Outputs
- Parameter sweep table
- Plots stored under `reports/physics/`
- Baseline comparison against known cases or analytical limits
