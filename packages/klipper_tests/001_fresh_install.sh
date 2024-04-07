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
        ./install-led_effect.sh --no-moonraker --no-service -k /opt/klipper/ --venv /opt/venv/
        exit 0
';
    docker-compose exec -T klipper bash -c '
        cd /opt
        /opt/venv/bin/python klipper/klippy/klippy.py \
            -v \
            -I printer_data/run/klipper.tty \
            -a printer_data/run/klipper.sock \
            printer_data/config/printer.cfg \
            -l printer_data/logs/klippy.log          
' &
    
    set +e
    # shellcheck disable=SC2034
    for i in {1..100}; do
        INFO=$(docker-compose exec -T moonraker curl http://localhost:7125/printer/info)
        # shellcheck disable=SC2181
        if [ $? -ne 0 ]; then
            sleep 1s
            continue;
        fi

        if [[ "$INFO" =~ \"state\":\ *\"ready\" ]]; then
            exit 0
        fi
        if [[ "$INFO" =~ \"state\":\ *\"error\" ]]; then
            exit 1
        fi
        sleep 0.5s
        
    done
    set -e
    exit 1
}



run