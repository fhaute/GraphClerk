# Coding Standards (Mandatory)

These standards are part of the project contract.

## Core rules
1. Code must be readable before clever.
2. Every public function, class, service, and model must have a docstring.
3. Every non-trivial private function should have a docstring or explanatory comment.
4. Complex logic must be broken into small, testable functions.
5. No hidden side effects.
6. No silent exception swallowing.
7. No broad `except` blocks without explicit error handling.
8. No business logic inside API route handlers when it belongs in services.
9. No database access from unrelated layers.
10. No hardcoded configuration values.
11. No unused dependencies.
12. No fake implementations unless explicitly marked as temporary and tracked.

## Python standards
- Use Python 3.12+.
- Use type hints everywhere practical.
- Use Pydantic models for external input/output schemas.
- Use SQLAlchemy models only for persistence, not API contracts.
- Use service classes or service functions for business logic.
- Keep route handlers thin.
- Prefer explicit errors over magic fallbacks.
- Use enums for controlled vocabularies such as `source_fidelity`, `modality`, `relation_type`, and `answer_mode`.

## Docstring standard
Every public class/function/method should explain:
- what it does
- expected inputs
- returned output
- important errors or failure modes
- architectural constraints if relevant

Example:
```python
async def create_evidence_unit(command: CreateEvidenceUnitCommand) -> EvidenceUnit:
    \"\"\"Create a source-backed evidence unit for an artifact.

    The function preserves traceability to the original artifact and must not
    rewrite or summarize source content unless the resulting EvidenceUnit is
    explicitly marked as derived.

    Raises:
        ArtifactNotFoundError: If the referenced artifact does not exist.
        InvalidSourceFidelityError: If source_fidelity is unsupported.
    \"\"\"
```

## Comments standard
Comments should explain why, not repeat what the code says.

Bad:
```python
# increment i
i += 1
```

Good:
```python
# Keep traversal bounded so one dense graph region cannot explode the packet.
```

## Layering rules
```text
API routes:
- request validation
- call service
- return response

Services:
- business logic
- orchestration
- validation

Repositories:
- database reads/writes

Models:
- persistence shape only

Schemas:
- external contracts

Adapters:
- external tools, models, OCR engines, vector stores
```

## Code review checklist
Every implementation slice should answer:
- Is this within the requested phase?
- Are protected concepts respected?
- Are public functions documented?
- Are errors explicit?
- Are tests included?
- Is the code easy to remove or refactor if this slice fails?

