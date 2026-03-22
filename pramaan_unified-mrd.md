# PRAMAAN Unified Master Requirements Document (MRD)

**Date**: March 21, 2026
**Target**: Aligning the theoretical architecture with the *actual* Python codebase implementation in the repository.

---

## 1. What Was Analyzed in the Codebase
To write this document, I performed a deep-dive analysis of the actual Python files in the `/agent` and root directories:
*   `run_agent.py`: The main orchestrator connecting the APScheduler (daily 02:00 AM cron) to the Tavily search hunt and the local `/inbox/` sweep.
*   `agent/classifier.py`: The decision engine utilizing the `Groq` API (`llama-3.1-8b-instant`) to determine if a data source is structured, semi-structured, or unstructured.
*   `agent/tools.py`: The tactical execution layer containing the `TAVILY_CONFIG` (whitelisting `pib.gov.in`, `mcdonline.nic.in` with a 50-call daily limit), PDF parsing logic (`PyMuPDF/fitz`), and Web Scraping logic (`BeautifulSoup` + `markdownify`).
*   `agent/loader.py`: The downstream daemon that sweeps `/data/unstructured/raw/`, sends the document to the FastAPI `/scrape/analyze` endpoint for LLM Ontology Mapping, and pushes the extracted JSON entities to Neo4j via the `/ingest/entities` endpoint, finally archiving the file to the `processed/` folder.

---

## 2. What is Required (Dependencies & Config)
Based on the code analysis, the pipeline strictly requires the following to run:

### Environment Variables (`.env`)
1.  `GROQ_API_KEY`: Used by `classifier.py` for routing.
2.  `TAVILY_API_KEY`: Used by `run_agent.py` to autonomously hunt for new urban infrastructure news.
3.  `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Used by the backend to commit nodes to the graph.

### Python Packages (`requirements.txt`)
*   `apscheduler`: For the `--daemon` background clock.
*   `groq`: For fast classification.
*   `tavily-python`: For autonomous web search.
*   `pymupdf` (fitz): For extracting text from manual local PDF uploads.
*   `beautifulsoup4` & `markdownify`: For synchronous web scraping of government portals.

---

## 3. The Architecture: Connecting the Dots
The architecture is a strict **4-Step Decoupled Pipeline**:

**Step 1: The Hunter (`run_agent.py`)** -> *Finds the Data*
Instead of waiting for humans, the agent wakes up, grabs the `TAVILY_API_KEY`, and searches whitelisted domains (like `pib.gov.in`) for keywords like "Delhi MCD AMRUT drain". It gathers 5-10 highly relevant URLs.

**Step 2: The Router (`agent/classifier.py`)** -> *Decides the Shape*
For every URL found (or file placed in `/inbox/`), the Agent asks the Groq LLM: *"What is this?"*
The LLM applies strict rules: If it's an `.aspx` or HTML press release, it classifies it as `unstructured` and routes it to Path 3.

**Step 3: The Fetcher (`agent/tools.py`)** -> *Downloads to Disk*
The Agent uses `BeautifulSoup` and `markdownify` to scrape the web page, cleans the HTML into pure Markdown text, and physically saves the file into `data/unstructured/raw/<filename>.md`. **The Agent's job finishes here.**

**Step 4: The Sweeper & AI Embedder (`agent/loader.py` + FastAPI)** -> *Understands and Stores*
A completely separate script (`loader.py`) sweeps the `data/unstructured/raw/` directory. It finds the `.md` file, sends it to the central PRAMAAN AI Backend, which uses a massive LLM to perform Named Entity Recognition (NER). It realizes the text mentions "Ward 45" and "Drain". It then hits the Neo4j API to permanently link the `Asset` node to the `Region` node. Finally, it moves the `.md` file to the `processed/` folder.

---

## 4. A Layman Example: The Tale of the Gali 7 Drain

Imagine the Delhi Municipal Corporation finishes repairing a storm-water drain on Gali No. 7 in Ward 45. They post a generic press release on `pib.gov.in`. 

1.  **2:00 AM:** The Hunter (`run_agent.py`) wakes up. It asks Tavily: *"Show me new MCD updates."* It finds the `pib.gov.in` link about the drain.
2.  **2:01 AM:** The Router (`classifier.py`) looks at the link and says: *"This is a regular webpage. It is Unstructured Data."*
3.  **2:02 AM:** The Fetcher (`tools.py`) goes to the webpage, strips away all the annoying menus and ads, and saves just the text of the press release as a Markdown file in `data/unstructured/raw/drain_update.md`.
4.  **2:05 AM:** The Sweeper (`loader.py`) sees the new `drain_update.md` file. It hands it to the big AI Brain on the Backend. 
5.  **2:06 AM:** The AI reads the human text, extracts *"Asset: Drain"*, *"Location: Gali 7, Ward 45"*, and *"Scheme: SFC Grant"*. It translates this into a strict Graph JSON.
6.  **2:07 AM:** The Graph Engine (Neo4j) draws a line connecting the Drain to Ward 45. 
7.  **8:00 AM:** A citizen opens the PRAMAAN UI, clicks on the **Ward Map**, and magically sees a new Green pin for a Completed Drain on Gali 7.

---

## 5. How to Test Each Step (CLI Guide)

Because the pipeline is modular, you can test every single step in isolation without running the entire backend daemon.

### Test Step A: Classify a Source (The Router)
Test if the Groq LLM correctly routes a PIB press release.
```bash
python agent/classifier.py
# Expected Output: JSON dict returning {"source_type": "unstructured", "fetch_method": "web_crawl", ...}
```

### Test Step B: Manually Fetch a URL (The Hunter + Router + Fetcher)
Bypass the daily timer and force the agent to download a specific URL immediately into the raw folder.
```bash
python run_agent.py --url "https://pib.gov.in/PressReleasePage.aspx?PRID=123456"
# Expected Result: A new .md file appears in data/unstructured/raw/
```

### Test Step C: Test Local PDF/Image Uploads (Inbox Sweep)
Drop a sample PDF into your `e:\INDIA_INNOVATES\Pramaan\inbox\` folder.
```bash
python run_agent.py --file "my_sample_report.pdf"
# Expected Result: The PDF is moved to data/semi_structured/raw/ and converted to a .md file using PyMuPDF.
```

### Test Step D: Test AI Extraction & Neo4j Load (The Sweeper)
Ensure your FastAPI backend (`uvicorn`) and Neo4j Docker are running.
Place a fake `.md` file containing governance text into `data/unstructured/raw/`.
```bash
python agent/loader.py
# Expected Result: Terminal logs showing the file was sent to the FastAPI analyzer, successfully written to Neo4j, and moved to the 'processed' folder.
```

### Test Step E: Run the Full Autonomous Pipeline
Turn on the infinite loop daemon that wakes up at 2:00 AM to do everything autonomously.
```bash
python run_agent.py --daemon
# Expected Result: APScheduler starts quietly in the background.
```
