export interface LessonMeta {
  slug: string;
  title: string;
  module: string;
  order: number;
}

export const requiredLessons: LessonMeta[] = [
  { slug: "start-here", title: "先从这里开始", module: "Orientation", order: 1 },
  { slug: "why-affine-bodies", title: "为什么需要仿射体", module: "Orientation", order: 2 },
  { slug: "vectors-matrices-transforms", title: "向量、矩阵与坐标变换", module: "Math", order: 3 },
  { slug: "affine-state", title: "仿射状态：A 和 t", module: "ABD Foundations", order: 4 },
  { slug: "svd-polar-rotation", title: "SVD、Polar Decomposition 与旋转提取", module: "Math", order: 5 },
  { slug: "rigid-body-basics", title: "刚体动力学基础", module: "Physics", order: 6 },
  { slug: "generalized-coordinates-forces", title: "广义坐标、Jacobian 与力映射", module: "Simulation", order: 7 },
  { slug: "implicit-time-stepping", title: "隐式时间积分", module: "Numerics", order: 8 },
  { slug: "newton-hessian-kkt", title: "Newton、Hessian 与 KKT", module: "Numerics", order: 9 },
  { slug: "single-body-abd", title: "单体 ABD 核心思想", module: "ABD", order: 10 },
  { slug: "multi-body-mabd", title: "M-ABD：多体、关节与拓扑求解", module: "M-ABD", order: 11 },
  { slug: "repo-evidence-map", title: "如何阅读本仓库的证据", module: "Reproduction", order: 12 },
];

export const futureLessons = [
  "affine-deformation-modes",
  "coordinate-packing",
  "positive-definite-solves",
  "corotated-elasticity",
  "finite-difference-oracles",
  "dense-kkt-derivation",
  "residual-corrected-rhs",
  "ball-joint-worked-example",
  "hinge-joint-worked-example",
  "universal-joint-worked-example",
  "prismatic-joint-worked-example",
  "joint-limit-clamps",
  "chain-block-tridiagonal",
  "tree-abd-aba-intuition",
  "loop-schur-complement",
  "graph-gauss-seidel",
  "contact-force-mapping",
  "affine-actuation",
  "spinning-box-diagnostics",
  "rbd-baseline-caveats",
  "experiment-matrices",
  "asset-provenance",
  "adding-verified-claims",
  "adding-experiment-lanes",
  "implementation-bugs",
  "symbol-glossary",
  "further-reading",
];
