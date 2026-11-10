import { Easing, interpolate } from "remotion";

const ease = Easing.bezier(0.16, 1, 0.3, 1);

/** 0 -> 1 over `len` frames starting at `from`, clamped. */
export const progress = (frame: number, from: number, len = 15): number =>
  interpolate(frame, [from, from + len], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });
