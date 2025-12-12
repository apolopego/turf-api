# ======================================================
# Simple TURF API with FastAPI
# - Endpoint: /turf?skus=SKU_1,SKU_5,SKU_7
# ======================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

# ---------- Load base data once ----------
data_file = "data_turf.xlsx"
sheet_name = "Turf"

df = pd.read_excel(data_file, sheet_name=sheet_name)

# adjust sku_columns if needed
sku_columns = [
    "SKU_1","SKU_2","SKU_3","SKU_4","SKU_5",
    "SKU_6","SKU_7","SKU_8","SKU_9","SKU_10",
    "SKU_11","SKU_12","SKU_13","SKU_14","SKU_15",
    "SKU_16","SKU_17","SKU_18","SKU_19","SKU_20","SKU_21","SKU_22","SKU_23","SKU_24"
]

X = df[sku_columns].values
sku_to_idx = {s: i for i, s in enumerate(sku_columns)}

# ---------- Basic TURF functions ----------

def reach_of_combo(X, indices):
    hits = X[:, indices].sum(axis=1)
    return float((hits > 0).mean())

def greedy_sequence(X, selected_skus, forced_start=None):
    """
    selected_skus: list of strings (SKU_1, SKU_5, ...)
    forced_start: None for optimal start, or "SKU_x" for forced
    """
    selected_indices = [sku_to_idx[s] for s in selected_skus]

    seq = []
    remaining = selected_indices.copy()
    results = []

    # step 1
    if forced_start is None:
        best_idx = None
        best_reach = -1.0
        for idx in remaining:
            r = reach_of_combo(X, [idx])
            if r > best_reach:
                best_reach = r
                best_idx = idx
        start = best_idx
        start_reach = best_reach
    else:
        start = sku_to_idx[forced_start]
        start_reach = reach_of_combo(X, [start])

    seq.append(start)
    remaining.remove(start)

    results.append({
        "step": 1,
        "sku_added": sku_columns[start],
        "combination": sku_columns[start],
        "reach_pct": start_reach,
        "delta": start_reach
    })

    # step 2+
    step = 2
    while remaining:
        current_reach = reach_of_combo(X, seq)

        best_next = None
        best_increase = -1.0
        best_total_reach = -1.0

        for idx in remaining:
            trial = seq + [idx]
            r = reach_of_combo(X, trial)
            inc = r - current_reach
            if inc > best_increase:
                best_increase = inc
                best_next = idx
                best_total_reach = r

        seq.append(best_next)
        remaining.remove(best_next)

        combo_names = [sku_columns[i] for i in seq]

        results.append({
            "step": step,
            "sku_added": sku_columns[best_next],
            "combination": " + ".join(combo_names),
            "reach_pct": best_total_reach,
            "delta": best_increase
        })

        step += 1

    return results

# ---------- FastAPI app ----------

app = FastAPI()

# CORS so Excel / browser can call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/turf")
def run_turf(skus: str):
    """
    Example: /turf?skus=SKU_1,SKU_5,SKU_7
    """
    selected_skus = [s.strip() for s in skus.split(",") if s.strip()]

    # optimal sequence
    optimal = greedy_sequence(X, selected_skus, forced_start=None)

    # forced sequences
    forced = {}
    for s in selected_skus:
        forced[s] = greedy_sequence(X, selected_skus, forced_start=s)

    return {
        "selected_skus": selected_skus,
        "optimal": optimal,
        "forced": forced
    }

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
