import { AbsoluteFill, useCurrentFrame } from "remotion";
import { progress } from "../anim";
import { colors, fonts, safe } from "../theme";
import type { SceneProps } from "../types";

export const Title: React.FC<SceneProps> = ({ args, title, part, index }) => {
  const frame = useCurrentFrame();
  const heading = args.heading ?? title;
  const kicker = args.kicker ?? (part ? `Part ${part} · Video ${index}` : "API Engineering Handbook");
  return (
    <AbsoluteFill
      style={{
        background: colors.bg,
        fontFamily: fonts.sans,
        justifyContent: "center",
        padding: `0 ${safe.x}px`,
      }}
    >
      <div style={{ opacity: progress(frame, 0), color: colors.green, fontSize: 48, fontWeight: 700, letterSpacing: 2 }}>
        {kicker}
      </div>
      <div
        style={{
          opacity: progress(frame, 8, 20),
          translate: `0px ${(1 - progress(frame, 8, 20)) * 40}px`,
          color: colors.text,
          fontSize: 160,
          fontWeight: 800,
          lineHeight: 1.05,
          marginTop: 24,
        }}
      >
        {heading}
      </div>
      <div style={{ opacity: progress(frame, 24), color: colors.muted, fontSize: 52, marginTop: 32 }}>
        {args.subtitle ?? "API Engineering Handbook"}
      </div>
    </AbsoluteFill>
  );
};
