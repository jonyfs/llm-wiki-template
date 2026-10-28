/* A made-up wiki about sleep and memory, with the shape of a real one: an index, a log, four page types,
   tags, a few orphans, broken links and contradictions. Dates are relative to today, so the "last 7 days"
   filters always have something to show. Deterministic: the same call gives the same vault. */

export interface DemoFile {
	path: string;
	fm: Record<string, unknown>;
	headings: string[];
	links: string[]; // basenames
	broken: string[]; // links to pages that do not exist
	ctime: number;
	mtime: number;
}

const DAY = 86400000;

const CONCEPTS = [
	"sleep-spindles", "slow-wave-sleep", "rem-sleep", "memory-consolidation", "working-memory", "circadian-rhythm", "melatonin",
	"adenosine", "caffeine", "sleep-deprivation", "napping", "hippocampus", "neocortex", "synaptic-homeostasis", "dreaming",
	"glymphatic-system", "chronotype", "sleep-debt", "blue-light", "cortisol", "spaced-repetition", "attention", "emotional-memory",
	"insomnia", "sleep-apnea", "sleep-hygiene", "exercise", "stress", "sleep-music",
];
const ENTITIES = [
	"ana-reis", "bruno-lima", "carla-mendes", "daniel-okafor", "elena-petrova", "farid-haddad", "grace-liu", "hugo-silva", "ines-costa",
	"jonas-berg", "northside-sleep-lab", "circadian-institute", "memory-research-group", "sleep-clinic-network", "open-sleep-data",
	"night-owl-study", "school-start-trial", "shift-work-cohort", "mobile-sleep-app", "wearable-tracker",
];
const SOURCES = [
	"paper-spindle-density-and-recall", "paper-slow-wave-boost-with-sound", "paper-rem-and-emotional-memory", "paper-caffeine-half-life",
	"paper-nap-length-and-learning", "paper-blue-light-before-bed", "paper-chronotype-school-start", "paper-shift-work-health",
	"paper-sleep-debt-weekend-recovery", "paper-glymphatic-clearance", "paper-apnea-and-attention", "paper-insomnia-cbt",
	"paper-exercise-and-sleep-depth", "paper-melatonin-dose", "paper-stress-and-cortisol-rhythm", "paper-dream-recall-diary",
	"paper-working-memory-after-short-sleep", "paper-synaptic-scaling-overnight", "paper-spaced-repetition-and-sleep",
	"paper-hippocampal-replay", "article-sleep-hygiene-checklist", "article-teen-sleep-guidelines", "article-wearables-accuracy",
	"article-jet-lag-guide", "article-nutrition-and-sleep", "podcast-sleep-and-learning", "podcast-why-naps-work", "podcast-circadian-basics",
	"podcast-insomnia-stories", "podcast-night-shift-nurses", "book-notes-the-sleeping-brain", "book-notes-rhythms-of-life",
	"book-notes-memory-craft", "notes-lab-meeting-march", "notes-lab-meeting-april", "notes-clinic-visit", "transcript-keynote-sleep-science",
	"transcript-panel-school-start", "report-annual-sleep-survey", "report-wearable-benchmark", "dataset-open-sleep-data-2024",
	"dataset-night-owl-study", "benchmark-apnea-screening", "spec-sleep-diary-template", "thread-forum-insomnia-tips",
	"thread-reddit-nap-debate", "clip-news-daylight-saving", "clip-bookmarked-talk",
];
const SYNTHESES = [
	"how-sleep-supports-memory", "caffeine-versus-napping", "chronotype-and-school-start", "sleep-debt-can-it-be-repaid",
	"shift-work-and-health", "evidence-on-blue-light", "sleep-hygiene-what-holds-up", "what-wearables-can-tell",
	"insomnia-treatment-map", "open-questions-on-dreaming", "draft-sleep-and-mood",
];

