import { useEffect, useState } from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useDelayRender, useVideoConfig } from "remotion";
import { progress } from "../anim";
import { colors, fonts, sizes } from "../theme";
import type { SceneProps } from "../types";

type Step = { n: number; label: string; x: number; y: number; w: number; h: number };
type Sidecar = { width: number; height: number; steps: Step[] };

const SCALE = 1.5;

/** Walks through a numbered SVG diagram, highlighting one step at a time. */
export const DiagramWalk: React.FC<SceneProps> = ({ args }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const { delayRender, continueRender, cancelRender } = useDelayRender();
  const [handle] = useState(() => delayRender("diagram steps"));
  const [data, setData] = useState<Sidecar | null>(null);

  const svg = args.svg ?? "";
  const stem = svg.replace(/\.svg$/, "");

  useEffect(() => {
    fetch(staticFile(`diagrams/${stem}.json`))
      .then((r) => r.json())
      .then((d: Sidecar) => {
        setData(d);
        continueRender(handle);
      })
      .catch((e) => cancelRender(e));
  }, [stem, handle, continueRender, cancelRender]);

  if (!data) return null;

  const [lo, hi] = (args.steps ?? "1").split("-").map(Number);
  const range = data.steps.filter((s) => s.n >= lo && s.n <= (hi || lo));
  const slot = durationInFrames / range.length;
  const idx = Math.min(Math.floor(frame / slot), range.length - 1);
  const local = frame - idx * slot;
  const cur = range[idx];
  const prev = range[Math.max(idx - 1, 0)];
  const t = idx === 0 ? 1 : progress(local, 0, 14);
  const mix = (a: number, b: number) => interpolate(t, [0, 1], [a, b]);

  const width = data.width * SCALE;
  const height = data.height * SCALE;
  return (
    <AbsoluteFill style={{ background: colors.bg, fontFamily: fonts.sans, alignItems: "center" }}>
      <div
        style={{
          marginTop: 26,
          opacity: progress(local, 0, 10),
          background: colors.green,
          color: "#fff",
          fontSize: sizes.small,
          fontWeight: 700,
          borderRadius: 40,
          padding: "8px 36px",
        }}
      >
        {cur.n}. {cur.label}
      </div>
      <div
        style={{
          position: "relative",
          marginTop: 22,
          width,
          height,
          overflow: "hidden",
          borderRadius: 24,
          boxShadow: "0 6px 30px rgba(15,23,42,0.18)",
        }}
      >
        <Img src={staticFile(`diagrams/${svg}`)} style={{ width, height, display: "block" }} />
        <div
          style={{
            position: "absolute",
            left: mix(prev.x, cur.x) * SCALE,
            top: mix(prev.y, cur.y) * SCALE,
            width: mix(prev.w, cur.w) * SCALE,
            height: mix(prev.h, cur.h) * SCALE,
            border: `6px solid ${colors.green}`,
            borderRadius: 16,
            boxSizing: "border-box",
            boxShadow: "0 0 0 4000px rgba(248,250,252,0.68)",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
