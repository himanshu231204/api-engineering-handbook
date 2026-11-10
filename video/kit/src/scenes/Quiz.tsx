import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { progress } from "../anim";
import { colors, fonts, safe, sizes } from "../theme";
import type { SceneProps } from "../types";

/** Shows q1..q3 one at a time; each answer (a1..a3) appears in the last third of its slot. */
export const Quiz: React.FC<SceneProps> = ({ args }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const questions = [1, 2, 3].map((n) => ({ q: args[`q${n}`], a: args[`a${n}`] })).filter((x) => x.q);
  const slot = durationInFrames / Math.max(questions.length, 1);
  const active = Math.min(Math.floor(frame / slot), questions.length - 1);
  const local = frame - active * slot;
  const current = questions[active];
  if (!current) return null;
  const showAnswer = local > slot * 0.6;
  return (
    <AbsoluteFill
      style={{ background: colors.bg, fontFamily: fonts.sans, justifyContent: "center", padding: `0 ${safe.x}px` }}
    >
      <div style={{ color: colors.purple, fontSize: 48, fontWeight: 700 }}>
        Check yourself · {active + 1} of {questions.length}
      </div>
      <div
        style={{
          opacity: progress(local, 0, 15),
          color: colors.text,
          fontSize: 76,
          fontWeight: 800,
          lineHeight: 1.15,
          marginTop: 24,
        }}
      >
        {current.q}
      </div>
      {current.a ? (
        <div
          style={{
            opacity: showAnswer ? progress(local, slot * 0.6, 15) : 0,
            marginTop: 40,
            background: colors.greenSoft,
            border: `3px solid ${colors.green}`,
            borderRadius: 20,
            padding: "24px 36px",
            color: colors.text,
            fontSize: sizes.small,
            lineHeight: 1.35,
          }}
        >
          {current.a}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
