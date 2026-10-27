# 200 Growth Improvements for the GitHub Pages Site

Goal: make `https://jonyfs.github.io/llm-wiki-template/` fast, installable, crawlable, citable by LLMs, and shareable, so it becomes known quickly.

## Design and visual impact (1-30)

1. Move the live graph into the hero as a compact, high-impact preview.
2. Add a static poster frame for the graph so first paint is instant.
3. Use a single dominant accent color and remove competing gradients.
4. Add a dark/light hero split that demonstrates both themes side by side.
5. Replace generic cards with a bento layout for features.
6. Add a sticky mini-CTA that appears after scrolling past the hero.
7. Add a "used by" logo strip once real users exist.
8. Add a timeline of compounding value across 1/7/30 days.
9. Add a short looping GIF of an ingest operation.
10. Add a before/after comparison of RAG vs wiki answers.
11. Add a diagram of the three layers with hover states.
12. Add a code-style quick start with copy buttons.
13. Add a terminal-style animated typing demo.
14. Add a "star count" badge that updates from GitHub API.
15. Add a "forks" badge next to stars.
16. Add a "last updated" badge.
17. Add a gradient-free, high-contrast dark theme.
18. Add a light theme tuned for print and screenshots.
19. Add consistent 8px spacing scale.
20. Add a max-width reading column for long sections.
21. Add section anchors with smooth scroll and offset.
22. Add a progress bar for long pages.
23. Add a back-to-top button.
24. Add a table of contents for the long-form article.
25. Add collapsible FAQ items.
26. Add a "copy link to section" affordance.
27. Add a footer with sitemap links.
28. Add a 404 page with search suggestions.
29. Add a custom favicon and apple-touch-icon.
30. Add an Open Graph image that matches the hero.

## UX and interaction (31-60)

31. Make the live graph pause when off-screen.
32. Make the live graph respect prefers-reduced-motion.
33. Add hover tooltips with page title and degree.
34. Add click-to-open a node detail drawer.
35. Add drag-to-pan and wheel-to-zoom on the graph.
36. Add a "reset view" button on the graph.
37. Add a legend that can be collapsed.
38. Add a "show labels" toggle.
39. Add a "highlight connected" mode.
40. Add keyboard navigation for graph nodes.
41. Add focus-visible styles for all interactive elements.
42. Add skip links for main content.
43. Add a language selector with persisted choice.
44. Add a theme toggle with system preference sync.
45. Add a search box for page content.
46. Add anchor links in headings.
47. Add a "copy code" button on snippets.
48. Add a "share" button with Web Share API.
49. Add a "print" stylesheet.
50. Add a "save for later" bookmark hint.
51. Add a newsletter signup (optional, privacy-first).
52. Add a feedback widget.
53. Add a "report an issue" link.
54. Add a "suggest improvement" link.
55. Add a "view source" link to each section.
56. Add a "last reviewed" date per section.
57. Add a "was this helpful?" prompt.
58. Add a "related pages" list at the end.
59. Add a "next step" recommendation.
60. Add a "start over" reset for demos.

## Performance and Core Web Vitals (61-90)

61. Inline critical CSS and defer the rest.
62. Preload the hero font.
63. Preload the social preview image.
64. Lazy-load below-the-fold images.
65. Use WebP/AVIF for raster assets.
66. Serve SVGs instead of PNGs where possible.
67. Minify HTML, CSS, and JS in the workflow.
68. Enable gzip/brotli via GitHub Pages defaults.
69. Add a service worker for caching.
70. Cache static assets with long max-age.
71. Use a single CSS file to reduce requests.
72. Use a single JS file to reduce requests.
73. Defer non-critical JavaScript.
74. Use requestAnimationFrame for animations.
75. Throttle scroll handlers.
76. Debounce resize handlers.
77. Avoid layout thrashing in the graph.
78. Use transform instead of top/left.
79. Use will-change sparingly.
80. Reduce DOM size for the i18n walker.
81. Avoid large inline JSON blobs.
82. Split the i18n dictionary into chunks.
83. Load translations on demand.
84. Use IntersectionObserver for reveals.
85. Pause animations when tab is hidden.
86. Reduce canvas redraws when idle.
87. Use a fixed canvas resolution.
88. Avoid reflow on stats updates.
89. Measure LCP, CLS, INP and log them.
90. Add a performance budget in CI.

