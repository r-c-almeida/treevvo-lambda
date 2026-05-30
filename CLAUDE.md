# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Python AWS Lambda service that generates AI travel itineraries (roteiros de viagem) using OpenAI, triggered by SQS messages. The codebase is in Brazilian Portuguese.

## Commands

```bash
# Run handler locally with the sample SQS event (events/sample-sqs-event.json)
python scripts/run_lambda_sample_event.py

# Poll the real SQS queue locally (requires AWS credentials)
python scripts/poll_sqs_local.py
python scripts/poll_sqs_local.py --once   # single batch then exit

# Build the Lambda deployment ZIP (x86_64, Python 3.14 by default)
python scripts/build_lambda_zip.py

# ARM64 (Graviton) / Python 3.12 variants
python scripts/build_lambda_zip.py --platform manylinux2014_aarch64
python scripts/build_lambda_zip.py --python-version 312
```

Artifact lands in `dist/treevvo-lambda.zip`. There is no test suite.

## Environment

Copy `.env.example` to `.env`. Required variables:

- `LLM_PROVIDER` — `openai` (default) or `claude`; selects which LLM is active
- `OPENAI_API_KEY` — required when `LLM_PROVIDER=openai`
- `ANTHROPIC_API_KEY` — required when `LLM_PROVIDER=claude`
- `S3_TRIP_PROFILE_BUCKET` — if blank, S3 persistence is silently skipped
- `SQS_GENERATE_TRIP_QUEUE_URL` / `AWS_DEFAULT_REGION` — for local SQS polling
- `TRANSCRIPTS_ROOT` — root folder containing subfolders with `transcricao*.txt` files (defaults to repo root / Lambda package root)
- `LOG_LEVEL` / `LOG_MAX_CHARS` — logging control

In Lambda, `AWS_REGION` is set automatically; never set `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` there (use the execution role).

## Architecture

### Request flow

```
SQS message
  → lambda_function.lambda_handler
  → sqs_generate_worker.handle_sqs_lambda_event   # batch loop, returns batchItemFailures
  → process_message_body → GenerateScriptPayload.from_request_data
  → service_factory.create_generate_script_service()
  → GenerateScriptService.generate()
      → TripProfileS3Service.mark_trip_creation_started()  (status: PENDING → CREATING)
      → Application(base_dir=<folder>).run()
          → TripPipeline.run()   (alias: RouterService)
              attractions → tips → routization → maps → generate_trip
      → TripProfileS3Service.persist_after_generation()   (status: → FINISHED or ERROR)
```

### Agent pipeline (`source/agents/`)

Each agent is a `ServiceBase` subclass. `ServiceBase.__init__` reads the agent's system instructions from `docs/instructions/<name>.txt` and creates an `OpenAIChat` instance backed by `ChatGPTChat`. All agents call `OpenAIChat.chat(prompt)` and return plain text.

Active pipeline order in `TripPipeline.run`:
1. `AttractionsAgent` — tourist attractions
2. `TipsAgent` — travel tips
3. _(HotelAgent is instantiated but commented out of the sequence)_
4. `RoutizationAgent` — day-by-day route plan (receives attractions + tips)
5. `MapsAgent` — map links (receives route plan)
6. `GenerateTripAgent` — final formatted itinerary (receives all prior outputs)

To re-enable hotels, uncomment the relevant lines in `router_service.py` and pass `hotel=hotel_text` to subsequent agents.

### LLM layer (`source/llms/`)

`ChatGPTChat` (in `chatgpt_chat.py`) is the raw OpenAI client. Default model: `gpt-5.4-mini`. SSL verification is **disabled by default** (`DEFAULT_SSL_VERIFY = False`) to handle corporate proxy environments. `OpenAIChat` is a thin façade on top.

**Provider selection** is handled by `llm_factory.create_llm_chat(instruction, *, model=None)`, which reads `LLM_PROVIDER` and returns either `OpenAIChat` or `ClaudeChat`. Both expose the same interface: `chat(user_message, *, response_format="text") -> str`. `ServiceBase` always calls the factory — no agent touches the provider directly. Default model for Claude: `claude-sonnet-4-6`.

### S3 profile schema (`source/cloud/aws/s3.py`)

Each user has `<user_prefix>/profile.json` with a `trips` array. Each trip entry is identified by its `id` field (UUID). The **producer** must create the entry with `status: PENDING` before enqueuing; the Lambda only updates the existing entry — it never inserts a new one. Trip lifecycle: `PENDING → CREATING → FINISHED | ERROR`.

Generated itinerary files land at `<user_prefix>/trips/<filename>.json` and must be valid JSON (the pipeline is expected to return JSON text from the final agent).

### Transcript files

Each folder payload field maps to a subfolder under `TRANSCRIPTS_ROOT`. Inside that subfolder, files matching `transcricao*.txt` are read and concatenated into a single block passed to all agents. The pipeline continues without error if no files are found (only a log warning is emitted).

### Deploy package

`scripts/build_lambda_zip.py` installs `requirements.txt` as manylinux wheels (no Docker needed), then copies `lambda_function.py`, `application.py`, `source/`, and `docs/` into `dist/treevvo-lambda.zip`. Lambda handler entry point: `lambda_function.lambda_handler`. Enable **Report batch item failures** on the SQS event source mapping.
