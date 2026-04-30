# Change Control (Protected Terms & Silent Change Prevention)

## Protected terms
- Artifact
- EvidenceUnit
- GraphNode
- GraphEdge
- SemanticIndex
- FileClerk
- RetrievalPacket
- SourceFidelity
- ModelAdapter
- IngestionPipeline
- ContextBudget

## Change requirements
Any change to protected terms requires:
1. Written reason
2. Impact analysis
3. Contract update
4. Migration or update plan
5. Tests updated
6. Explicit approval

## Forbidden silent changes
- Renaming core models without migration notes
- Changing JSON output shape without contract update
- Changing `source_fidelity` values without tests
- Changing retrieval packet schema silently
- Moving responsibilities between layers without docs

