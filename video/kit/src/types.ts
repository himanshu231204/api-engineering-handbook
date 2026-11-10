// Mirrors the JSON written by video/tools/timeline.py (build_timeline).
export type CueTL = {
  scene: string;
  args: Record<string, string>;
  startFrame: number;
  frames: number;
};

export type CaptionTL = { startFrame: number; endFrame: number; text: string };

export type BeatTL = {
  name: string;
  startFrame: number;
  frames: number;
  audio: string | null;
  cues: CueTL[];
  captions: CaptionTL[];
};

export type Timeline = {
  fps: number;
  width: number;
  height: number;
  title: string;
  part: number;
  index: number;
  beats: BeatTL[];
  totalFrames: number;
};

export type SceneProps = {
  args: Record<string, string>;
  beat: string;
  title: string;
  part: number;
  index: number;
};

export type EpisodeProps = { timeline: Timeline };
