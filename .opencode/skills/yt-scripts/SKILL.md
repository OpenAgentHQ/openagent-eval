# SKILL: YouTube Script Generator for Technical Projects

## PURPOSE
Transform any technical project or codebase into a high-quality, production-grade YouTube video script optimized for NotebookLM AI video generation, technical education, and startup showcase presentations.

---

## TRIGGER CONDITIONS
Use this skill when the user:
- Uploads or pastes a codebase, folder structure, or project description
- Asks to "generate a YouTube script" or "create a video script" for a project
- Wants to explain their project for portfolio, demo, or educational purposes
- Says phrases like "make a video about my project", "script for my AI project", "YouTube breakdown of my codebase"

---

## REQUIRED INPUTS
Before generating, gather (or infer from provided files):
1. **Project codebase** — folder structure, key files, README
2. **Tech stack** — frameworks, databases, LLMs, cloud providers
3. **Target audience** — beginners / developers / recruiters / founders (default: all)
4. **Video length** — short (5–8 min) / medium (10–15 min) / long (20–30 min) (default: medium)
5. **Tone** — educational / startup-pitch / deep-dive (default: educational + startup)

If any of these are missing, ask before proceeding.

---

## ANALYSIS PROTOCOL

Before writing a single line of script, perform a deep system analysis covering:

### Architecture Analysis
- Full project architecture and design patterns
- Folder structure and module responsibilities
- Data flow between components
- Backend system (APIs, services, workers)
- Frontend system (UI framework, state management, routing)
- AI/ML layer (LLMs, agents, chains, embeddings)
- Database design (relational, NoSQL, vector DBs)
- Authentication and authorization mechanisms
- Queue/worker systems (Celery, BullMQ, etc.)
- Streaming architecture (SSE, WebSockets, etc.)
- Deployment architecture (Docker, K8s, cloud)

### AI-Specific Analysis (if applicable)
- LangGraph nodes, edges, and state management
- Agent orchestration and tool calling
- Reflection / self-correction loops
- MCP server communication
- RAG pipeline and vector database usage
- LLM routing strategy (local vs. cloud models)
- Memory systems (short-term, long-term, episodic)
- Prompt engineering patterns

### Business/Product Analysis
- WHY the project exists (problem being solved)
- WHO the target users are
- WHAT real-world pain point it addresses
- HOW the architecture choices reflect business goals
- WHY specific technologies were chosen over alternatives

---

## OUTPUT FORMAT

Generate the complete script in this exact structure:

---

### 1. VIDEO TITLE IDEAS
Provide 5 compelling titles following this formula:
- Pattern: `[I Built / How I Built] + [Project Core] + [Impressive Qualifier]`
- Examples: "I Built a Production-Grade AI Agent System Using LangGraph", "How I Built a Multi-Agent RAG Pipeline From Scratch"
- Include titles optimized for SEO, curiosity, and technical credibility

### 2. THUMBNAIL TEXT IDEAS
Provide 5 short, punchy thumbnail text options (max 6 words each):
- Use power words: "Full Stack", "Production", "Real-World", "From Scratch", "Complete"
- Should pair with a screenshot of the running project

### 3. VIDEO DESCRIPTION
Write a full YouTube description (300–500 words) including:
- 2-sentence hook
- What viewers will learn (bullet list)
- Tech stack mentioned
- Timestamps placeholder
- Social / GitHub links placeholder
- SEO keywords naturally embedded

### 4. FULL YOUTUBE SCRIPT

Write the complete narration script with these sections. Each section should include:
- **[NARRATION]** — exact words to say
- **[VISUAL]** — what to show on screen
- **[ANIMATION]** — motion graphic or transition suggestion

#### Script Sections:

**INTRO (Hook + Problem)**
- Open with a powerful, relatable pain point (15–30 seconds)
- Make the viewer feel the problem instantly
- No "Hello everyone" openers — start with the hook

**THE PROBLEM**
- Explain what problem this project solves
- Use a real-world scenario or analogy
- Why existing tools/solutions fall short

**PROJECT INTRODUCTION**
- One-sentence project description
- Show the live demo or final output first ("reveal early")
- Build excitement before diving into tech

**SYSTEM ARCHITECTURE OVERVIEW**
- High-level diagram narration
- Explain the "big picture" before details
- Use simple analogies (e.g., "Think of this like a post office routing system...")

**TECH STACK BREAKDOWN**
- For each major technology: what it is, why it was chosen, what it replaces
- Be opinionated — explain tradeoffs

