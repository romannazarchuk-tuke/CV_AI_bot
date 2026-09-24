---
name: weasyprint-cv-styling
description: 'Design, implement, and verify production-ready CV styling with Jinja2 HTML templates and WeasyPrint PDF output. Use for resume layout, print CSS, page breaks, typography, fonts, localization, PDF rendering failures, and visual quality checks.'
argument-hint: 'Describe the CV template, layout issue, styling goal, or PDF rendering failure.'
user-invocable: true
---

# WeasyPrint CV Styling

## Purpose

Use this skill to turn resume data into a readable, stable, professional PDF through a Jinja2 template and WeasyPrint. Treat HTML, CSS, fonts, assets, and rendered PDF as one output pipeline.

## When to Use

- Create or revise a CV/resume Jinja2 template.
- Fix pagination, clipping, overflow, blank pages, or broken page breaks.
- Improve typography, spacing, hierarchy, and print readability.
- Support Cyrillic or other localized text and verify font embedding.
- Diagnose WeasyPrint errors involving assets, fonts, CSS, or native dependencies.
- Verify that user-provided resume content cannot become unsafe HTML or filesystem input.

## Procedure

1. **Locate the rendering boundary.** Find the template, CSS/assets, render service, data model, and nearest tests or CLI entry point. Confirm whether the service expects a complete HTML document and which media mode it uses.
2. **State the layout hypothesis.** Identify the smallest likely cause, such as an unbounded flex item, missing print rule, unsupported CSS feature, incorrect asset URL, or font fallback. Choose one concrete check that can disconfirm it before changing unrelated files.
3. **Inspect the data contract.** Use the existing Pydantic/domain model and template context. Do not add presentation assumptions to the data model unless the current contract cannot express the required content. Escape user text by default; only allow trusted, deliberately sanitized markup.
4. **Build print-first structure.** Keep semantic sections and predictable DOM order. Prefer stable block layout, CSS Grid only where the installed WeasyPrint version supports the needed behavior, and explicit sizing for repeated elements. Keep decorative styling subordinate to content.
5. **Define print CSS deliberately.** Set `@page` size and margins, base font and line-height, heading hierarchy, link treatment, color contrast, and print-safe spacing. Use `break-before`, `break-after`, `break-inside`, and `orphans`/`widows` where supported. Avoid viewport units, JavaScript-dependent layout, fixed-position elements that can duplicate unexpectedly, and browser-only CSS features.
6. **Handle fonts and assets.** Use bundled or configured font files with stable paths/URLs. Verify every referenced asset exists, is readable by the rendering process, and supports the document's scripts. Do not log resume content, secrets, or full filesystem paths when reporting failures.
7. **Render safely and asynchronously.** Keep blocking WeasyPrint and filesystem work off the event loop in async applications. Use temporary files/directories with cleanup, bounded input, explicit timeouts where the surrounding service supports them, and actionable error handling for missing native libraries or malformed HTML/CSS.
8. **Validate the output.** Run the narrowest focused test or render command first. Check that the PDF is created, non-empty, has the expected page count, contains selectable text, embeds or resolves required fonts, and has no unexpected blank pages or content clipping. If visual inspection is available, inspect every page at a readable scale.
9. **Check edge cases.** Test long names, long URLs, missing optional sections, multi-page employment history, Cyrillic text, empty lists, unusual punctuation, and content near page boundaries. Confirm that sections do not overlap and that page breaks remain intentional.
10. **Report precisely.** Summarize changed files, the rendering command or test used, output checks, assumptions, and any remaining environment requirement such as Cairo/Pango or other WeasyPrint native libraries.

## Decision Points

- **Layout issue only on PDF:** prefer print CSS or WeasyPrint-supported structure over browser-specific fixes.
- **Layout issue in both browser and PDF:** inspect the HTML structure and data shape before tuning CSS.
- **Text is clipped or overflows:** first test wrapping, min/max sizes, long unbroken strings, and flex/grid constraints; do not hide content as a first fix.
- **Cyrillic or symbols render incorrectly:** verify font coverage and embedding before changing font sizes or content.
- **Assets work in a browser but not in WeasyPrint:** replace relative/browser-only URLs with a controlled base URL or explicit resource resolution, then test file permissions.
- **WeasyPrint fails to start:** distinguish Python package errors from missing native libraries and report the exact dependency boundary; do not weaken PDF generation or silently fall back to an unverified format.
- **Content crosses a page boundary:** keep the content visible and use a targeted break rule; avoid globally shrinking typography unless the design requirement demands it.

