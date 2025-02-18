# Performance Optimizer Observation Platform

Stop flushing your performance down the drain.

## Overview

This command line tool uses Linux's `perf_event_open` functionality to compare the performance of multiple commands
with a colorful terminal user interface.

![image](https://github.com/andrewrk/poop/assets/106511/6fc9d22b-f95b-46ce-8dc5-d5cecc77c226)

## Usage

```
Usage: poop [options] <command1> ... <commandN>

Compares the performance of the provided commands.

Options:
 -d, --duration <ms>    (default: 5000) how long to repeatedly sample each command
 --color <when>         (default: auto) color output mode
                            available options: 'auto', 'never', 'ansi'
 -e, --events <list>    (default: '') a comma-separated event list (see also the
                            output of `$ perf list`)

```

> [!NOTE]  
> This fork is created for adding some intel CPU specific perf events while I
> was working on other projects. It's initially made to check whether it's
> possible to query other events that was not available in `std.os.linux.PERF`.
> Currently only part of perf events for Tiger Lake (11-th gen) are supported.
> If you need more available events to query, please see the "Development"
> section below.

## Building from Source

Tested with [Zig](https://ziglang.org/) `0.12.0`

```
zig build
```

## Development
### Add perf events supported by your CPU
1. Save the output of perf list
    ```bash
    $ perf list --detail > perflist.txt
    ```
2. Parse the list and convert it to Zig struct literal
    ```bash
    $ python parse_perflist.py perflist.txt > YOU_CPU_CODE_NAME.zig
    ```
3. Update or comment out any literal of which the `name` field is filled with
    the placeholder "PLEASE_RENAME_THIS_WITHIN_16_CHARS". Then move the
    generated zig file to "src/events/".
4. Update the line shown as follows in "src/events.zig" according to the name
    your file:
    ```zig
    pub const available_perf_measurements = @import("events/tigerlake.zig").avaliable_perf_measurements;
    ```

(I might come back to this project to avoid extending supports with this
approach in the future... But still hope it helps if anyone has a need to hack
it for their own needs.)

## Comparison with Hyperfine

Poop (so far) is brand new, whereas
[Hyperfine](https://github.com/sharkdp/hyperfine) is a mature project with more
configuration options and generally more polish.

However, poop does report peak memory usage as well as 5 other hardware
counters, which I personally find useful when doing performance testing. Hey,
maybe it will inspire the Hyperfine maintainers to add the extra data points!

Poop does not run the commands in a shell. This has the upside of not
including shell spawning noise in the data points collected, and the downside
of not supporting strings inside the commands.

Poop treats the first command as a reference and the subsequent ones
relative to it, giving the user the choice of the meaning of the coloring of
the deltas. Hyperfine always prints the wall-clock-fastest command first.

While Hyperfine is cross-platform, Poop is Linux-only.


[1]: https://github.com/ziglang/zig/blob/0.12.0/lib/std/os/linux.zig#L6977-L7111

