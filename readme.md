# ECM Drilling Machine – Single Z-Axis

### Overview
A benchtop electrochemical machining (ECM) drilling setup designed to drill 1–1.5 mm holes in 6061-T6 aluminum using a closed-loop electrolyte system and a Raspberry Pi-controlled motion/power platform.

---

### Features
- 0–30 V / 10 A constant-current ECM loop  
- Stepper-driven Z-axis (TR8×2 lead screw) with limit switches  
- Raspberry Pi control with PWM pump and INA219 sensing  
- Emergency stop, relay-cut safety interlocks  
- Modular firmware with Python scripts  

---

### Directory Structure
firmware/ → all control scripts
hardware/ → schematics, pin maps
mechanical/ → CADs, STLs, drawings
docs/ → project reports and logs
data/ → experiment CSVs
