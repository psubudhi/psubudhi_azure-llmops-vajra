from pathlib import Path

DOCS = {
    "bearing_fault_sop.md": """# Bearing Fault SOP

## Symptoms
- Abnormal increase in stand torque.
- Motor power rises together with torque under similar reduction.
- Rolling force may become unstable.
- In real plants, bearing housing temperature or vibration may increase.

## Likely causes
- Bearing wear.
- Lubrication starvation.
- Lubricant contamination.
- Coupling misalignment.
- Overload or excessive strip tension.

## Immediate actions
1. Reduce rolling load if production permits.
2. Inspect lubrication flow, pressure, and contamination.
3. Check bearing housing temperature.
4. Check coupling alignment and mechanical looseness.
5. Increase monitoring frequency for torque, motor power, and vibration.

## Planned maintenance
- Schedule bearing inspection during the current or next maintenance window.
- Reserve a bearing set if anomaly probability is high or repeated.
""",
    "electric_motor_fault_sop.md": """# Electric Motor Fault SOP

## Symptoms
- Motor power deviation is high.
- Power-to-torque relationship is inconsistent.
- Motor power increases without proportional mechanical load increase.
- Drive alarms, current imbalance, or cooling issues may appear in plant systems.

## Likely causes
- Motor efficiency degradation.
- Drive module fault.
- Electrical supply imbalance.
- Cooling problem.
- Mechanical overload reflected as secondary electrical stress.

## Immediate actions
1. Check drive alarms and motor current balance.
2. Inspect motor cooling and ventilation.
3. Compare torque increase against motor power increase.
4. If torque also rises, inspect mechanical sources before replacing motor parts.
""",
    "work_roll_friction_sop.md": """# Work Roll Friction SOP

## Symptoms
- Rolling force increases under stable reduction.
- Torque increases with force.
- Work roll mileage is high.
- Force-per-reduction ratio increases.

## Likely causes
- Roll surface wear.
- Poor lubrication or emulsion concentration.
- Excessive roll roughness.
- Roll cooling issue.

## Immediate actions
1. Check emulsion concentration and flow.
2. Inspect work roll surface condition.
3. Verify roll cooling nozzles.
4. Plan roll change if mileage threshold is crossed.
""",
    "reduction_scheme_anomaly_sop.md": """# Reduction Scheme Anomaly SOP

## Symptoms
- Mill-level abnormality across multiple stands.
- Reduction pattern changes unexpectedly.
- Rolling force and torque deviations appear in several stands.
- Gap and thickness reduction signals are inconsistent.

## Likely causes
- Incorrect pass schedule.
- Setup model mismatch.
- Gauge control issue.
- Material property mismatch.

## Immediate actions
1. Verify pass schedule and reduction setup.
2. Check entry and exit thickness values.
3. Compare roll gap settings against recipe.
4. Confirm material grade and yield-strength assumptions.
5. Escalate to process engineer if multiple stands are affected.
""",
    "maintenance_priority_policy.md": """# Maintenance Priority Policy

Priority score should consider:
- anomaly probability,
- fault confidence,
- health index,
- equipment criticality,
- spare availability,
- procurement lead time,
- repeated alert count,
- production impact.

Risk bands:
- 0 to 30: Low
- 31 to 55: Medium
- 56 to 75: High
- 76 to 100: Critical

Critical alerts require immediate inspection or controlled load reduction.
High alerts require same-shift maintenance planning and spare verification.
Medium alerts require increased monitoring and planned inspection.
""",

    "cascading_impact_sop.md": """# Cascading Impact SOP

## Context
A 5-stand tandem cold mill is a coupled process. A local abnormality in one stand can disturb inter-stand tension, adjacent motor load, exit gauge stability, and product quality.

## Symptoms
- Primary stand has high torque, force, or motor power deviation.
- Adjacent upstream/downstream tension shifts.
- Downstream motor power changes after upstream load disturbance.
- Multiple stands show moderate z-score deviations.

## Actions
1. Identify the primary abnormal stand.
2. Compare upstream and downstream stand torque/force/motor power.
3. Review inter-stand tension before isolating the fault as a single component issue.
4. Stabilize speed/load if cascading risk is high.
5. Document whether the adjacent stand effect is primary, secondary, or unrelated.
""",
    "physical_constraint_rules.md": """# Physical Constraint Rules for Rolling Mill Diagnosis

## Rule patterns
- Torque and motor power rising together under stable reduction suggests mechanical load increase.
- Motor power rising without proportional torque increase suggests electrical drive or motor efficiency issue.
- Force and torque rising with high work-roll mileage suggests friction, lubrication, or roll wear.
- Multi-stand gap/reduction deviation suggests reduction schedule or setup abnormality.
- Adjacent tension shifts suggest cascading line imbalance.

## Use
These rules validate ML predictions and help maintenance engineers choose the first inspection path. They should be used with SOPs, sensor evidence, and engineer judgement.
""",
    "emergency_shutdown_sop.md": """# Emergency Shutdown SOP

Emergency shutdown or controlled slowdown should be considered when:
- risk is critical,
- anomaly probability remains above threshold for repeated windows,
- torque and motor power rise rapidly together,
- product quality or operator safety may be affected,
- the same critical fault repeats after maintenance.

Before shutdown:
1. Notify shift supervisor.
2. Stabilize strip tension if possible.
3. Reduce speed/load in a controlled way.
4. Log the event and preserve sensor evidence.
""",
}


def main():
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    for name, content in DOCS.items():
        path = docs_dir / name
        path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {len(DOCS)} docs to {docs_dir.resolve()}")


if __name__ == "__main__":
    main()
