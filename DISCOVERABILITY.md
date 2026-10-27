# LLM Wiki Template: Discoverability Catalog

100 candidate improvements to make this repository findable by search engines, LLMs, agent harnesses, and developer communities, and to convert that visibility into forks, stars, and adoption. Items are grouped by lever; numbering is continuous. None of these change the core template contract; they are presentation, distribution, and machine-readable surface work.

Baseline: repository `jonyfs/llm-wiki-template` (Python stdlib scripts, markdown wiki, multi-agent skills). Current About/description and topics are set via the GitHub UI, not versioned in the repo.

## 1. GitHub repository metadata

1. Rename the repository to include the primary keyword and value proposition, e.g. `llm-wiki-template` is already keyword-rich; consider `llm-wiki` only if the shorter name is available and redirectable. Do not keyword-stuff.
2. Write the About field as a 2-3 sentence summary that names the problem (persistent LLM-maintained notebook) and the audience (developers using Claude/Cursor/Copilot). Max 350 chars; this is the meta description in search snippets.
3. Set 10-15 topics mixing language (`python`), platform (`claude-code`, `cursor`, `copilot`), domain (`llm`, `knowledge-base`, `second-brain`), and use case (`personal-knowledge-management`, `rag-alternative`). Avoid generic tags like `misc` or `tutorial`.
4. Add a website/homepage URL pointing to a GitHub Pages or docs site (see section 3), so the repo card links out and gains a crawlable canonical.
5. Set a recognized SPDX license (MIT is present) so GitHub populates the license field that downstream tools and search filters read.
6. Upload a 1280x640 social preview image (2:1, under 1 MB) with the project name, tagline, and a screenshot of `wiki/index.md`. This is what appears in X/Reddit/Slack link cards.
7. Enable Discussions and seed 3-5 categories (Q&A, Ideas, Showcase, Announcements) so community questions become indexable, long-tail content.
8. Enable Issues with templates (bug report, feature request, documentation) and a `good first issue` label to lower contribution friction.
9. Add a `CONTRIBUTING.md` at the root with a 5-minute quick start, code style, and how to run tests; GitHub surfaces this in the new-issue flow.
10. Add a `CODE_OF_CONDUCT.md` (Contributor Covenant) and `SECURITY.md` (vulnerability reporting) to qualify for GitHub's community health score and "good first issue" surfacing.
11. Pin the repository on the owner's profile and add a one-line profile README linking to it.
12. Create GitHub Releases with semver tags and auto-generated changelogs; releases are a distribution channel and a "last updated" freshness signal.
13. Add release artifacts (zip of the template, no build needed) so "Download" counts as an adoption metric.
14. Set default branch protection and required status checks (CI) so the repo reads as maintained, not abandoned.
15. Add a `.github/FUNDING.yml` with sponsor links (GitHub Sponsors, Ko-fi) to capture goodwill; not revenue, but signals activity.
16. Add repository-level `CODEOWNERS` so PRs route to the maintainer and review turnaround stays fast.
17. Add a `CITATION.cff` file so academics and tooling can cite the template; GitHub renders a "Cite this repository" button.
18. Set the repository's primary language correctly (Python) by ensuring `.py` files outweigh markdown in the root; add a `.gitattributes` linguist override if needed.
19. Add a `topics` refresh step to CI or a checklist so topics stay current as features land.
20. Verify the repo is not marked as a fork's stale duplicate; if forked from `caelaxie/llm-wiki-template`, ensure the README credits and the repo is positioned as the canonical, more complete version.

## 2. README as a landing page

