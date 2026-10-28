/* Just enough of the Obsidian API for the plugin's BrainView to run in a web page.
   The build aliases the `obsidian` module to this file. See build.sh. */

/* eslint-disable @typescript-eslint/no-explicit-any */

interface ElOptions {
	cls?: string | string[];
	text?: string;
	type?: string;
	value?: string;
	href?: string;
	title?: string;
	attr?: Record<string, string | number | boolean | null | undefined>;
}

// Obsidian adds these helpers to every element; the view calls them directly.
const proto = Element.prototype as any;
if (!proto.createEl) {
	proto.createEl = function (tag: string, o: ElOptions | string = {}, cb?: (el: HTMLElement) => void): HTMLElement {
		const opts: ElOptions = typeof o === "string" ? { cls: o } : o;
		const el = document.createElement(tag) as any;
		if (opts.cls) el.className = Array.isArray(opts.cls) ? opts.cls.join(" ") : opts.cls;
		if (opts.text != null) el.textContent = opts.text;
		if (opts.type) el.type = opts.type;
		if (opts.value != null) el.value = opts.value;
		if (opts.href) el.href = opts.href;
		if (opts.title) el.title = opts.title;
		for (const [k, v] of Object.entries(opts.attr ?? {})) if (v != null) el.setAttribute(k, String(v));
		(this as Element).appendChild(el);
		cb?.(el);
		return el;
	};
	proto.createDiv = function (o?: ElOptions | string) {
		return this.createEl("div", o);
	};
	proto.createSpan = function (o?: ElOptions | string) {
		return this.createEl("span", o);
	};
	proto.empty = function () {
		while (this.firstChild) this.removeChild(this.firstChild);
	};
	proto.addClass = function (...c: string[]) {
		this.classList.add(...c);
	};
	proto.removeClass = function (...c: string[]) {
		this.classList.remove(...c);
	};
	proto.hasClass = function (c: string) {
		return this.classList.contains(c);
	};
	proto.toggleClass = function (c: string, on: boolean) {
		this.classList.toggle(c, on);
	};
	proto.setText = function (t: string) {
		this.textContent = t;
	};
	proto.hide = function () {
		this.style.display = "none";
	};
	proto.show = function () {
		this.style.display = "";
	};
}

// The engine can compute a negative radius for a cell that swings behind the camera, and canvas then throws and the
// engine drops to its simplest drawing. A zero radius draws nothing, which is what a cell behind the camera should do.
const ctxProto = CanvasRenderingContext2D.prototype as any;
if (!ctxProto.__llmwArc) {
	const arc = ctxProto.arc;
	ctxProto.arc = function (x: number, y: number, r: number, ...rest: unknown[]) {
		return arc.call(this, x, y, r < 0 ? 0 : r, ...rest);
	};
	ctxProto.__llmwArc = true;
}

/** A short message in the corner, like Obsidian's. */
export class Notice {
	constructor(message: string, timeout = 3500) {
		const host = document.querySelector(".llm-wiki-brain") ?? document.body;
		const el = document.createElement("div");
		el.className = "llm-wiki-brain-notice";
		el.setAttribute("role", "status");
		el.textContent = message;
		host.appendChild(el);
		window.setTimeout(() => el.remove(), timeout);
	}
}

export class TFile {
	extension = "md";
	name: string;
	basename: string;
	parent: { path: string };
	stat: { ctime: number; mtime: number };
	constructor(public path: string, ctime: number, mtime: number) {
		this.name = path.split("/").pop() ?? path;
		this.basename = this.name.replace(/\.md$/, "");
		this.parent = { path: path.split("/").slice(0, -1).join("/") };
		this.stat = { ctime, mtime };
	}
}

export class HoverPopover {}

export interface WorkspaceLeaf {
	app: any;
	containerEl: HTMLElement;
}

/** The base class of the plugin's view: it only needs a content element and a place to register cleanups. */
export class ItemView {
	app: any;
	leaf: WorkspaceLeaf;
	contentEl: HTMLElement;
	private cleanups: (() => void)[] = [];
	constructor(leaf: WorkspaceLeaf) {
		this.leaf = leaf;
		this.app = leaf.app;
		this.contentEl = leaf.containerEl;
	}
	getState(): Record<string, unknown> {
		return {};
	}
	async setState(): Promise<void> {}
	registerEvent(ref: { off?: () => void } | undefined): void {
		if (ref?.off) this.cleanups.push(ref.off);
	}
	registerInterval(id: number): number {
		this.cleanups.push(() => window.clearInterval(id));
		return id;
	}
	/** Runs everything registered above; the page calls it when it tears the view down. */
	dispose(): void {
		this.cleanups.splice(0).forEach((f) => f());
	}
}
