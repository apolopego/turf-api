# ============================================================
# TURF analysis en Python para 20 SKUs
# - Calcula Reach, Frequency y Delta por combinacion
# - Muestra barra de avance en consola
# - Exporta resultados a Excel con una hoja "Consola"
#   donde vienen los 20 SKUs para que el cliente seleccione
#   los que quiera usar en el simulador de Excel.
# ============================================================

import pandas as pd
import itertools
from math import comb
from tqdm import tqdm

# ============================
# CONFIGURACION
# ============================

input_file = "data_turf.xlsx"      # Archivo de entrada
input_sheet = "Turf"              # Nombre de la hoja
id_column = "ID"                   # Si no tienes ID, pon None

# Lista de columnas de SKUs (20 productos)
sku_columns = [
    "SKU_1","SKU_2","SKU_3","SKU_4","SKU_5",
    "SKU_6","SKU_7","SKU_8","SKU_9","SKU_10",
    "SKU_11","SKU_12","SKU_13","SKU_14","SKU_15",
    "SKU_16","SKU_17","SKU_18","SKU_19","SKU_20"
]

# ============================
# TURF functions
# ============================

def reach_of_combo(X, indices):
    hits = X[:, indices].sum(axis=1)
    return (hits > 0).mean()

def greedy_sequence(X, sku_cols, selected_indices, forced_start=None):

    seq = []
    remaining = selected_indices.copy()
    results = []

    # ----- Step 1 -----
    if forced_start is None:
        best_idx = None
        best_reach = -1
        for idx in remaining:
            r = reach_of_combo(X, [idx])
            if r > best_reach:
                best_reach = r
                best_idx = idx
        start = best_idx
    else:
        start = forced_start
        best_reach = reach_of_combo(X, [start])

    seq.append(start)
    remaining.remove(start)

    results.append({
        "step": 1,
        "sku_added": sku_cols[start],
        "combination": sku_cols[start],
        "reach_pct": best_reach,
        "delta": best_reach
    })

    # ----- Step 2+ -----
    step = 2
    while remaining:
        current_reach = reach_of_combo(X, seq)

        best_next = None
        best_increase = -1
        best_total = -1

        for idx in remaining:
            trial = seq + [idx]
            r = reach_of_combo(X, trial)
            inc = r - current_reach
            if inc > best_increase:
                best_increase = inc
                best_next = idx
                best_total = r

        seq.append(best_next)
        remaining.remove(best_next)

        combo_names = [sku_cols[i] for i in seq]

        results.append({
            "step": step,
            "sku_added": sku_cols[best_next],
            "combination": " + ".join(combo_names),
            "reach_pct": best_total,
            "delta": best_increase
        })

        step += 1

    return pd.DataFrame(results)

# ============================
# MAIN
# ============================

def main():

    # Load data
    df = pd.read_excel(input_file, sheet_name=input_sheet)
    sim = pd.read_excel(input_file, sheet_name=simulador_sheet)

    # Get selected SKUs
    selected_skus = sim.loc[sim["Seleccion"] == 1, "SKU"].tolist()

    if len(selected_skus) == 0:
        print("No SKUs selected in Simulador sheet.")
        return

    X = df[sku_columns].values

    sku_to_idx = {s:i for i,s in enumerate(sku_columns)}
    selected_indices = [sku_to_idx[s] for s in selected_skus]

    # ----- Optimal sequence -----
    optimal_df = greedy_sequence(X, sku_columns, selected_indices)

    # ----- Forced start sequences -----
    forced_dict = {}
    for s in selected_skus:
        idx = sku_to_idx[s]
        forced_dict[s] = greedy_sequence(X, sku_columns, selected_indices, forced_start=idx)

    # ----- Export -----
    with pd.ExcelWriter(output_file, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        optimal_df.to_excel(writer, sheet_name="TURF_incremental_optimo", index=False)

        for s, dt in forced_dict.items():
            dt.to_excel(writer, sheet_name=f"TURF_incremental_{s}", index=False)

    print("DONE: all incremental TURF sheets created.")


if __name__ == "__main__":
    main()