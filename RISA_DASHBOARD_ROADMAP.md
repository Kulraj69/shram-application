# RISA Dashboard Utilization Roadmap — 100% Adoption Plan
## Version 1.0 | Technical PM: Kulraj Sabharwal

---

## Executive Summary

**Goal**: Transform the RISA dashboard from a partial tool into the **single source of truth** for all operational work. No external workarounds. No manual queries. No tribal knowledge gaps.

**Current State**:
- PA Orders dashboard exists with core features
- 13,509+ orders tracked
- ~80% manual work reduction achieved in Primary Care Dashboard
- Remaining 20% = high-value operational blind spots

**Target State**:
- 100% dashboard utilization across PM, Ops, CS, Leadership
- Zero reliance on external BigQuery queries for operational decisions
- Full workflow coverage: intake → automation → tracking → writeback → analytics
- Client monitoring fully self-service

---

## Problem Analysis

### Why Dashboard Utilization Stalls at <100%

| Barrier | Impact | Root Cause |
|---------|--------|------------|
| **Missing features** | Users work around gaps | Feature completeness debt |
| **Trust deficit** | PMs double-check outputs | Analytics errors, data reliability |
| **Workflow disconnects** | Steps happen outside dashboard | Writeback gaps, manual handoffs |
| **Knowledge gaps** | "I don't know if dashboard has X" | No feature discovery UX |
| **Badging/approval gaps** | Approval requires external steps | Missing approval workflows |
| **Reporting gaps** | Leadership pulls raw data | No executive dashboards |

---

## Phase 1: Quick Wins (Week 1-2)

### 1.1 Feature Discovery Overlay
**Problem**: Users don't know what dashboard can do.
**Fix**: In-app feature tooltips + "New in Dashboard" notification banner.

```
Impact: +15% adoption among occasional users
Effort: Low (frontend overlay)
Owner: PM + Frontend
```

### 1.2 Status Comment Fetch from CMM
**Problem**: Status shows "Sent to Plan" but no plan response details.
**Fix**: Auto-fetch CoverMyMeds status comments on status page.

```
Impact: Eliminates manual CMM login for status checks
Effort: Medium (new API integration)
Owner: Backend + RPA
```

### 1.3 Dev/Prod Analytics Link Toggle
**Problem**: PMs confused about which dashboard to use.
**Fix**: Clear environment indicator + prominent link to switch.

```
Impact: Prevents prod accidents from dev testing
Effort: Low (UI change)
Owner: Frontend
```

### 1.4 Missing Data Pre-Filter
**Problem**: Users scan entire list looking for actionable items.
**Fix**: One-click "Show only items with missing data" filter.

```
Impact: -50% time to find actionable items
Effort: Low (filter logic)
Owner: Backend + Frontend
```

---

## Phase 2: Feature Completeness (Week 3-6)

### 2.1 Planned Task Incorporation

**Current Gap**: Planned/queued tasks not visible in dashboard.

| Task Type | Current State | Target State |
|-----------|---------------|--------------|
| Scheduled PA submissions | Manual tracking | Dashboard queue view |
| Retry queue | Hidden in logs | Visible retry dashboard |
| Exception routing | IRC/chat notification | Dashboard alert + queue |

**API Addition**:
```python
GET /api/v1/planned-tasks
Response: {
  "scheduled": [...],
  "retry_queue": [...],
  "exception_routes": [...]
}
```

**Impact**: Complete task visibility, zero "did I submit that?" questions.

### 2.2 Approval Systems

**Current Gap**: Approvals require email/Slack/handoff.

**Target**: In-dashboard approval workflow.

| Approval Type | Current Flow | Target Flow |
|---------------|---------------|-------------|
| High-value PA | Email chain | Dashboard approval modal |
| Denial escalation | IRC ping | Dashboard queue + approve |
| Manual override | Direct DB write | Dashboard approve + audit |

**API Addition**:
```python
POST /api/v1/approvals
{
  "task_id": "...",
  "approval_type": "high_value_pa",
  "approved_by": "user_id",
  "notes": "..."
}
```

**Impact**: Full audit trail, faster approvals, zero email threads.

### 2.3 Client Operational Gaps Closed

**NYCBS Gaps**:
- [ ] Batch file status visibility
- [ ] Denial letter attachment confirmation
- [ ] SFTP push/pull status dashboard
- [ ] Error log visibility per batch

**Astera Gaps**:
- [ ] Email attachment fetch status
- [ ] Bulk submission progress tracking
- [ ] Single PA submission confirmation
- [ ] OncoEMR writeback status

**Impact**: Client self-service for status questions.

