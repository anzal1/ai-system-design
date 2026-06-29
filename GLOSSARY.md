# Glossary

Short definitions for terms used across the course.

## Agent

An AI system where a model dynamically chooses steps and tools to complete a task, usually based on feedback from the environment.

## AI Orchestration Layer

The application layer that assembles prompts, manages retrieval, calls models, executes tools, validates outputs, handles fallbacks, and emits traces.

## Context

The information made visible to the model for a request: instructions, user input, retrieved documents, tool results, memory, and product state.

## Eval

A repeatable test that measures some aspect of AI system behavior, such as task success, faithfulness, tool correctness, safety, or format adherence.

## Faithfulness

Whether an answer is supported by the provided evidence.

## Hybrid Search

Retrieval that combines lexical search, such as keyword or BM25, with semantic vector search.

## Indirect Prompt Injection

A prompt injection attack delivered through retrieved content, tool output, web pages, documents, emails, or other external data.

## Model Routing

Choosing which model or execution path should handle a request based on task, risk, latency, cost, data policy, or provider health.

## RAG

Retrieval-augmented generation. A pattern where external knowledge is retrieved at request time and provided to a model as context.

## Reranker

A second-stage relevance model that reorders retrieved candidates before context assembly.

## Tool Gateway

A layer that validates, authorizes, executes, and logs tool calls proposed by a model or agent.

## Workflow

A system where LLM calls and tools are orchestrated through predefined code paths.