// Words in a source or synthesis name that point at a concept.
const KEYWORDS: [string, string[]][] = [
	["spindle", ["sleep-spindles", "memory-consolidation"]], ["slow-wave", ["slow-wave-sleep", "memory-consolidation"]],
	["rem", ["rem-sleep", "emotional-memory"]], ["caffeine", ["caffeine", "adenosine"]], ["nap", ["napping", "sleep-debt"]],
	["blue-light", ["blue-light", "melatonin", "circadian-rhythm"]], ["chronotype", ["chronotype", "circadian-rhythm"]],
	["school", ["chronotype", "attention"]], ["shift", ["circadian-rhythm", "stress"]], ["sleep-debt", ["sleep-debt", "sleep-deprivation"]],
	["glymphatic", ["glymphatic-system", "slow-wave-sleep"]], ["apnea", ["sleep-apnea", "attention"]], ["insomnia", ["insomnia", "stress", "sleep-hygiene"]],
	["exercise", ["exercise", "slow-wave-sleep"]], ["melatonin", ["melatonin", "circadian-rhythm"]], ["cortisol", ["cortisol", "stress"]],
	["dream", ["dreaming", "rem-sleep"]], ["working-memory", ["working-memory", "sleep-deprivation"]], ["synaptic", ["synaptic-homeostasis", "slow-wave-sleep"]],
	["spaced", ["spaced-repetition", "memory-consolidation"]], ["hippocamp", ["hippocampus", "neocortex", "memory-consolidation"]],
	["hygiene", ["sleep-hygiene", "blue-light"]], ["jet-lag", ["circadian-rhythm", "melatonin"]], ["nutrition", ["sleep-hygiene", "cortisol"]],
	["wearable", ["sleep-hygiene", "attention"]], ["learning", ["memory-consolidation", "spaced-repetition"]], ["memory", ["memory-consolidation"]],
	["circadian", ["circadian-rhythm", "chronotype"]], ["daylight", ["circadian-rhythm", "blue-light"]], ["sleeping-brain", ["neocortex", "slow-wave-sleep", "rem-sleep"]],
	["mood", ["emotional-memory", "stress", "rem-sleep"]],
];
const CONCEPT_LINKS: [string, string][] = [
	["sleep-spindles", "slow-wave-sleep"], ["sleep-spindles", "hippocampus"], ["slow-wave-sleep", "memory-consolidation"], ["rem-sleep", "dreaming"],
	["rem-sleep", "emotional-memory"], ["memory-consolidation", "hippocampus"], ["memory-consolidation", "neocortex"], ["hippocampus", "neocortex"],
	["working-memory", "attention"], ["circadian-rhythm", "melatonin"], ["circadian-rhythm", "chronotype"], ["circadian-rhythm", "cortisol"],
	["adenosine", "caffeine"], ["adenosine", "sleep-debt"], ["sleep-debt", "sleep-deprivation"], ["sleep-deprivation", "working-memory"],
	["napping", "sleep-debt"], ["blue-light", "melatonin"], ["stress", "cortisol"], ["insomnia", "stress"], ["insomnia", "sleep-hygiene"],
	["sleep-apnea", "sleep-deprivation"], ["exercise", "sleep-hygiene"], ["synaptic-homeostasis", "slow-wave-sleep"], ["glymphatic-system", "slow-wave-sleep"],
	["spaced-repetition", "memory-consolidation"], ["dreaming", "emotional-memory"], ["attention", "sleep-deprivation"],
];
const CONTRADICTS: [string, string][] = [
	["thread-reddit-nap-debate", "paper-nap-length-and-learning"],
	["article-sleep-hygiene-checklist", "paper-blue-light-before-bed"],
	["paper-sleep-debt-weekend-recovery", "podcast-sleep-and-learning"],
];
const ORPHANS = new Set(["sleep-music", "clip-bookmarked-talk", "parking-lot"]);

