import fs from "node:fs";
import path from "node:path";

import { simulateConfiguration } from "../../frontend/js/simulation-reference.js";

const [, , inputPath] = process.argv;

if (!inputPath) {
  console.error("Usage: node tests/reference/run_js_simulation.mjs <config.json>");
  process.exit(1);
}

const absoluteInputPath = path.resolve(process.cwd(), inputPath);
const raw = fs.readFileSync(absoluteInputPath, "utf8");
const config = JSON.parse(raw);
const result = simulateConfiguration(config);

process.stdout.write(JSON.stringify(result));
