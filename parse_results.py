import sys
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
from tabulate import tabulate

def extract_latency(output_lines):
    for line in output_lines:
        if "Objective:" in line and "(MINimum)" in line:
            parts = line.split('=')
            if len(parts) > 1:
                latency = parts[1].strip().split("(MINimum)")[0].strip()
                return int(latency)
    print("Objective: LATENCY not found in the file.")
    exit(1)

path = 'outputs/'
files = ['lb', 'pando', 'epaxos', 'mencius', 'multipaxos']
storages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

file_to_names = {
    'lb': 'Lower Bound',
    'pando': 'Pando',
    'del': 'Delegate',
    'epaxos': 'EPaxos',
    'mencius': 'Mencius',
    'multipaxos': 'Multi-Paxos'
}

activity_w = {file: [] for file in files}
activity_r = {file: [] for file in files}
read_quorum = {file: [] for file in files}
write_quorum = {file: [] for file in files}

def extract_specific_latencies(output_lines, filename):
    write_latency = 0
    latency = 0
    read_q = 0
    write_q = 0
    for line in output_lines:
        parts = line.split()
        if len(parts) > 2:
            if parts[1].startswith("R_10"):
                read_q += float(parts[3])
                if parts[2] != "*":
                    print("Read quorum not found.")
            elif parts[1].startswith("W_10"):
                write_q += float(parts[3])
                if parts[2] != "*":
                    print("Write quorum not found.")
            elif parts[1] == "WL_10":
                write_latency += float(parts[2])
            elif parts[1] == "L_10":
                latency += float(parts[2])
    activity_w.get(filename).append(write_latency)
    if filename != 'pando':
        if write_latency < latency:
            latency -= write_latency
    activity_r.get(filename).append(latency)
    read_quorum.get(filename).append(read_q)
    write_quorum.get(filename).append(write_q)

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

    plt.figure(figsize=(12, 6))
    for i, system in enumerate(systems):
        bar_positions = x + i * bar_width
        plt.bar(bar_positions, latencies[system][:num_groups], bar_width, label=file_to_names.get(system, system))

    plt.xlabel('Storage Overhead', fontsize=13)
    plt.ylabel(f'{read_or_write} Latency (ms)', fontsize=13)
    plt.xticks(x + group_width / 2 - bar_width / 2, [f'{i+1}' for i in range(num_groups)], fontsize=11)
    plt.yticks(fontsize=11)

    plt.legend(loc='upper left', frameon=False, handleheight=1.3, handlelength=2.3, fontsize=12, markerscale=1.5)
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
    latencies = {file: [] for file in files}
    gap_volume = {file: [] for file in files}
    for filename in files:
        for storage in storages:
            full_path = f"{path}form_{filename}_{storage}.sol"
            with open(full_path, 'r') as file:
                output_lines = file.readlines()

            if storage < 6:
                print(f"Extracting LATENCY value from file: {full_path}")
                latency = extract_latency(output_lines)
                print(f"Extracted value: {latency}")
                if latencies.get(filename) is not None:
                    latencies.get(filename).append(latency)
                else:
                    print(f"Error: {filename} not found in latencies dictionary.")

            extract_specific_latencies(output_lines, filename)

    print()
    for filename in files:
        gp = calculate_gap_volume(filename)
        gap_volume.get(filename).append(gp)
    
    create_table(gap_volume)

    print()
    print(f"Activity for w:\n {activity_w}")
    print(f"Activity for r:\n {activity_r}")
    print(f"Read quorum:\n {read_quorum}")
    print(f"Write quorum:\n {write_quorum}")

    plot_latency(activity_w)
    plot_latency(activity_r, 'Read')

if __name__ == '__main__':
	main()