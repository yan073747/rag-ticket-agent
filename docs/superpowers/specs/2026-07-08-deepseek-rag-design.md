# DeepSeek RAG Enhancement Design

## Goal

Upgrade the enterprise knowledge base from a retrieval-style demo into a real RAG customer service agent by adding DeepSeek as the answer generation layer.

The system must still rely on uploaded company documents as the source of truth. DeepSeek can organize and rewrite the answer, but it must not answer from general knowledge when the retrieved evidence is weak.

## Scope

- Default model: `deepseek-v4-flash`.
- API-compatible provider: DeepSeek Chat Completions API.
- Configuration through environment variables.
- Safe fallback when no API key is configured.
- Existing confidence, source citation, and ticket escalation behavior stays in place.

## Architecture

The current pipeline is:

1. User asks a question.
2. Chroma retrieves relevant document chunks.
3. The backend calculates confidence.
4. Low confidence creates a ticket.
5. High confidence returns an answer with sources.

After this enhancement:

1. User asks a question.
2. Chroma retrieves relevant document chunks.
3. The backend calculates confidence.
4. Low confidence creates a ticket without calling DeepSeek.
5. High confidence sends the question and retrieved chunks to DeepSeek.
6. DeepSeek returns a concise answer based only on the provided context.
7. The backend still returns sources, confidence, and ticket status.

## Components

### Config

Add environment variables:

- `DEEPSEEK_API_KEY`: optional API key.
- `DEEPSEEK_BASE_URL`: defaults to `https://api.deepseek.com`.
- `DEEPSEEK_MODEL`: defaults to `deepseek-v4-flash`.
- `DEEPSEEK_TIMEOUT_SECONDS`: defaults to `30`.

### LLM Service

Create a small service that:

- Checks whether DeepSeek is configured.
- Builds a strict system prompt.
- Calls `/chat/completions`.
- Returns generated answer text.
- Falls back to local source-based answer if the API key is missing or the API call fails.

### RAG Service

Keep the existing retrieval and confidence logic. Only call DeepSeek when:

- At least one source was retrieved.
- Confidence is greater than or equal to the low-confidence threshold.

If confidence is low, create a ticket first and do not call the model.

## Prompt Rules

The system prompt must require:

- Answer only from the provided company knowledge base context.
- Do not invent facts.
- If the context is insufficient, say that the knowledge base does not contain enough information.
- Keep the answer clear and suitable for customer service.

## Testing

Add tests for:

- Missing API key falls back to local answer.
- Low-confidence questions do not call the model.
- DeepSeek response is used when the model service returns an answer.

Network calls are not used in unit tests. Tests should mock the LLM service boundary.
