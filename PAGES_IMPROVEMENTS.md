# GitHub Pages improvements catalog (up to 200)


Catalog of candidate improvements for the Pages site (`index.html`). Apply in batches; track in commits.


## Design & visual polish (40 items)
1. Adopt 8px spacing scale across all components
2. Define color tokens for light and dark themes
3. Add light/dark theme toggle persisted in localStorage
4. Respect prefers-color-scheme on first paint
5. Use a single accent gradient (indigo to teal) everywhere
6. Add elevation shadows only on hover
7. Add subtle noise texture to hero background
8. Improve card hover border transition to accent
9. Add glow effect to primary CTA
10. Use text-wrap: balance on all headings
11. Set readable line length (65ch) on paragraphs
12. Add tabular-nums for numeric stats
13. Increase base font to 17px desktop
14. Add letter-spacing -0.01em to headings
15. Use font-weight 600 nav, 700 headings
16. Add focus ring 2px accent with offset
17. Add skip-to-content link visible on focus
18. Add smooth scroll for anchor links
19. Add scroll-margin-top for sticky nav
20. Add section dividers between major blocks
21. Use CSS grid auto-fit for feature cards
22. Stack hero CTA vertically on mobile
23. Compare table horizontal scroll with shadow hint
24. Code block horizontal scroll with fade edge
25. Touch targets at least 44x44px
26. Hamburger menu under 640px
27. Nav collapses to brand plus CTA on mobile
28. Test layouts at 320, 375, 768, 1024, 1440
29. Add container max-width 1120px with 24px gutters
30. Section vertical rhythm 96px desktop 64px mobile
31. Card padding 24px gap 20px
32. Hero padding 96px top
33. Sticky nav height 64px
34. Use gap instead of margins for vertical stacks
35. Add fade-in sections on scroll via IntersectionObserver
36. Add button hover translateY plus shadow
37. Add link underline animation on hover
38. Add CTA glow pulse subtle 3s loop
39. Add reduced-motion alternative for all animations
40. Add mobile nav slide-in with backdrop

## Content & copy (40 items)
41. Rewrite hero in plain language for non-technical readers
42. Add one-sentence value proposition above the fold
43. Add 'Who is this for' section
44. Add FAQ with at least 8 questions
45. Add testimonials or social proof (stars count badge)
46. Add roadmap teaser section
47. Add final CTA section before footer
48. Add 'How it works in 60 seconds' quick start
49. Add comparison table LLM wiki vs RAG vs note apps
50. Add compatibility list of agents
51. Add glossary of terms used
52. Add 'What you do vs what the assistant does' table
53. Add troubleshooting section for common pitfalls
54. Add 'When not to use this' section for honesty
55. Add changelog link in footer
56. Add license and contributing links in footer
57. Add 'Star on GitHub' CTA with star count
58. Add 'Use this template' primary CTA in nav
59. Add reading time estimate on article
60. Add last-updated date on article
61. Add table of contents for long pages
62. Add breadcrumbs on sub-pages
63. Add 'Edit this page' link to GitHub
64. Add 'Report an issue' link
65. Add author/contributor credits section
66. Add 'Inspired by' attribution to Karpathy gist
67. Add version badge (template v1.0)
68. Add status badge (active/maintained)
69. Add 'Try in 30 seconds' interactive demo
70. Add 'Common workflows' examples
71. Add 'Daily workflow' cheat sheet
72. Add 'Ingest walkthrough' step-by-step
73. Add 'Query walkthrough' step-by-step
74. Add 'Lint walkthrough' step-by-step
75. Add 'Refresh walkthrough' step-by-step
76. Add 'Migration' notes for derived wikis
77. Add 'FAQ: is this RAG?' answer
78. Add 'FAQ: does it scale?' answer
79. Add 'FAQ: who owns the data?' answer
80. Add 'FAQ: can I use other LLMs?' answer

