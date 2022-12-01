#!/bin/bash
KLIPPER_PATH="${HOME}/klipper"
SYSTEMDDIR="/etc/systemd/system"

set_config_dir()
{
    if [-d "${HOME}/printer_data/config"]; then
        KLIPPER_CONFIG_DIR="${HOME}/printer_data/config"
    else
        KLIPPER_CONFIG_DIR="${HOME}/klipper_config"
     fi
}

# Step 1:  Verify Klipper has been installed
check_klipper()
{
    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
        echo "Klipper service found!"
    else
        echo "Klipper service not found, please install Klipper first"
        exit -1
    fi

}

# Step 2: link extension to Klipper
link_extension()
{
    echo "Linking extension to Klipper..."
    ln -sf "${SRCDIR}/led_effect.py" "${KLIPPER_PATH}/klippy/extras/led_effect.py"
}

# Step 3: Add updater
# webcamd to moonraker.conf
echo -e "Adding update manager to moonraker.conf"

update_section=$(grep -c '\[update_manager led_effect\]' \
${KLIPPER_CONFIG_DIR}/moonraker.conf || true)
if [ "${update_section}" -eq 0 ]; then
  echo -e "\n" >> ${KLIPPER_CONFIG_DIR}/moonraker.conf
  while read -r line; do
    echo -e "${line}" >> ${KLIPPER_CONFIG_DIR}/moonraker.conf
  done < "$PWD/file_templates/moonraker_update.txt"
  echo -e "\n" >> ${KLIPPER_CONFIG_DIR}/moonraker.conf
else
  echo -e "[update_manager led_effect] already exist in moonraker.conf [SKIPPED]"
fi



# Step 4: restarting Klipper
restart_klipper()
{
    echo "Restarting Klipper..."
    sudo systemctl restart klipper
}

# Helper functions
verify_ready()
{
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not run as root"
        exit -1
    fi
}

# Force script to exit if an error occurs
set -e

# Find SRCDIR from the pathname of this script
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/src/ && pwd )"

# Parse command line arguments
while getopts "k:" arg; do
    case $arg in
        k) KLIPPER_PATH=$OPTARG;;
    esac
done

# Run steps
verify_ready
link_extension
restart_klipper