**BACKEND ARCHITECTURE**
- API design, service layer, data models
- How requests flow through the system
- Error handling and retry logic

**FRONTEND ARCHITECTURE** (if applicable)
- UI framework, component design, state management
- Real-time features (if any)
- UX decisions

**AI / AGENT ARCHITECTURE** (if applicable)
- LangGraph workflow with node-by-node explanation
- Tool calling mechanism
- How the agent makes decisions
- Memory and context management

**DATABASE DESIGN**
- Schema decisions and why
- Vector DB pipeline (if RAG)
- Caching strategy (Redis, etc.)

**WORKFLOW WALKTHROUGH**
- Step-by-step: what happens when a user triggers an action
- Trace a single request end-to-end through the entire system

**ASYNC & QUEUE ARCHITECTURE** (if applicable)
- Why async was needed
- Queue design and worker behavior
- How failures are handled

**PRODUCTION OPTIMIZATIONS**
- Performance improvements made
- Caching layers
- Rate limiting, pagination, batching

**SECURITY FEATURES**
- Auth strategy
- Data protection
- Input validation

**DEPLOYMENT ARCHITECTURE**
- Docker/K8s setup
- Environment management
- CI/CD pipeline overview

**CHALLENGES & ENGINEERING LEARNINGS**
- 3–5 specific hard problems encountered
- How each was solved
- What would be done differently

**FUTURE IMPROVEMENTS**
- Honest roadmap of what's next
- Missing features and why they were deprioritized

**CLOSING CTA**
- Summarize what was built
- GitHub link prompt
- Subscribe / like / comment ask
- One final inspiring statement

---

### 5. VISUAL SCENE DIRECTIONS

For each major section, provide:
```
SCENE [N]: [Section Name]
Duration: [estimated seconds]
Screen: [what to show — terminal, browser, diagram, code, etc.]
Animation: [zoom in, slide, highlight, transition type]
Overlay Text: [any text to display on screen]
B-Roll Suggestion: [optional supporting footage idea]
```

---

## SCRIPT STYLE RULES

### DO:
- Start sentences with strong verbs: "This handles...", "Notice how...", "Here's where it gets interesting..."
- Use analogies for complex concepts: "It's like a traffic controller for AI agents"
- Build narrative tension: tease the solution before revealing it
- Use second person: "You'll see...", "When you run this..."
- Vary sentence length: short punchy lines after complex explanations
- Sound like a senior engineer talking to a smart friend

### DON'T:
- Generic openers: "Hello everyone, today we're going to..."
- Passive voice: "The data is processed by..." → "The system processes..."
- Over-explain basics: assume viewer is a developer
- Use buzzwords without substance: "leveraging AI to synergize..."
- Read code line-by-line — explain behavior and intent instead

---

## QUALITY CHECKLIST

Before outputting the final script, verify:
- [ ] Hook grabs attention in first 10 seconds
- [ ] Every technology choice is justified
- [ ] Architecture is explained at multiple levels (beginner + expert)
- [ ] A complete request lifecycle is traced end-to-end
- [ ] At least 3 real engineering challenges are discussed
- [ ] Visual directions accompany every major section
- [ ] CTA is natural, not forced
- [ ] Script is NotebookLM-friendly (clean narration, no markdown artifacts in speech)
- [ ] Total narration time matches target video length

---

## LENGTH TARGETS

| Video Length | Word Count | Sections to Prioritize |
|---|---|---|
| Short (5–8 min) | 800–1,200 words | Hook, Architecture, Workflow, CTA |
| Medium (10–15 min) | 1,800–2,500 words | All core sections |
| Long (20–30 min) | 3,500–5,000 words | Full deep-dive with all sections |

---

## EXAMPLE USAGE

**User says:** "Here's my LangGraph multi-agent codebase. Generate a YouTube script."

**Claude should:**
1. Analyze the full codebase structure
2. Identify: LangGraph nodes, state schema, tools, LLMs used, backend, frontend
3. Determine: what problem it solves, who uses it, why these tech choices
4. Generate: titles, thumbnail text, description, full script, scene directions
5. Output: complete, ready-to-record script in the format above

---

## NOTES FOR CLAUDE

- Never generate shallow or generic content — every paragraph must be technically grounded in the actual project
- If the codebase is missing, ask the user to share it before generating
- If certain sections (e.g., MCP, LangGraph) don't apply, skip them gracefully
- The script should feel like: "Top AI engineer explaining a production-grade startup system"
- Prioritize engineering storytelling over documentation narration
