# RAG Evaluation Script Design

## Goal

Add an offline batch evaluation workflow for the enterprise knowledge base RAG agent. The workflow should help demonstrate that the project is not only runnable, but also measurable.

## Scope

- Use a JSON question set as input.
- Reuse the existing RAG service instead of creating another answer pipeline.
- Produce a Markdown report suitable for GitHub technical review and reproducible demo verification.
- Track both answer quality and escalation behavior.

## Evaluation Case Format

Each question case contains:

- `id`: stable case identifier.
- `question`: user question.
- `expected_keywords`: keywords that should appear in a correct answer.
- `should_escalate`: whether the question should be transferred to a ticket.

## Metrics

The report includes:

- Total cases.
- Passed cases.
- Pass rate.
- Keyword hit rate.
- Escalation accuracy.
- Average confidence.
- Average source count.

## Pass Rule

A case passes when:

- The escalation result matches `should_escalate`.
- If the case should not escalate, all expected keywords appear in the answer.

For escalation cases, expected keywords can be empty. The key behavior is that the system refuses to answer without reliable knowledge base evidence and creates a ticket.

## Output

The script writes:

- `docs/evaluation/evaluation_report.md`

The report includes a summary table and per-case details.
