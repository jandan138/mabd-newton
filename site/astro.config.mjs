import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

export default defineConfig({
  output: "static",
  integrations: [mdx()],
  site: "https://jandan138.github.io",
  base: "/mabd-newton",
});
