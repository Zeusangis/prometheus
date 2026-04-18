# AI Talent Intelligence System

## Overview

This project is a full-funnel AI-powered talent evaluation system that goes beyond traditional Applicant Tracking Systems (ATS).

Instead of relying on resumes and keyword matching, it builds a multi-stage verification pipeline that evaluates candidates using:

- real code evidence
- AI interviews
- dynamic skill validation
- human-in-the-loop decision making

The system ensures that hiring decisions are based on verified ability, not self-reported claims.

## System Architecture (6 Stages)

### Stage 1: Intelligent Job Description Builder

- Input: raw job title + requirements
- Output: structured, bias-reduced job description
- Removes exclusionary language and organizes skills into required vs optional

### Stage 2: Resume Screening + GitHub Skill Verification

This is the core differentiation layer.

#### Resume Processing

- Extracts skills from uploaded resume
- Matches against job description

#### GitHub Intelligence Module

The system analyzes a candidate's public GitHub profile using the GitHub API.

It:

- Fetches repositories and languages used
- Analyzes code distribution across projects
- Aggregates evidence of technical skills
- Builds a confidence-based skill profile

#### Output

```json
{
  "skills": {
    "python": {
      "confidence": 0.85,
      "evidence": ["api-service", "ml-project"]
    },
    "docker": {
      "confidence": 0.6,
      "evidence": ["deployment-tool"]
    }
  },
  "developer_level": "intermediate"
}
```

This ensures that claimed skills are backed by real coding evidence, not just resume text.

### Stage 3: Adaptive AI Interview Engine

- AI conducts live interview using Claude API
- Questions adapt based on resume + GitHub findings
- Weak or unverified skills are probed further in real-time

### Stage 4: Real-Time Transcription System

- Browser-based audio capture
- WebSocket streaming backend
- Whisper API for low-latency transcription

### Stage 5: Transcript Analysis + Bias Audit

- Evaluates candidate responses
- Scores communication + technical depth
- Detects interviewer bias in questioning patterns

### Stage 6: Offer Engine + Human Override (HITL)

- Generates hiring recommendation
- Creates offer letter + onboarding plan
- Recruiter has final override control

## Key Innovation

Unlike traditional hiring systems, this platform replaces assumptions with verified engineering signals.

It combines:

- Resume claims
- Real GitHub code evidence
- Adaptive AI interviews
- Structured evaluation scoring

## Tech Stack

- Python (Flask backend)
- GitHub API integration
- Claude API (LLM reasoning layer)
- Whisper API (speech-to-text)
- WebSockets (real-time streaming)
- pdfplumber (resume parsing)

## GitHub Intelligence Module (Core Feature)

This subsystem analyzes a candidate's GitHub activity to infer:

- Programming languages used
- Skill strength based on real repository usage
- Engineering maturity level
- Evidence-backed skill validation

It transforms raw GitHub data into a structured skill confidence model, forming the foundation of technical verification in the pipeline.

## Why This Project Matters

Traditional ATS systems:

- rely on keywords
- miss real skill depth
- are easily gamed

This system:

- verifies actual code contributions
- adapts interviews dynamically
- reduces hiring bias
- improves signal quality in recruitment

## Future Enhancements

- Code architecture analysis (AST-based deep review)
- Continuous skill tracking post-hire
- Team composition optimization engine
- Career path recommendation system

## Summary

This is not just a hiring tool.

It is a multi-stage AI talent intelligence system that verifies, evaluates, and predicts engineering capability using real-world data.
