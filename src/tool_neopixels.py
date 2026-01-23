
# Support for tool-specific LED mappings
#
# Copyright (C) 2026 AcrimoniousMirth
#
# This file may be distributed under the terms of the GNU GPLv3 license.

class ToolNeoPixelsConfig:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name().split()[-1]
        self.tool = config.get("tool")
        self.groups = {}
        
        # Parse groups from config
        # We need to replicate simple chain parsing logic here since we can't easily access led_effect's instance yet
        options = config.get_prefix_options("")
        for opt in options:
            if opt in ["tool", "leds"]:
                continue
            val = config.get(opt)
            # Simple parsing of "1" or "1,2" or "1-3"
            indices = []
            for item in val.split(','):
                item = item.strip()
                if '-' in item:
                    start, end = map(int, item.split('-'))
                    # Inclusive range for config convenience, converted to 0-indexed list
                    if start <= end:
                         indices.extend(range(start-1, end))
                    else:
                         indices.extend(range(start-1, end-2, -1)) # reversed
                else:
                    indices.append(int(item) - 1)
            self.groups[opt] = indices

        self.leds_config = config.get("leds", None)
        self.chain = None
        self.printer.add_object("tool_neopixels " + self.name, self)
        self.printer.register_event_handler('klippy:ready', self._handle_ready)

    def _handle_ready(self):
        if self.leds_config:
            # We need to resolve the physical chain object
            # self.leds_config looks like "neopixel:sb_leds" or "neopixel:sb_leds (1-10)"
            # We'll use a simplified parser here or rely on the fact that we just need the object name mostly
            # But wait, led_effect's parse_chain does robust parsing. 
            # Let's try to lookup the ledFrameHandler to use its parser if possible, or reimplement basic one.
            
            # Basic parsing: "type:name (indices)"
            parts = self.leds_config.split()
            chain_name = parts[0].replace(':', ' ')
            
            try:
                self.chain = self.printer.lookup_object(chain_name)
            except Exception:
                pass

    def get_target(self, group, index):
        if group in self.groups and index < len(self.groups[group]):
            led_index = self.groups[group][index]
            if self.chain:
                return self.chain, led_index
        return None

    def get_all_targets(self, group):
        targets = []
        if group in self.groups:
            for led_index in self.groups[group]:
                if self.chain:
                    targets.append((self.chain, led_index))
        return targets

    def get_involved_chains(self, group):
        if group in self.groups and self.chain:
            return [self.chain]
        return []

def load_config_prefix(config):
    return ToolNeoPixelsConfig(config)
