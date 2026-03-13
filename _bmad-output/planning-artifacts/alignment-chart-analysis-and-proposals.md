# Alineamiento Político en Votaciones Divididas — Analysis & Proposals

**Author**: Mary (Business Analyst)  
**Date**: 2026-03-12  
**Status**: Ready for decision

---

## 1. How the Chart Works (Code Audit)

### 1.1 Data pipeline — end-to-end

```
Votes DB (senado_col.json / camara_col.json)
    ↓
processing.py  →  build_legislator_data()
    ↓  per votación: compute coalition majorities, flag "contested"
    ↓  per legislator+year: accumulate {total, aligned} counters
    ↓
    leg["yearly_alignment"][year][coalition] = {"total": N, "aligned": K}
    ↓
export.py  →  generate_site_data()
    ↓  convert raw counters to % (if total > min_total=5, else None)
    ↓  compute era_alignment windows (weighted averages)
    ↓
docs/data/legislators/{key}.json
    ↓
app.js  →  renderAlignmentChart() + era summary cards
```

### 1.2 What "contested" means (current definition)

A _votación_ is flagged `contested = True` when:

| Condition | Result |
|-----------|--------|
| `pacto_majority != cd_majority` | Contested |
| Either side returns `N/A` or `AUSENTE` | Not contested |
| Title contains "proposición de orden", "solicitud de licencia", "cuestión previa" | Not contested |

When a vote is contested, *every legislator* who voted (not AUSENTE/PRESIDENTE) accumulates:
- **+1 total** for each coalition that had a clear majority
- **+1 aligned** for each coalition whose majority matched the legislator's own vote

### 1.3 Yearly % computation

In `export.py`, per legislator, per year, per coalition:

```python
pct = round(aligned / total * 100, 1) if total > 5 else None
```

If a legislator has ≤5 contested votes in a given year for a given coalition, the year shows `null` on the chart.

### 1.4 Era summary cards

Three fixed windows, each showing "% voted with one key party":

| Card label | Year range | Coalition shown |
|---|---|---|
| "2010–2018" | 2010–2018 | `CONSERVADOR` |
| "2018–2022" | 2018–2022 | `CD` |
| "2022–2026" | 2022–2026 | `PACTO` |

These are computed in `export.py → compute_era_alignment()` as a weighted average across all qualifying years in the window.

---

## 2. How the Argentine Original Differed

The Argentine original tracked four coalitions: **PJ** (government 2003-2015, 2019-2023), **UCR**, **JxC/PRO** (government 2015-2019), **LLA** (government 2023+).

Key differences that made it work well there:

| Factor | Argentina | Colombia (current) |
|---|---|---|
| Historical data depth | 2003 – present | 2017 – present (Senado); 2022 – present (Cámara) |
| Bloc discipline | Very high (2 dominant blocs) | Moderate (6+ parties, shifting coalitions) |
| Votes per year | ~400–600 plenary votes/yr | ~50–150 plenary votes/yr (nominal) |
| "Contested" baseline | PJ ≠ main opposition, both had large blocs → many qualifying votes | PACTO ≠ CD, but PACTO barely existed pre-2022 → few qualifying votes |
| Year masks | Explicit per-coalition era filters in `compute_weighted_alignment` | None for Colombian coalitions |
| Era eras | Matched real electoral cycles with data | 2010-2018 era has zero data |

---

## 3. Diagnosis: Why the Chart Shows So Little Data for Colombia

### Problem 1 — Era 2010-2018 is empty
The Senado SODA dataset (`ucmr-52df`) starts from approximately 2017. The era card "2010–2018" will always return `null` for all legislators, yet it is displayed as a blank / "N/A" column.

### Problem 2 — Pacto Histórico barely existed pre-2022
The current `contested` criterion requires both PACTO and CD to have a clear majority. Before 2022, Pacto-classified legislators (Polo Democrático, Colombia Humana, etc.) formed less than ~10% of either chamber. In most votes, `compute_combined_majority()` returns `N/A` for the PACTO bloc because there simply aren't enough members to form a majority. Result: almost no votes qualify as "contested" for years 2017–2021.

**Verified from data:** Top senators (224 total votes, active 2017–2023) show `yearly_alignment` non-null values for only **one year out of seven**.

### Problem 3 — Contestation definition doesn't match pre-Petro politics
For 2018–2022 (Duque era), the meaningful political divide was:
- **Government**: Centro Democrático + Partido Conservador + Cambio Radical
- **Opposition**: Liberal + left parties

Using `PACTO ≠ CD` as the criterion misses this. Many real contested votes between government and opposition in the Duque era are not counted.

### Problem 4 — min_total=5 is too strict for Colombia's vote frequency
Colombian plenary votes are fewer and party caucuses smaller than Argentina's. A threshold of 5 contested votes/year/coalition eliminates too many valid data points, especially for smaller parties and for the 2017-2021 period.

### Problem 5 — Cambio Radical (CR) is absent from alignment tracking
CR is one of the six canonical parties in the party breakdown (law search), but it has no presence in the alignment chart. It frequently holds the swing-vote balance and was part of the Duque governing coalition.

---

## 4. Proposals

### Option A — Quick Fix: Adjust Eras to Match Real Data
**Complexity**: Low (1–2 hours)  
**Files**: `export.py` (~10 lines), `app.js` (~25 lines)

Replace the three era windows with two that align with actual Colombian data and political history:

| New card | Year range | Coalition shown | Political context |
|---|---|---|---|
| "2018–2022" (Duque era) | 2018–2022 | `CD` | CD governed; CD votes are meaningful |
| "2022–2026" (Petro era) | 2022–2026 | `PACTO` | PH governs; Pacto votes are meaningful |

