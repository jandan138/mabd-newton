import { requiredLessons, type LessonMeta } from "../data/lessons";

export interface LessonFrontmatter {
  title: string;
  description: string;
  module: string;
  order: number;
  status: "complete" | "planned";
  claimStatus: "conceptual" | "passed" | "incomplete" | "not_verified" | "unsupported";
  repoEvidence?: string[];
}

export interface LessonModule {
  default: unknown;
  frontmatter: LessonFrontmatter;
}

export const lessonModules = import.meta.glob("../content/lessons/*.mdx");

const slugFromPath = (modulePath: string) => modulePath.split("/").pop()?.replace(/\.mdx$/, "") ?? "";

export const availableLessonSlugs = new Set(
  Object.keys(lessonModules)
    .map(slugFromPath)
    .filter((slug) => slug.length > 0),
);

export const availableLessons: LessonMeta[] = requiredLessons.filter((lesson) =>
  availableLessonSlugs.has(lesson.slug),
);

export const lessonModulePath = (slug: string) => `../content/lessons/${slug}.mdx`;
