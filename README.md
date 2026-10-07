# analyse-10k
A system that analyses the Form-10K submitted by companies to SEC

### What is 10-K?
Form 10K is an annual financial report that the publicly listed US companies should file with the SEC.It runs to hundreds of pages. 
In India its split between companies annual report and MCA filings. 

### Why 10-K?
It provides a deep, audited look into a company's financial performance, business operations, legal proceedings, and risk factors.

### What's this project?
this is a system that answers questions about a public company's 10-K annual report, cites the exact passage behind every answer, and is tested against hand-verified questions so we measure changes instead of guessing.

#### why this project when we have chatbot?
Two things go wrong if we resort chatbot: 
- The report is too long for it to read well, 
- AI can sound confident while making up an answer, but if the numbers are made-up then its a disaster in accounting.

#### how to solve this?
- **Retrieval**: dig those passages from the report that matches the question.
- **Grounded answers**: make LLM to answer from only those passages that match the question and also cite the passages used.
- **Evals**: a fixed set of questions with known answers measures correctness, citation grounding, and whether the system admits when the answer is not in the filing.

# In scope (Phase 1)
1. Download one 10-K from SEC EDGAR
2. Split it into sections (for example Item 1A Risk Factors, Item 7 MD&A) and then into chunks that keep their section label
3. Embed chunks and store them in PostgreSQL with pgvector
4. Retrieve the top relevant chunks for a question
5. Generate an answer from retrieved chunks only, with citations
6. Eval suite of about 20 hand-verified questions and a repeatable scoring run
7. Docker Compose setup so the whole thing runs with one command

ToDo: (not yet planned in phase 1)
Tables and financial statements (known weak spot, see Known limitations)
Multiple companies or multiple years
Frontend UI
Agents, drafting, or any write path
Authentication and deployment

## Working
```
EDGAR 10-K (HTML)
      |
      v
 [1] Parse + split into sections
      |
      v
 [2] Chunk (keep section label, chunk index)
      |
      v
 [3] Embed chunks  ---->  PostgreSQL + pgvector
                                 |
 Question --> [4] Embed question + similarity search (top k chunks)
                                 |
                                 v
                    [5] LLM answers using ONLY those chunks
                                 |
                                 v
              Answer + citations (section, chunk id, passage)

```

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| API | FastAPI |
| Database | PostgreSQL with pgvector |
| Embeddings | Open-source sentence-transformers model (runs locally, free) |
| LLM | Provider API, selected through environment variables |
| Parsing | BeautifulSoup |
| Tests / evals | pytest plus a custom eval runner |
| Packaging | Docker, Docker Compose |

## Planned API

| Endpoint | Purpose |
|---|---|
| `POST /ingest` | Download and index a filing by company and year |
| `POST /ask` | Body: `{ "question": "..." }`. Returns `{ "answer": "...", "citations": [{ "section": "...", "chunk_id": 123, "passage": "..." }] }` |
| `GET /health` | Service and database check |

## Planned data model

- `filings`: id, company, fiscal year, source URL
- `chunks`: id, filing_id, section, chunk_index, text, embedding (vector)

## Evals

The eval set is a YAML file of questions I verified by hand against the filing.

```yaml
- id: q01
  question: "..."
  expected_answer: "..."        # key fact or figure to look for
  evidence_text: "..."          # short phrase that must appear in the cited chunk
  answerable: true
- id: q18
  question: "..."               # deliberately not answered in the filing
  answerable: false
```

Each run scores three checks:

1. **Answer correctness:** does the answer contain the expected fact or figure?
2. **Citation grounding:** does a cited chunk actually contain the evidence text?
3. **Abstention:** for unanswerable questions, does the system say it cannot find the answer instead of guessing?

Results are saved per run so I can change one thing (chunk size, number of retrieved chunks, prompt wording) and compare scores.

## Phase 1 milestones

- [ ] Repo, Docker Compose, Postgres with pgvector running
- [ ] Download one 10-K from EDGAR (with a declared User-Agent, as SEC requires)
- [ ] Section splitting works on the chosen filing
- [ ] Chunking with section labels
- [ ] Embeddings stored and similarity search returns sensible chunks
- [ ] `POST /ask` returns an answer with citations
- [ ] Eval set of about 20 questions written and verified by hand
- [ ] Eval runner prints correctness, grounding, and abstention scores
- [ ] Baseline scores recorded below
- [ ] One experiment run (for example chunk size) with before/after scores

