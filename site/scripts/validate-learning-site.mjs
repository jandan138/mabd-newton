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

const issues = [];
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
  }
}

if (issues.length) {
  for (const issue of issues) console.error(issue);
  process.exit(1);
}

console.log("learning site validation passed");