21. Make the first sentence a complete, self-contained declarative pitch naming the thing, what it does, and who it is for (not "A living notebook..." alone; add "for developers using Claude Code, Cursor, or Copilot"). This sentence is reused by search snippets, social cards, and AI summaries.
22. Answer "what / who / how" within the first screenful, before any badge row. Move badges below the pitch.
23. Reduce the badge row to 3-4 actionable badges (build status, license, Python version, last commit); remove decorative shields.
24. Add a 10-second animated GIF or terminal cast showing ingest -> query -> lint, above the fold. Visible output is the highest-return README element.
25. Add a "Quick start in 60 seconds" block with copy-pasteable commands that produce a working result on a clean machine.
26. Add an "Examples" section with a link to a populated sample notebook (a second repo or a `examples/` folder) so visitors see real output, not an empty template.
27. Add a comparison table: LLM wiki vs. RAG/vector DB vs. plain notes, with honest trade-offs. This captures "alternative to RAG" search intent.
28. Add a "Who is this for / not for" section to filter the right users and reduce bounce from wrong-fit visitors.
29. Add alt text to every image and diagram in the README describing what it shows and why it matters; image search is a real traffic source.
30. Do not put critical information only in images; GitHub does not OCR them.
31. Add a table of contents for the README once it exceeds ~2 screens.
32. Add "Star this repo" CTA only after value is demonstrated (bottom of README and in docs nav), never as a modal on first visit.
33. Add a "Used by" / "Showcase" section linking to public notebooks built from the template; social proof compounds.
34. Add a "Roadmap" link (GitHub Projects or `ROADMAP.md`) so visitors see momentum.
35. Keep the README under ~1500 words; move deep reference to `docs/` and link.
36. Add a "Frequently asked questions" section answering the 5 most common objections (why not RAG, cost, privacy, offline, model lock-in).
37. Add a "Contributing" and "Security" pointer block near the bottom.
38. Add a "Cite" block with BibTeX/APA from `CITATION.cff`.
39. Ensure the README renders correctly on mobile and in dark mode (test images).
40. Add a "Languages" note or multilingual README (see section 8).

## 3. Docs site and machine-readable surfaces

41. Publish a GitHub Pages site from `docs/` or a separate branch with a clean URL; apply standard SEO (unique titles, meta descriptions, sitemap, responsive).
42. Add `robots.txt` permitting all crawlers and pointing at the sitemap.
43. Add `sitemap.xml` listing the docs pages and the README anchor sections.
44. Add an `llms.txt` at the repo root (and on the Pages site) following the llmstxt.org format: title, one-paragraph summary, then sections linking to `AGENTS.md`, README, scripts, and skills. This is the single highest-leverage AI-discoverability file.
45. Add an `llms-full.txt` concatenating the README, AGENTS.md core, and skill summaries for agents that fetch one file.
46. Add `AGENTS.md`-style entry files for other harnesses already present (`.cursorrules`, `CLAUDE.md`, `.github/copilot-instructions.md`); keep them as links to one source of truth.
47. Add a `.well-known/` directory on the Pages site with `ai-plugin.json`-style manifest and an `agent-card.json` describing the template's capabilities (A2A-style), so agents can discover it programmatically.
48. Add JSON-LD structured data (Organization, SoftwareApplication, FAQPage) to the Pages site, with FAQ questions matching the README FAQ verbatim.
49. Add Open Graph and Twitter Card meta tags to the Pages site with title, description, and the social preview image.
50. Add an RSS/Atom feed for releases and docs updates to trigger recrawls.
51. Add a `humans.txt` and a `security.txt` for completeness and trust signals.
52. Add a `CNAME` if a custom domain is available; a branded URL compounds authority.
53. Ensure markdown files are served with `Content-Type: text/markdown` or `text/plain`, not forced download; some crawlers skip downloads.
54. Add an `index.md`-equivalent landing page on Pages that mirrors the README pitch and links into the repo.
55. Add a "Try in Codespaces" / "Open in Gitpod" button so the template is runnable in one click; lowers time-to-first-run.
56. Add a "Use this template" badge and enable "Template repository" in settings so GitHub shows the "Use this template" button prominently.

## 4. AI/LLM and harness discoverability

57. Publish the template's skills as a reusable bundle (zip) and document how to drop them into `.claude/skills`, `.opencode/skills`, etc.; harness users adopt via copy.
58. Add a `SKILL.md`-compatible manifest listing each skill's name, description, and path, so skill registries can index them.
59. Add a `package.json`-style `template.json` describing the template (name, version, files, placeholders) for scaffolding tools.
60. Register the template in community lists: "awesome-llm", "awesome-claude-code", "awesome-cursor", "awesome-copilot" via PRs.
61. Add a "Compatible with" badge list (Claude Code, Cursor, OpenCode, Copilot, Codex) in the README to capture harness-specific search queries.
62. Write a short "How to use with X" subsection per major harness (Claude Code, Cursor, Copilot, OpenCode) with exact commands; each becomes a long-tail landing page.
63. Add a `CLAUDE.md`/`AGENTS.md` example showing a populated mini-wiki so agents reading the repo see a concrete end state.
64. Add an `examples/populated-wiki/` folder with a tiny but complete notebook (2 sources, 4 pages) so the template is self-demonstrating.
65. Add a "starter kit" release that is a zipped, ready-to-open Obsidian vault with the sample wiki.
66. Ensure `AGENTS.md` stays under 8 KB (already done) so it is cheap for any agent to load; advertise this as a feature.
67. Add a `llms.txt` entry for the skills directory so agents know which playbooks exist without loading all of them.
68. Add a changelog of skill versions so harness users can track updates.
69. Add a "Migration from RAG" guide showing how to move an existing vector-store corpus into `raw/` + `wiki/`.
70. Add a benchmark number: "time to first answer" and "tokens per query" vs. a RAG baseline, measured with `scripts/benchmark.py`-style harness. Quantified claims travel.

