import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const repoRoot = path.resolve(root, "..");
const requiredBanner = "not evidence of a completed full M-ABD implementation or full paper reproduction";
const forbiddenBasePaths = ["/physics-primitive-agent", "https://jandan138.github.io/physics-primitive-agent"];
const forbiddenClaimPatterns = [
  { label: "M-ABD is implemented", pattern: /\bM-ABD\s+is\s+implemented\b/i },
  { label: "implemented M-ABD", pattern: /\bimplemented\s+M-ABD\b/i },
  { label: "full M-ABD implementation is complete", pattern: /\bfull\s+M-ABD\s+implementation\s+is\s+complete\b/i },
  { label: "paper-faithful solver", pattern: /\bpaper-faithful\s+solver\b/i },
  { label: "reproduces the paper", pattern: /\breproduces\s+the\s+paper\b/i },
  { label: "Newton supports affine-body dynamics", pattern: /\bNewton\s+supports\s+affine-body\s+dynamics\b/i },
  { label: "matches paper results", pattern: /\bmatches\s+paper\s+results\b/i },
  { label: "baseline comparison passed", pattern: /\bbaseline\s+comparison\s+passed\b/i },
  { label: "unmodified Newton supports affine-body dynamics", pattern: /\bunmodified\s+Newton\s+(?:already\s+)?supports\s+affine-body\s+dynamics\b/i },
  { label: "unmodified Newton supports M-ABD", pattern: /\bunmodified\s+Newton\s+(?:already\s+)?supports\s+M-ABD\b/i },
  { label: "Newton rigid-body solvers are equivalent", pattern: /\bNewton\s+rigid-body\s+solvers\s+are\s+equivalent\b/i },
  { label: "paper-faithful implicit RBD baseline", pattern: /\bpaper-faithful\s+implicit\s+RBD\s+baseline\b/i },
  { label: "body_q proxy is paper-faithful affine collision", pattern: /\bbody_q\s+proxy\s+is\s+paper-faithful\s+affine\s+collision\b/i },
  { label: "spinning-box comparison is a passed paper experiment", pattern: /\bspinning-box\s+comparison\s+protocol\s+report\s+is\s+a\s+passed\s+paper\s+experiment\b/i },
  { label: "paper-faithful collision or contact solve", pattern: /\bpaper-faithful\s+(?:collision|contact)\s+solve\b/i },
  { label: "paper trajectory agreement", pattern: /\bpaper\s+trajectory\s+agreement\b/i },
  { label: "M-ABD lane pass", pattern: /\bM-ABD\s+lane\s+pass\b/i },
  { label: "generic inequality-constrained M-ABD KKT", pattern: /\bgeneric\s+inequality-constrained\s+M-ABD\s+KKT\b/i },
  { label: "full robot-control reproduction", pattern: /\bfull\s+robot-control\s+(?:or\s+closed-loop\s+actuation\s+)?reproduction\b/i },
  { label: "comparative baselines are reproduced", pattern: /\bcomparative\s+baselines\s+are\s+reproduced\b/i },
  { label: "CPU timings are paper-comparable", pattern: /\bCPU\s+timings\s+are\s+paper-comparable\b/i },
  { label: "Phase 29 diagnostics are a solver fix", pattern: /\bPhase\s*29\b.*\b(?:solver|projection|decoupled\s+velocity\s+semantics)\s+fix\b/i },
  { label: "Phase 30 source-audit absence is proof", pattern: /\bPhase\s*30\b.*\bsource-audit\b.*\bproof\b.*\b(?:private\s+author-code\s+behavior|Newton\s+solver\s+modification|paper\s+experiment\s+pass)\b/i },
  { label: "Phase 31 availability is proof of artifact absence", pattern: /\bPhase\s*31\b.*\b(?:project-page|video|Code\s*\(coming\s+soon\))\b.*\bproof\b.*\b(?:private|unpublished|author-owned)\b/i },
  { label: "private or unpublished author artifacts do not exist", pattern: /\bproof\s+that\s+(?:private|unpublished|author-owned)\b.*\b(?:code|implementation|solver\s+artifacts?)\b.*\bdo(?:es)?\s+not\s+exist\b/i },
];
const requiredFrontmatterKeys = ["title", "description", "module", "order", "status", "claimStatus"];
const requiredLessonComponents = ["<ProblemCard", "<ConceptCard", "<RememberBox"];
const requiredTutorialComponents = [
  {
    marker: "<LearningGoals",
    importPattern: /^\s*import\s+LearningGoals\s+from\s+["']\.\.\/\.\.\/components\/LearningGoals\.astro["'];?\s*$/m,
    importName: "LearningGoals",
  },
  {
    marker: "<PrereqBox",
    importPattern: /^\s*import\s+PrereqBox\s+from\s+["']\.\.\/\.\.\/components\/PrereqBox\.astro["'];?\s*$/m,
    importName: "PrereqBox",
  },
  {
    marker: "<CheckpointQuiz",
    importPattern: /^\s*import\s+CheckpointQuiz\s+from\s+["']\.\.\/\.\.\/components\/CheckpointQuiz\.astro["'];?\s*$/m,
    importName: "CheckpointQuiz",
  },
  {
    marker: "<PracticePrompt",
    importPattern: /^\s*import\s+PracticePrompt\s+from\s+["']\.\.\/\.\.\/components\/PracticePrompt\.astro["'];?\s*$/m,
    importName: "PracticePrompt",
  },
];
const requiredGuidedTutorialComponents = [
  {
    marker: "<GuidedProjectStep",
    importPattern: /^\s*import\s+GuidedProjectStep\s+from\s+["']\.\.\/\.\.\/components\/GuidedProjectStep\.astro["'];?\s*$/m,
    importName: "GuidedProjectStep",
  },
  {
    marker: "<WorkedExercise",
    importPattern: /^\s*import\s+WorkedExercise\s+from\s+["']\.\.\/\.\.\/components\/WorkedExercise\.astro["'];?\s*$/m,
    importName: "WorkedExercise",
  },
];

const mathBridgeRequiredLessonSlugs = new Set([
  "vectors-matrices-transforms",
  "affine-state",
  "svd-polar-rotation",
  "generalized-coordinates-forces",
  "implicit-time-stepping",
  "newton-hessian-kkt",
  "single-body-abd",
  "multi-body-mabd",
]);

const mathBridgeComponent = {
  marker: "<MathBridge",
  importPattern: /^\s*import\s+MathBridge\s+from\s+["']\.\.\/\.\.\/components\/MathBridge\.astro["'];?\s*$/m,
  importName: "MathBridge",
};

const requiredExecutableTutorialComponents = [
  {
    marker: "<ToySolverStep",
    importPattern: /^\s*import\s+ToySolverStep\s+from\s+["']\.\.\/\.\.\/components\/ToySolverStep\.astro["'];?\s*$/m,
    importName: "ToySolverStep",
  },
  {
    marker: "<MisconceptionRepair",
    importPattern: /^\s*import\s+MisconceptionRepair\s+from\s+["']\.\.\/\.\.\/components\/MisconceptionRepair\.astro["'];?\s*$/m,
    importName: "MisconceptionRepair",
  },
];

const handCalcRequiredLessonSlugs = new Set([
  "vectors-matrices-transforms",
  "affine-state",
  "svd-polar-rotation",
  "generalized-coordinates-forces",
  "implicit-time-stepping",
  "newton-hessian-kkt",
  "single-body-abd",
  "multi-body-mabd",
]);

const handCalcComponent = {
  marker: "<HandCalc",
  importPattern: /^\s*import\s+HandCalc\s+from\s+["']\.\.\/\.\.\/components\/HandCalc\.astro["'];?\s*$/m,
  importName: "HandCalc",
};

const chapterRecapRequiredLessonSlugs = new Set([
  "affine-state",
  "implicit-time-stepping",
  "repo-evidence-map",
]);

const chapterRecapComponent = {
  marker: "<ChapterRecap",
  importPattern: /^\s*import\s+ChapterRecap\s+from\s+["']\.\.\/\.\.\/components\/ChapterRecap\.astro["'];?\s*$/m,
  importName: "ChapterRecap",
};
const requiredFigureProps = ["alt", "caption", "kind", "provenance", "claimStatus"];
const allowedFigureAssetImport = /^\.\.\/\.\.\/assets\/diagrams\/[^/]+\.(?:png|webp)$/;
const rasterDiagramAssetImport = /^\.\.\/\.\.\/assets\/diagrams\/([^/]+\.(?:png|webp))$/;
const requiredLessonFigureProvenance = "ai-generated-raster";
const aiDiagramManifestPath = "src/assets/diagrams/ai-diagram-manifest.json";
const aiDiagramManifestDisplayPath = "site/src/assets/diagrams/ai-diagram-manifest.json";
const forbiddenAssetExtensions = new Set([".pdf", ".tex", ".mp4", ".mov", ".avi", ".log", ".usd", ".usda", ".usdc"]);

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) return walk(fullPath);
    return [fullPath];
  });
}

function readIfExists(relativePath) {
  const fullPath = path.join(root, relativePath);
  if (!fs.existsSync(fullPath)) return null;
  return fs.readFileSync(fullPath, "utf8");
}

function requiredLessonSlugs() {
  const lessons = readIfExists("src/data/lessons.ts");
  if (lessons === null) return null;
  return [...lessons.matchAll(/\bslug:\s*"([^"]+)"/g)].map((match) => match[1]);
}

function frontmatter(text) {
  if (!text.startsWith("---\n")) return "";
  const end = text.indexOf("\n---", 4);
  if (end === -1) return "";
  return text.slice(4, end);
}

function isAllowedClaimWarning(line) {
  return /\b(Avoid|avoid|Do not|do not|unsupported|not evidence|not verified|not claim|not implemented|not a completed)\b|不是|不能|不等于|未验证|不声称|不要|没有|并非/.test(line);
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function hasForbiddenBasePathInLinkContext(text, forbidden) {
  const escaped = escapeRegExp(forbidden);
  const contexts = [
    new RegExp(`\\b(?:href|src)\\s*=\\s*["'][^"']*${escaped}`, "i"),
    new RegExp(`\\b(?:base|site)\\s*:\\s*["'][^"']*${escaped}`, "i"),
    new RegExp(`["'](?:https?:\\/\\/[^"']*)?${escaped}(?:[^"']*)["']`, "i"),
  ];
  return contexts.some((pattern) => pattern.test(text));
}

function rootRelativeLinkIssues(relative, text) {
  const issues = [];
  const linkPattern = /\b(?:href|src)\s*=\s*["'](\/[^"']*)["']/gi;
  for (const match of text.matchAll(linkPattern)) {
    const value = match[1];
    if (value.startsWith("/mabd-newton/")) {
      continue;
    }
    issues.push(`${relative}: root-relative link ${value} must use BASE_URL or an absolute external URL`);
  }
  return issues;
}

function displayPath(file) {
  if (file.startsWith(root)) return path.relative(root, file);
  return path.relative(repoRoot, file);
}

function stripExamplesAndComments(text) {
  return text
    .replace(/```[\s\S]*?```/g, "")
    .replace(/\{\/\*[\s\S]*?\*\/\}/g, "")
    .replace(/<!--[\s\S]*?-->/g, "");
}

function figureCalls(text) {
  return [...stripExamplesAndComments(text).matchAll(/^[ \t]*<Figure\b[\s\S]*?(?:\/>|<\/Figure>)/gm)].map((match) => match[0]);
}

function checkpointDetailsCount(text) {
  const cleaned = stripExamplesAndComments(text);
  return [...cleaned.matchAll(/^[ \t]*<CheckpointQuiz\b[\s\S]*?<\/CheckpointQuiz>/gm)]
    .reduce((count, checkpoint) => count + [...checkpoint[0].matchAll(/<details\b/g)].length, 0);
}

function componentDetailsCount(text, componentName) {
  const cleaned = stripExamplesAndComments(text);
  const pattern = new RegExp(`^[ \\t]*<${componentName}\\b[\\s\\S]*?<\\/${componentName}>`, "gm");
  return [...cleaned.matchAll(pattern)]
    .reduce((count, component) => count + [...component[0].matchAll(/<details\b/g)].length, 0);
}

function assetImports(text) {
  return [...text.matchAll(/^\s*import\s+(\w+)\s+from\s+["']([^"']+\.(?:svg|png|jpg|jpeg|webp|gif))["'];?\s*$/gim)]
    .map((match) => ({ name: match[1], path: match[2] }));
}

function figurePropValue(figure, prop) {
  const pattern = new RegExp(`${prop}\\s*=\\s*(?:"([^"]+)"|'([^']+)'|\\{\\s*"([^"]+)"\\s*\\}|\\{\\s*'([^']+)'\\s*\\})`, "m");
  const match = figure.match(pattern);
  return match ? match.slice(1).find((value) => value !== undefined) : null;
}

function figureSrcName(figure) {
  const match = figure.match(/\bsrc\s*=\s*\{\s*(\w+)\s*\}/m);
  return match ? match[1] : null;
}

function importsFigureComponent(text) {
  return /^\s*import\s+Figure\s+from\s+["']\.\.\/\.\.\/components\/Figure\.astro["'];?\s*$/m.test(text);
}

function manifestEntries(value) {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.entries)) return value.entries;
  if (Array.isArray(value?.diagrams)) return value.diagrams;
  return null;
}

function aiDiagramManifestIssues(importedRasterDiagrams) {
  if (importedRasterDiagrams.length === 0) return [];

  const issues = [];
  const text = readIfExists(aiDiagramManifestPath);
  if (text === null) {
    return [`${aiDiagramManifestDisplayPath}: missing AI diagram manifest`];
  }

  let manifest;
  try {
    manifest = JSON.parse(text);
  } catch (error) {
    return [`${aiDiagramManifestDisplayPath}: invalid JSON (${error.message})`];
  }

  const entries = manifestEntries(manifest);
  if (entries === null) {
    return [`${aiDiagramManifestDisplayPath}: must be an array or contain entries/diagrams array`];
  }

  const entriesByFile = new Map();
  for (const entry of entries) {
    if (entry && typeof entry.file === "string") {
      if (entriesByFile.has(entry.file)) {
        issues.push(`${aiDiagramManifestDisplayPath}: duplicate entry for ${entry.file}`);
      }
      entriesByFile.set(entry.file, entry);
    }
  }

  for (const diagram of importedRasterDiagrams) {
    const entry = entriesByFile.get(diagram.file);
    if (entry === undefined) {
      issues.push(`${aiDiagramManifestDisplayPath}: missing entry for ${diagram.file}`);
      continue;
    }
    if (entry.lesson !== diagram.lesson) {
      issues.push(`${aiDiagramManifestDisplayPath}: ${diagram.file} lesson must be ${diagram.lesson}`);
    }
    if (entry.provenance !== requiredLessonFigureProvenance) {
      issues.push(`${aiDiagramManifestDisplayPath}: ${diagram.file} provenance must be ${requiredLessonFigureProvenance}`);
    }
    if (entry.claimStatus !== "conceptual" && entry.claimStatus !== "not_evidence") {
      issues.push(`${aiDiagramManifestDisplayPath}: ${diagram.file} claimStatus must be conceptual or not_evidence`);
    }
    if (typeof entry.prompt !== "string" || entry.prompt.trim() === "") {
      issues.push(`${aiDiagramManifestDisplayPath}: ${diagram.file} prompt must be a non-empty string`);
    }
    if (typeof entry.reviewNotes !== "string" || entry.reviewNotes.trim() === "") {
      issues.push(`${aiDiagramManifestDisplayPath}: ${diagram.file} reviewNotes must be a non-empty string`);
    }
  }

  return issues;
}

const issues = [];
const importedRasterDiagrams = [];
const requiredLessons = requiredLessonSlugs();

if (requiredLessons === null) {
  issues.push("missing src/data/lessons.ts");
} else if (requiredLessons.length === 0) {
  issues.push("src/data/lessons.ts must define required lesson slugs");
}

for (const slug of requiredLessons ?? []) {
  const lessonPath = path.join(root, "src/content/lessons", `${slug}.mdx`);
  if (!fs.existsSync(lessonPath)) {
    issues.push(`missing required lesson: ${slug}`);
  }
}

const config = readIfExists("astro.config.mjs");
if (config === null) {
  issues.push("missing astro.config.mjs");
} else if (!config.includes('base: "/mabd-newton"')) {
  issues.push("astro.config.mjs must use base: /mabd-newton");
}

const layout = readIfExists("src/layouts/LearnLayout.astro");
if (layout === null) {
  issues.push("missing src/layouts/LearnLayout.astro");
} else if (!layout.includes(requiredBanner)) {
  issues.push("LearnLayout.astro missing claim-boundary banner");
}

const deployWorkflow = readIfExists("../.github/workflows/deploy-learning-site.yml");
if (deployWorkflow === null) {
  issues.push("missing .github/workflows/deploy-learning-site.yml");
} else if (
  deployWorkflow.includes("actions/configure-pages@v5")
  && !/enablement:\s*true/.test(deployWorkflow)
) {
  issues.push("deploy-learning-site.yml must set configure-pages enablement: true");
}

const checkedFiles = [
  ...walk(path.join(root, "src")).filter((file) => /\.(astro|mdx|ts)$/.test(file)),
  path.join(root, "README.md"),
  path.join(repoRoot, ".github/workflows/deploy-learning-site.yml"),
].filter((file) => fs.existsSync(file));

for (const file of walk(path.join(root, "src/assets"))) {
  const extension = path.extname(file).toLowerCase();
  if (forbiddenAssetExtensions.has(extension)) {
    issues.push(`${displayPath(file)}: forbidden asset extension ${extension}`);
  }
}

for (const file of checkedFiles) {
  const relative = displayPath(file);
  const text = fs.readFileSync(file, "utf8");

  for (const forbidden of forbiddenBasePaths) {
    if (hasForbiddenBasePathInLinkContext(text, forbidden)) {
      issues.push(`${relative}: hardcoded wrong deployment base ${forbidden}`);
    }
  }

  issues.push(...rootRelativeLinkIssues(relative, text));

  const lines = text.split(/\r?\n/);
  lines.forEach((line, index) => {
    for (const claim of forbiddenClaimPatterns) {
      if (claim.pattern.test(line) && !isAllowedClaimWarning(line)) {
        issues.push(`${relative}:${index + 1}: forbidden unsupported claim phrase ${claim.label}`);
      }
    }
  });

  if (relative.endsWith(".mdx")) {
    const fm = frontmatter(text);
    for (const key of requiredFrontmatterKeys) {
      if (!new RegExp(`^${key}:`, "m").test(fm)) {
        issues.push(`${relative}: missing frontmatter key ${key}:`);
      }
    }
    for (const marker of requiredLessonComponents) {
      if (!text.includes(marker)) {
        issues.push(`${relative}: missing learning component ${marker}`);
      }
    }
    const cleanedLessonText = stripExamplesAndComments(text);
    for (const component of requiredTutorialComponents) {
      if (!component.importPattern.test(cleanedLessonText)) {
        issues.push(`${relative}: missing ${component.importName} component import`);
      }
      if (!cleanedLessonText.includes(component.marker)) {
        issues.push(`${relative}: missing tutorial component ${component.marker}`);
      }
    }
    for (const component of requiredGuidedTutorialComponents) {
      if (!component.importPattern.test(cleanedLessonText)) {
        issues.push(`${relative}: missing ${component.importName} component import`);
      }
      if (!cleanedLessonText.includes(component.marker)) {
        issues.push(`${relative}: missing guided tutorial component ${component.marker}`);
      }
    }
    if (componentDetailsCount(text, "WorkedExercise") < 2) {
      issues.push(`${relative}: WorkedExercise must include at least two <details> blocks`);
    }
    const lessonSlug = path.basename(file, ".mdx");
    if (mathBridgeRequiredLessonSlugs.has(lessonSlug)) {
      if (!mathBridgeComponent.importPattern.test(cleanedLessonText)) {
        issues.push(`${relative}: missing MathBridge component import`);
      }
      if (!cleanedLessonText.includes(mathBridgeComponent.marker)) {
        issues.push(`${relative}: missing required MathBridge component`);
      }
    }
    for (const component of requiredExecutableTutorialComponents) {
      if (!component.importPattern.test(cleanedLessonText)) {
        issues.push(`${relative}: missing ${component.importName} component import`);
      }
      if (!cleanedLessonText.includes(component.marker)) {
        issues.push(`${relative}: missing executable tutorial component ${component.marker}`);
      }
    }
    if (handCalcRequiredLessonSlugs.has(lessonSlug)) {
      if (!handCalcComponent.importPattern.test(cleanedLessonText)) {
        issues.push(`${relative}: missing HandCalc component import`);
      }
      if (!cleanedLessonText.includes(handCalcComponent.marker)) {
        issues.push(`${relative}: missing required HandCalc component`);
      }
    }
    if (chapterRecapRequiredLessonSlugs.has(lessonSlug)) {
      if (!chapterRecapComponent.importPattern.test(cleanedLessonText)) {
        issues.push(`${relative}: missing ChapterRecap component import`);
      }
      if (!cleanedLessonText.includes(chapterRecapComponent.marker)) {
        issues.push(`${relative}: missing required ChapterRecap component`);
      }
    }
    if (checkpointDetailsCount(text) < 2) {
      issues.push(`${relative}: CheckpointQuiz must include at least two <details> questions`);
    }
    const figures = figureCalls(text);
    if (figures.length === 0) {
      issues.push(`${relative}: missing learning component <Figure`);
    }
    if (figures.length > 0 && !importsFigureComponent(text)) {
      issues.push(`${relative}: missing Figure component import from ../../components/Figure.astro`);
    }
    const imports = assetImports(text);
    const importsByName = new Map(imports.map((imported) => [imported.name, imported.path]));
    figures.forEach((figure, index) => {
      for (const prop of requiredFigureProps) {
        if (figurePropValue(figure, prop) === null) {
          issues.push(`${relative}: Figure ${index + 1} missing required prop ${prop}`);
        }
      }
      if (figurePropValue(figure, "kind") !== "diagram") {
        issues.push(`${relative}: Figure ${index + 1} kind must be diagram`);
      }
      if (figurePropValue(figure, "provenance") !== requiredLessonFigureProvenance) {
        issues.push(`${relative}: Figure ${index + 1} provenance must be ${requiredLessonFigureProvenance}`);
      }
      const claimStatus = figurePropValue(figure, "claimStatus");
      if (claimStatus !== "conceptual" && claimStatus !== "not_evidence") {
        issues.push(`${relative}: Figure ${index + 1} claimStatus must be conceptual or not_evidence`);
      }
      const srcName = figureSrcName(figure);
      if (srcName === null) {
        issues.push(`${relative}: Figure ${index + 1} src must reference an imported PNG/WebP asset`);
        return;
      }
      const importedPath = importsByName.get(srcName);
      if (importedPath === undefined) {
        issues.push(`${relative}: Figure ${index + 1} src ${srcName} is not imported`);
        return;
      }
      if (!allowedFigureAssetImport.test(importedPath)) {
        issues.push(`${relative}: Figure ${index + 1} asset ${importedPath} must be from ../../assets/diagrams/*.png or *.webp`);
      }
    });
    for (const imported of imports) {
      const rasterDiagramMatch = imported.path.match(rasterDiagramAssetImport);
      if (rasterDiagramMatch) {
        importedRasterDiagrams.push({
          file: rasterDiagramMatch[1],
          lesson: path.basename(file, ".mdx"),
        });
      }
      if (imported.path.includes("/assets/") && !allowedFigureAssetImport.test(imported.path)) {
        issues.push(`${relative}: imported site asset ${imported.path} must be a PNG/WebP from ../../assets/diagrams/*.png or *.webp`);
      }
    }
  }
}

issues.push(...aiDiagramManifestIssues(importedRasterDiagrams));

if (issues.length) {
  for (const issue of issues) console.error(issue);
  process.exit(1);
}

console.log("learning site validation passed");
