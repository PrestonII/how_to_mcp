# How To: BIMIT Module 6 — Plan Generation

> **Audience:** New engineers onboarding to the BIMIT Engine platform
> **Module:** Module 6 (Plan Generation)
> **Prerequisites:** Familiarity with Node.js, TypeScript, and REST APIs
> **Last Updated:** February 2026

---

## Overview

Module 6 generates PDF reports by taking floor plan assets produced by Module 5 and placing them onto formatted Airtable-linked sheets. This guide walks you through the architecture, local development setup, and the API testing workflow.

> **Note:** This guide was created from the onboarding session recording on Feb 18, 2026.
> Screenshots are extracted from that session at the relevant moments.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Codebase Structure](#2-codebase-structure)
3. [Airtable Integration](#3-airtable-integration)
4. [Local Development Setup](#4-local-development-setup)
5. [API Testing with Postman](#5-api-testing-with-postman)
6. [Environment Configuration](#6-environment-configuration)
7. [Module 5 Code Reference](#7-module-5-code-reference)
8. [Next Steps](#8-next-steps)

---

## 1. Architecture Overview

Module 6 sits at the end of the BIMIT scan-to-BIM pipeline. Understanding where it fits within the broader system is essential before diving into the code.

### 1.1 System Architecture — Server and Plugin Relationship

> 📸 **[Screenshot placeholder: Figma: server-plugin architecture overview]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

The BIMIT Engine is divided into two primary components:

- **Server** — A Node.js/TypeScript API that orchestrates processing jobs
- **Plugin** — A Revit/desktop plugin that triggers server jobs and receives results

When a user initiates plan generation from the plugin, the following sequence occurs:
1. Plugin sends an API request to the server's `area_plan_create` endpoint
2. Server fetches required assets from Module 5 (stored in Airtable/S3)
3. Server generates the PDF report
4. Server writes results back to Airtable and returns a response

### 1.2 Data Flow Between Modules

> 📸 **[Screenshot placeholder: Data flow: Module 4 → 5 → 6]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

| Module | Purpose | Output Used By |
|--------|---------|----------------|
| Module 4 | Scan processing / point cloud | Module 5 |
| Module 5 | Asset generation (walls, rooms, doors) | Module 6 |
| **Module 6** | **Plan generation → PDF** | End user / Airtable |

### 1.3 API Call Sequence

> 📸 **[Screenshot placeholder: API call sequence diagram]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

The key API endpoint for Module 6 is:

```
POST /area_plan_create
```

This endpoint accepts a job configuration payload, retrieves Module 5 assets, and orchestrates the PDF generation pipeline.

> 📸 **[Screenshot placeholder: Module dependency relationships]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

> **Important:** Module 6 is dependent on Module 5's assets being fully processed and stored in Airtable before a plan generation job is triggered. Always verify Module 5 status before debugging Module 6 failures.

> 📸 **[Screenshot placeholder: Architecture summary: Plugin triggers server flow]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

---

## 2. Codebase Structure

### 2.1 Directory Layout

> 📸 **[Screenshot placeholder: File navigation: Module 6 directory structure]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

The Module 6 repository follows a standard Express/TypeScript structure:

```
module-6/
├── src/
│   ├── routes/
│   │   └── area_plan_create.ts   ← Main endpoint handler
│   ├── services/
│   │   ├── airtable.ts           ← Airtable API client
│   │   ├── s3.ts                 ← AWS S3 client
│   │   └── pdf_generator.ts      ← PDF generation logic
│   ├── types/
│   │   └── index.ts              ← Shared TypeScript types
│   └── index.ts                  ← Express app entry point
├── .env.sample                   ← Environment variable template
├── package.json
└── tsconfig.json
```

### 2.2 The `area_plan_create` Route

> 📸 **[Screenshot placeholder: Route definition: area_plan_create]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

The main entry point for plan generation is defined in `src/routes/area_plan_create.ts`. This route:

1. Validates the incoming request payload
2. Looks up the project run in Airtable
3. Fetches assets from S3 (linked from Module 5)
4. Invokes the PDF generation service
5. Uploads the output PDF to S3
6. Updates the Airtable record with the result URL

### 2.3 Module Organization

> 📸 **[Screenshot placeholder: Module organization overview]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

> 📸 **[Screenshot placeholder: Code entry point for plan generation]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

> **Note:** Module 6's codebase is less polished than Module 5. When you see patterns that seem inconsistent or underdocumented, refer to Module 5 as the reference implementation (see [Section 7](#7-module-5-code-reference)).

---

## 3. Airtable Integration

Airtable serves as the primary database for tracking project runs, linking assets, and storing output results. You will interact with it frequently during development and debugging.

### 3.1 Project Runs Table

> 📸 **[Screenshot placeholder: Airtable: Project Runs table]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

The **Project Runs** table tracks each execution of the pipeline. Key fields include:

| Field | Type | Description |
|-------|------|-------------|
| `Run ID` | Auto-number | Unique identifier for the run |
| `Status` | Single select | Current state of the run |
| `Module 5 Record` | Linked record | Reference to Module 5 output |
| `Output PDF URL` | URL | S3 link to generated PDF |
| `Error Message` | Long text | Populated on failure |
| `Created At` | Date | Timestamp of run creation |

**Status values:**
- `pending` — Job queued, not yet started
- `processing` — Currently running
- `complete` — Successfully finished
- `failed` — Encountered an error

### 3.2 Asset Storage and S3 Linking

> 📸 **[Screenshot placeholder: Airtable: Asset storage and S3 linking]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

Module 5 assets are stored in AWS S3 and linked back to Airtable records. To fetch an asset:

1. Look up the Module 5 Airtable record ID (from the Project Run)
2. Read the `Asset URL` field — this is a pre-signed or public S3 URL
3. Download the asset from S3 before processing

> 📸 **[Screenshot placeholder: Airtable: Status field and tracking]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

### 3.3 Linked Records

> 📸 **[Screenshot placeholder: Airtable: Linked record relationships]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

The Project Runs table links to several other tables:

- **Projects** — Top-level project metadata
- **Module 5 Outputs** — Asset records from the previous stage
- **Users** — Who initiated the run

Always query by the linked record IDs — not by display names — to avoid issues with name changes.

---

## 4. Local Development Setup

### 4.1 Prerequisites

Before starting, ensure you have:

- **Node.js** v18 or higher
- **npm** v9 or higher
- **Git Bash** (on Windows — do not use PowerShell; see note below)
- **VS Code** (recommended editor)
- A `.env` file with the required variables (see [Section 6](#6-environment-configuration))

> **Terminal Warning — Windows Users:** Do **not** use PowerShell for npm commands. The build scripts rely on Unix-style shell syntax. Use **Git Bash** or **WSL** instead.
>
> > 📸 **[Screenshot placeholder: PowerShell vs Git Bash — use Git Bash]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

### 4.2 Running Tests

> 📸 **[Screenshot placeholder: Terminal: npm run test]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

Before making changes, run the test suite to confirm the baseline passes:

```bash
npm run test
```

Expected output:
```
> module-6@1.0.0 test
> jest

PASS src/routes/area_plan_create.test.ts
PASS src/services/pdf_generator.test.ts

Test Suites: 2 passed, 2 total
Tests:       12 passed, 12 total
```

If tests fail before you've made any changes, check your `.env` configuration (Section 6).

### 4.3 Starting the Local Development Server

> 📸 **[Screenshot placeholder: Terminal: npm run dev]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

To run the server locally:

```bash
npm run dev
```

The server starts on **port 3000** by default (configurable via `PORT` in `.env`).

> 📸 **[Screenshot placeholder: Terminal: successful server startup]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

You should see:
```
[nodemon] starting `ts-node src/index.ts`
Server running on http://localhost:3000
Connected to Airtable ✓
```

### 4.4 VS Code Setup

> 📸 **[Screenshot placeholder: VS Code: recommended settings]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

Recommended VS Code extensions for this project:

- **ESLint** — Linting
- **Prettier** — Code formatting
- **REST Client** — Test endpoints without Postman
- **Airtable** — Browse linked records

Add the following to `.vscode/settings.json`:
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "typescript.tsdk": "node_modules/typescript/lib"
}
```

---

## 5. API Testing with Postman

Once the local server is running (`npm run dev`), use Postman to test the `area_plan_create` endpoint.

### 5.1 Configuring the Local Endpoint

> 📸 **[Screenshot placeholder: Postman: local endpoint configuration]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

Create a new POST request in Postman:

| Setting | Value |
|---------|-------|
| Method | `POST` |
| URL | `http://localhost:3000/area_plan_create` |
| Content-Type | `application/json` |
| Authorization | `Bearer <your_api_key>` |

### 5.2 Request Body Structure

> 📸 **[Screenshot placeholder: Postman: request body]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

The request body follows this structure:

```json
{
  "project_run_id": "recXXXXXXXXXXXXXX",
  "project_id": "recYYYYYYYYYYYYYY",
  "output_format": "pdf",
  "options": {
    "sheet_size": "A1",
    "include_legend": true,
    "scale": "1:100"
  }
}
```

**Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `project_run_id` | ✅ | Airtable record ID from Project Runs table |
| `project_id` | ✅ | Airtable record ID from Projects table |
| `output_format` | ✅ | Always `"pdf"` for Module 6 |
| `options` | ❌ | Optional rendering configuration |

### 5.3 Successful Response

> 📸 **[Screenshot placeholder: Postman: successful API response]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

On success, the endpoint returns:

```json
{
  "status": "complete",
  "pdf_url": "https://s3.amazonaws.com/bimit-outputs/runs/recXXX/plan.pdf",
  "airtable_record_id": "recXXXXXXXXXXXXXX",
  "processing_time_ms": 4521
}
```

### 5.4 Error Debugging

> 📸 **[Screenshot placeholder: Postman: error response and debugging]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

Common errors and their fixes:

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `401 Unauthorized` | Missing or invalid API key | Check `Authorization` header |
| `404 Not Found` | Invalid Airtable record ID | Verify IDs in Airtable directly |
| `500 Module5AssetNotFound` | Module 5 not completed | Check Module 5 Airtable status |
| `500 S3DownloadError` | Bad AWS credentials | Verify `.env` AWS keys |
| `ECONNREFUSED` | Server not running | Run `npm run dev` first |

> **Tip:** When you see a `500` error, check the terminal running `npm run dev` — it logs detailed stack traces that Postman won't show.

---

## 6. Environment Configuration

### 6.1 Setting Up Your `.env` File

> 📸 **[Screenshot placeholder: .env file: required variables]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

Copy the sample file and fill in your values:

```bash
cp .env.sample .env
```

Then edit `.env` with your credentials.

### 6.2 `.env.sample` vs `.env.example`

> 📸 **[Screenshot placeholder: Comparison: .env.sample vs .env.example]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

> **Important:** This repo uses `.env.sample` (not `.env.example`). Some internal references may say `.env.example` — they mean the same thing here. Always copy `.env.sample`.

### 6.3 Required Environment Variables

> 📸 **[Screenshot placeholder: .env: AWS S3 configuration]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

```bash
# Server
PORT=3000
NODE_ENV=development

# Airtable
AIRTABLE_API_KEY=your_airtable_personal_access_token
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX

# AWS S3
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=bimit-outputs

# Module 5 API (for fetching upstream assets)
MODULE5_API_URL=http://localhost:3001
MODULE5_API_KEY=your_module5_api_key
```

**Where to get each value:**

| Variable | Source |
|----------|--------|
| `AIRTABLE_API_KEY` | Airtable → Account → Personal Access Tokens |
| `AIRTABLE_BASE_ID` | From the Airtable base URL: `airtable.com/<BASE_ID>/...` |
| `AWS_ACCESS_KEY_ID` / `SECRET` | AWS IAM Console — ask a team lead for the dev credentials |
| `S3_BUCKET_NAME` | Check with team lead — dev bucket differs from production |
| `MODULE5_API_KEY` | Set in Module 5's `.env` and shared via 1Password |

---

## 7. Module 5 Code Reference

Module 5 is a better-maintained codebase and serves as the reference implementation for coding patterns in the BIMIT Engine.

### 7.1 Module 5 Directory Structure

> 📸 **[Screenshot placeholder: Module 5: directory structure]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

When writing new code in Module 6, use Module 5 as a template. Key differences:

| Aspect | Module 6 (current) | Module 5 (reference) |
|--------|-------------------|----------------------|
| Documentation | Sparse | Comprehensive JSDoc |
| Error handling | Basic try/catch | Typed error classes |
| Test coverage | ~40% | ~85% |
| Code organization | Monolithic | Modular services |

### 7.2 Inline Documentation Style

> 📸 **[Screenshot placeholder: Module 5: documentation style]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

Module 5 uses JSDoc for all exported functions. Follow this pattern in Module 6:

```typescript
/**
 * Fetch assets for a given project run from Module 5.
 *
 * @param projectRunId - Airtable record ID of the project run
 * @param options - Optional fetch configuration
 * @returns Array of asset objects with S3 URLs
 * @throws {AssetNotFoundError} When the run has no associated assets
 */
export async function fetchModule5Assets(
  projectRunId: string,
  options?: FetchOptions
): Promise<Asset[]> {
  // implementation
}
```

### 7.3 Modular Architecture Pattern

> 📸 **[Screenshot placeholder: Module 5: modular architecture]**
> *Run `python3 extract_frames.py` with the video file to populate this image.*

Module 5 separates concerns clearly:

- `routes/` — HTTP handlers only (no business logic)
- `services/` — Business logic (testable without HTTP context)
- `repositories/` — Data access (Airtable, S3)
- `types/` — Shared TypeScript interfaces

Apply this pattern when adding new features to Module 6.

---

## 8. Next Steps

After completing this guide, you should be able to:

- [x] Describe where Module 6 fits in the BIMIT pipeline
- [x] Navigate the Module 6 codebase
- [x] Run tests and start the local server
- [x] Test the API with Postman
- [x] Configure your local environment

**Suggested next tasks:**

1. **Run a test job end-to-end** — Get a `project_run_id` from staging Airtable and trigger a full plan generation locally
2. **Read the Module 5 codebase** — Spend 30–60 minutes reading the Module 5 services layer to understand target code quality
3. **Review open tickets** — Check the project board for Module 6 bugs or improvements to pick up
4. **Set up staging environment** — Ask a team lead for staging credentials to test against real data

---

## Appendix: Quick Reference

### Common Commands

```bash
npm run dev          # Start local server with hot reload
npm run build        # Compile TypeScript
npm run test         # Run test suite
npm run test:watch   # Run tests in watch mode
npm run lint         # Check for linting errors
npm run lint:fix     # Auto-fix linting issues
```

### Key Airtable Tables

| Table | Purpose |
|-------|---------|
| Project Runs | Track each plan generation job |
| Projects | Top-level project records |
| Module 5 Outputs | Assets from upstream module |

### Key Files

| File | Purpose |
|------|---------|
| `src/routes/area_plan_create.ts` | Main API endpoint |
| `src/services/pdf_generator.ts` | PDF rendering logic |
| `src/services/airtable.ts` | Airtable client wrapper |
| `.env.sample` | Environment variable template |

---

*This guide was generated from the BIMIT Plan Orientation session (Feb 18, 2026).*
*To regenerate with updated screenshots, run `python3 generate_howto.py` after extracting new frames.*
