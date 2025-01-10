import os

os.system("sudo apt install glpk-utils")
if os.system("mkdir formulations && mkdir outputs") != 0:
    os.system("rm formulations/* && rm outputs/*")

storages = [1, 2, 3, 4, 5]
executables = ['lb', 'pando', 'epaxos', 'mencius', 'multipaxos']

def modify_forms(filename):
    full_path = f"formulations/{filename}"
    with open(full_path, 'r') as file:
        lines = file.readlines()
    
    processed_lines = []
    k = 0
    for line in lines:
        if "M_W + M_W" in line:
            processed_line = line.replace("M_W + M_W", "2 M_W")
        elif "CDC_SEL_CAP_" in line:
            if ":" in line:
                name = line.split(":")[0].strip()
            processed_line = line.replace(name, f"{name}_{k}")
            k += 1
            if k == 2:
                k = 0
        else:
            processed_line = line
        
        processed_lines.append(processed_line)

    with open(full_path, 'w') as file:
        file.writelines(processed_lines)

for execs in executables:
     execc = "./bin/f-avail-"
     if execs == 'pando' or execs == 'del' or execs == 'fp':
        execc += "ecc-"
     execc += execs

     for storage in storages:
        output = f"form_{execs}_{storage}.lp"
        if 'mencius' in execs or 'multipaxos' in execs:
            extra_options = "--max-replicas 10"
        elif 'pando' in execs:
            extra_options = "--max-splits 5 --max-replicas 10"
        elif 'epaxos' in execs:
            extra_options = "--max-replicas 10 --reads-as-writes"
        else:
            extra_options = ""
        os.system(f"{execc} --access-sets data/access-set --max-failures 1 {extra_options} --max-storage-overhead {storage} --lp-path formulations/{output}")
        modify_forms(output)
        os.system(f"glpsol --lp formulations/{output} -o outputs/{output[:-2]}sol")