## 5. Community, content, and distribution

71. Write a launch post (Dev.to, Medium, Hacker News "Show HN") titled around the problem ("I stopped using RAG for my personal notes") linking to the repo.
72. Write a tutorial post: "Build a personal knowledge base with Claude Code and this template" with screenshots.
73. Record a 5-minute screencast (YouTube) showing ingest + query + lint; embed in README.
74. Post to r/LocalLLaMA, r/ClaudeAI, r/obsidianmd, r/programming with a problem-first framing, not a promo.
75. Submit to Hacker News "Show HN" with a concise, honest description and a demo link.
76. Submit to Product Hunt with a clear tagline and the populated example as the demo.
77. Pitch to newsletters (TLDR, The Batch, Latent Space, Console.dev) with a one-paragraph summary.
78. Answer Stack Overflow / Reddit questions about "LLM knowledge base", "RAG alternative", "second brain AI" linking to the template when genuinely relevant.
79. Present at a meetup or record a podcast episode; link the repo in show notes.
80. Write a comparison post: "LLM Wiki vs. Obsidian + Smart Connections vs. Notion AI" to capture comparison search intent.
81. Create a "awesome-llm-wiki" list repo that curates derived notebooks; this template is the seed entry.
82. Add a "Discussions: Show and tell" category and feature community notebooks in the README "Showcase".
83. Run a "first contribution" campaign: 5 small docs issues labeled `good first issue` during launch week.
84. Add a "Star history" badge (star-history.com) once stars grow; a curve is more credible than a round number.
85. Add a "Contributors" badge and thank-you section to recognize and retain contributors.
86. Translate the README into 2-3 high-value languages (Portuguese, Spanish, Chinese) to capture non-English search traffic; keep `README.pt-BR.md` etc.
87. Add hreflang tags on the Pages site for each language version.
88. Localize topic tags is not possible (GitHub topics are English), but localize the Pages site meta descriptions.
89. Add a "Press / mentions" section once the first external write-up lands.
90. Set up a simple analytics (Plausible/Umami) on the Pages site to measure which keywords and referrers convert; iterate.

## 6. Maintenance signals and trust

91. Keep `pushed_at` fresh: schedule a monthly dependency-free maintenance commit (docs typo fix, test) so the repo does not read as abandoned.
92. Publish a dated "Maintenance note" in README or Discussions every quarter summarizing what changed.
93. Keep all CI green on every push; a red badge kills conversion.
94. Respond to issues within 48 hours during launch; responsiveness is a signal both humans and AI crawlers weight.
95. Add a "Status: actively maintained" line with the last-reviewed date in README.
96. Archive honestly if ever abandoned (set archived flag, add a successor link) rather than leaving a dead repo; abandoned repos still rank and mislead.
97. Keep the test suite count and coverage visible (badge) so adopters trust the template.
98. Add a "Compatibility matrix" (Python 3.9-3.13, OS) to reduce "does it work for me" friction.
99. Add a "Security" note: no network calls, no dependencies, stdlib-only; this is a strong trust signal for a template that runs arbitrary agent code.
100. Add a final "Get started" CTA linking to the "Use this template" button and the 60-second quick start, so the last thing a visitor sees is an action, not a footer.

## Suggested first batch (highest leverage, lowest effort)

- Items 2, 3, 6, 44, 45, 56, 21, 25, 29, 71, 73, 95. These are the cheap, high-impact wins: metadata, llms.txt, template button, README pitch, a demo, and a launch post.

## Measurement (how to know it is working)

- GitHub search: target keywords appear on page 1-2 when logged out.
- Google Search Console: rising impressions/clicks for repo name + topic queries.
- README engagement: unique visitors rising; clone-to-view ratio trending below 1:1.
- Registry/downloads not applicable (no package); use "Use this template" clicks and forks.
- Issues opened by strangers: at least one per month after launch.
- LLM/agent referrals: track `llms.txt` fetches and Pages traffic from AI user-agents.
- Referrer mix: any meaningful source beyond github.com and Google.
