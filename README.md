# LED Effects for Klipper

## Description

This is the standalone repository of the Klipper LED Effects module developed by [Paul McGowan](https://github.com/mental405) with contributions from myself.
It allows Klipper to run effects and animations on addressable LEDs, such as Neopixels, WS2812 or SK6812.

Check out Paul's printer:

[![Hello Friend. -International Edition-](https://i3.ytimg.com/vi/-VpZTDSu1-8/hqdefault.jpg)](https://www.youtube.com/watch?v=-VpZTDSu1-8)

See the chapter in this video from Vector3D what it can do and how to set it up (start from the beginning to learn how to connect the LEDs):

[![The 3D Printer Upgrade You didn’t know you needed](https://i3.ytimg.com/vi/14LC8Tcd_JQ/hqdefault.jpg)](https://youtu.be/14LC8Tcd_JQ?t=779)

And this one (in french) from Tom's Basement:

[![Klipper LED EFFECTS : C'est Noël avant l'heure dans votre imprimante 3D ! (Tuto Leds)](http://i3.ytimg.com/vi/6rGjlBjFhss/hqdefault.jpg)](https://www.youtube.com/watch?v=6rGjlBjFhss)

## Disclaimer
**This is work in progress and currently in "beta" state.**
I don't take any responsibility for any damage that happens while using this software.

## Support

For questions and support use the Q&A section on the [Discussions](https://github.com/julianschill/klipper-led_effect/discussions) page.

If you found a bug or you want to file a feature request open an [issue](https://github.com/julianschill/klipper-led_effect/issues).

If you need direct support or want to help by testing or contributing, please contact me on the [Klipper](https://discord.klipper3d.org/) or [Voron](https://discord.gg/voron) Discord. User: 5hagbard23

## Installation

### Automatic installation

The module can be installed into a existing Klipper installation with an install script. 

    cd ~
    git clone https://github.com/julianschill/klipper-led_effect.git
    cd klipper-led_effect
    ./install-led_effect.sh

If your directory structure differs from the usual setup you can configure the
installation script with parameters:

    ./install-led_effect.sh [-k <klipper path>] [-s <klipper service name>] [-c <configuration path>]

### Manual installation
Clone the repository:

    cd ~
    git clone https://github.com/julianschill/klipper-led_effect.git

Stop Klipper:

    systemctl stop klipper

Link the file in the Klipper directory (adjust the paths as needed):

    ln -s klipper-led_effect/src/led_effect.py ~/klipper/klippy/extras/led_effect.py

Start Klipper:

    systemctl start klipper

Add the updater section to moonraker.conf and restart moonraker to receive 
updates:

    [update_manager led_effect]
    type: git_repo
    path: ~/klipper-led_effect
    origin: https://github.com/julianschill/klipper-led_effect.git
    is_system_service: False

## Uninstall

Remove all led_effect definitions in your Klipper configuration and the updater
section in the Moonraker configuration. Then run the script to remove the link:

    cd ~
    cd klipper-led_effect
    ./install-led_effect.sh -u

If your directory structure differs from the usual setup you can configure the
installation script with parameters:

    ./install-led_effect.sh -u [-k <klipper path>] [-s <klipper service name>] [-c <configuration path>]

If that fails, you can delete the link in Klipper manually:

    rm ~/klipper/klippy/extras/led_effect.py

Delete the repository (optional):

    cd ~
    rm -rf klipper-led_effect

## Configuration

Documentation can be found [here](docs/LED_Effect.md).

## Support
If you want to support me, either contribute code or 

[![kofi](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://ko-fi.com/Hagbard)
