import { AbsoluteFill, useCurrentFrame } from "remotion";
import { progress } from "../anim";
import { colors, fonts, safe, sizes } from "../theme";
import type { SceneProps } from "../types";

export const Concept: React.FC<SceneProps> = ({ args, beat }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        background: colors.bg,
        fontFamily: fonts.sans,
        justifyContent: "center",
        padding: `0 ${safe.x}px ${safe.bottom - 120}px`,
      }}
    >
      <div style={{ opacity: progress(frame, 0), color: colors.green, fontSize: 44, fontWeight: 700 }}>
        {beat}
      </div>
      <div
        style={{
          opacity: progress(frame, 6, 20),
          color: colors.text,
          fontSize: sizes.headline,
          fontWeight: 800,
          lineHeight: 1.1,
          marginTop: 16,
        }}
      >
        {args.heading ?? beat}
      </div>
      {args.body ? (
        <div
          style={{
            opacity: progress(frame, 20, 20),
            color: colors.slate,
            fontSize: sizes.body,
            lineHeight: 1.35,
            marginTop: 40,
            maxWidth: 1500,
          }}
        >
          {args.body}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
