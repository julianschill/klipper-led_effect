#!/bin/bash

set -euxo pipefail

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/ && pwd )"

for i in $(ls "$ROOT_DIR" | grep -E "^[0-9]{3}_.*\.sh$"); do
    echo "Running $i"
    bash "$ROOT_DIR/$i"
done