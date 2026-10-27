# Design System Improvements for the GitHub Pages site

Catalog of 100 candidate improvements for `index.html` (the Pages landing page). Grouped by lever. Apply in batches; mark done in commits.

## Typography & readability (1-15)
1. Adopt a type scale (1.25 ratio) for h1-h6 instead of ad-hoc clamp.
2. Load Inter (or system stack) with `font-display: swap`.
3. Set `max-width: 65ch` on body paragraphs for readable line length.
4. Use `tabular-nums` for any numeric stats.
5. Increase base font size to 17px on desktop, 16px on mobile.
6. Add `letter-spacing: -0.01em` to headings.
7. Use `text-wrap: balance` on headings (modern browsers).
8. Define `--font-sans` and `--font-mono` tokens.
9. Monospace code blocks: ligatures off, 13.5px.
10. Add `hyphens: auto` for long words in narrow columns.
11. Ensure heading color contrast >= 4.5:1 on card backgrounds.
12. Use `font-weight: 600` for nav, 700 for h1/h2.
13. Add `line-height: 1.1` for hero title.
14. Italic emphasis for secondary clauses in hero sub.
15. Add a visible focus ring style for all interactive elements.

## Color & theming (16-30)
16. Define color tokens in `:root` and a `[data-theme="light"]` override.
17. Add a light/dark toggle persisted in localStorage.
18. Respect `prefers-color-scheme` on first load.
19. Use a single accent gradient (indigo -> teal) consistently.
20. Card background slightly lighter than page bg for elevation.
21. Border color derived from text color with alpha.
22. Hover states shift border to accent, not background.
23. Disabled state: 40% opacity + no pointer.
24. Success/info colors: teal for positive, amber for warning.
25. Ensure all text passes WCAG AA (4.5:1 normal, 3:1 large).
26. Add a subtle grid/noise texture to hero background.
27. Use `color-mix()` for hover tints (modern).
28. Define `--shadow-sm/md/lg` tokens.
29. Apply elevation shadows only on hover.
30. Add a "glow" on primary CTA.

## Layout & spacing (31-45)
31. Use an 8px spacing scale (4/8/12/16/24/32/48/64/96).
32. Container max-width 1120px with 24px gutters.
33. Section vertical rhythm: 96px desktop, 64px mobile.
34. Card padding 24px, gap 20px in grids.
35. Hero padding 96px top.
36. Sticky nav height 64px.
37. Add a skip-to-content link.
38. Use CSS grid for feature cards (auto-fit minmax).
39. Compare table: sticky first column on mobile.
40. Quick-start code block: max-width 720px centered.
41. Footer: two columns desktop, stacked mobile.
42. Add section anchor offsets for sticky nav (scroll-margin-top).
43. Use `gap` instead of margins for vertical stacks.
44. Add a divider between major sections.
45. Hero CTA group: wrap gracefully on small screens.

## Imagery & diagrams (46-60)
46. Replace emoji icons with a consistent SVG icon set.
47. Add an animated SVG flow diagram (draw-on).
48. Add a screenshot of the wiki folder in an editor.
49. Add a before/after "RAG vs wiki" diagram.
50. Lazy-load below-the-fold images with `loading="lazy"`.
51. Provide `width`/`height` to prevent CLS.
52. Use WebP with PNG fallback for photos.
53. Add alt text to every image.
54. Add a `favicon.svg` and `apple-touch-icon`.
55. Add an OG image (1280x640) referenced in meta.
56. Add a diagram of the three folders (raw/wiki/.agents).
57. Add a small "compounding" sparkline animation.
58. Use `decoding="async"` on images.
59. Prefer inline SVG for icons (no extra requests).
60. Add a logo mark in nav.

## Motion & interaction (61-70)
61. Respect `prefers-reduced-motion`.
62. Smooth scroll for anchor links.
63. Fade-in sections on scroll (IntersectionObserver).
64. Button hover: translateY(-1px) + shadow.
65. Card hover: border color shift to accent.
66. Flow diagram arrows animate on view.
67. CTA glow pulse (subtle, 3s loop).
68. Link underline animation on hover.
69. Mobile nav slide-in with backdrop.
70. Add a "copy" button on code blocks.

## Accessibility (71-80)
71. Skip-to-content link visible on focus.
72. All interactive elements keyboard-focusable.
73. Focus ring: 2px accent outline, 2px offset.
74. ARIA labels on icon-only buttons.
75. Semantic landmarks: header/nav/main/footer.
76. Heading order h1 -> h2 -> h3 (no skips).
77. `aria-current` on active nav link.
78. Color not sole conveyor of info (compare table uses text).
79. Reduced-motion alternative for animations.
80. Test with axe-core in CI.

## Responsive & mobile (81-88)
81. Hamburger menu under 640px.
82. Stack hero CTA vertically on mobile.
83. Compare table horizontal scroll with shadow hint.
84. Code block horizontal scroll with fade edge.
85. Touch targets >= 44x44px.
86. Nav collapses to brand + CTA only.
87. Feature grid single column under 480px.
88. Test at 320px, 375px, 768px, 1024px, 1440px.

## Performance & SEO (89-95)
89. Inline critical CSS; defer non-critical.
90. Minify HTML/CSS in the workflow.
91. Add `<link rel="canonical">`.
92. Add JSON-LD SoftwareApplication schema.
93. Add Open Graph + Twitter Card meta.
94. Add a sitemap.xml (static) and robots.txt.
95. Preconnect to font host if external fonts used.

## Content & IA (96-100)
96. Add a "Who is this for" section.
97. Add a "FAQ" section with 5 questions.
98. Add testimonials/social proof (stars count badge).
99. Add a "Roadmap / what's next" teaser.
100. Add a final CTA section before footer.
