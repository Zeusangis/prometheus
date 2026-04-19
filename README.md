# Prometheus

AI-powered technical recruiting — screen candidates smarter, not harder.

## Problem

Technical recruiting is broken. Recruiters can't evaluate code, so they rely on resumes that are easy to fake. Candidates list skills they don't have, and engineers waste hours in interviews with people who aren't qualified. There's no fast, objective way to know if someone can actually do the job.

## Solution

Prometheus gives recruiters an AI-powered pipeline that automatically verifies a candidate's technical ability before any human time is spent. It scrapes their GitHub profile, analyses their actual code against the job requirements, and then conducts an AI interview that digs into their real understanding of their own work.

## How it works

1. Recruiter creates a job posting and configures what to look for — languages, code quality metrics, interview tone, and custom questions
2. Candidate receives a link (via LinkedIn, email, etc.) and fills out a simple application form with their resume and GitHub username
3. Prometheus scrapes their GitHub and scores them across metrics like language match, code quality, security practices, and test coverage
4. The AI interviewer conducts a personalised interview based on their actual GitHub projects, asking them to explain their own code and decisions
5. Recruiter sees a full dashboard with scores, GitHub analysis, and the complete interview transcript for every candidate

## Key features

- **GitHub scraper** — analyses real code against configurable metrics with weighted scoring
- **AI interviewer** — conducts personalised interviews based on each candidate's actual GitHub profile
- **Job creation wizard** — 4-step setup for job details, scraper config, interview setup, and review
- **Recruiter dashboard** — overview of all jobs, applicant counts, and score distributions
- **Candidate detail page** — full breakdown of scores, GitHub analysis summary, and interview transcript
- **Applicant-facing flow** — clean application form and AI interview interface via shareable link

## AI usage

- **GitHub analysis** — AI reads and evaluates the candidate's repositories, assessing code quality, security practices, and how well their skills match the job requirements
- **AI interviewer** — conducts the interview dynamically, asking follow-up questions based on the candidate's GitHub profile and probing deeper when answers need clarification
- **Interview summary** — AI generates a written assessment of the candidate after the interview completes

## Tech stack

**Frontend** — React, Vite, TanStack Router, TanStack Query, Tailwind CSS, Recharts

**Backend** — Python, Flask (or FastAPI)

## Running locally

### Frontend
```bash
cd client
npm install
npm run dev
```

### Backend
```bash
cd server
pip install -r requirements.txt
python app.py
```

### Environment variables
Create a `.env` file inside the `client/` folder:
