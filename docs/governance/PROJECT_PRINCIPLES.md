# GraphClerk Project Principles

GraphClerk is a **local-first, graph-guided evidence-routing layer for RAG systems**.

It does not try to replace RAG frameworks, vector databases, or LLMs.
It improves the layer between user intent and LLM context.

## Core principle
**Search meaning first, then retrieve evidence.**

## Core principles
1. GraphClerk retrieves meaning first, then evidence.
2. Original source artifacts are never overwritten.
3. Evidence units preserve traceability to original artifacts.
4. Semantic indexes are access paths, not source truth.
5. The graph organizes source-backed meaning.
6. The File Clerk returns structured retrieval packets, not vague prose.
7. LLMs synthesize answers from packets; they do not create truth.
8. Local-first ingestion is preferred.
9. Multimodal content must normalize into evidence units.
10. Every major behavior must be testable.
11. Context should be pruned before reaching the LLM.
12. Retrieval should expose confidence, ambiguity, and source support.

## Non-goals
- GraphClerk is not a full autonomous agent framework.
- GraphClerk is not a chatbot by itself.
- GraphClerk is not a vector database.
- GraphClerk is not a document storage system only.
- GraphClerk is not EBES.
- GraphClerk does not replace original source material with summaries.

