import type React from "react";
import type { SceneProps } from "../types";
import { CodeReveal } from "./CodeReveal";
import { Concept } from "./Concept";
import { DiagramWalk } from "./DiagramWalk";
import { Mistakes } from "./Mistakes";
import { Quiz } from "./Quiz";
import { Recap } from "./Recap";
import { Terminal } from "./Terminal";
import { Title } from "./Title";

export const scenes: Record<string, React.FC<SceneProps>> = {
  Title,
  Concept,
  DiagramWalk,
  Terminal,
  CodeReveal,
  Mistakes,
  Recap,
  Quiz,
};
