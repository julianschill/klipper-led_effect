#!/bin/bash
# Force script to exit if an error occurs
set -e

KLIPPER_PATH="${HOME}/klipper"
SYSTEMDDIR="/etc/systemd/system"
MOONRAKER_CONFIG_DIR="${HOME}/printer_data/config"
RESTART_SERVICE=1
UPDATE_MOONRAKER=1
IGNORE_ROOT=0
VENV_PATH="${HOME}/klippy-env"




usage(){ echo "Usage: $0 [-k <klipper path>] [-c <moonraker config path>]" 1>&2; exit 1; }

args=$(getopt -a -o k:c:uh --long klipper:,moonraker:,uninstall,help,no-moonraker,no-service,ignore-root,venv: -- "$@")
# shellcheck disable=SC2181
if [[ $? -gt 0 ]]; then
    usage
fi
eval set -- "${args}"
while :; do
    case $1 in
    -k | --klipper)
        shift
        KLIPPER_PATH=$1
        shift
        ;;
    -c | --moonraker)
        shift
        MOONRAKER_CONFIG_DIR=$1
        shift
        ;;
    --venv)
        shift
        VENV_PATH=$1
        shift
        ;;
    --no-moonraker)
        UPDATE_MOONRAKER=0
        shift
        ;;
    --no-service)
        RESTART_SERVICE=0
        shift
        ;;
    --ignore-root)
        IGNORE_ROOT=1
        shift
        ;;
    -u | --uninstall)
        UNINSTALL=1
        shift
        ;;
    -h | --help)
        usage
        ;;
    --) 
        shift
        break
        ;;
    *)
        echo >&2 Unsupported option: "$1"
        usage
        ;;
    esac
done

# Fall back to old directory for configuration as default
if [ $UPDATE_MOONRAKER -ne 0 ] && [ ! -d "${MOONRAKER_CONFIG_DIR}" ]; then
    echo "\"$MOONRAKER_CONFIG_DIR\" does not exist. Falling back to "${HOME}/klipper_config" as default."
    MOONRAKER_CONFIG_DIR="${HOME}/klipper_config"
fi

# Find SRCDIR from the pathname of this script
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/ && pwd )"

# Verify Klipper has been installed
check_klipper()
{
    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
        echo "Klipper service found."
    else
        echo "[ERROR] Klipper service not found, please install Klipper first"
        exit -1
    fi
}

check_folders()
{
    if [ ! -d "$KLIPPER_PATH/klippy/extras/" ]; then
        echo "[ERROR] Klipper installation not found in directory \"$KLIPPER_PATH\". Exiting"
        exit -1
    fi
    echo "Klipper installation found at $KLIPPER_PATH"

    if [ $UPDATE_MOONRAKER -ne 0 ] && [ ! -f "${MOONRAKER_CONFIG_DIR}/moonraker.conf" ]; then
        echo "[ERROR] Moonraker configuration not found in directory \"$MOONRAKER_CONFIG_DIR\". Exiting"
        exit -1
    fi
    echo "Moonraker configuration found at $MOONRAKER_CONFIG_DIR"
}

# Link extension to Klipper
link_extension()
{
    echo -n "Linking extension to Klipper... "
    ln -sf "${SRCDIR}/packages/led_effect/led_effect/" "${KLIPPER_PATH}/klippy/extras/led_effect"
    echo "[OK]"
}


# Restart moonraker
restart_moonraker()
{
    echo -n "Restarting Moonraker... "
    sudo systemctl restart moonraker
    echo "[OK]"
}

# Add updater for led_effect to moonraker.conf
add_updater()
{
    echo -e -n "Adding update manager to moonraker.conf... "

    update_section=$(grep -c '\[update_manager led_effect\]' ${MOONRAKER_CONFIG_DIR}/moonraker.conf || true)
    if [ "${update_section}" -eq 0 ]; then
        echo -e "\n" >> ${MOONRAKER_CONFIG_DIR}/moonraker.conf
        while read -r line; do
            echo -e "${line}" >> ${MOONRAKER_CONFIG_DIR}/moonraker.conf
        done < "$PWD/file_templates/moonraker_update.txt"
        echo -e "\n" >> ${MOONRAKER_CONFIG_DIR}/moonraker.conf
        echo "[OK]"
        restart_moonraker
        else
        echo -e "[update_manager led_effect] already exists in moonraker.conf [SKIPPED]"
    fi
}

restart_klipper()
{
    echo -n "Restarting Klipper... "
    sudo systemctl restart klipper
    echo "[OK]"
}

start_klipper()
{
    echo -n "Starting Klipper... "
    sudo systemctl start klipper
    echo "[OK]"
}

stop_klipper()
{
    echo -n "Stopping Klipper... "
    sudo systemctl stop klipper
    echo "[OK]"
}

uninstall()
{
    if [ -d "${KLIPPER_PATH}/klippy/extras/led_effect" ]; then
        echo -n "Uninstalling... "
        rm -f "${KLIPPER_PATH}/klippy/extras/led_effect"
        echo "[OK]"
        echo "You can now remove the [update_manager led_effect] section in your moonraker.conf and delete this directory. Also remove all led_effect configurations from your Klipper configuration."
    else
        echo "led_effect not found in \"${KLIPPER_PATH}/klippy/extras/\". Is it installed?"
        echo "[FAILED]"
    fi
}

# Helper functions
verify_ready()
{
    if [ "$EUID" -eq 0 ]; then
        echo "[ERROR] This script must not run as root. Exiting."
        exit 1
    fi
}

# Run steps
[ $IGNORE_ROOT -ne 0 ] && verify_ready
[ $RESTART_SERVICE -eq 1 ] && check_klipper
check_folders
[ $RESTART_SERVICE -eq 1 ] && stop_klipper
if [ ! $UNINSTALL ]; then
   link_extension
   [ $UPDATE_MOONRAKER -eq 1 ] && add_updater
else
    uninstall
fi
[ $RESTART_SERVICE -eq 1 ] && start_klipper

