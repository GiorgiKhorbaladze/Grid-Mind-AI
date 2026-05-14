# Full Report Template

> **Usage:** Reference skeleton for the complete GridMind-AI analytical report.
> All sections are populated automatically by `GridMindReportGenerator.generate_markdown()`.
> Field placeholders use `{variable_name}` notation matching `ReportData` attributes.

---

# {title}

_{subtitle}_

| Field | Value |
|-------|-------|
| **Market** | {market} |
| **Period** | {date_range} |
| **Generated** | {generated_at} |
| **Model Confidence** | {confidence_score} |
| **Total Arbitrage Value** | {total_arbitrage_value} {currency} |

---

## Executive Summary

> {executive_summary}

---

## Key Findings

### 1. {finding_1_title}  `{finding_1_impact}`

{finding_1_detail}

### 2. {finding_2_title}  `{finding_2_impact}`

{finding_2_detail}

<!-- Add additional findings as needed -->

---

## Arbitrage Insights

| Time Window | Direction | Spread ($/MWh) | Confidence | Notes |
|-------------|-----------|---------------|------------|-------|
| {window_1}  | {direction_1} | ${spread_1} | {confidence_1} | {notes_1} |
| {window_2}  | {direction_2} | ${spread_2} | {confidence_2} | {notes_2} |

---

## Battery Recommendations

### CHARGE — {charge_window}

**Target SoC:** {charge_soc}%
**Rationale:** {charge_rationale}

### DISCHARGE — {discharge_window}

**Target SoC:** {discharge_soc}%
**Rationale:** {discharge_rationale}

### HOLD — {hold_window}

**Target SoC:** {hold_soc}%
**Rationale:** {hold_rationale}

---

## Volatility Analysis

| Period | Mean ($/MWh) | Std Dev | Min | Max | Vol. Index |
|--------|-------------|---------|-----|-----|-----------|
| {period_1} | ${mean_1} | ${std_1} | ${min_1} | ${max_1} | {vi_1} |
| {period_2} | ${mean_2} | ${std_2} | ${min_2} | ${max_2} | {vi_2} |

---

*This report was generated automatically by GridMind-AI. All figures are model-derived
estimates and must be independently validated before use in any trading or investment decision.*