---

## Phase 3: Write-back & Integration (Week 7-10)

### 3.1 FHIR Write-back Completion

**Current**: Partial writeback to OncoEMR.
**Target**: Complete FHIR-compliant writeback for all outcomes.

| Writeback Type | Current | Target |
|----------------|---------|--------|
| Approval note | Text note created | Structured FHIR DocumentReference |
| Denial letter | Manual upload | Auto-upload + FHIR attachment |
| Status update | Manual IRC | Auto-FHIR subscription |

**API Addition**:
```python
POST /api/v1/fhir/writeback
{
  "resource_type": "DocumentReference",
  "patient_mrn": "...",
  "outcome": "approved",
  "document_url": "...",
  "author": "rpa-service"
}
```

**Impact**: Complete EMR integration, zero manual documentation.

### 3.2 Fax Workflow Sync

**Current**: Fax handled separately.
**Target**: Fax integrated into main dashboard.

| Fax Feature | Description |
|-------------|-------------|
| Inbound fax queue | Fax received → dashboard notification |
| Fax-to-PA routing | Fax parsed → PA order auto-created |
| Fax status tracking | Sent/failed/delivered in dashboard |
| Fax attachment linking | Fax linked to related PA order |

**API Addition**:
```python
GET /api/v1/fax/inbox
GET /api/v1/fax/{id}/route-to-pa
POST /api/v1/fax/{id}/attach-to-order
```

**Impact**: Fax no longer a separate workflow.

### 3.3 Calling Workflow Integration

**Current**: Calling workflow not in dashboard.
**Target**: Call outcomes visible and actionable in dashboard.

| Call Feature | Description |
|--------------|-------------|
| Call queue | Patients requiring call → dashboard |
| Call status | Attempted/completed/failed logged |
| Call outcome | Connected/voicemail/no-answer tracked |
| Callback scheduling | Schedule follow-up call from dashboard |

**Impact**: Complete patient communication hub.

### 3.4 GG Sync (Glucose Guardian?)

**Current**: Unknown external sync.
**Target**: Dashboard shows GG sync status + errors.

```
Impact: Visibility into external integrations.
```

---

## Phase 4: Analytics & Trust (Week 11-14)

### 4.1 RISA Pharma Analytics — Trust Recovery

**Problem**: Analytics gave wrong values, PMs lost trust.

**Fix**: Systematic data reliability pass.

| Issue | Fix | Verification |
|-------|-----|--------------|
| Wrong PA counts | Re-validate BigQuery queries | Cross-check with RPA logs |
| Error spike false positives | Tune alert thresholds | 30-day stable run |
| Missing data indicators | Fix ETL pipeline | Daily reconciliation |
| Stale dashboard data | Increase refresh frequency | Real-time <5min lag |

**Metrics to Track**:
```
- Dashboard value vs source-of-truth match rate: Target 99.9%
- Time since last analytics error: Target >30 days
- PM trust score (monthly survey): Target >4/5
```

### 4.2 Executive Reports in Astera

**Current**: Leadership pulls raw data.
**Target**: Automated executive reports in dashboard.

| Report | Refresh | Contents |
|--------|---------|----------|
| Daily Ops Summary | Every 4 hours | Volume, approval rate, errors |
| Weekly Trend Report | Monday AM | WoW comparison, anomaly flags |
| Client Health Score | Daily | Per-client SLA adherence |
| FTE Efficiency | Weekly | PAs per FTE, automation rate |

**API Addition**:
```python
GET /api/v1/reports/executive/daily
GET /api/v1/reports/executive/weekly
GET /api/v1/reports/client-health
```

**Impact**: Zero raw data pulls by leadership.

### 4.3 Per-Feature Improvement Tracking

**Problem**: No visibility into which features reduce manual work.

**Solution**: Dashboard analytics for dashboard usage.

| Metric | Track |
|--------|-------|
| Feature usage heatmap | Which features used most |
| Time-to-action | How fast users complete tasks |
| Abandonment rate | Where users drop off |
| Search-to-action | Does search find what users need |

**Impact**: Data-driven dashboard improvement.

---

## Phase 5: Stack Mapping (Week 15-16)

### 5.1 Sales Team Capability Map

**Purpose**: "If a client comes, what can we build?"

