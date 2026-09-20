# Document Chunking From Scratch

## Problem

Retrieval systems do not retrieve documents. They retrieve chunks. Every downstream quality number, recall, precision, answer faithfulness, is bounded by how the corpus was cut up before indexing. A chunk that ends mid-sentence embeds poorly and reads poorly in context. A heading separated from its body means the section title matches a query but the answer text is in a different chunk that may not be retrieved at all.

Chunking is decided once, at ingestion time, and its mistakes are invisible until you run retrieval evals. Most teams pick a default splitter and never look at the boundaries it produces.

## What You Build

One file, `chunker.py`, containing three chunking strategies over a realistic markdown runbook:

- **Fixed-size**: cut every N characters with character overlap. The baseline everything else is measured against.
- **Sentence-aware**: split into sentences, pack whole sentences into chunks under a size budget, carry trailing sentences forward as overlap.
- **Recursive structure-aware**: split on the largest structural boundary first (H2 headings, then H3, then paragraphs, then sentences), recursing only when a piece is still too large. When a section must be split, its heading is propagated onto every child chunk.

The demo measures boundary quality for all three: chunks ending mid-sentence, chunks starting mid-sentence, and headings orphaned from their body text.

## How It Works

Fixed-size chunking is a sliding window: step = size minus overlap, slice, repeat. It needs no parsing, which is exactly why its boundaries land anywhere, including inside words.

Sentence-aware chunking first segments the text with a regex that looks for terminal punctuation followed by whitespace and a plausible sentence start. Sentences are then packed greedily: add sentences until the next one would exceed the budget, emit the chunk, and seed the next chunk with the last sentence of the previous one so context spans the boundary.

Recursive chunking encodes a priority list of separators, strongest structure first. A piece that fits the budget is kept whole. A piece that does not fit is split at the current level and each fragment recurses to the next level. The one non-obvious move is heading propagation: when a section is too large to keep intact, the naive approach leaves the heading line as its own fragment. This implementation strips the heading, splits the body, and prefixes the heading onto each child chunk, shrinking the child budget by the heading length. Every chunk then knows what section it came from.

## Design Decisions

- **Character budgets, not token budgets.** Real systems budget in model tokens. Characters keep this dependency-free, and the ratio is stable enough (roughly 4 characters per token for English) that the structural argument is unchanged. Swapping in a tokenizer changes one function.
- **Overlap measured in sentences for the structure-aware strategies.** Character overlap on a sentence-packed chunk would reintroduce the mid-sentence boundaries the strategy exists to avoid. Overlapping by whole sentences keeps boundaries clean and still gives the retriever redundant context.
- **Heading propagation instead of heading-only chunks.** A chunk containing just `## Common Alerts` is noise in the index: it matches section-title queries but contains no answer. Prefixing the heading onto body chunks makes each chunk self-describing, which is the same idea behind contextual chunk augmentation in production RAG systems.
- **Regex sentence splitting.** It mishandles abbreviations and decimal numbers. That is an accepted simplification; the module is about chunk assembly, not sentence segmentation.

## Failure Modes

- **A single sentence longer than the budget** cannot be packed and will produce an oversized chunk. Production splitters fall back to word or character splitting for this case.
- **Documents without structure** (OCR dumps, chat logs, minified HTML) give the recursive strategy nothing to split on, and it degrades to sentence packing. Its advantage is entirely dependent on structure existing.
- **Too much overlap** inflates the index, retrieves near-duplicate chunks, and wastes context budget on repeated text. Fusion and deduplication downstream partially mask this, which makes it hard to notice.
- **Too little overlap** breaks answers that span a boundary: the query matches chunk A but the fact it needs is the first sentence of chunk B.
- **Chunks too large** dilute embeddings (one vector averaging several topics) and blow the context budget with irrelevant text. Chunks too small lose the context needed to interpret them. Both failure modes show up as retrieval that looks fine on keyword match and fails on semantic queries.

How chunking propagates into retrieval quality: the embedding of a chunk is a lossy summary of its text. A chunk that mixes the end of one section with the start of another embeds as neither, so the vector sits between the two topics and matches queries about neither one well. Lexical search suffers differently: the term is present, so BM25 finds the chunk, but the surrounding context handed to the model is the wrong section. Boundary quality is not cosmetic. It decides what the retriever can even express.

## What Production Systems Do Differently

- Budget in tokenizer tokens, matched to the embedding model's own tokenizer and context limit.
- Use format-specific parsers: markdown ASTs, HTML DOM, PDF layout analysis, code syntax trees. Structure detection is most of the engineering effort.
- Attach metadata to each chunk (source document, section path, page number) rather than relying only on prefixed headings.
- Augment chunks with generated context (a model-written one-line summary of where the chunk sits in the document) before embedding.
- Tune chunk size per corpus with retrieval evals, not defaults. Common production sizes are 256 to 1024 tokens with 10 to 20 percent overlap.

## Run It

```bash
cd build-from-scratch/chunker
python3 chunker.py
```

Runs in under a second. Prints boundary-quality metrics for all three strategies and asserts that the structure-aware strategies beat fixed-size on broken boundaries, that no strategy drops content, and that no heading is orphaned by the recursive splitter.

## Exercises

1. Change the fixed-size budget to 200 and 800 characters and observe how the boundary-quality metrics move. Explain why broken boundaries per chunk stay roughly constant while broken boundaries per document do not.
2. Add a fourth metric: count chunks whose text spans two different H2 sections. Which strategy is worst?
3. Extend `split_sentences` to handle abbreviations like "e.g." and "Dr." without ending a sentence. Add a test document that breaks the current regex first.
4. Add code-block awareness: a fenced code block must never be split, even if it exceeds the budget. Decide what to do when a block alone is oversized and document the decision.
5. Implement chunk metadata: return `(text, section_path)` tuples where `section_path` is like `["Payments Service Runbook", "Common Alerts", "RefundBacklog"]`, and remove heading propagation from the text itself. Discuss what this changes for lexical versus vector retrieval.

## Further Reading

- [LangChain text splitters documentation](https://python.langchain.com/docs/concepts/text_splitters/) - the reference implementation of recursive character splitting that this module reimplements minimally.
- [Anthropic: Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) - production evidence that adding document context to chunks before embedding cuts retrieval failure rates.
- [Pinecone: Chunking Strategies](https://www.pinecone.io/learn/chunking-strategies/) - a practitioner survey of chunk-size tradeoffs with concrete retrieval effects.
