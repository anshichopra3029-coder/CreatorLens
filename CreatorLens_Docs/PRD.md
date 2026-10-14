# CreatorLens — Product Requirements Document (PRD)

**Document status:** Product baseline / planned scope  
**Version:** 1.0  
**Last updated:** 14 October 2026  
**Project type:** Student data-science mini project

> **Status note:** This document describes the intended product. It does not assert that the features have already been implemented. Update the implementation status as development progresses.

## 1. Product Summary

CreatorLens is a web application that helps social media content creators understand historical post performance using data analysis and visualizations. Users will be able to upload a supported CSV dataset, review summary metrics, compare content categories, explore trends, and read insights derived from the data. A later phase may add a machine-learning model that estimates a clearly defined engagement outcome when the available data is sufficient for credible training and evaluation.

The initial product is intended for a mini-project demonstration and will use uploaded datasets rather than requiring direct access to Instagram, YouTube, or other social platforms.

## 2. Problem Statement

Creators can see metrics such as views, likes, comments, shares, and reach, but individual numbers do not always explain broader performance patterns. Comparing many posts manually is time-consuming, and creators may rely on guesswork when deciding what content to publish or how to evaluate engagement.

**Core problem:** How can social media performance data be organized and analyzed so that creators can identify patterns and make better-informed content decisions?

## 3. Proposed Solution

CreatorLens will provide a simple workflow:

1. Upload a supported CSV file of historical post data.
2. Validate, clean, and profile the dataset.
3. Calculate metrics that are supported by the columns present.
4. Visualize trends and compare categories or platforms where those fields exist.
5. Present evidence-based, understandable insights with suitable caveats.
6. Optionally train and evaluate a machine-learning model for a defined engagement target.
7. In a later phase, let users sign in and persist their dataset metadata and analyses securely.

The application must adapt to the dataset's actual schema. It must not imply that a column, analysis, or prediction exists when the uploaded data does not support it.

## 4. Product Goals

- Turn raw post-level data into understandable summaries and visual comparisons.
- Reduce the effort required to inspect and compare content performance.
- Make the analysis process transparent: users should know which data and metric produced a chart or insight.
- Demonstrate practical use of Python, data cleaning, exploratory data analysis (EDA), visualization, and optionally supervised machine learning.
- Provide a maintainable foundation that can later support authentication and persistent user-specific records.

## 5. Non-Goals

The first release will not:

- Connect directly to social-platform APIs or scrape social platforms.
- Publish or schedule posts.
- Guarantee growth, virality, or improved engagement.
- Infer causation from simple correlations.
- Claim to know a creator's real audience demographics unless the dataset contains valid demographic fields.
- Require subscriptions, payment processing, team workspaces, or enterprise analytics.
- Use generated or fabricated metrics as if they came from a real creator's dataset.

## 6. Target Users

### Primary user
A small or early-stage social media creator who has exported or otherwise obtained a CSV containing historical post metrics and wants to understand performance without writing analysis code.

### Secondary user
A student, analyst, or project evaluator reviewing a data-science workflow from data ingestion through analysis and visualization.

## 7. Main User Journey

1. The user opens the landing page and understands what CreatorLens does.
2. The user navigates to the dashboard or uploads a CSV.
3. The system validates the file and reports whether the available columns support analysis.
4. The user views summary metrics, charts, and a table of posts.
5. The user filters the results by available dimensions such as platform, content type, or date.
6. The user reviews insights with clear explanations and caveats.
7. If a validated model is available, the user may use the prediction page; otherwise, the page explains that predictions are not available yet.
8. In the later authenticated release, the user signs in and can access only their own saved dataset records and analyses.

## 8. Functional Requirements

Priority definitions: **P0** = required for the first usable release; **P1** = next phase; **P2** = optional enhancement.

| ID | Requirement | Priority | Acceptance condition |
|---|---|---:|---|
| FR-01 | Provide a landing page that explains CreatorLens and links to the application sections. | P0 | Navigation and calls to action work on desktop and mobile. |
| FR-02 | Provide a dashboard layout with KPI cards, charts, and a recent-posts table. | P0 | Components render with clearly labelled demo data before a real dataset is loaded; demo data is marked as such. |
| FR-03 | Accept CSV uploads and validate file type, size, parseability, and basic tabular structure. | P0 | Invalid files receive a useful error; valid files return row and column metadata. |
| FR-04 | Use a reusable frontend API client to communicate with FastAPI. | P0 | API base URL is configured through an environment variable; network errors are visible to users. |
| FR-05 | Expose a health endpoint and initial dashboard endpoints. | P0 | Endpoints return documented response shapes and sensible error codes. |
| FR-06 | Clean and profile uploaded datasets. | P1 | Missing values, duplicate records, date parsing, numeric types, and invalid metric values are handled or reported explicitly. |
| FR-07 | Calculate engagement metrics only when their required columns are available. | P1 | Metric name, numerator, denominator, and interpretation are documented in the UI or docs. |
| FR-08 | Compare available content categories, platforms, and time periods. | P1 | Filters only use dimensions that exist in the dataset; empty results are handled. |
| FR-09 | Display data-backed insights. | P1 | Every insight can be traced to a computed statistic or analysis and is not presented as causal proof. |
| FR-10 | Provide a prediction page. | P0 shell / P2 model | The shell explains that no trained model is available until one passes evaluation. Predictions are never fabricated. |
| FR-11 | Implement and evaluate an ML model if the dataset supports a meaningful target. | P2 | Uses a justified target, train/test separation, baseline comparison, appropriate metrics, and leakage checks. |
| FR-12 | Add sign-up, sign-in, sign-out, and profile controls through Clerk. | P1 | Authentication works with configured Clerk credentials and protected pages/API routes enforce access. |
| FR-13 | Persist user-owned dataset metadata and analysis records in PostgreSQL. | P1 | Records survive application restarts and each user can access only their own records. |
| FR-14 | Provide error, loading, empty, and success states across data-related pages. | P0 | These states are visible and do not leave the page stuck or misleading. |
| FR-15 | Provide project setup and usage documentation. | P0 | A new developer can configure the environment and start both applications using the README. |