| Client Ask | RISA Capability | Status |
|------------|-----------------|--------|
| Prior auth automation | PA Order Pipeline | ✅ Live |
| Eligibility verification | EV-BV Service | ✅ Live |
| EHR integration | OncoEMR writeback | ✅ Live |
| Fax-based workflows | Fax API | ✅ Live |
| AI document processing | PDF extraction + Medical necessity | ✅ Live |
| Multi-payer support | 50+ payer configs | ✅ Live |
| Real-time status tracking | Dashboard + CMM polling | ✅ Live |
| Bulk processing | CSV batch + SFTP | ✅ Live |
| Custom reporting | BigQuery + Dashboard | 🟡 Partial |
| Mobile access | None | 🔴 Gap |
| White-label | None | 🔴 Gap |
| Client portal | None | 🔴 Gap |

**Impact**: Sales knows what's possible before promising.

### 5.2 Ops Team Feature Catalog

**Purpose**: "Does feature X exist?"

| Category | Feature | Dashboard Location | Documentation |
|----------|---------|-------------------|----------------|
| **PA Orders** | Create order | Worklists → New | `/api/v1/pa-orders/create` |
| **PA Orders** | View order | Worklists → Search | `/api/v1/pa-orders/{id}` |
| **PA Orders** | Submit to plan | Order → Send to Plan | `/api/v1/pa-orders/{id}/submit` |
| **Status** | Track status | Status page | `/api/v1/status/{id}` |
| **Documents** | Upload letter | Order → Upload | `/api/v1/documents/upload` |
| **Analytics** | View KPIs | Summary page | `/api/v1/summary-stats` |
| **SFTP** | Upload batch | SFTP page | `/api/v1/sftp/upload` |
| **Validator** | Check eligibility | Validator page | `/api/v1/coverage/check` |
| **Fax** | Send fax | Fax page | `/api/v1/fax/submit` |
| **Reports** | Daily summary | Reports → Daily | `/api/v1/reports/daily` |

**Impact**: Zero "does X exist?" questions.

---

## Measurement Framework

### Dashboard Utilization Score

```
UTILIZATION_SCORE = (
  Active_Users / Total_Users × 25% +
  Feature_Adoption_Rate × 25% +
  Decision_queries_Via_Dashboard / Total_Decision_Queries × 25% +
  Manual_Steps_Eliminated / Total_Pre_Dashboard_Steps × 25%
)
```

**Target**: 100% by Week 16.

### Key Metrics to Track

| Metric | Baseline | Week 4 | Week 8 | Week 12 | Week 16 |
|--------|----------|--------|--------|---------|---------|
| Active daily users | X | +20% | +40% | +60% | +80% |
| Feature adoption | 60% | 75% | 85% | 95% | 100% |
| Manual query reduction | 80% | 85% | 92% | 97% | 100% |
| Analytics error rate | Y | -50% | -80% | -95% | 0% |
| Client escalations | Z | -20% | -40% | -60% | -80% |
| Decision speed | A min | -15% | -30% | -50% | -70% |

---

## Technical Dependencies

### Backend
- [ ] Planned task visibility API
- [ ] Approval workflow API
- [ ] FHIR writeback completion
- [ ] Fax integration endpoints
- [ ] Calling workflow API
- [ ] Executive report APIs

### Frontend
- [ ] Feature discovery overlay
- [ ] Env indicator + switcher
- [ ] Missing data filter
- [ ] Approval modal
- [ ] Executive reports page
- [ ] Feature usage analytics

### RPA
- [ ] Status comment fetch from CMM
- [ ] Auto-writeback trigger
- [ ] Denial letter auto-upload
- [ ] Fax routing automation

### Data
- [ ] Analytics pipeline fix
- [ ] ETL reconciliation
- [ ] BigQuery query validation
- [ ] Real-time dashboard refresh

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Feature overload | Medium | Low | Phase rollout, feedback loops |
| Analytics trust takes time | High | High | Start Week 1, show progress |
| Client-side adoption resistance | Medium | Medium | Champion users, training sessions |
| Scope creep | High | Medium | Strict phase gates |
| Data reliability fix reveals more issues | Medium | Medium | Buffer time in phases |

---

## Success Criteria

**Week 16 Delivered**:
- [ ] Zero PM manual BigQuery queries for operational decisions
- [ ] Zero client escalations due to "can't see status"
- [ ] Analytics errors: zero for 30+ consecutive days
- [ ] Feature adoption: 100% of available features used weekly
- [ ] Executive reports: zero raw data pulls
- [ ] Approval workflows: 100% in-dashboard

**Business Impact**:
- NYCBS volume growth sustainable without proportional FTE increase
- Client retention improved via transparency
- Leadership decision speed: -70%
- Operational trust score: >4.5/5

---

*Document Status: Draft v1.0*
*Author: Kulraj Sabharwal, Technical PM*
*Last Updated: April 2026*
