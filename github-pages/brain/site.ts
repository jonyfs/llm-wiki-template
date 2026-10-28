/* The plugin's own BrainView, running on the landing page over made-up data.
   Layout in the build: this file sits next to a checkout of llm-wiki-brain (see build.sh), so ../src is the plugin. */

import { BrainView } from "../src/view";
import { translate, StringKey, Vars, Lang } from "../src/i18n";
import { DEFAULT_SETTINGS, BrainSettings } from "../src/vaultGraph";
import { cleanViews, SavedView } from "../src/views";
import { TFile } from "obsidian";
import { buildDemoVault } from "./demo";

/* eslint-disable @typescript-eslint/no-explicit-any */

const KEY = "llmw.brain.v1";

// The plugin tip mentions a plain scroll to zoom; on a page that would trap the scroll, so zoom needs Ctrl or Cmd here.
const TIP: Record<Lang, string> = {
	en: "Drag to rotate, Ctrl or Cmd + scroll to zoom, click to select.",
	"pt-BR": "Arraste para girar, Ctrl ou Cmd + rolagem para dar zoom, clique para selecionar.",
	es: "Arrastra para girar, Ctrl o Cmd + rueda para hacer zoom, clic para seleccionar.",
	fr: "Glissez pour tourner, Ctrl ou Cmd + molette pour zoomer, cliquez pour sélectionner.",
};

/** Obsidian's vault and metadata cache, answered from the demo files. */
function fakeApp(host: HTMLElement) {
	const { files, log } = buildDemoVault();
	const byPath = new Map<string, TFile>();
	const byBase = new Map<string, TFile>();
	const meta = new Map<string, (typeof files)[number]>();
	for (const f of files) {
		const t = new TFile(f.path, f.ctime, f.mtime);
		byPath.set(f.path, t);
		byBase.set(t.basename, t);
		meta.set(f.path, f);
	}
	const resolvedLinks: Record<string, Record<string, number>> = {};
	const unresolvedLinks: Record<string, Record<string, number>> = {};
	for (const f of files) {
		resolvedLinks[f.path] = {};
		for (const l of f.links) {
			const dest = byBase.get(l);
			if (dest) resolvedLinks[f.path][dest.path] = 1;
		}
		unresolvedLinks[f.path] = {};
		for (const l of f.broken) unresolvedLinks[f.path][l] = 1;
	}
	const handlers = new Map<string, ((...a: unknown[]) => void)[]>();
	const app = {
		vault: {
			getMarkdownFiles: () => Array.from(byPath.values()),
			getAbstractFileByPath: (p: string) => byPath.get(p) ?? null,
		},
		metadataCache: {
			resolvedLinks,
			unresolvedLinks,
			getFirstLinkpathDest: (link: string) => byBase.get(link) ?? null,
			getFileCache: (file: TFile) => {
				const f = meta.get(file.path);
				if (!f) return null;
				const fmLinks = typeof f.fm.contradicts === "string" ? [{ key: "contradicts", link: String(f.fm.contradicts).replace(/^\[\[|\]\]$/g, ""), original: String(f.fm.contradicts), displayText: "" }] : [];
				return { frontmatter: f.fm, frontmatterLinks: fmLinks, headings: f.headings.map((heading) => ({ heading, level: 2 })), tags: [] };
			},
		},
		workspace: {
			on(name: string, cb: (...a: unknown[]) => void) {
				handlers.set(name, [...(handlers.get(name) ?? []), cb]);
				return { off: () => handlers.set(name, (handlers.get(name) ?? []).filter((x) => x !== cb)) };
			},
			trigger(name: string, ...args: unknown[]) {
				(handlers.get(name) ?? []).forEach((cb) => cb(...args));
			},
			getLeaf: () => ({ openFile: async () => {} }),
		},
	};
	return { app, log, files, host };
}

function load(): Partial<BrainSettings> {
	try {
		return JSON.parse(localStorage.getItem(KEY) ?? "{}");
	} catch {
		return {};
	}
}

function pageLang(): Lang {
	const l = (document.documentElement.lang || "en").toLowerCase();
	return l.startsWith("pt") ? "pt-BR" : l.startsWith("es") ? "es" : "en";
}

interface Mounted {
	view: BrainView;
	app: ReturnType<typeof fakeApp>["app"];
}

