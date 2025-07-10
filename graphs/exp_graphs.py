import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns

#Cargar el CSV
df = pd.read_csv("exp_data.csv", delimiter=";")
os.makedirs("charts", exist_ok=True)

#Preparar datos
def to_float_percent(val):
    try:
        return float(val.strip('%')) / 100
    except:
        return None

df["milp_gap"] = df["milp_gap"].apply(to_float_percent)
df["milp_trf_gap"] = df["milp_trf_gap"].apply(to_float_percent)

for col in ["milp_obj", "rf_obj", "milp_time", "rf_time", "milp_trf_obj", "milp_trf_time"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

#Ordenar percentiles
orden_percentiles = ['P00', 'P10', 'P20', 'P25', 'P30', 'P40', 'P50',
                     'P60', 'P70', 'P75', 'P80', 'P90', 'P100']
df["percentile"] = df["percentile"].str.extract(r'(\d+)').astype(int)
df["percentile"] = df["percentile"].apply(lambda x: f"P{x:02d}")
df["percentile"] = pd.Categorical(df["percentile"], categories=orden_percentiles, ordered=True)
df.sort_values("percentile", inplace=True)

#Calcular diferencias
df["diff_obj"] = df["rf_obj"] - df["milp_obj"]
df["diff_time"] = df["rf_time"] - df["milp_time"]
df["diff_obj_pct"] = 100 * (df["rf_obj"] - df["milp_obj"]) / df["milp_obj"]
df["diff_time_pct"] = 100 * (df["rf_time"] - df["milp_time"]) / df["milp_time"]

def guardar_grafico(fig, nombre):
    fig.savefig(f"charts/results/{nombre}.png", bbox_inches="tight")
    plt.close(fig)

#Ordenar embalses
orden_dams = [f"{i} DAM" for i in range(2, 13)]
df["dams"] = pd.Categorical(df["dams"], categories=orden_dams, ordered=True)

#MILP (tRF) vs RF + linea MIPGap

for pct in orden_percentiles:
    subset = df[df["percentile"] == pct].sort_values("dams")
    if subset.empty:
        continue

    #Filtrar donde hay ambos valores
    subset = subset[
        subset["rf_obj"].notna() &
        subset["milp_trf_obj"].notna() &
        subset["milp_trf_gap"].notna()
    ]
    if subset.empty:
        continue

    x_labels = subset["dams"].astype(str)
    x = range(len(x_labels))
    offset = 0.2
    x1 = [i - offset for i in x]
    x2 = [i + offset for i in x]

    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax1.bar(x1, subset["milp_trf_obj"], width=0.4, color="#1B3B6F", label="MILP (tRF)")
    ax1.bar(x2, subset["rf_obj"], width=0.4, color="#74C2E1", label="RF")

    ax1.set_ylabel("Función Objetivo (€)")
    ax1.set_xlabel("Número de embalses")
    ax1.set_xticks(x)
    ax1.set_xticklabels(x_labels, rotation=45)
    ax1.axhline(0, color='black', linewidth=0.8)
    ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(x, subset["milp_trf_gap"] * 100, 'o--', color="#e70088", label="MIPGap (MILP tRF)")
    ax2.plot(x, subset["milp_gap"] * 100, 's--', color="#7e004a", label="MIPGap (MILP 900s)")
    ax2.set_ylabel("MIPGap (%)", color="black")
    ax2.tick_params(axis='y', labelcolor="black")

    ax1.set_title(f"MILP (tRF) vs RF – {pct}")
    lines_labels = ax1.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    labels = ax1.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
    ax1.legend(lines_labels, labels, loc="upper left")

    fig.tight_layout()
    guardar_grafico(fig, f"milptrf_vs_rf_objetivo_{pct}")


#Gráficas beneficio y tiempo
width = 0.25
offset = width / 2
for pct in orden_percentiles:
    subset = df[df["percentile"] == pct].sort_values("dams")
    if subset.empty:
        continue

    x_labels = subset["dams"]
    x = range(len(x_labels))
    x1 = [i - offset for i in x]
    x2 = [i + offset for i in x]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), sharex=True)

    #Subplot 1: Beneficio
    ax1.bar(x1, subset["milp_obj"], width=width, label="MILP", color="#4C72B0")
    ax1.bar(x2, subset["rf_obj"], width=width, label="RF", color="#74C2E1")
    ax1.set_ylabel("Función Objetivo (€)")
    ax1.set_xlabel("Número de embalses")
    ax1.set_title("Beneficio")
    ax1.set_xticks(x)
    ax1.set_xticklabels(x_labels, rotation=45)
    ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.3)

    ax1b = ax1.twinx()
    ax1b.plot(x, subset["diff_obj_pct"], color="#001363", marker="o", label="Δ% Beneficio")
    ax1b.set_ylabel("Δ%")
    ax1b.axhline(0, color='black', linewidth=0.8, linestyle='--')

    #Subplot 2: Tiempo 
    ax2.bar(x1, subset["milp_time"], width=width, label="MILP", color="#4C72B0")
    ax2.bar(x2, subset["rf_time"], width=width, label="RF", color="#74C2E1")
    ax2.set_ylabel("Tiempo de resolución (s)")
    ax2.set_xlabel("Número de embalses")
    ax2.set_title("Tiempo de resolución")
    ax2.set_xticks(x)
    ax2.set_xticklabels(x_labels, rotation=45)
    ax2.grid(True, linestyle='--', linewidth=0.5, alpha=0.3)

    ax2b = ax2.twinx()
    ax2b.plot(x, subset["diff_time_pct"], color="#b30067", marker="o", label="Δ% Tiempo")
    ax2b.set_ylabel("Δ%")
    ax2b.axhline(0, color='black', linewidth=0.8, linestyle='--')

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax1b.get_legend_handles_labels()
    h3, l3 = ax2b.get_legend_handles_labels()
    ax1.legend(h1 + h2 + h3, l1 + l2 + l3, loc="best")

    plt.suptitle(f"RF vs MILP – {pct}", fontsize=14)
    plt.tight_layout()
    guardar_grafico(fig, f"combined_{pct}")


