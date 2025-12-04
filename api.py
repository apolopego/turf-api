# ======================================================
# TURF API with FastAPI
# Includes:
# - Reach
# - Delta Reach
# - Frequency
# - Delta Frequency
# For both: Optimal and Forced paths
# ======================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

# ---------- Load base data ----------
data_file = "data_turf.xlsx"
sheet_name = "Turf"

df = pd.read_excel(data_file, sheet_name=sheet_name)

sku_columns = [
    "SKU_1","SKU_2","SKU_3","SKU_4","SKU_5",
    "SKU_6","SKU_7","SKU_8","SKU_9","SKU_10",
    "SKU_11","SKU_12","SKU_13","SKU_14","SKU_15",
    "SKU_16","SKU_17","SKU_18","SKU_19","SKU_20"
]

X = df[sku_columns].values
sku_to_idx = {s: i for i, s in enumerate(sku_columns)}
total_people = X.shape[0]


# ---------- TURF CORE: Reach + Frequency ----------
def reach_and_freq(X, indices):
    """
    Compute:
    - Reach %
    - Frequency for REACHED people
    """
    subset = X[:, indices]
    hits_per_person = subset.sum(axis=1)

    reach_mask = hits_per_person > 0
    reach = reach_mask.sum()

    reach_pct = reach / total_people if total_people > 0 else 0

    if reach > 0:
        freq = hits_per_person[reach_mask].sum() / reach
    else:
        freq = 0

    return reach_pct, freq


# ---------- TURF Greedy (Optimal OR Forced) ----------
def greedy_sequence(X, selected_skus, forced_start=None):
    """
    TURF path with:
    - reach
    - delta reach
    - frequency
    - delta frequency
    Continues even if delta reach = 0.
    """
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
    else:
        best_idx = sku_to_idx[forced_start]
        best_reach, best_freq = reach_and_freq(X, [best_idx])

    seq.append(best_idx)
    remaining.remove(best_idx)

    results.append({
        "step": 1,
        "sku_added": sku_columns[best_idx],
        "combination": sku_columns[best_idx],
        "reach_pct": best_reach,
        "delta_reach": best_reach - prev_reach,
        "freq": best_freq,
        "delta_freq": best_freq - prev_freq
    })

    prev_reach = best_reach
    prev_freq = best_freq

    # STEP 2+
    step = 2
    while remaining:
        best_idx = None
        best_reach = -1
        best_freq = -1
        best_inc = -999  # allow zero or negative increments

        for idx in remaining:
            r, f = reach_and_freq(X, seq + [idx])
            inc = r - prev_reach

            # PRIORIDAD:
            # 1) mayor delta alcance
            # 2) si delta = 0 → mayor frecuencia
            if inc > best_inc or (inc == best_inc and f > best_freq):
                best_inc = inc
                best_idx = idx
                best_reach = r
                best_freq = f

        # siempre agrega un SKU, aunque inc sea 0
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

    """
    Returns full TURF path:
    step, sku_added, combination, reach_pct, delta_reach, freq, delta_freq
    """
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
        best_reach = -1
        best_freq = -1
        best_inc = -1

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


# ---------- FASTAPI ----------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- ENDPOINT ----------
@app.get("/turf")
def run_turf(skus: str):
    """
    Example:
    http://127.0.0.1:8000/turf?skus=SKU_1,SKU_5,SKU_7
    """
    selected_skus = [s.strip() for s in skus.split(",") if s.strip()]

    # OPTIMAL
    optimal = greedy_sequence(X, selected_skus, forced_start=None)

    # FORCED
    forced = {}
    for s in selected_skus:
        forced[s] = greedy_sequence(X, selected_skus, forced_start=s)

    return {
        "selected_skus": selected_skus,
        "optimal": optimal,
        "forced": forced
    }


# ---------- LOCAL RUN ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
