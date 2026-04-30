# Testing Rules

## Minimum rules
1. Every service gets unit tests.
2. Every public endpoint gets API tests.
3. Every schema contract gets validation tests.
4. Ingestion must test source preservation.
5. Retrieval must test packet structure.
6. Graph traversal must test limits and edge filtering.
7. Model outputs must be validated before persistence.
8. No test may be removed just to make implementation pass.
9. Regressions must receive regression tests.
10. Multimodal extractors must test traceability to artifacts.

## Future test categories
- contract tests
- unit tests
- API tests
- ingestion tests
- retrieval tests
- graph traversal tests
- vector search tests
- evaluation tests
- UI smoke tests

