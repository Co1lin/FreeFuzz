from typing import List, Tuple
import os
import sys
import time
import argparse
import tempfile
import shutil
from functools import partial
from tqdm import tqdm
import multiprocessing as mp
from IPython import embed


def case_to_time(case: str) -> int:
    return int(case[:-len('.py')])


def exec_cases(cases: List[str], input_dir: str, cases_dir: str, cov_dir: str, min_time: int) -> bool:
    if not cases:
        return True
    timestamp_ms: int = case_to_time(cases[-1]) - min_time
    with tempfile.TemporaryDirectory() as tmp_dir:
        merged_code: str = ''
        for case in cases:
            case_path = os.path.join(cases_dir, case)
            with open(case_path, 'r') as f:
                merged_code += f.read()
                merged_code += '\n\n'
        merged_file = os.path.join(tmp_dir, f'merged.py')
        with open(merged_file, 'w') as f:
            f.write(merged_code)
        
        cov_file = os.path.join(cov_dir, f'{timestamp_ms/1000:.3f}.profraw')
        cmd = f'LLVM_PROFILE_FILE={cov_file} python {merged_file} 2>&1'
        # exec cmd and get output
        print(f'executing {cmd}...', flush=True)
        output = os.popen(cmd).read()
        # print(f'{cases[0]}: {output = }', flush=True)
        if output:
            log_dir = os.path.join(input_dir, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            shutil.copy(merged_file, os.path.join(log_dir, f'{timestamp_ms}.py'))
            with open(os.path.join(log_dir, f'{timestamp_ms}.log'), 'w') as f:
                f.write(output)
        assert os.path.isfile(cov_file)
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, help="input directory")
    parser.add_argument("-j", type=int, default=16, help="number of workers")
    args = parser.parse_args()
    
    input_dir = args.input_dir
    cases_dir = os.path.join(input_dir, 'cases')
    assert os.path.isdir(cases_dir)
    cov_dir = os.path.join(input_dir, 'cov')
    os.makedirs(cov_dir, exist_ok=True)

    cases = os.listdir(cases_dir)
    cases.sort(key=lambda x: case_to_time(x))
    print(f'{len(cases) = }', flush=True)
    min_time = case_to_time(cases[0])
    cases_per_call = len(cases) // 256

    with mp.Pool(args.j) as pool:
        # split cases to 16 processes with pool.map
        results = pool.map(
            partial(exec_cases, input_dir=input_dir, cases_dir=cases_dir, cov_dir=cov_dir, min_time=min_time),
            [cases[i:i+cases_per_call]
                for i in range(0, len(cases), cases_per_call)])
        assert all(results)
        # for partial_cases in [
        #     cases[i:i+cases_per_call]
        #     for i in range(0, len(cases), cases_per_call)
        # ]:            
        #     exec_cases(partial_cases, cases_dir, cov_dir, min_time)
        #     embed()