Also drops the empty "2010–2018" card entirely.

**Pros**: Minimal code change, immediately removes useless blank columns, era labels are historically honest.  
**Cons**: Does not fix the core problem — "Duque era" alignment with CD will still be largely null because the `contested` criterion (PACTO≠CD) wasn't generating contested-vote counts for 2018-2022.

---

### Option B — Era-Aware Contestation Logic
**Complexity**: Medium (4–8 hours)  
**Files**: `processing.py` (~20 lines), data structures, `export.py`, `app.js`

Define a political era table and change the `is_contested` (and alignment counting) logic to be year-aware:

| Era | Years | Government bloc | Opposition bloc |
|---|---|---|---|
| Santos II | 2014–2018 | LIBERAL + CONSERVADOR | CD |
| Duque | 2018–2022 | CD + CONSERVADOR + CR | LIBERAL + PACTO |
| Petro | 2022–2026 | PACTO | CD + CONSERVADOR |

For each votación, determine which era it falls in, then:
- `contested = government_majority ≠ opposition_majority`
- Count alignment against all side-defined blocs

**Data structure change:** `yearly_alignment` would store more coalition keys, or eras would have their own alignment tracking.

**Pros**: Historically accurate contestation for all three eras. Would generate meaningful data back to 2017 (when SODA data starts). Aligns with how Colombian citizens understand the political landscape.  
**Cons**: Non-trivial code change. Requires redesigning what the era summary cards show and what the line chart tracks over time.

---

### Option C — "Alineamiento con el Gobierno" (Government Alignment)
**Complexity**: Medium (3–6 hours)  
**Files**: `processing.py`, `export.py`, `app.js`

Instead of tracking multiple coalitions simultaneously, compute a single "% voted with the government" metric that changes over time:

- 2014–2018: government = Santos (Liberal + Conservador + U)
- 2018–2022: government = Duque (CD + Conservador)
- 2022–2026: government = Petro (Pacto)

The line chart would show a single line: "% voted with the governing coalition that year." Each era summary card would show the same metric for that window.

**Pros**: Conceptually simplest for a general audience. Directly answers "was this legislator pro-government or opposition?" Clear, single metric.  
**Cons**: Loses the nuance of which specific party the legislator aligned with. Requires the same era-aware government-definition logic as Option B.

---

### Option D — Lower Threshold + Drop Empty Era
**Complexity**: Very Low (30 min)  
**Files**: `export.py` (2 constants), `app.js` (2 era definitions)

Two minimal changes:
1. Reduce `min_total` from `5` to `2` in `compute_era_alignment()` and from `5` to `3` in the yearly % computation — captures more sparse data points.
2. Drop the "2010–2018" era card entirely; shift to 2017–2021 for the Duque-era card.

**Pros**: Zero risk, surfaces whatever data exists.  
**Cons**: Does NOT fix the root cause (wrong contestation criterion pre-2022). With a lower threshold, partially noisy results may appear.

---

### Option E — Focus on Current Legislature Only (2022–2026)
**Complexity**: Very Low (1 hour)  
**Files**: `app.js` (~15 lines), `export.py` (drop era 1 & 2)

Show only the 2022–2026 window where both Cámara and Senado data is solid, and the political alignment schema (PACTO vs. CD + CON) works correctly. Remove historical era cards.

**Pros**: The chart works correctly and shows clean data for the current majority of active legislators.  
**Cons**: Loses all historical comparisons. Legislators who served in multiple periods lose their historical context.

---

## 5. Recommendation Matrix

| Option | Data Quality | Historical Accuracy | Implementation Effort | Audience Clarity |
|---|---|---|---|---|
| A — Adjust eras only | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| B — Era-aware contestation | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| C — Govt alignment only | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| D — Lower threshold | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| E — Current legislature only | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**Recommended path: A + B (staged)**
- **Phase 1 (immediate)**: Apply Option A — drop the empty 2010-2018 era and relabel to "Duque era" and "Petro era". Also apply Option D's threshold reduction. Minutes of work, instant improvement.
- **Phase 2 (next sprint)**: Implement Option B — era-aware contestation. This is the real fix that makes the line chart meaningful across 2017–2026 for Senado, and 2022–2026 for Cámara.

---

## 6. Files Requiring Changes (by option)

### Option A + D (Phase 1)
| File | Change |
|---|---|
| `como_voto_generator/export.py` | Update `era_alignment` dict keys: remove `"2010-2018"`, change to `"2018-2022"` and `"2022-2026"` only. Lower `min_total` from 5→3 in yearly %, 5→2 in era computation (or keep conservative at 3). |
| `docs/app.js` | Update `ERA_DEFS` and `ERA_DEFS_EXP` arrays: 2 eras instead of 3, updated labels and coalition keys. |
| `docs/index.html` | No functional change needed (card is populated by JS). |

### Option B (Phase 2)
| File | Change |
|---|---|
| `como_voto_generator/processing.py` | Add era lookup table. Modify `build_legislator_data()` to determine government/opposition blocs by vote year. Add new alignment keys (`govt`, or era-specific keys). |
| `como_voto_generator/export.py` | Update era computation and per-year % calculation to reference new alignment keys. |
| `docs/app.js` | Update `renderAlignmentChart()` datasets and `ERA_DEFS` accordingly. |

---

## 7. Decision Needed

Which option(s) should be implemented? Recommended starting point:

> **Option A + D first** (era adjustment + lower threshold) — ship immediately.  
> **Option B** — plan for the next development cycle once we confirm Cámara data is fully ingested.

Please indicate your preference to proceed.