## PWA and offline (91-110)

91. Add a web app manifest.
92. Add theme-color and background-color.
93. Add icons in 192x192 and 512x512.
94. Add a maskable icon.
95. Add a service worker with precache.
96. Add an offline fallback page.
97. Add "add to home screen" prompt.
98. Add a standalone display mode.
99. Add shortcuts in the manifest.
100. Add screenshots in the manifest.
101. Add categories and description in the manifest.
102. Add a scope and start_url.
103. Add an update notification for new versions.
104. Add a "what's new" changelog page.
105. Add a versioned cache name.
106. Add background sync for analytics.
107. Add push notification opt-in (optional).
108. Add an install button in the UI.
109. Add offline search over cached pages.
110. Add a "you are offline" banner.

## SEO and search engines (111-140)

111. Add a canonical URL.
112. Add Open Graph tags.
113. Add Twitter Card tags.
114. Add JSON-LD SoftwareApplication.
115. Add JSON-LD FAQPage.
116. Add JSON-LD BreadcrumbList.
117. Add a sitemap.xml.
118. Add a robots.txt.
119. Add hreflang for en/pt/es.
120. Add a meta description with target keywords.
121. Add a title with primary keyword first.
122. Add H1 with the main value proposition.
123. Add descriptive H2/H3 headings.
124. Add alt text for all images.
125. Add descriptive link text.
126. Add internal links between sections.
127. Add a "last modified" header via Pages.
128. Add a 404 with noindex.
129. Add a clean URL structure.
130. Add a robots meta for staging.
131. Add a Google Search Console verification file.
132. Add a Bing Webmaster verification file.
133. Add structured data for the organization.
134. Add structured data for the author.
135. Add a license and citation metadata.
136. Add a "how to cite" section.
137. Add a "press kit" page.
138. Add a "media" page with screenshots.
139. Add a "changelog" page.
140. Add a "roadmap" page.

## LLM and AI discoverability (141-165)

141. Add an llms.txt file.
142. Add an llms-full.txt file.
143. Add a machine-readable summary at the top.
144. Add a "for AI agents" section.
145. Add explicit "use cases" in plain language.
146. Add a "glossary" for domain terms.
147. Add a "concepts" section with definitions.
148. Add a "faq" with concise answers.
149. Add a "quick start" with exact commands.
150. Add a "compatibility" matrix.
151. Add a "comparison" table.
152. Add a "pitfalls" section.
153. Add a "step by step" walkthrough.
154. Add "related pages" links.
155. Add "claims" with citations.
156. Add a "sources" list.
157. Add a "canonical url" per page.
158. Add a "last updated" date.
159. Add a "version" string.
160. Add a "license" string.
161. Add a "contact" email.
162. Add a "repository" link.
163. Add a "documentation" link.
164. Add a "examples" link.
165. Add a "community" link.

## Social, viral, and conversion (166-185)

166. Add a "star on GitHub" CTA.
167. Add a "use this template" CTA.
168. Add a "fork" CTA.
169. Add a "share on X" button.
170. Add a "share on LinkedIn" button.
171. Add a "share on Reddit" button.
172. Add a "copy link" button.
173. Add a "download assets" button.
174. Add a "bookmark" hint.
175. Add a "tell a friend" prompt.
176. Add a "showcase" of real wikis.
177. Add a "testimonials" section.
178. Add a "case studies" section.
179. Add a "metrics" section with stars/forks.
180. Add a "roadmap" CTA.
181. Add a "sponsor" button.
182. Add a "contributing" link.
183. Add a "code of conduct" link.
184. Add a "security" link.
185. Add a "citation" link.

## Accessibility and growth ops (186-200)

186. Add ARIA landmarks.
187. Add a skip link.
188. Add focus styles.
189. Add reduced-motion support.
190. Add color-contrast checks in CI.
191. Add axe-core checks in CI.
192. Add Lighthouse CI checks.
193. Add Plausible or Umami analytics.
194. Add a "404" tracking event.
195. Add a "CTA click" tracking event.
196. Add a "graph interaction" tracking event.
197. Add a "language change" tracking event.
198. Add a "theme change" tracking event.
199. Add a weekly growth report.
200. Add a monthly SEO review.
