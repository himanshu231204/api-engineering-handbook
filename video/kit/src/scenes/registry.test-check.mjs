// Fails when the scene registry and scene_names.json disagree, or a diagram sidecar is malformed.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const kit = path.resolve(here, "../..");
const problems = [];

const names = JSON.parse(readFileSync(path.join(kit, "scene_names.json"), "utf8"));
const registryPath = path.join(here, "registry.ts");
if (!existsSync(registryPath)) {
  problems.push("src/scenes/registry.ts does not exist");
} else {
  const src = readFileSync(registryPath, "utf8");
  const match = src.match(/export const scenes[^=]*=\s*\{([^}]*)\}/);
  if (!match) {
    problems.push("registry.ts has no `export const scenes = { ... }` object");
  } else {
    const keys = match[1]
      .split(",")
      .map((k) => k.trim().split(":")[0].trim())
      .filter(Boolean);
    for (const n of names) if (!keys.includes(n)) problems.push(`registry missing scene '${n}'`);
    for (const k of keys) if (!names.includes(k)) problems.push(`registry has unlisted scene '${k}'`);
    for (const n of names) {
      if (!existsSync(path.join(here, `${n}.tsx`))) problems.push(`missing component file ${n}.tsx`);
    }
  }
}

const stepsDir = path.join(kit, "diagram_steps");
if (existsSync(stepsDir)) {
  for (const file of readdirSync(stepsDir).filter((f) => f.endsWith(".json"))) {
    const data = JSON.parse(readFileSync(path.join(stepsDir, file), "utf8"));
    data.steps.forEach((s, i) => {
      if (s.n !== i + 1) problems.push(`${file}: step ${i} has n=${s.n}, expected ${i + 1}`);
      if (!(s.w > 0 && s.h > 0)) problems.push(`${file}: step ${s.n} needs positive w/h`);
      if (s.x < 0 || s.y < 0 || s.x + s.w > data.width || s.y + s.h > data.height) {
        problems.push(`${file}: step ${s.n} lies outside ${data.width}x${data.height}`);
      }
    });
  }
}

if (problems.length) {
  console.error(problems.join("\n"));
  process.exit(1);
}
console.log(`registry OK (${names.length} scenes)`);