## Explanatory images & diagrams (40 items)
81. Add SVG flow diagram raw to wiki
82. Add three-layer diagram (raw/wiki/schema)
83. Add ingest sequence diagram
84. Add query sequence diagram
85. Add compounding growth sparkline
86. Add before/after RAG vs wiki diagram
87. Add folder tree illustration
88. Add frontmatter example block with highlighting
89. Add wikilink graph screenshot style
90. Add page-type cards with icons
91. Add animated arrow draw-on for flow
92. Add icon set replacing emoji
93. Add logo mark in nav
94. Add favicon.svg and apple-touch-icon
95. Add OG image 1280x640
96. Add screenshot of wiki in editor
97. Add screenshot of index.md
98. Add screenshot of a source page
99. Add screenshot of a concept page
100. Add screenshot of a synthesis page
101. Add diagram of citation footnotes
102. Add diagram of claims ledger
103. Add diagram of learning paths
104. Add dark and light variants of diagrams
105. Add alt text to every image
106. Add width and height to prevent CLS
107. Lazy-load below-the-fold images
108. Use WebP with PNG fallback
109. Prefer inline SVG for icons
110. Add a 'how a page looks' mockup
111. Add a 'compounding over time' timeline
112. Add a 'what changes when you add a source' diff view
113. Add animated node pulse on graph
114. Add hover tooltips on graph nodes
115. Add legend for graph node colors
116. Add a mini-map for large graphs
117. Add zoom and pan on graph
118. Add graph export as PNG button
119. Add graph fullscreen toggle
120. Add reduced-motion fallback for graph

## Skills pipeline & results (41 items)
121. Add a 'Skills pipeline' section explaining each skill
122. Explain ingest skill step-by-step with diagram
123. Explain query skill step-by-step with diagram
124. Explain lint skill checks list
125. Explain refresh skill and drift detection
126. Explain clarify skill for ambiguity
127. Explain plan skill for multi-step work
128. Show sample ingest output (before/after files)
129. Show sample query answer with citations
130. Show sample lint report
131. Show sample refresh report
132. Add 'What the assistant actually does' walkthrough
133. Add 'What you never have to do' list
134. Add 'Time saved' estimate per operation
135. Add 'Error prevention' list (broken links etc)
136. Add 'Quality gates' list (frontmatter validation)
137. Add 'Audit trail' explanation (log.md)
138. Add 'Reproducibility' explanation (raw_sha256)
139. Add 'Provenance' explanation (sources field)
140. Add 'Idempotency' explanation (re-ingest)
141. Add 'Conflict handling' explanation
142. Add 'Multi-agent' support explanation
143. Add 'Skill invocation' explanation
144. Add 'Context budget' explanation
145. Add 'Token efficiency' note
146. Add 'No vendor lock-in' note
147. Add 'Offline' capability note
148. Add 'Version control' (git) benefits
149. Add 'Branching workflows' note
150. Add 'Review via PR' note
151. Add 'CI checks' note
152. Add 'Test suite' note
153. Add 'Migration path' note
154. Add 'Backwards compat' note
155. Add 'Extensibility' note (add skills)
156. Add 'Community' note (contributing)
157. Add 'Roadmap' note
158. Add 'Benchmarks' placeholder
159. Add 'Case studies' placeholder
160. Add 'FAQ: how do skills trigger?'
161. Add 'FAQ: can I add my own skill?'

## Differentiator & positioning (20 items)
162. Add 'Why this is different' section (RAG vs wiki)
163. Add 'Why not just use ChatGPT?' section
164. Add 'Why not Notion/Obsidian?' section
165. Add 'Why markdown + git?' section
166. Add 'Why an assistant and not a pipeline?' section
167. Add 'Compounding' as the core differentiator
168. Add 'Persistent artifact' as differentiator
169. Add 'No re-retrieval' as differentiator
170. Add 'Cross-references pre-built' as differentiator
171. Add 'Contradictions flagged' as differentiator
172. Add 'Audit trail' as differentiator
173. Add 'Local-first' as differentiator
174. Add 'Agent-agnostic' as differentiator
175. Add 'Zero infra' as differentiator
176. Add 'Open source' as differentiator
177. Add 'Template, not framework' positioning
178. Add 'Bring your own agent' positioning
179. Add 'Own your data' positioning
180. Add 'Compounds with use' positioning
181. Add 'Start in 60 seconds' positioning

## SEO, performance & a11y (20 items)
182. Add canonical URL meta
183. Add Open Graph meta (title, desc, image, url)
184. Add Twitter Card meta
185. Add JSON-LD SoftwareApplication schema
186. Add robots.txt
187. Add sitemap.xml
188. Add favicon.svg and apple-touch-icon
189. Inline critical CSS
190. Minify HTML/CSS in workflow
191. Add preconnect for external fonts (if used)
192. Add lazy loading for images
193. Add width/height to images for CLS
194. Add decoding async on images
195. Add aria-labels on icon buttons
196. Add semantic landmarks header/nav/main/footer
197. Ensure heading order h1 to h3
198. Add aria-current on active nav
199. Color not sole conveyor of info
200. Test with axe-core in CI

