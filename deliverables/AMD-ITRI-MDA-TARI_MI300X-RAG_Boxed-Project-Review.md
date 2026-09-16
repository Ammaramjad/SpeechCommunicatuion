# AMD–ITRI Project Review

**MI300X Enterprise Document RAG Project Report**  
Enterprise document retrieval and source-grounded Chinese answer generation

---

## Document control (attestation — not a legal signature)

| Field | Value |
|---|---|
| Document title | AMD–ITRI Project Review: MI300X Enterprise Document RAG (boxed / पेटी format) |
| Template followed | **AMD–ITRI PROJECT REVIEW** boxed slide template (widescreen navy field, cyan rules, rounded content boxes) |
| How “पेटी” was interpreted | Official boxed layout of the AMD–ITRI Project Review deck — header boxes, rounded cards, KPI boxes — not a ZIP archive |
| How “एमडीए टारी” was interpreted | Spoken/Hinglish rendering of **AMD ITRI** (the Project Review template). This is **not** an SEC Management’s Discussion & Analysis (MD&A) filing. |
| Version | 1.0 |
| Date | **2026-09-11** |
| Author (as stated on sources) | Dr. Ammar Amjad, National Yang Ming Chiao Tung University (NYCU) |
| Platform | AMD Instinct MI300X · PyTorch 2.3 · ROCm 6.2 · Implemented RAG prototype |
| Prepared from | `AMD-ITRI-Project-Review-TEMPLATE.pdf` and `AMD-ITRI-MI300X-Final-Comparison-Report-SOURCE.pdf` |
| Classification | Project review · Technical report |
| Attestation | Prepared/generated as a document-control conversion of the uploaded sources onto the AMD–ITRI boxed template. **No handwritten, cryptographic, or legal personal signature was created or forged.** |

---

## Cover

- **Series:** AMD – ITRI PROJECT REVIEW  
- **Also titled in the comparison source:** AMD–ITRI High-Performance Computing Platform  
- **Report:** MI300X Enterprise Document RAG Project Report / MI300X RAG Project Report  
- **Subtitle:** Enterprise document retrieval and source-grounded Chinese answer generation  
- **Author:** Dr. Ammar Amjad  
- **Affiliation:** National Yang Ming Chiao Tung University  
- **Hardware line:** AMD Instinct™ MI300X · PyTorch 2.3 / ROCm 6.2 · Implemented RAG prototype  

---

## 1. Business problem and implemented solution

**Title (template):** RAG turns scattered PDF and Excel content into grounded answers

### BUSINESS PROBLEM

Enterprise knowledge is spread across PDF reports and Excel sheets. Finding the right information manually is slow, and answers often lack a traceable source.

### IMPLEMENTED SOLUTION

Retrieval-Augmented Generation (RAG): the system first retrieves the most relevant document chunks, then Qwen2.5-7B-Instruct generates a Traditional Chinese answer grounded in them.

### Pipeline boxes (template)

| Step | Content |
|---|---|
| 1 Data Preparation | PDF + Excel → text extraction → 500-char chunks → BGE embeddings → vector index |
| 2 Retrieval | User question → query embedding → dot-product similarity → Top-3 chunks |
| 3 Generation | Retrieved context + sources → Qwen2.5-7B-Instruct → Traditional Chinese answer with filenames |

### Comparison-source implementation boxes (same substance)

**Data preparation**

- PDF text extraction using pypdf  
- Excel reading using openpyxl  
- 500-character chunks with 100-character overlap  

**Retrieval model — BAAI/bge-small-zh-v1.5**

- Chinese semantic embeddings  
- Normalized vectors and Top-3 retrieval  

**Generation model — Qwen2.5-7B-Instruct**

- bfloat16 inference on MI300X  
- Traditional Chinese answer with sources  

---

## 2. Project objective

**Title (template):** Objective: a searchable knowledge base that answers with sources  
**Title (comparison source):** The project makes enterprise documents searchable and answerable

### PROBLEM ADDRESSED

- Information distributed across PDF and Excel files  
- Manual search is time-consuming  
- Answers may lack document sources  
- Answers need traceable document sources (comparison-source wording)

### IMPLEMENTED OBJECTIVE

- Build a searchable document knowledge base / Chinese document knowledge index  
- Retrieve relevant chunks for a question  
- Generate source-grounded Traditional Chinese answers with Qwen  

---

## 3. Knowledge index construction