## 9. Planned Pages

- **Landing (`/`)** — product overview, core value proposition, features, workflow, navigation.
- **Dashboard (`/dashboard`)** — KPI cards, trends, category comparison, recent posts.
- **Upload (`/upload`)** — CSV upload, validation response, preview, remove/re-upload flow.
- **Analytics (`/analytics`)** — filters, comparison charts, time trends, summary metrics.
- **Insights (`/insights`)** — computed observations, methodology/context, limitations.
- **Predictions (`/predictions`)** — model status and eventual prediction interface.
- **Settings (`/settings`)** — future profile and dataset preferences.

The Predictions and Settings pages may initially be informative placeholders. A placeholder must not pretend that the future capability is operational.

## 10. Metric Definitions and Data Integrity

Metrics depend on the columns available in a user's dataset. Do not assume every dataset has views, reach, impressions, likes, comments, shares, or follower counts.

When the necessary fields are present, a possible definition is:

`view_based_engagement_rate = (likes + comments + shares) / views * 100`

This is only one possible metric. A reach-based rate has a different denominator and must be labelled separately. Do not compare rates calculated with different denominators without explanation. Handle zero denominators safely and state whether missing engagement components were excluded or treated as zero.

For analysis:

- Distinguish missing values from real zeros.
- Avoid counting repeated snapshots of a post as independent posts without first resolving the data semantics.
- Clearly label sample data and illustrative insights.
- Do not infer that a variable caused performance merely because the variables are correlated.
- For predictive modelling, keep information that would not be known at prediction time out of the features.

## 11. Non-Functional Requirements

- **Usability:** Simple navigation, readable charts, clear terminology, helpful validation messages.
- **Responsive design:** Desktop-first analytics layout that remains usable on tablet and mobile.
- **Maintainability:** Reusable React components, typed API contracts, modular backend services, and documented setup.
- **Reliability:** Predictable API responses, input validation, controlled error handling, and tests for core data processing.
- **Security:** No secrets in source control; validate uploads; protect authenticated resources; enforce user ownership in the backend.
- **Transparency:** Clearly distinguish demo data, computed findings, and model-generated estimates.
- **Performance:** Handle the selected mini-project dataset without freezing the UI; large-file limits must be configurable and documented.

## 12. Success Criteria

The first demonstrable release is successful when:

1. Frontend and backend can be started locally using the documented steps.
2. All navigation routes load and display coherent states.
3. The frontend can retrieve dashboard data from the backend.
4. A valid CSV receives a useful validation/preview response, and invalid files are rejected gracefully.
5. The real data pipeline (P1) creates reproducible summaries and charts from a supported dataset.
6. Insights are based on actual computations, not static claims.
7. If ML is included, its evaluation results and limitations are reported.
8. In the authenticated release, a user cannot read or modify another user's records by changing an ID in a request.

## 13. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Dataset lacks expected columns | Profile the file first and enable only supported analyses. |
| Dataset is too small or unsuitable for ML | Deliver EDA and visual analytics; omit ML or clearly mark it as experimental. |
| Engagement definitions vary by platform | Document formulas and avoid misleading comparisons. |
| Uploads contain malformed or oversized data | Configure limits, validate structure, return clear errors. |
| UI suggests insights that are not evidence-based | Derive insights from computed statistics and include context. |
| Authentication is implemented only on the frontend | Verify Clerk identity in FastAPI and enforce authorization server-side. |
| Team members overwrite one another's work | Use Git branches, small commits, and documented module boundaries. |

## 14. Phased Delivery Plan

### Phase 1 — Basic web foundation
Landing page, app shell, planned page layouts, responsive components, mock API data, FastAPI skeleton, CSV upload validation, local run instructions. No Clerk or PostgreSQL.

### Phase 2 — Real data science
Dataset profiling, preprocessing, feature engineering, EDA, dynamic charts, metric definitions, data-backed insights, automated tests. ML only if justified by the dataset.

### Phase 3 — Authentication and persistence
Clerk authentication, backend token verification, PostgreSQL schema and migrations, user-owned dataset/analysis records, authorization tests.

### Phase 4 — Polish and presentation
Accessibility and responsive checks, error/empty states, deployment configuration if needed, demo dataset, screenshots, README, project report, and demo script.

## 15. Open Decisions

- Which dataset will be used for the final evaluation and demonstration?
- Which CSV column names will be normalized, and which can be mapped through a configurable column-mapping UI?
- Will uploaded CSV files be stored locally for the student demo or in object storage for a deployed environment? PostgreSQL should normally store metadata and relationships, not large binary files.
- Is the selected dataset sufficient for a predictive model, and what target can legitimately be predicted?
