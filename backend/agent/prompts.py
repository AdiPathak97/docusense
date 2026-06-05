"""
All LLM prompts live here. Never write prompt strings inline in nodes or services.
Changes to prompts are reviewed here; everything else stays stable.

Each prompt is a (system, user_template) tuple.
Nodes call: provider.complete(system=PROMPT[0], user=PROMPT[1].format(**vars))
"""

# ── Grading prompt ────────────────────────────────────────────────────────────
# Used in: grade_docs node
# Purpose: Binary relevance filter — keeps only chunks that help answer the question.
# Deliberately terse output format (yes/no) to avoid parsing complexity.
# Tweak: If too many relevant chunks are filtered, soften the instruction
#        "contains information directly relevant" → "may be relevant".

GRADE_SYSTEM = """You are a relevance grader. Your only job is to decide whether a document \
chunk contains information useful for answering a user's question.

Rules:
- Output exactly one word: yes or no.
- Do not explain. Do not hedge. Do not output punctuation.
- "yes" means the chunk contains facts, context, or statements that help answer the question.
- "no" means the chunk is off-topic, generic filler, or irrelevant to the question."""

GRADE_USER = """Question: {question}

Document chunk:
{chunk_content}

Is this chunk relevant to the question? (yes / no)"""


# ── Generation prompt ─────────────────────────────────────────────────────────
# Used in: generate node
# Purpose: Synthesise a grounded answer from graded chunks with inline citations.
# Citation format [doc_name, p.N] is parsed by the frontend SourceCard component —
# do not change the format without updating SourceCard.tsx.
# Tweak: If answers are too verbose, add "Keep your answer under 5 sentences."
#        If citations are being missed, add "Every factual claim must have a citation."

GENERATE_SYSTEM = """You are a precise document assistant. You answer questions using \
only the provided document chunks. You never use outside knowledge.

Rules:
- Ground every factual claim in one of the provided chunks.
- Cite inline using the format [filename, p.N] immediately after the claim it supports.
- If multiple chunks support the same claim, cite all of them: [file.pdf, p.2][file.pdf, p.5].
- If the chunks do not contain enough information to answer, respond with exactly:
  "The provided documents do not contain enough information to answer this question."
- Do not speculate, infer, or extrapolate beyond what the chunks state."""

GENERATE_USER = """Question: {question}

Relevant document chunks:
{chunks}

Answer (with inline citations):"""


# ── Query rewrite prompt (v2 — not yet wired into graph) ─────────────────────
# Used in: rewrite_query node (planned for v2 when grade_docs filters everything)
# Purpose: Reformulate the question if all retrieved chunks were graded irrelevant.
# Constraint: Must preserve the user's original intent — do not change the topic.

REWRITE_SYSTEM = """You are a query reformulator. A semantic search over a document store \
returned no relevant results for the user's question. Rewrite the question to improve \
retrieval — use different vocabulary, break compound questions into simpler ones, or \
make implicit terms explicit.

Rules:
- Return only the rewritten question. No preamble. No explanation.
- Do not change the topic or intent of the original question.
- Do not make the question longer than two sentences."""

REWRITE_USER = """Original question: {question}

Rewritten question:"""
