#!/bin/bash
# Force script to exit if an error occurs
set -e

KLIPPER_PATH="${HOME}/klipper"
SYSTEMDDIR="/etc/systemd/system"
MOONRAKER_CONFIG_DIR="${HOME}/printer_data/config"

# Fall back to old directory for configuration as default
if [ ! -d "${MOONRAKER_CONFIG_DIR}" ]; then
    echo "\"$MOONRAKER_CONFIG_DIR\" does not exist. Falling back to "${HOME}/klipper_config" as default."
    MOONRAKER_CONFIG_DIR="${HOME}/klipper_config"
fi

usage(){ echo "Usage: $0 [-k <klipper path>] [-c <configuration path>]" 1>&2; exit 1; }
# Parse command line arguments
while getopts "k:c:h" arg; do
    case $arg in
        k) KLIPPER_PATH=$OPTARG;;
        c) MOONRAKER_CONFIG_DIR=$OPTARG;;
        h) usage;;
    esac
done

# Find SRCDIR from the pathname of this script
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/src/ && pwd )"

# Step 1:  Verify Klipper has been installed
check_klipper()
{
    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
        echo "Klipper service found!"
    else
        echo "Klipper service not found, please install Klipper first"
        exit -1
    fi

    if [ ! -d "$KLIPPER_PATH/klippy/extras/" ]; then
        echo "Klipper installation not found in directory \"$KLIPPER_PATH\". Exiting"
        exit -1
    fi
    echo "Klipper found at $KLIPPER_PATH"

    if [ ! -f "${MOONRAKER_CONFIG_DIR}/moonraker.conf" ]; then
        echo "Moonraker configuration not found in directory \"$MOONRAKER_CONFIG_DIR\". Exiting"
        exit -1
    fi
    echo "Moonraker configuration found at $MOONRAKER_CONFIG_DIR"
}

# Step 2: link extension to Klipper
link_extension()
{
    echo "Linking extension to Klipper..."
    ln -sf "${SRCDIR}/led_effect.py" "${KLIPPER_PATH}/klippy/extras/led_effect.py"
    echo "done"
}

# Step 3: Add updater for led_effect to moonraker.conf
add_updater()
{
    echo -e "Adding update manager to moonraker.conf"

    update_section=$(grep -c '\[update_manager led_effect\]' \
    ${MOONRAKER_CONFIG_DIR}/moonraker.conf || true)
    if [ "${update_section}" -eq 0 ]; then
    echo -e "\n" >> ${MOONRAKER_CONFIG_DIR}/moonraker.conf
    while read -r line; do
        echo -e "${line}" >> ${MOONRAKER_CONFIG_DIR}/moonraker.conf
    done < "$PWD/file_templates/moonraker_update.txt"
    echo -e "\n" >> ${MOONRAKER_CONFIG_DIR}/moonraker.conf
    else
    echo -e "[update_manager led_effect] already exists in moonraker.conf [SKIPPED]"
    fi
}
# Step 4: restarting Klipper
restart_klipper()
{
    echo "Restarting Klipper..."
    sudo systemctl restart klipper
    echo "done"
}

# Step 5: restarting Moonraker
restart_moonraker()
{
    echo "Restarting Moonraker..."
    sudo systemctl restart Moonraker
    echo "done"
}

# Helper functions
verify_ready()
{
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not run as root. Exiting."
        exit -1
    fi
}

# Run steps
verify_ready
link_extension
restart_klipper
add_updater
restart_moonraker
