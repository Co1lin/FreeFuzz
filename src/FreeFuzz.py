from utils.skip import need_skip_torch
import configparser
from os.path import join
import subprocess
from utils.printer import dump_data
import argparse
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FreeFuzz: a fuzzing frameword for deep learning library")
    parser.add_argument("--conf", type=str, default="demo.conf", help="configuration file")
    args = parser.parse_args()

    config_name = args.conf
    freefuzz_cfg = configparser.ConfigParser()
    freefuzz_cfg.read(join(__file__.replace("FreeFuzz.py", "config"), config_name))

    libs = freefuzz_cfg["general"]["libs"].split(",")
    print("Testing on ", libs)
    
    mongo_cfg = freefuzz_cfg["mongodb"]
    host = mongo_cfg["host"]
    port = int(mongo_cfg["port"])

    # output configuration
    output_cfg = freefuzz_cfg["output"]
    torch_output_dir = output_cfg["torch_output"]
    tf_output_dir = output_cfg["tf_output"]

    if "torch" in libs:
        # database configuration
        from classes.database import TorchDatabase
        TorchDatabase.database_config(host, port, mongo_cfg["torch_database"])
        s_time = time.time()
        i_round = 0
        to_break = False
        while True:
            api_list = TorchDatabase.get_api_list()
            for i_api, api_name in enumerate(api_list):
                lasted_time = time.time() - s_time
                if lasted_time > 4 * 3600:
                    to_break = True
                    break
                print(f'{i_round = }, {i_api}/{len(api_list)}: {api_name}\t\tlastted {lasted_time/60:.2f} min', flush=True)
                if need_skip_torch(api_name):
                    continue
                try:
                    res = subprocess.run(["python3", "FreeFuzz_api.py", config_name, "torch", api_name], shell=False, timeout=100)
                except subprocess.TimeoutExpired:
                    dump_data(f"{api_name}\n", join(torch_output_dir, "timeout.txt"), "a")
                except Exception as e:
                    dump_data(f"{api_name}\n  {e}\n", join(torch_output_dir, "runerror.txt"), "a")
                else:
                    if res.returncode != 0:
                        dump_data(f"{api_name}\n", join(torch_output_dir, "runcrash.txt"), "a")
            i_round += 1
            if to_break:
                break
    if "tf" in libs:
        # database configuration
        from classes.database import TFDatabase
        TFDatabase.database_config(host, port, mongo_cfg["tf_database"])
        s_time = time.time()
        i_round = 0
        to_break = False
        while True:
            api_list = TFDatabase.get_api_list()
            for i_api, api_name in enumerate(api_list):
                lasted_time = time.time() - s_time
                if lasted_time > 4 * 3600:
                    to_break = True
                    break
                print(f'{i_round = }, {i_api}/{len(api_list)}: {api_name}\t\tlastted {lasted_time/60:.2f} min', flush=True)
                try:
                    res = subprocess.run(["python3", "FreeFuzz_api.py", config_name, "tf", api_name], shell=False, timeout=100)
                except subprocess.TimeoutExpired:
                    dump_data(f"{api_name}\n", join(tf_output_dir, "timeout.txt"), "a")
                except Exception as e:
                    dump_data(f"{api_name}\n  {e}\n", join(tf_output_dir, "runerror.txt"), "a")
                else:
                    if res.returncode != 0:
                        dump_data(f"{api_name}\n", join(tf_output_dir, "runcrash.txt"), "a")
            i_round += 1
            if to_break:
                break
    
    not_test = []
    for l in libs:
        if l not in ["tf", "torch"]: not_test.append(l)
    if len(not_test):
        print(f"WE DO NOT SUPPORT SUCH DL LIBRARY: {not_test}!")