function rng(seed: number): () => number {
	let a = seed;
	return () => {
		a = (a + 0x6d2b79f5) | 0;
		let t = Math.imul(a ^ (a >>> 15), 1 | a);
		t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
}

const title = (base: string) => {
	const s = base.replace(/-/g, " ");
	return s[0].toUpperCase() + s.slice(1);
};
const day = (t: number) => new Date(t).toISOString().slice(0, 10);

export function buildDemoVault(now = Date.now()): { files: DemoFile[]; log: string } {
	const r = rng(20261028);
	const pick = <T>(a: T[]) => a[Math.floor(r() * a.length)];
	const known = new Set([...CONCEPTS, ...ENTITIES, ...SOURCES, ...SYNTHESES, "index", "log", "parking-lot", "lab-whiteboard"]);
	const conceptsFor = (name: string) => {
		const out: string[] = [];
		for (const [k, cs] of KEYWORDS) if (name.includes(k)) for (const c of cs) if (!out.includes(c)) out.push(c);
		return out;
	};
	const hubs = ["memory-consolidation", "circadian-rhythm", "sleep-deprivation", "slow-wave-sleep"];
	const files = new Map<string, DemoFile>();
	const add = (folder: string, base: string, type: string | null, extra: Record<string, unknown>, links: string[], created: number): DemoFile => {
		const tags = (extra.tags as string[] | undefined) ?? [];
		const mtime = r() < 0.18 ? now - Math.floor(r() * 6 * DAY) : created + Math.floor(r() * (now - created));
		const f: DemoFile = {
			path: `wiki/${folder}${base}.md`,
			fm: { ...(type ? { type } : {}), ...extra, tags },
			headings: type === "source" ? ["Summary", "Claims ledger", "Open questions"] : type === "synthesis" ? ["Answer", "Evidence", "Open questions"] : ["What it is", "Evidence", "Related"],
			links: Array.from(new Set(links.filter((l) => l !== base))),
			broken: [],
			ctime: created,
			mtime: Math.max(created, mtime),
		};
		files.set(base, f);
		return f;
	};

	const firstSeen = new Map<string, number>();
	const log: { t: number; op: string; text: string }[] = [];
	// Sources arrive over the last five months, one every three days or so.
	SOURCES.forEach((base, i) => {
		const created = now - Math.round(150 - i * (146 / (SOURCES.length - 1))) * DAY;
		const cs = ORPHANS.has(base) ? [] : conceptsFor(base);
		if (!cs.length && !ORPHANS.has(base)) cs.push(pick(hubs));
		const ents = ORPHANS.has(base) ? [] : [pick(ENTITIES), ...(r() < 0.45 ? [pick(ENTITIES)] : [])];
		const extra = r() < 0.7 ? [pick(hubs)] : [];
		const links = ORPHANS.has(base) ? [] : [...cs, ...ents, ...extra];
		for (const l of links) if (!firstSeen.has(l)) firstSeen.set(l, created + DAY);
		const kind = base.split("-")[0];
		const tags = ["#" + (kind === "paper" ? "research" : kind === "podcast" || kind === "transcript" ? "audio" : kind === "thread" || kind === "clip" ? "web" : "reading"), ...(cs[0] ? ["#" + cs[0].split("-")[0]] : [])];
		add("sources/", base, "source", { tags, status: r() < 0.25 ? "draft" : "reviewed", source_role: kind === "paper" || kind === "dataset" ? "primary" : "secondary" }, links, created);
		log.push({ t: created, op: "ingest", text: title(base) });
	});
	for (const [from, to] of CONTRADICTS) {
		const f = files.get(from);
		if (f) {
			f.fm.contradicts = `[[${to}]]`;
			if (!f.links.includes(to)) f.links.push(to);
		}
	}

	CONCEPTS.forEach((base) => {
		const created = firstSeen.get(base) ?? now - Math.round(20 + r() * 100) * DAY;
		const links: string[] = [];
		for (const [a, b] of CONCEPT_LINKS) {
			if (a === base) links.push(b);
			else if (b === base && r() < 0.35) links.push(a);
		}
		const words = base.split("-");
		add("concepts/", base, "concept", { tags: ["#" + words[0], ...(words.length > 1 ? ["#" + words[1]] : [])] }, ORPHANS.has(base) ? [] : links, created);
	});
	ENTITIES.forEach((base, i) => {
		const created = firstSeen.get(base) ?? now - Math.round(30 + r() * 100) * DAY;
		const org = i >= 10;
		add("entities/", base, "entity", { tags: [org ? "#organization" : "#person"] }, [pick(CONCEPTS.filter((c) => !ORPHANS.has(c)))], created);
	});

	SYNTHESES.forEach((base, i) => {
		const created = now - Math.round(70 - i * 6) * DAY;
		const cs = conceptsFor(base);
		const sources = SOURCES.filter((s) => !ORPHANS.has(s) && conceptsFor(s).some((c) => cs.includes(c)));
		const links = [...cs, ...sources.slice(0, 5), ...(r() < 0.6 ? [pick(CONCEPTS.filter((c) => !ORPHANS.has(c)))] : [])];
		const f = add("syntheses/", base, "synthesis", { tags: ["#synthesis", ...(cs[0] ? ["#" + cs[0].split("-")[0]] : [])], status: i % 3 === 0 ? "draft" : "reviewed" }, links, created);
		if (base === "draft-sleep-and-mood") f.broken.push("sleep-mood-study", "mood-diary");
		log.push({ t: created, op: "query", text: title(base) });
	});
	// A source with a link to a page nobody wrote yet.
	files.get("paper-stress-and-cortisol-rhythm")?.broken.push("cortisol-awakening-response");

	// Two loose notes that never got a type; one is linked, one is an orphan.
	add("notes/", "lab-whiteboard", null, { tags: ["#scratch"] }, ["memory-consolidation", "sleep-spindles"], now - 12 * DAY);
	add("notes/", "parking-lot", null, { tags: ["#scratch"] }, [], now - 3 * DAY);

	const all = Array.from(files.values());
	const index: DemoFile = {
		path: "wiki/index.md",
		fm: { type: "index", tags: [] },
		headings: ["Syntheses", "Concepts", "Entities", "Sources"],
		links: [...SYNTHESES, ...CONCEPTS.filter((c) => !ORPHANS.has(c)).slice(0, 14)].filter((l) => known.has(l)),
		broken: [],
		ctime: now - 160 * DAY,
		mtime: now - DAY,
	};
	for (const f of all) f.links = f.links.filter((l) => known.has(l));
	const logPage: DemoFile = { path: "wiki/log.md", fm: { type: "log", tags: [] }, headings: ["Log"], links: [], broken: [], ctime: now - 160 * DAY, mtime: now };

	for (let d = 125; d > 0; d -= 40) log.push({ t: now - d * DAY, op: "lint", text: `${3 + (d % 4)} orphan pages found` });
	log.sort((a, b) => a.t - b.t);
	const text = ["# Log", "", ...log.map((e) => `## [${day(e.t)}] ${e.op} | ${e.text}`)].join("\n") + "\n";
	return { files: [index, logPage, ...all], log: text };
}
