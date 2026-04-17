# Full-Funnel Talent Intelligence System

## Architecture and End-to-End Workflow

## Overview

The Full-Funnel Talent Intelligence System is an agentic, multi-stage hiring pipeline designed to move beyond traditional Applicant Tracking Systems (ATS). Instead of relying on static keyword filtering, the system performs multi-modal claim verification, adaptive interviewing, and AI-driven evaluation while preserving Human-In-The-Loop (HITL) decision control.

The system is built as a stateful workflow, where each stage generates structured outputs that directly inform and improve the next stage.

## System Architecture

### 1. Core Architectural Layers

#### Input Layer

- Recruiter inputs (Job Description)
- Candidate inputs (Resume, audio responses)

#### Processing and Intelligence Layer

- LLM orchestration (Claude API)
- Resume parsing and structuring
- External verification APIs (for example, GitHub)
- Real-time transcription (Whisper API)
- Adaptive interview engine

#### Data Flow Layer (State Management)

- Structured JSON schema passed across stages
- Context persistence (skills, gaps, verification flags)
- Candidate profile continuously enriched

#### Evaluation and Decision Layer

- Transcript analysis
- Skill scoring and competency mapping
- Bias detection module
- AI recommendation engine

#### Presentation and Control Layer

- Unified recruiter dashboard
- Offer generation engine
- Human override controls (HITL)

## End-to-End Workflow (6 Stages)

### Stage 1: Inclusive JD Builder

#### Objective

Transform raw recruiter input into a structured, bias-aware job description.

#### Process

- Recruiter provides role title and requirements
- LLM processes and restructures content

#### Technology

- Claude API

#### Output

- Structured Job Description:
  - Required Skills
  - Nice-to-Have Skills
- Bias-scanned, inclusive language
- Standardized format for downstream processing

### Stage 2: Resume Screening and Modular Claim Verification (Core Differentiator)

#### Objective

Validate candidate claims before advancing to deeper evaluation.

#### Process

1. Resume ingestion and text extraction
2. Initial keyword filtering (lightweight screening)
3. Skill mapping against JD
4. Activation of role-specific verification plugins

#### Technology

- `pdfplumber` (text extraction)
- Claude API (semantic matching)
- External APIs (for example, GitHub)

#### Verification Logic

- Cross-check claimed skills against real-world evidence
- Example:
  - "Docker" -> check GitHub repositories for usage

#### Output (Standardized JSON Schema)

```json
{
  "matched_skills": [],
  "missing_skills": [],
  "claimed_not_found": [],
  "verification_sources": {}
}
```

#### Key Innovation

- Moves from self-reported skills to evidence-backed skills
- Flags inconsistencies early in the pipeline

### Stage 3: Adaptive AI Interview

#### Objective

Dynamically evaluate candidate skills through contextual questioning.

#### Process

- Candidate enters live conversational interface
- AI interviewer accesses Stage 2 outputs
- Questions adapt in real time based on:
  - Verified skills
  - Missing skills
  - Unverified claims

#### Example Behavior

- If "Docker" is unverified:
  - AI asks candidate to explain containerization workflow

#### Technology

- Claude API (streaming responses)

#### Output

- Context-aware interview dialogue
- Targeted probing of weak or unverified areas

### Stage 4: Real-Time Transcription

#### Objective

Enable natural, low-latency voice interaction.

#### Process

- Audio captured in browser
- Streamed in chunks to backend
- Transcribed and returned in real time

#### Technology

- Browser MediaRecorder API
- WebSockets
- FastAPI backend
- Whisper API

#### Output

- Live transcript stream
- Text synchronized with conversation

### Stage 5: Transcript Analysis and Bias Auditing

#### Objective

Generate a structured, fair, and explainable evaluation.

#### Process

- Combine:
  - Full interview transcript
  - Original JD
  - Verification data (Stage 2)
- Analyze candidate responses against required competencies
- Audit AI-generated questions for bias

#### Technology

- Claude API (large context window)

#### Output

- Structured evaluation report:
  - Competency scores
  - Strengths and weaknesses
  - Skill gap analysis
- Bias audit report:
  - Flags potential bias patterns
  - Supports fairness compliance

#### Key Value

- Ensures responsible AI usage
- Provides transparent reasoning

### Stage 6: Offer Engine and Human Override (HITL)

#### Objective

Deliver actionable hiring decisions with human control.

#### Process

- Aggregate outputs from all prior stages
- Generate final recommendation
- Present insights in a unified dashboard

#### Technology

- Claude API (decision and content generation)
- `html2pdf.js` (offer generation)

#### Dashboard Includes

- AI Match Score
- Verified vs Unverified Skills
- Interview Insights
- Bias Audit Results

#### AI Outputs

- Hire / No-Hire recommendation
- Personalized onboarding plan
- Auto-generated offer letter

#### Human-in-the-Loop Control

- Recruiter makes final decision via:
  - Approve AI recommendation
  - Override AI decision

## Key System Innovations

### 1. Claim Verification Layer

- Detects discrepancies between resume claims and real-world evidence
- Reduces false positives in hiring

### 2. Adaptive Interview Engine

- Moves from static to dynamic evaluation
- Focuses on candidate-specific gaps

### 3. Continuous Context Flow

- Each stage enriches candidate profile
- Eliminates redundant evaluation

### 4. Bias-Aware AI

- Built-in auditing for fairness
- Encourages ethical hiring practices

### 5. Human-in-the-Loop Governance

- AI assists, humans decide
- Maintains accountability and trust

## Summary

This system redefines hiring by shifting from:

- Keyword filtering to evidence-based validation
- Static interviews to adaptive evaluation
- Black-box AI to explainable decision-making

The result is a scalable, fair, and intelligence-driven hiring pipeline that improves recruiter efficiency and candidate quality while keeping humans in control of final decisions.

## Optional Next Deliverables

- Clean architecture diagram (boxes and arrows for slides)
- Compressed 1-minute pitch script for judges