**Title (template):** Documents become a persistent vector index in five steps  
**Title (comparison source):** Document content becomes a persistent semantic index

### Five-step boxes

1. **PDF + Excel** — Enterprise source documents (PDF pages; Excel rows and sheets)  
2. **Text extraction** — pypdf (PDF); openpyxl (Excel rows)  
3. **Chunking** — Clean text; 500-character chunks; 100-character overlap  
4. **BGE embeddings** — BAAI/bge-small-zh-v1.5; normalized, on MI300X  
5. **Vector index** — `gama_embeddings.npy`, `gama_chunks.json`, and (comparison source) `index_summary.json`

### INDEX FACTS

- 25 document sections extracted  
- 17 searchable text chunks created  
- Embeddings normalized for dot-product similarity  
- Index persisted to disk for reuse across queries  
- Verified output stated as 25 extracted sections and 17 searchable chunks  

The comparison PDF text contains the typo “seaReachable”; the matching template and chart labels use **searchable**. That wording is used here.

---

## 4. Implemented architecture

**Title:** The architecture links document evidence to the generated answer

### OFFLINE · INDEX CONSTRUCTION

Enterprise documents (PDF · Excel) → Text extraction & chunking (pypdf · openpyxl · 500/100) → BGE embeddings (bge-small-zh-v1.5 · MI300X) → Vector index (.npy + .json)

### ONLINE · QUESTION ANSWERING

User question (Traditional Chinese query) → Top-3 retrieval (normalized · dot-product) → Qwen2.5-7B-Instruct (bfloat16 · device_map=auto) → Grounded answer (Traditional Chinese + source filenames)

Evidence chunks connect the offline index to online retrieval.

**Environment line:** Runs on AMD Instinct MI300X · PyTorch 2.3 · ROCm 6.2  

**Caption:** The system retrieves relevant document evidence before Qwen2.5-7B generates the answer.

### Additional facts from the comparison-source architecture diagram

These items appear on the comparison report’s implemented-flow figure (embedded in the PDF as `assets/implemented-flow-source.png`):

- Embedding path: BAAI/bge-small-zh-v1.5, Sentence Transformers, batch size 32, normalized vector embeddings  
- Index metadata: source + page + sheet + row  
- Similarity: `score(q, d) = qᵀd` on normalized vectors (cosine)  
- Retrieval: Top-3 relevant chunks  
- Generation: `max_new_tokens = 300`  
- Observed LLM generation time on the diagram: 2.55 seconds  

---

## 5. Model roles and retrieval

**Title (template):** Two models, two roles: retrieval and generation

### BAAI/bge-small-zh-v1.5 — Embedding and retrieval

- Converts / transforms document chunks and user queries into semantic / comparable vectors  
- Supports normalized vector search and Top-3 retrieval by dot-product similarity  
- Chinese semantic embeddings  

### Qwen2.5-7B-Instruct — Answer generation

- Uses retrieved context and system instructions  
- Generates source-grounded Traditional Chinese answers and source filenames  
- bfloat16 inference on MI300X  

**Footer box:** No model training or fine-tuning is claimed in this project.

---

## 6. Verified results and comparison

**Title (template):** Verified results on AMD Instinct MI300X  
**Title (comparison source):** MI300X results and comparison

### KPI boxes

| Metric | Value |
|---|---|
| Document sections extracted | 25 |
| Searchable text chunks created | 17 |
| Observed Qwen response-generation time | 2.55 s |
| Retrieved chunks per query | Top-3 |

**Execution environment:** AMD Instinct MI300X · PyTorch 2.3 · ROCm 6.2

### Response time comparison (seconds)

Values taken from the comparison-source bar chart.

| Model | Observed response time (s) |
|---|---|
| Qwen2.5-7B | 2.55 |
| Llama 3.1 8B Instruct | 3.1 |
| Mistral 7B Instruct | 2.9 |

### OBSERVATIONS

- Qwen2.5-7B-Instruct loaded and executed successfully on MI300X (bfloat16, device_map=auto).  
- The answer used the retrieved documents and stated “insufficient information” instead of inventing a third source.  
- **Note:** 2.55 seconds is an observed single-query generation time, not a general GPU benchmark.

---

## 7. Proposed deployment model

**Badge (template):** PROPOSED · NOT YET IMPLEMENTED

### Four function boxes (both sources)

1. **Controlled upload** — Authorized users upload PDF / Excel documents  
2. **Versioning & indexing** — Track document versions; re-embed and update the index  
3. **Source-grounded Q&A** — Retrieve evidence, then generate the answer with Qwen  
4. **Citations & feedback** — Show source filenames; collect user ratings to improve quality  

