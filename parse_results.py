import sys
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
from tabulate import tabulate

path = 'outputs'
files = ['lb', 'pando', 'epaxos', 'mencius', 'multipaxos']
storages = [1, 2, 3, 4, 5]
reads = writes = [100, 10000, 1000000]

file_to_names = {
    'lb': 'Lower Bound',
    'pando': 'Pando',
    'del': 'Delegate',
    'epaxos': 'EPaxos',
    'mencius': 'Mencius',
    'multipaxos': 'Multi-Paxos'
}

def extract_latency(output_lines):
    for line in output_lines:
        if "Objective:" in line and "(MINimum)" in line:
            parts = line.split('=')
            if len(parts) > 1:
                latency = parts[1].strip().split("(MINimum)")[0].strip()
                return int(latency)
    print("Objective: LATENCY not found in the file.")
    exit(1)

def reset_globals(files):
    global activity_w
    activity_w = {file: [] for file in files}

def extract_specific_latencies(output_lines, filename):
    write_latency = 0
    for line in output_lines:
        parts = line.split()
        if len(parts) > 2:
            if "WL" in parts[1]:
                if parts[2] == "*":
                    write_latency += float(parts[3])
                else:
                    write_latency += float(parts[2])
    activity_w.get(filename).append(write_latency)

def integrand(x, approach):
    if activity_w[approach][int(x)] != 0 and activity_w['lb'][int(x)] < activity_w[approach][int(x)]:
        return (activity_w[approach][int(x)] - activity_w['lb'][int(x)])
    else:
        return 0

def calculate_gap_volume(approach):
    print(f"Calculating GapVolume for {approach}")
    if approach == 'lb':
        return 0
    gap_volume, error_rate = quad(integrand, 0, len(storages) - 1, args=(approach,))
    print(f"Error rate in GapVolume for {approach}: {error_rate}")
    return gap_volume

def plot_latency(latencies, read_or_write='Write'):
    num_groups = 5
    systems = list(latencies.keys())
    num_systems = len(systems)

    group_width = 0.8
    bar_width = group_width / num_systems
    x = np.arange(num_groups)

    plt.figure(figsize=(14, 8))
    for i, system in enumerate(systems):
        bar_positions = x + i * bar_width
        plt.bar(bar_positions, latencies[system][:num_groups], bar_width, label=file_to_names.get(system, system))

    plt.xlabel('Storage Overhead', fontsize=13)
    plt.ylabel(f'{read_or_write} Latency (ms)', fontsize=13)
    plt.xticks(x + group_width / 2 - bar_width / 2, [f'{i+1}' for i in range(num_groups)], fontsize=11)
    plt.yticks(fontsize=11)

    plt.legend(loc='upper left', frameon=False, handleheight=1.3, handlelength=2.3, fontsize=10, markerscale=1.5)
    legend = plt.gca().get_legend()
    for handle in legend.legend_handles:
        handle.set_edgecolor('black')
        handle.set_linewidth(1.5)
    plt.tight_layout()

    plt.savefig(f'{read_or_write}_latency.png')

def create_table(gap_volumes):
    print(gap_volumes)

    table_data = [
        ["Pando", f"{gap_volumes['pando'][0]:.2f}"],
        ["EPaxos", f"{gap_volumes['epaxos'][0]:.2f}"],
        ["Mencius", f"{gap_volumes['mencius'][0]:.2f}"],
        ["MultiPaxos", f"{gap_volumes['multipaxos'][0]:.2f}"]
    ]

    headers = ["GapVolume", "NA - East US"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def main():
    results_activity_w = {}
    for read in reads:
        for write in writes:
            reset_globals(files)

            for filename in files:
                for storage in storages:
                    full_path = f"{path}/form_{filename}_{storage}_10rep_{read}r_{write}w.sol"
                    with open(full_path, 'r') as file:
                        output_lines = file.readlines()

                    extract_specific_latencies(output_lines, filename)

            results_activity_w[(read, write)] = {file: activity_w[file][:] for file in files}

            print()
            print(f"Reads: {read}, Writes: {write}")
            print(f"Activity for w:\n {activity_w}")

    fig, axes = plt.subplots(3, 3)
    fig.subplots_adjust(hspace=1, wspace=0.8)
    colors = ['blue', 'orange', 'green', 'red', 'purple']
    systems = files
    
    for i, read in enumerate(reads):
        for j, write in enumerate(writes):
            ax = axes[i, j]
            key = (read, write)

            activity_data = results_activity_w.get(key, None)
            if not activity_data:
                ax.text(0.5, 0.5, "No Data", ha='center', va='center', fontsize=12)
                ax.set_xticks([])
                ax.set_yticks([])
                continue

            bar_data = {system: [activity_data[system][storage - 1] for storage in storages] for system in systems}

            # Plot the bar chart
            num_systems = len(systems)
            bar_width = 0.15
            x = np.arange(len(storages))

            for k, system in enumerate(systems):
                ax.bar(x + k * bar_width, bar_data[system], bar_width, label=file_to_names.get(system, system), color=colors[k])

            ax.set_title(f"Reads: {read}, Writes: {write}", fontsize=8)
            ax.set_ylabel("Latency (ms)", fontsize=9)
            ax.set_xlabel("Storage Overhead", fontsize=9)
            ax.set_xticks(x + (num_systems - 1) * bar_width / 2)
            ax.set_xticklabels([str(s) for s in storages])
            ax.tick_params(axis='x', labelsize=8)
            ax.tick_params(axis='y', labelsize=8)

            if i == 2 and j == 2:
                ax.legend(loc='upper center', bbox_to_anchor=(-1.4, 5.7), ncol=5, fontsize=8)

    plt.tight_layout()
    plt.savefig("grid_latency_barplot.pdf", format='pdf')
    plt.show()
    exit(0)

    print()
    for filename in files:
        gp = calculate_gap_volume(filename)
        gap_volume.get(filename).append(gp)
    
    create_table(gap_volume)

    plot_latency(activity_w)

if __name__ == '__main__':
	main()
