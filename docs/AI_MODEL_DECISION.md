# AI Model Decision: Gemini vs Bedrock

## Current Stack (March 2026)

| Agent | Model/Service |
|-------|--------------|
| Storyteller | Gemini 2.0 Flash (gemini-2.0-flash-exp) |
| Avatar | Gemini 2.0 Flash (vision) |
| Visual (scenes) | Imagen 3.0 via Vertex AI |
| Voice | Google Cloud Text-to-Speech |
| Memory | ChromaDB (local vector store) |

## Why We Chose Gemini

- Fast and cheap per token — critical for real-time interactive storytelling
- Native multimodal input (image + text in one call) for camera/emotion pipeline
- Google Cloud TTS has expressive, child-friendly voice options
- Already integrated and working across all 4 agents
- Free tier / low-cost tier suitable for MVP stage

## Amazon Bedrock — Pros

- Model diversity: Claude, Llama, Mistral, Titan, Stable Diffusion under one API
- Claude (Anthropic) may produce higher quality creative writing
- Bedrock Guardrails for built-in child safety content filtering
- Single-cloud simplicity if deploying on AWS (ECS, Lambda)
- Stable Diffusion / Titan Image for scene generation without Vertex AI
- Easy model swapping without infrastructure changes

## Amazon Bedrock — Cons

- Requires rewriting all 4 agents (storyteller, avatar, visual, voice)
- Gemini Flash is faster and cheaper per token at comparable quality
- AWS Polly has fewer expressive/child-friendly voice options than Google TTS
- Bedrock multimodal support varies by model — less unified than Gemini
- No free tier — cost increase at MVP stage
- Managed vector search (OpenSearch Serverless) adds complexity vs local ChromaDB

## Decision

**Stay with Gemini for MVP.** The rewrite cost is not justified at this stage.

## When to Reconsider

- Content safety requirements demand Bedrock Guardrails
- Need to A/B test different models for story quality
- Deploying to AWS and want single-cloud architecture
- Gemini creative writing quality doesn't meet the bar
- Scaling beyond MVP where model flexibility matters

## Migration Path

The agent architecture is modular — each agent (storyteller, avatar, visual, voice) has an isolated model client. Switching to Bedrock would mean swapping the client inside each agent without touching the orchestrator, WebSocket layer, or frontend.
