#!/bin/bash

set -euxo pipefail

trap destroy EXIT

destroy() {
    docker-compose down -t0 || true
}

run() {
    docker-compose up -d 
    docker-compose exec -T klipper bash -c '
        cd /app
        ./install-led_effect.sh -k /opt/klipper/
        cd /opt
        /opt/venv/bin/python klipper/klippy/klippy.py \
            -v \
            -I printer_data/run/klipper.tty \
            -a printer_data/run/klipper.sock \
            printer_data/config/printer.cfg \
            -l printer_data/logs/klippy.log          
' &
    sleep 5
    set +e
    ! docker-compose logs log 2>&1 | tee /dev/stderr | grep -q "Config error"
}



run