"""Just a script to parse the output of `$ perf list --detail` to dictionary
and Zig struct literal in a quick and dirty way.

Usage
-----
1. Save the output of `perf list --detail` to a file
    ```bash
    $ perf list --detail > perflist.txt
    ```
2. Parse it and generate initial Zig struct literal
    ```bash
    $ pythn parse_perflist.py perflist.txt > out.txt
    ```
3. Choose a proper abbreviation for any event name of which the length exceeds
    16 characters. (the name field will be filled with
    "PLEASE_RENAME_THIS_WITHIN_16_CHARS")
"""
import argparse

DEBUG = False
EXPECTED_MAX_NUM_LINES_OF_DESC = 50

def log_debug(content):
    if DEBUG:
        print(content)

def peek_line(f):
    pos = f.tell()
    line = f.readline()
    f.seek(pos)
    return line

def is_event(line: str):
    return line[0:2] == "  " and line[2:4] != "  "

def is_event_content(line: str):
    return line.startswith("       ")  # 7 spaces

class PerfListParser(object):
    def __init__(self, input_file: str):
        self.f = open(input_file, "r")
        self.cur_section = ""
        self.cur_line = ""
        self.data = {}

    def parse_section(self):
        line = self.cur_line
        assert(line[0] != " ")
        idx_semicolon = line.find(":")
        self.cur_section = line[0:idx_semicolon]
        self.data.update({self.cur_section: {}})
        log_debug(f"[DEBUG] found section '{self.cur_section}' from line '{line}'")

    def parse_item(self):
        line = self.cur_line
        assert(is_event(line))

        idx_event_tag_start = line.find("[")
        if idx_event_tag_start != -1:
            event_name_str = line[0:idx_event_tag_start].strip()
        else:
            event_name_str = line.strip()

        idx_OR = event_name_str.find("OR")
        if idx_OR != -1:
            # We pick the first name only
            event_name = event_name_str[0:idx_OR].strip()
        else:
            event_name = event_name_str.strip()
        log_debug(f"event name: {event_name}")

        # Proceed next lines to find event config (event, inv, cmask, umask)
        next_line = peek_line(self.f)
        idx_config_start, idx_config_end = -1, -1

        safety_cnt = 0
        while is_event_content(next_line):
            safety_cnt += 1
            if safety_cnt > EXPECTED_MAX_NUM_LINES_OF_DESC:
                # a dumb safety check to avoid falling into infinite loop for ill-formed input file
                raise RuntimeError("wut?")

            line = self.f.readline()
            idx_config_start = line.find("/")

            if idx_config_start != -1:
                idx_config_end = line[idx_config_start + 1:].find("/")
            if idx_config_end != -1:
                config_like_str = line[idx_config_start + 1 : idx_config_start + idx_config_end + 1]
                if config_like_str.startswith("event"):
                    event_config = self.parse_event_config(config_like_str)
                    log_debug(config_like_str)
                    self.data[self.cur_section].update({event_name: event_config})

            next_line = peek_line(self.f)

    def parse_event_config(self, config_str: str) -> dict:
        config = {"event": 0, "umask": 0, "edge": 0, "inv": 0, "cmask": 0}
        for part in config_str.split(","):
            key, val = part.split("=")
            config[key] = int(val, 16)
        return config

    def parse(self):
        while True:
            line = self.f.readline()
            if len(line) == 0:  # EOF
                break

            self.cur_line = line
            stripped = line.strip()

            if line.startswith("  "):
                self.parse_item()
            elif len(stripped) != 0 and stripped[0] != " ":
                self.parse_section()

# These events are already included in poop
EVENTS_TO_EXCLUDE = [
    "cpu-cycles",
    "instructions",
    "cache-references",
    "cache-misses",
    "branch-misses",
];

STRUCT_TEMPLATE = """
.{{
    .name = "{abbr}",
    .full_name = "{name}",
    .config = .{{ .raw = .{{ .event = {event:#04x}, .umask = {umask:#04x}, .edge = {edge:#04x}, .inv = {inv:#04x}, .cmask = {cmask:#04x} }} }},
}},"""

class ZigStructCodegen(object):
    def __init__(self, perf_event_data: dict, event_name_max_len: int = 16):
        self.perf_event_data = perf_event_data
        self.event_name_max_len = event_name_max_len

    def gen(self):
        for section, events in self.perf_event_data.items():
            print(f"// {section}", end="")
            self.gen_event(events)

    def gen_event(self, events: dict):
        for name, config in events.items():
            if name in EVENTS_TO_EXCLUDE:
                continue
            if len(name) > self.event_name_max_len:
                abbr = "PLEASE_RENAME_THIS_WITHIN_16_CHARS"
            else:
                abbr = name
            print(STRUCT_TEMPLATE.format(
                abbr=abbr,
                name=name,
                event=config["event"],
                umask=config["umask"],
                edge=config["edge"],
                inv=config["inv"],
                cmask=config["cmask"],
            ), end="")
        print()


def main(input_file):
    plparser = PerfListParser(input_file)
    plparser.parse()

    codegen = ZigStructCodegen(plparser.data)
    codegen.gen()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(args.input_file)

