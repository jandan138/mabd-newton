import { defineCollection, z } from "astro:content";

const lessons = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string(),
    module: z.string(),
    order: z.number().int().positive(),
    status: z.enum(["complete", "planned"]),
    claimStatus: z.enum(["conceptual", "passed", "incomplete", "not_verified", "unsupported"]),
    repoEvidence: z.array(z.string()).default([]),
  }),
});

export const collections = { lessons };
