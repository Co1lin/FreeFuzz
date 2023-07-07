from typing import List, Tuple
import os
import sys
import time
import argparse
from tqdm import tqdm
from IPython import embed

def get_compiled_code(code: List[str], framework: str) -> str:
    if framework == 'torch':
        compiled_code: List[str] = ['import torch\n',]
        compiled_code += code[1:-1]
        compiled_code += [
            # 'def fn():\n',
            # f'    {code[-1]}',
            # '    return res\n',
            'class Module(torch.nn.Module):\n',
            '    def __init__(self):\n',
            '        super().__init__()\n',
            '    def forward(self):\n',
            f'        {code[-1]}',
            '        return res\n',
            'fn = Module()\n',
            # 'fn()\n',
            'exported = torch.jit.trace(fn, ())\n',
            'exported = torch.jit.optimize_for_inference(exported)\n',
            'exported()\n',
        ]
    elif framework == 'tf':
        compiled_code: List[str] = [
            code[0],
        ]
        for line in code[2:-3]:
            line = line.strip()
            compiled_code.append(f'{line}\n')
        compiled_code.append('@tf.function(jit_compile=True)\n')
        compiled_code.append('def fn():\n')
        compiled_code.append(f'    return {code[-3].strip().split("= ")[1]}\n')
        compiled_code.append('fn()\n')

    compiled_code_str = ''.join(compiled_code)
    try:
        # exec(compiled_code_str, globals(), globals())
        # s_time = time.time()
        exec(compiled_code_str, locals(), locals())
        # e_time = time.time()
        # print(f'{e_time - s_time = }')
    except Exception as e:
        print(f'Error: {e}')
        # print(compiled_code_str)
        return None
    return compiled_code_str


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, help="input directory")
    # parser.add_argument("output_dir", type=str, help="output directory")
    args = parser.parse_args()

    input_dir: str = args.input_dir
    assert os.path.exists(input_dir)
    framework = input_dir.split("-")[0]
    assert framework in ["tf", "torch"]
    if framework == "tf":
        import tensorflow as tf
    elif framework == "torch":
        import torch
    output_dir = f'{input_dir}-compiled'
    output_case_dir = os.path.join(output_dir, 'cases')
    os.makedirs(output_case_dir, exist_ok=True)
    processed_file = f'{output_dir}/processed.txt'
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as f:
            processed_ctimes = set(map(int, f.read().splitlines()))
    else:
        processed_ctimes = set()

    # time_codes: Tuple[float, List[str]] = []
    # iterate over all python programs in the output directory recursively
    i_prog = 0
    for root, dirs, files in os.walk(input_dir):
        if root == input_dir or 'success' not in root:
            continue
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                i_prog += 1
                ctime = int(1000 * os.path.getctime(file_path))
                case_path = os.path.join(output_case_dir, f'{ctime}.py')
                if i_prog % 1000 == 0:
                    print(f'{i_prog = }, {file_path}, {ctime = }', flush=True)
                # if os.path.exists(case_path):
                #     print(f'{case_path} exists, skip', flush=True)
                #     continue
                if ctime in processed_ctimes:
                    continue
                # else:
                #     print(f'{i_prog = }, {file_path}, {ctime = }', flush=True)
                #     embed()
                with open(processed_file, 'a') as f:
                    f.write(f'{ctime}\n')
                with open(file_path, "r") as f:
                    code: List[str] = f.readlines()
                
                compiled_code_str = get_compiled_code(code, framework)
                if compiled_code_str:
                    with open(case_path, 'w') as f:
                        f.write(compiled_code_str)
                else:
                    print(f'no compiled_code_str: {file_path}', flush=True)
                
                # embed()
                # heapq.heappush(time_codes, (ctime, code))
