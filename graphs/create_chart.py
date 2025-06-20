import json
import matplotlib.pyplot as plt
import os
import numpy as np
from instance_ana import InstanceData

def load_instance_objects_with_2dams(folder):
    instances = {}
    for percentil in sorted(os.listdir(folder), key=lambda x: int(x)):
        subpath = os.path.join(folder, percentil)
        if os.path.isdir(subpath):
            json_files = [f for f in os.listdir(subpath)
                          if f.endswith(".json") and "instance_2dams" in f]
            if json_files:
                path = os.path.join(subpath, sorted(json_files)[0])
                instances[percentil] = InstanceData.from_json(path)
            else:
                print(f"[WARNING] No se encontró 'instance_2dams' en percentil {percentil}")
    return instances

def save_plot(fig, filename, folder="charts"):
    os.makedirs(folder, exist_ok=True)
    fig.savefig(os.path.join(folder, filename), bbox_inches='tight')
    plt.close(fig)

def plot_bar_chart(data_dict, title, ylabel, color, filename):
    percentiles = sorted(data_dict.keys(), key=int)
    values = [data_dict[p] for p in percentiles]
    labels = [f"P{p}" for p in percentiles]
    x = np.arange(len(percentiles))

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(x, values, color=color, width=0.6)

    ax.set_title(title, fontsize=16)
    ax.set_xlabel("Escenario", fontsize=14)
    ax.set_ylabel(ylabel, fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=12)
    ax.tick_params(axis='y', labelsize=12)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    save_plot(fig, filename)

    save_plot(fig, filename)

def plot_avg_price_per_percentile(instances:dict[str, InstanceData]):
    data = {p: inst.get_avg_price() for p, inst in instances.items()}
    plot_bar_chart(data,
                   title="Precio medio de la energía por percentil",
                   ylabel="€/MWh",
                   color="#D96C6C",
                   filename="mean_average_price.png")


def plot_avg_inflow_per_percentile(instances:dict[str, InstanceData]):
    data = {p: inst.get_total_avg_inflow() for p, inst in instances.items()}
    plot_bar_chart(data,
                   title="Caudal medio total por percentil",
                   ylabel="Caudal medio (m³/s)",
                   color="#2C7FB8",
                   filename="mean_average_flow.png")


def plot_combined_flows(instances:dict[str, InstanceData]):
    percentiles = sorted(instances.keys(), key=int)
    labels = [f"P{p}" for p in percentiles]

    incoming_means = []
    unregulated_totals = []

    for p in percentiles:
        inst = instances[p]
        horizon = inst.get_decision_horizon()

        # Incoming flow
        incoming = inst.get_all_incoming_flows()[:horizon]
        incoming_mean = sum(incoming) / len(incoming) if incoming else 0
        incoming_means.append(incoming_mean)

        # Unregulated flow (como en get_total_avg_inflow)
        unreg_mean_total = 0
        for dam_id in inst.get_ids_of_dams():
            unreg = inst.get_all_unregulated_flows_of_dam(dam_id)[:horizon]
            if unreg:
                unreg_mean_total += sum(unreg) / len(unreg)
        unregulated_totals.append(unreg_mean_total)

    x = np.arange(len(percentiles))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width / 2, incoming_means, width, label="Incoming flow", color="#4C72B0")
    ax.bar(x + width / 2, unregulated_totals, width, label="Unregulated flow", color="#6BAED6")

    ax.set_title("Caudales medios por percentil", fontsize=16)
    ax.set_xlabel("Escenario", fontsize=14)
    ax.set_ylabel("Caudal medio (m³/s)", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=12)
    ax.legend(loc='upper left', frameon=True, fontsize=12)
    ax.tick_params(axis='y', labelsize=12)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    save_plot(fig, "combined_flows.png")

def plot_price_evolution_per_instance(instances:dict[str, InstanceData]):
    for percentil, inst in instances.items():
        prices = inst.get_all_prices()  # usa método de InstanceData
        if not prices:
            continue

        x = list(range(len(prices)))
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(x, prices, color="#1B4F72", linewidth=3)
        ax.set_title(f"Evolución del precio de la energía - Percentil {percentil}", fontsize=14)
        ax.set_xlabel("Franja temporal", fontsize=14)
        ax.set_ylabel("€/MWh", fontsize=14)
        ax.tick_params(axis='both', labelsize=14)
        ax.grid(True, linestyle='--', alpha=0.5)

        filename = f"price_evolution_percentil_{percentil}.png"
        save_plot(fig, filename)


def plot_all_prices_grid(instances:dict[str, InstanceData]):
    import math
    percentiles = sorted(instances.keys(), key=int)
    n = len(percentiles)
    cols = 3
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3 * rows), constrained_layout=True)
    axes = axes.flatten()

    for idx, percentil in enumerate(percentiles):
        ax = axes[idx]
        inst = instances[percentil]
        prices = inst.get_all_prices()
        if not prices:
            continue
        x = list(range(len(prices)))
        ax.plot(x, prices, color="#1B4F72", linewidth=3)
        ax.set_title(f"Percentil {percentil}", fontsize=14)
        ax.set_yticks(np.linspace(min(prices), max(prices), num=4))
        ax.set_xticks([])
        ax.grid(True, linestyle='--', alpha=0.3)

    for idx in range(len(percentiles), len(axes)):
        fig.delaxes(axes[idx])

    save_plot(fig, "price_evolution_grid.png")



if __name__ == "__main__":
    folder_path = "percentiles" 
    instances = load_instance_objects_with_2dams(folder_path)

    plot_avg_inflow_per_percentile(instances)
    plot_avg_price_per_percentile(instances)
    plot_combined_flows(instances)
    plot_price_evolution_per_instance(instances)
    plot_all_prices_grid(instances)
