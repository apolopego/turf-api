# ======================================================
# TURF API with FastAPI (FINAL VERSION)
# - Dynamic project (sheet)
# - Dynamic SKUs (SKU_1 ... SKU_n)
# - Dynamic filters
# - "ALL" disables the filter
# - Reach + DeltaReach + Frequency + DeltaFrequency
# ======================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

# -----------------------------
# Load Excel only once
# -----------------------------
data_file = "data_turf.xlsx"

app = FastAPI()

# CORS for Excel / browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# TURF METRICS
# =====================================================
def reach_and_freq(X, indices):
    """Returns reach_pct, frequency among reached."""
    subset = X[:, indices]
    hits = subset.sum(axis=1)

    reach_mask = hits > 0
    n_reach = reach_mask.sum()
    total = X.shape[0]

    reach_pct = n_reach / total if total > 0 else 0

    if n_reach > 0:
        freq = hits[reach_mask].sum() / n_reach
    else:
        freq = 0

    return reach_pct, freq


def greedy_sequence(X, sku_columns, selected_skus, sku_to_idx, forced_start=None):
    """Optimal or forced TURF sequence."""
    selected_indices = [sku_to_idx[s] for s in selected_skus]
    seq = []
    remaining = selected_indices.copy()
    results = []

    prev_reach = 0
    prev_freq = 0

    # STEP 1
    if forced_start is None:
        best_idx = None
        best_reach = -1
        best_freq = -1

        for idx in remaining:
            r, f = reach_and_freq(X, [idx])
            if r > best_reach:
                best_reach = r
                best_freq = f
                best_idx = idx

        start = best_idx
        start_reach = best_reach
        start_freq = best_freq
    else:
        start = sku_to_idx[forced_start]
        start_reach, start_freq = reach_and_freq(X, [start])

    seq.append(start)
    remaining.remove(start)

    results.append({
        "step": 1,
        "sku_added": sku_columns[start],
        "combination": sku_columns[start],
        "reach_pct": start_reach,
        "delta_reach": start_reach - prev_reach,
        "freq": start_freq,
        "delta_freq": start_freq - prev_freq
    })

    prev_reach = start_reach
    prev_freq = start_freq

    # STEP 2+
    step = 2
    while remaining:
        best_idx = None
        best_inc = -1
        best_reach = -1
        best_freq = -1

        for idx in remaining:
            r, f = reach_and_freq(X, seq + [idx])
            inc = r - prev_reach

            if inc > best_inc:
                best_inc = inc
                best_idx = idx
                best_reach = r
                best_freq = f

        seq.append(best_idx)
        remaining.remove(best_idx)

        combo_names = [sku_columns[i] for i in seq]

        results.append({
            "step": step,
            "sku_added": sku_columns[best_idx],
            "combination": " + ".join(combo_names),
            "reach_pct": best_reach,
            "delta_reach": best_reach - prev_reach,
            "freq": best_freq,
            "delta_freq": best_freq - prev_freq
        })

        prev_reach = best_reach
        prev_freq = best_freq
        step += 1

    return results


# =====================================================
# MAIN ENDPOINT
# =====================================================
@app.get("/turf")
def run_turf(skus: str, project: str, filters: str = None):
    """
    Example:
    /turf?skus=SKU_1,SKU_3,SKU_5&project=Sabores2025
    With filters:
    /turf?skus=SKU_1,SKU_3,SKU_5&project=Sabores2025&filters=Filter_1:Hombre|Filter_2:Mexico
    """

    # -------------------------
    # Load project sheet
    # -------------------------
    try:
        df = pd.read_excel(data_file, sheet_name=project)
    except:
        raise HTTPException(status_code=400, detail=f"Sheet '{project}' not found")

    # -------------------------
    # Identify SKU columns dynamically
    # -------------------------
    sku_columns = [c for c in df.columns if c.startswith("SKU_")]
    if len(sku_columns) == 0:
        raise HTTPException(status_code=400, detail="No SKU_ columns found in project")

    # -------------------------
    # Apply filters if provided
    # -------------------------
    if filters:
        rules = filters.split("|")
        for rule in rules:
            if ":" not in rule:
                continue

            col, val = rule.split(":", 1)
            col = col.strip()
            val = val.strip()

            # RULE: if val == ALL → skip
            if val.upper() == "ALL":
                continue

            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Filter column '{col}' not found")

            df = df[df[col] == val]

    if df.shape[0] == 0:
        raise HTTPException(status_code=400, detail="Filter removed all observations")

    # -------------------------
    # Convert SKUs to matrix
    # -------------------------
    X = df[sku_columns].values
    sku_to_idx = {s: i for i, s in enumerate(sku_columns)}

    # -------------------------
    # Selected SKUs
    # -------------------------
    selected_skus = [s.strip() for s in skus.split(",") if s.strip()]

    for s in selected_skus:
        if s not in sku_columns:
            raise HTTPException(status_code=400, detail=f"SKU '{s}' not found in project")

    # -------------------------
    # Run optimal sequence
    # -------------------------
    optimal = greedy_sequence(X, sku_columns, selected_skus, sku_to_idx, forced_start=None)

    # -------------------------
    # Run forced sequences
    # -------------------------
    forced = {}
    for s in selected_skus:
        forced[s] = greedy_sequence(X, sku_columns, selected_skus, sku_to_idx, forced_start=s)

    return {
        "project": project,
        "selected_skus": selected_skus,
        "filters_applied": filters if filters else "NONE",
        "optimal": optimal,
        "forced": forced
    }


# =====================================================
# LOCAL TESTING
# =====================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
