#!/usr/bin/env bash
set -euo pipefail
cd src
for file in test/*py; do 
    base_file=$(basename $file .py)
    echo $base_file
    python3 -m test.$base_file > /dev/null
done

for file in ccda_to_omop/test/*py; do 
    base_file=$(basename $file .py)
    echo $base_file
    python3 -m ccda_to_omop.test.$base_file > /dev/null
done

