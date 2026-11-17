# ADR 0003: Provider-independent AI via adapter interfaces
Status: Accepted (Phase 0.1)

**Decision:** LLM, embedding, STT and TTS each sit behind an internal interface (`app/ai/providers/`, created in Phase 5.1). No provider SDK is imported outside its adapter. Keys come only from environment variables.
**Privacy:** adapters must scrub PII before sending and must support zero-retention settings (see Constitution 1.4).
