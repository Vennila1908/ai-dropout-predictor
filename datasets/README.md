# Datasets

| File                       | Rows  | Origin                                                                                              |
|---------------------------- |-------|-----------------------------------------------------------------------------------------------------|
| `sample_students.csv`      | 450   | Committed sample for instant demo (15 students × 30 programs). Includes 9 curated low/medium/high risk profiles. |
| `synthetic_students.csv`   | varies| Run `python ml/training_scripts/generate_synthetic.py --rows 1000` to regenerate.                   |

## Schema

```
roll_no, name, age, gender, department_code, semester,
attendance_pct, internal_marks, semester_marks, backlogs,
fee_paid, fee_delay_days, financial_status,
family_background, behavioral_indicators, extracurricular,
placement_readiness, counselor_remarks, risk_level
```

`department_code` uses degree program codes such as **BA-HEP**, **BCA**, **BSC-EMCS**, **MBA**, **MCA**, and the other programs seeded at startup. Admins can add custom codes under **Degree courses**.

`risk_level` is the synthetic ground-truth label (with ~10 % noise) used during
training. The application infers `risk_level` itself at inference time, so the
column is optional in any CSV uploaded through the UI.

## Privacy

All names and roll numbers are randomly generated. **No real student data is
included in this repository.**