## A4 Print CSS Baseline

Start from a predictable A4 baseline and adjust only after rendering a representative long CV:

```css
@page {
	size: A4;
	margin: 16mm 16mm 18mm;
}

* {
	box-sizing: border-box;
}

html,
body {
	margin: 0;
	padding: 0;
}

body {
	color: #20252b;
	background: #ffffff;
	font-family: "Noto Sans", sans-serif;
	font-size: 10pt;
	line-height: 1.4;
}

.cv {
	width: 100%;
	max-width: 178mm;
	margin: 0 auto;
}

h1,
h2,
h3,
p,
ul,
ol {
	margin-top: 0;
}

img {
	max-width: 100%;
}

a {
	color: inherit;
	overflow-wrap: anywhere;
}
```

Use the actual printable width from `@page` margins rather than a viewport width. For A4 portrait, the page is `210mm x 297mm`; with 16mm side margins the usable width is `178mm`.

### Fonts and Localized Text

Register fonts with a controlled file URL or a stable `base_url`. The selected family must contain every script used by the CV, including Cyrillic and common symbols:

```css
@font-face {
	font-family: "Noto Sans";
	src: url("fonts/NotoSans-Regular.ttf") format("truetype");
	font-weight: 400;
	font-style: normal;
}

@font-face {
	font-family: "Noto Sans";
	src: url("fonts/NotoSans-Bold.ttf") format("truetype");
	font-weight: 700;
	font-style: normal;
}

body {
	font-family: "Noto Sans", sans-serif;
}
```

Keep font files with the template assets, verify their paths from the process that invokes WeasyPrint, and test real localized text. Do not rely on a machine-installed font or a browser-only remote URL. Avoid synthetic bold when a real weight file is available.

### Section and Page-Break Rules

Keep each heading with the content that follows it and avoid splitting compact CV entries:

```css
.section {
	margin: 0 0 7mm;
	break-inside: avoid;
}

.section__title {
	margin: 0 0 2.5mm;
	break-after: avoid;
}

.entry {
	margin: 0 0 4mm;
	break-inside: avoid;
}

.entry__header {
	break-after: avoid;
}

.page-break-before {
	break-before: page;
}

.page-break-after {
	break-after: page;
}

ul,
ol {
	padding-left: 5mm;
}

li {
	break-inside: avoid;
}
```

Apply `break-inside: avoid` to bounded semantic units such as one job, one education item, or one project. Do not apply it to the entire document or a potentially multi-page history block, because the renderer may create large whitespace or an unexpected blank page.

### Reliable Two-Column Details

For a narrow contact/details area, use explicit columns and allow long values to wrap:

```css
.details {
	display: grid;
	grid-template-columns: 38mm minmax(0, 1fr);
	column-gap: 5mm;
	row-gap: 1.5mm;
}

.details__label {
	font-weight: 700;
}

.details__value {
	min-width: 0;
	overflow-wrap: anywhere;
}
```

If the installed WeasyPrint version behaves inconsistently with a complex grid or flex layout, replace it with simple block markup or a table used strictly for tabular alignment. Never solve overflow by hiding text.

### Avoid These Print-CSS Traps

- Do not use `100vh`, `position: fixed`, JavaScript, or browser-only layout assumptions for the main document flow.
- Do not put `page-break-*` rules on every nested element; prefer the modern `break-*` properties and targeted selectors.
- Do not use `overflow: hidden` to conceal content that should be printed.
- Do not set `break-inside: avoid` on a wrapper that can legitimately span several pages.
- Do not use remote fonts or assets unless the resource resolver and network policy explicitly support them.
- Do not shrink the whole document below readable print sizes to force a one-page CV.

## Completion Criteria

A change is complete only when:

- The template receives the existing validated context without leaking secrets or trusting raw user markup.
- The focused render/test command succeeds, or the exact external blocker is documented.
- The PDF has readable hierarchy, consistent margins, no accidental blank pages, clipping, overlap, or horizontal overflow.
- Required scripts, fonts, and assets render correctly, including representative localized text.
- Long and missing content cases are handled intentionally.
- Async callers do not perform blocking rendering on the event loop.
- The final report names validation performed and any remaining native-environment requirements.
