const std = @import("std");
const PERF = std.os.linux.PERF;

pub const PerfType = enum { hw, raw };

// NOTE: here are some useful resources if you want to access non-generalized
// event through "raw" config:
// https://github.com/Maratyszcza/NNPACK/blob/master/bench/perf_counter.c
// https://github.com/torvalds/linux/blob/7ff71e6d/arch/x86/events/intel/core.c#L6812-L6817
// https://github.com/torvalds/linux/blob/7ff71e6d/arch/x86/events/perf_event.h#L637-L658
pub const PerfConfig = union(PerfType) {
    hw: PERF.COUNT.HW,
    raw: struct {
        event: u8 = 0,
        umask: u8 = 0,
        edge: u8 = 0,
        inv: u8 = 0,
        cmask: u8 = 0,

        const Self = @This();

        pub fn value(self: Self) u64 {
            // Based on: https://github.com/Maratyszcza/NNPACK/blob/70a77f4/bench/perf_counter.c#L717-L721
            return (@as(u64, self.event) |
                @as(u64, self.umask) << 8 |
                @as(u64, self.edge) << 18 |
                @as(u64, self.inv) << 23 |
                @as(u64, self.cmask) << 24);
        }
    },

    pub fn value(self: PerfConfig) u64 {
        return switch (self) {
            .hw => |v| @intFromEnum(v),
            .raw => |v| v.value(),
        };
    }

    pub fn perfType(self: PerfConfig) PERF.TYPE {
        return switch (self) {
            .hw => PERF.TYPE.HARDWARE,
            .raw => PERF.TYPE.RAW,
        };
    }
};

pub const PerfMeasurement = struct {
    name: []const u8,
    full_name: []const u8 = "",
    config: PerfConfig,
};

// TODO: switch this one according to CPU model
pub const available_perf_measurements = @import("events/tigerlake.zig").avaliable_perf_measurements;

// nah, i don't want to fix the name length issue for now...
comptime {
    for (available_perf_measurements) |m| {
        if (m.name.len > 16) {
            @compileError(std.fmt.comptimePrint("Please consider restricting the name within 16 characters: {s}", .{m.name}));
        }
    }
}
