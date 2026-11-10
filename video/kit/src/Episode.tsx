import { Audio } from "@remotion/media";
import { AbsoluteFill, Sequence, staticFile } from "remotion";
import { scenes } from "./scenes/registry";
import { colors, fonts, safe, sizes } from "./theme";
import type { EpisodeProps } from "./types";

export const Episode: React.FC<EpisodeProps> = ({ timeline }) => {
  return (
    <AbsoluteFill style={{ background: colors.bg }}>
      {timeline.beats.map((beat) => (
        <Sequence key={beat.name} name={beat.name} from={beat.startFrame} durationInFrames={beat.frames}>
          {beat.audio ? <Audio src={staticFile(`audio/${beat.audio}`)} /> : null}
          {beat.cues.map((cue, i) => {
            const Scene = scenes[cue.scene];
            if (!Scene) throw new Error(`Unknown scene '${cue.scene}' in beat '${beat.name}'`);
            return (
              <Sequence
                key={i}
                name={cue.scene}
                from={cue.startFrame - beat.startFrame}
                durationInFrames={cue.frames}
              >
                <Scene
                  args={cue.args}
                  beat={beat.name}
                  title={timeline.title}
                  part={timeline.part}
                  index={timeline.index}
                />
              </Sequence>
            );
          })}
        </Sequence>
      ))}
      {timeline.beats.flatMap((beat) =>
        beat.captions.map((c, i) => (
          <Sequence
            key={`${beat.name}-${i}`}
            name="Caption"
            from={c.startFrame}
            durationInFrames={Math.max(1, c.endFrame - c.startFrame)}
          >
            <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: safe.top - 20 }}>
              <div
                style={{
                  fontFamily: fonts.sans,
                  fontSize: sizes.caption,
                  fontWeight: 600,
                  color: "#ffffff",
                  background: "rgba(17,24,39,0.88)",
                  borderRadius: 14,
                  padding: "12px 28px",
                  maxWidth: 1500,
                  textAlign: "center",
                }}
              >
                {c.text}
              </div>
            </AbsoluteFill>
          </Sequence>
        )),
      )}
    </AbsoluteFill>
  );
};
