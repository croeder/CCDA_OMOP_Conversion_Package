#!/usr/bin/env bash
set -euo pipefail

cd src
for file in tests/*py; do 
    base_file=$(basename $file .py)
    if [[ $base_file != "__init__" ]] ; then
        echo "$base_file  $?"
        python3 -m unittest tests.$base_file > /dev/null 
        echo "$file  $?"
        echo ""
    fi
done


