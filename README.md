# Arun Mallikarjuna

Full-stack engineer (JavaScript/TypeScript, Python) who builds business tools and AI automation end to end: frontends, APIs, dashboards, reporting, and the training pipelines behind learned agents. Senior Software Engineer at [Tecnotree](https://www.tecnotree.com), Bengaluru.

[Portfolio](https://arun-portfolio-kappa.vercel.app) · [LinkedIn](https://linkedin.com/in/arunmallikarjun) · arunmallikarjun005@gmail.com

---

## ReportWright — paged reports for the web

**[Repo](https://github.com/MrArun005/reportwright) · [Live demo: gallery, designer, viewer](https://mrarun005.github.io/reportwright-demo/) · [Playground](https://mrarun005.github.io/reportwright-demo/play.html) · [npm](https://www.npmjs.com/package/@reportwright/engine)**

A drag-and-drop designer, an embeddable viewer and a JavaScript engine that writes PDF, Excel, Word, PowerPoint, HTML and CSV. No Chromium. MIT licensed. Published as a dozen npm packages, including a [zero-dependency streaming PDF writer](https://github.com/MrArun005/reportwright-pdf).

<p>
  <a href="https://mrarun005.github.io/reportwright-demo/"><img src="https://raw.githubusercontent.com/MrArun005/reportwright/main/docs/screenshots/ui-designer.jpg" alt="The ReportWright designer" width="64%"></a>
  <a href="https://mrarun005.github.io/reportwright-demo/#gallery"><img src="https://raw.githubusercontent.com/MrArun005/reportwright/main/docs/screenshots/sales-dashboard.png" alt="A rendered sales dashboard" width="34%"></a>
</p>

| Area | What it does |
|---|---|
| Design | Drag-and-drop designer with data panel, inspector, outline, live preview, undo; master reports, part libraries, themes |
| Layout | Headers and footers, bands, grouped tables with subtotals, pivots (tablix), lists, subreports, page breaks |
| Data | JSON, REST, GraphQL, SOAP, OData, CSV, XML; SQL through a server callback |
| Text | HarfBuzz shaping for Arabic, Hebrew, Indic, Thai; bidi; font subsetting; CJK and emoji |
| Output | PDF, PDF/A-2b/2a, PDF/UA-1 (checked with veraPDF), AES-256; Excel, Word, PowerPoint, HTML, CSV, SVG |
| Import | JasperReports `.jrxml`, SSRS `.rdl`/`.rdlc`, BIRT `.rptdesign`, ActiveReports `.rdlx-json` |
| Automation | Scheduled and batch runs, `pw render` / `pw test` / `pw diff` from the CLI, snapshot tests |

**Measured, not claimed.** On GitHub Actions runners, interleaved with the rivals, every output verified: a 10,000-row grouped report in 1.1 s against 3.1 s for QuestPDF, 5.4 s for JasperReports and 20 s for Puppeteer; 1,000,000 rows streamed in 48 s. Losses are listed too (QuestPDF wins warm single-page renders). Full tables and the runs: [Benchmarks](https://github.com/MrArun005/reportwright#benchmarks-honest-summary).

| Sales dashboard | Loan statement in Hindi | Pivots |
|---|---|---|
| ![Sales dashboard](https://raw.githubusercontent.com/MrArun005/reportwright/main/docs/screenshots/sales-dashboard.png) | ![Hindi loan statement](https://raw.githubusercontent.com/MrArun005/reportwright/main/docs/screenshots/loan-statement-hindi.png) | ![Tablix](https://raw.githubusercontent.com/MrArun005/reportwright/main/docs/screenshots/tablix-showcase.png) |

---

## Tailorwright — AI job-application automation

**[Repo](https://github.com/MrArun005/resume-tailor)** · TypeScript, Next.js, Claude and Gemini APIs

An LLM pipeline that fetches live postings, tailors a truthful, ATS-ready resume to each one (in the resume's own layout or a clean template), drafts a cold email where the posting exposes an address, and tracks every application by code. Every line stays grounded in the source resume. Ships four ways from one set of prompts and evals: web app, headless CLI for cron and CI, Claude Code skill, and subagent.

## Bolt — reinforcement-learning locomotion

**[Repo](https://github.com/MrArun005/Cool-Websites)** · Python, MuJoCo/MJX, JAX, Brax, Stable-Baselines3

A 12 kg simulated quadruped with real Unitree A1 motor limits, trained with PPO on 4,096 parallel environments on free Colab and Kaggle GPUs. Nine learned gaits and postures at 91–97% on seeded exams with zero falls, a canter at ~2 m/s, a 40 cm jump with run-up, and self-righting from any fall in under a second. Every policy ships with a model card, exam results, and the command that produced them.

## FriedLiver — a multi-agent IDE

**[FriedLiver Code](https://github.com/MrArun005/FriedLiver-Code)** (on VS Code / Code - OSS) · **[FriedLiver](https://github.com/MrArun005/FriedLiver)** (from scratch on Electron, Monaco, xterm.js, Agent Client Protocol)

Claude, Codex and Gemini coding agents side by side, with an Agent Manager board to run one task on several agents and compare. Every agent edit is a reviewed diff, every command waits for approval, every turn can be undone. The from-scratch build idles at 314 MB against 761 MB for VS Code ([method and numbers](https://github.com/MrArun005/editor-bench)).

---

## More

- [scroll-cinema-pipelines](https://github.com/MrArun005/scroll-cinema-pipelines) · scroll-driven cinematic web pages from video frame sequences, packaged as a Claude Code skill
- [seva](https://github.com/MrArun005/seva) · six working prototypes and an evidence dashboard for documented failures in Indian public digital services
- [cognodb-graph-benchmark](https://github.com/MrArun005/cognodb-graph-benchmark) · reproducible benchmark of CognoDB Cloud against Neo4j and Memgraph
- [forge27](https://github.com/MrArun005/forge27) · local DSA and system-design study app with a live streaming AI tutor
- [ai-interview-drill](https://github.com/MrArun005/ai-interview-drill) · harness for practising AI-assisted coding interviews
- [3D_Game](https://github.com/MrArun005/3D_Game) (Nightfall Drive) and [The-Im-Possible-City](https://github.com/MrArun005/The-Im-Possible-City) · Three.js worlds with every mesh and texture generated in code
- [incident-animation-3D](https://github.com/MrArun005/incident-animation-3D) · code-generated 3D reconstructions, starting with US Airways 1549

<sub>This repository also holds a small Pixi/WebGPU platformer; see [SUPER-PLUMBER-BROS.md](SUPER-PLUMBER-BROS.md).</sub>