## 2026-10 redesign (responsive, PWA, 3D graph)

- `github-pages/index.html` now only holds markup; styles live in `assets/site.css`, behaviour in `assets/app.js`, translations in `assets/i18n.js` and the graph in `assets/graph.js`. The inline theme script is allowed by a CSP hash, so changing it means recomputing the `sha256-` value in the `<meta>` CSP.
- Add new visible copy to `EXTRA_ROWS` in `assets/i18n.js` (exact English text, then pt, es). JS-written text goes through `llmwT()` and the `STR` table.
- PWA: `manifest.webmanifest` plus `sw.js` (`llm-wiki-v2`, stale-while-revalidate for assets). Every path in `PRECACHE` must exist or the install fails. Bump the cache name when the list changes.
- The nav switches to a hamburger below 1300px; the graph is a canvas 2D perspective renderer (no three.js, because the CSP only allows same-origin scripts).

### Graph (assets/graph.js)

- Cells are neurons: soma, dendrites and curved axons, with one shape per page type (pyramidal sources, stellate entities, branched concepts, large synthesis cells).
- The brain has a midline fissure, folded cortex outline, white-matter interior and cross-hemisphere tracts.
- Buttons play the wiki operations on the graph: add a page (ingest), ask the wiki (walks links two hops, then files a synthesis page) and run lint (flags pages with one link or none).
- Input: pinch and two-finger pan, Shift or right-drag to pan, double-tap to fly to a cell, orbit mode for touch (turns off `pan-y`), keyboard stepping through hubs with `[` and `]`.
- Performance: adaptive quality from measured frame time, LOD for dendrites, culling, no per-frame allocations in the hot path, DPR capped by canvas size, hard cap of 420 pages. `window.llmwGraph.stats()` reports frame time and quality.

### Page copy: skills first (2026-10)

- The page now explains the workflow in this order: how it works, what you can give it (files, links, pasted text, images), which skill runs for each request, everyday examples, then benefits.
- Every skill and slash command named on the page is checked against `.agents/skills/` and `.agents/commands/` by `tests/test_github_pages.py`, so the copy cannot promise a skill that does not exist.
- Keep the honest limits in the copy: the skills are instructions in `AGENTS.md`, not an enforced lock, and links or pasted text only enter `raw/` after the assistant asks.

### Graph full screen

- `#gFull` (or the `F` key on the canvas) fullscreens `#graphWrap` with the Fullscreen API. Where that fails or is missing (iPhone Safari), the wrapper becomes `position: fixed` instead (`.is-full`), and Esc leaves it.
- In full screen only the graph and its controls show: type filters, zoom, reset, auto-rotate, orbit, exit, and the add / ask / lint buttons plus the stats line. Orbit mode turns on by itself while full screen (nothing to scroll) and goes back afterwards.
- The fixed fallback needs `html.graph-full #graph { contain: none }`: sections use `content-visibility: auto`, which implies `contain: paint` and would otherwise trap a fixed child inside the section.

### One page, five parts (reader journey)

The landing page is a single document ordered by what a newcomer asks next. A numbered label (`.eyebrow`) opens each part and the hero lists them as reading-order chips.

1. **Understand the idea** (`#problem`): retrieval vs. a maintained wiki, who does what, three layers, the three operations (ingest, query, lint), the vocabulary.
2. **See it working** (`#graph`): the live graph. It sits right after the operations because its Add / Ask / Run lint buttons play them, and its legend uses the page types from the vocabulary.
3. **Use it** (`#inputs`): what you can add, every request goes through a skill, `index.md` and `log.md`, everyday examples.
4. **Why it pays off** (`#features`): benefits, why it works, who it is for, comparison with RAG and note apps.
5. **Start** (`#start`): quick start, compatible agents, make it yours, FAQ, common problems, call to action, repo metrics.

- Part 1 paraphrases Karpathy's gist and says so. Its six inline SVG figures use the page tokens and the graph's colour per page type, carry almost no text (labels sit in HTML beside them) and each has an `aria-label`.
- `tests/test_github_pages.py` checks that the parts are numbered 1 to 5, that every nav and chip link has a target, and that the graph comes after the operations.
- The page builder scripts were one-off; edit `index.html` directly. Any new inline script needs its CSP hash, which the tests check.