function mount(host: HTMLElement): Mounted {
	const { app, log } = fakeApp(host);
	const lang = pageLang();
	const saved = load();
	const settings: BrainSettings = {
		...DEFAULT_SETTINGS,
		...saved,
		savedViews: cleanViews(saved.savedViews),
		pinned: Array.isArray(saved.pinned) ? saved.pinned.filter((p) => typeof p === "string") : [],
		reduceMotion: matchMedia("(prefers-reduced-motion: reduce)").matches,
		followActiveNote: false,
		hoverPreview: false,
		explorerHover: false,
		autoFlowOnCreate: false,
	};
	const store = () => {
		try {
			localStorage.setItem(KEY, JSON.stringify({ savedViews: settings.savedViews, pinned: settings.pinned, onboarded: settings.onboarded }));
		} catch {
			/* private mode: the demo still works, nothing is remembered */
		}
	};
	const plugin = {
		settings,
		lang,
		layout: {},
		t: (key: StringKey, vars?: Vars) => (key === "tip.idle" ? TIP[lang] : translate(lang, key, vars)),
		readLog: async () => log,
		saveLayout: () => {},
		persist: async (patch: Partial<BrainSettings>) => {
			Object.assign(settings, patch);
			store();
		},
		saveViews: async (list: SavedView[]) => {
			settings.savedViews = list;
			store();
		},
	};
	host.empty();
	// A plain wheel keeps scrolling the page: the engine only sees it with Ctrl or Cmd held, or in full screen.
	host.addEventListener("wheel", (e) => {
		const full = document.getElementById("graphWrap")?.classList.contains("is-full");
		if (!(e.ctrlKey || e.metaKey || full)) e.stopImmediatePropagation();
	}, { capture: true });
	const view = new (BrainView as any)({ app, containerEl: host }, plugin) as BrainView;
	void view.onOpen();
	return { view, app };
}

/** Full screen where the browser has it; a fixed overlay where it does not (iPhone). */
function installFullscreen(view: BrainView, host: HTMLElement) {
	const wrap = document.getElementById("graphWrap") ?? host;
	const root = document.documentElement;
	const on = () => wrap.classList.contains("is-full");
	const set = (v: boolean) => {
		wrap.classList.toggle("is-full", v);
		root.classList.toggle("graph-full", v);
	};
	document.addEventListener("fullscreenchange", () => {
		if (!document.fullscreenElement) set(false);
	});
	document.addEventListener("keydown", (e) => {
		if (e.key === "Escape" && on() && !document.fullscreenElement) set(false);
	});
	(view as any).toggleFullscreen = () => {
		if (on()) {
			set(false);
			if (document.fullscreenElement) void document.exitFullscreen();
			return;
		}
		set(true);
		const req = wrap.requestFullscreen?.bind(wrap);
		if (req) void req().catch(() => {});
	};
}

/** The plugin's "Open note" button has nothing to open here. */
function dropOpenButton(view: BrainView) {
	const orig = (view as any).showInfo.bind(view);
	(view as any).showInfo = (info: unknown) => {
		orig(info);
		(view.contentEl.querySelector(".llm-wiki-brain-actions button") as HTMLElement | null)?.remove();
	};
}

function syncTheme(m: Mounted) {
	const light = document.documentElement.getAttribute("data-theme") === "light";
	document.body.classList.toggle("theme-light", light);
	document.body.classList.toggle("theme-dark", !light);
	m.app.workspace.trigger("css-change");
}

/** The accessible list: the best connected pages, as buttons that select them. */
function fillHubs(m: Mounted, list: HTMLElement | null) {
	if (!list) return;
	const e = (m.view as any).engine;
	if (!e) return;
	list.empty();
	const rows = (m.view as any).graph.pages
		.map((p: any) => ({ p, d: e.degree(p.path) }))
		.sort((a: any, b: any) => b.d - a.d)
		.slice(0, 12);
	for (const { p, d } of rows) {
		const li = list.createEl("li");
		const b = li.createEl("button", { text: `${p.label} · ${d}`, attr: { type: "button", title: p.path } });
		b.addEventListener("click", () => e.selectPath(p.path, true));
	}
}

function start() {
	const host = document.getElementById("brain");
	if (!host) return;
	let m: Mounted | null = null;
	const run = () => {
		if (m) {
			m.view.dispose();
			void m.view.onClose();
		}
		m = mount(host);
		installFullscreen(m.view, host);
		dropOpenButton(m.view);
		syncTheme(m);
		window.setTimeout(() => m && fillHubs(m, document.getElementById("gList")), 600);
	};
	const init = () => {
		run();
		new MutationObserver(() => m && syncTheme(m)).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
		document.addEventListener("llmw:lang", () => run());
	};
	// The engine is busy from the first frame, so wait until the section is close to the screen.
	if ("IntersectionObserver" in window) {
		const io = new IntersectionObserver((es) => {
			if (es.some((x) => x.isIntersecting)) {
				io.disconnect();
				init();
			}
		}, { rootMargin: "600px 0px" });
		io.observe(host);
	} else init();
	(window as any).llmwBrain = { stats: () => (m?.view as any)?.engine?.stats(), engine: () => (m?.view as any)?.engine };
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
else start();
