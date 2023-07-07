#!/bin/bash
# python gen_cases.py --input_dir torch-output-500 2>&1 | tee gen.log
# repeat running gen_cases.py until it returns 0
while true; do
    python gen_cases.py --input_dir $1 2>&1 | tee -a gen.log
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        break
    fi
    echo "gen_cases.py crashes with exit code ${PIPESTATUS[0]}, restarting..."
done