### Future-state interface (concept)

- **Q:** Ask a question about your enterprise documents…  
- **A:** Grounded answer · Sources: report.pdf, data.xlsx · Was this helpful? Yes / No  

**Caption:** Proposed roadmap; the current project validated the underlying MI300X RAG workflow.

### Proposed 12-box enterprise flow (comparison-source diagram)

The comparison report includes a detailed proposed-architecture figure (`assets/proposed-deployment-source.png`). Labels transcribed into boxes:

1. **Enterprise data sources** — PDF documents; Excel spreadsheets; internal reports; databases (SharePoint, etc.); policies & guidelines  
2. **Secure upload & validation** — File validation; access control (RBAC); virus/malware scan; document versioning; metadata capture  
3. **Document processing** — PDF/Excel parsing; text extraction (OCR noted on diagram); content cleaning; semantic chunking; metadata tagging  
4. **Embedding & indexing** — Generate vector embeddings; store in vector database; build searchable index; maintain metadata  
5. **Vector database** — PostgreSQL + pgvector, Weaviate, Qdrant, etc.; document ingestion periodically or on new documents  
6. **User query** — Enterprise web interface; SSO / authentication; role-based access; multi-language support  
7. **Retrieval layer** — Query embedding; similarity search (Top-K); metadata filtering; optional re-ranking; retrieve relevant chunks  
8. **RAG orchestration** — Combine query + retrieved context; instruction / system prompt; token-limit context management; safety and guardrails  
9. **LLM inference (MI300X)** — Run LLM on AMD MI300X (ROCm); high-throughput inference; optimized for enterprise workloads; scalable and secure deployment  
10. **Grounded response** — Source-grounded answer; citations and document links; reduced hallucinations; show relevant excerpts  
11. **Enterprise application** — Q&A chat interface; document preview; conversation history; user feedback (thumbs up/down)  
12. **Monitoring & continuous improvement** — Usage analytics/KPIs; latency and throughput; GPU utilization (MI300X / ROCm); retrieval quality; ratings; index updates; security, compliance, and audit logs  

This 12-box flow is **proposed**, matching the template badge. It is not described as already implemented.

---

## 8. Request for renewed MI300X access

### WHAT THE INITIAL ALLOCATION ACHIEVED

The first MI300X allocation validated the technical feasibility of the full workflow on AMD hardware with PyTorch 2.3 / ROCm 6.2:

- Document indexing (PDF + Excel → 17 chunks)  
- Normalized Top-3 semantic retrieval  
- Qwen2.5-7B-Instruct inference (bfloat16)  
- Source-grounded Traditional Chinese answers  

### PLANNED NEXT STEPS WITH RENEWED ACCESS

1. Expand official product and service documents  
2. Create a 50–100 question evaluation set  
3. Measure retrieval quality and inference performance reproducibly / systematically  
4. Build the proposed enterprise knowledge interface  

### EXPECTED DELIVERABLES (comparison source)

- Reproducible MI300X benchmark report  
- Validated source-grounded RAG results  
- A proposed interface for enterprise knowledge support  

---

## Closing

Thank you to AMD and ITRI for enabling this work.

---

## Transfer notes

| Item | Status |
|---|---|
| All numbered metrics (25, 17, 2.55 s, Top-3, 3.1 s, 2.9 s, batch 32, max_new_tokens 300) | Transferred from sources |
| Template boxed section titles | Followed exactly |
| Comparison-source unique files (`index_summary.json`) | Added to the index box |
| Implemented-flow figure | Embedded as original image; facts also transcribed |
| Proposed-deployment figure | Embedded as original image; labels transcribed into 12 boxes |
| Decorative cover network graphic | Recreated as a similar node motif, not a pixel-identical logo |
| AMD Instinct™ wordmark styling | Text attribution only; no trademark artwork was copied |
| Legal / personal signature | **Not created.** Document-control attestation only |

Sources used:

- Template: `deliverables/sources/AMD-ITRI-Project-Review-TEMPLATE.pdf` (LibreOffice Impress “AMD – ITRI PROJECT REVIEW” boxed deck)  
- Content: `deliverables/sources/AMD-ITRI-MI300X-Final-Comparison-Report-SOURCE.pdf` (PowerPoint “Final Comparison Report”) plus all unique template narrative that the comparison deck omitted  
