# RISA Labs - Astera Daily Stats Reporting
## Daily Operations Dashboard for Astera Pharmacy Client

**Version 1.0 | Created: April 2026**
**Owner: Kulraj Sabharwal, Technical PM**

---

## Overview

This document defines the daily operational metrics and reporting structure for the Astera pharmacy client integration. Unlike NYCBS (health system with batch focus), Astera operates in a high-volume pharmacy environment requiring real-time submission tracking and rapid turnaround monitoring.

---

## Astera Daily Stats Sheet Structure

```
ASTERA DAILY STATS (Single Tab per Day)
├── Header Section
│   ├── Report Date
│   ├── Generated At
│   ├── Client: Astera
│   └── Timezone: ET
│
├── Volume Metrics
│   ├── Total Submissions Received
│   ├── Total Submissions Processed
│   ├── Total Submissions Pending
│   ├── Submissions by Source (Email, API, Manual)
│   └── Submissions by Drug/Therapy Class
│
├── Processing Metrics
│   ├── Processing Rate (PAs/hour)
│   ├── Average Processing Time (seconds)
│   ├── Peak Processing Hours
│   ├── Batch vs Individual Mix
│   └── Queue Depth Over Time
│
├── Outcome Metrics
│   ├── Approval Rate (%)
│   ├── Denial Rate (%)
│   ├── Pend Rate (%)
│   ├── Appeals Filed
│   └── Outcomes by Payer
│
├── Quality Metrics
│   ├── First-Pass Success Rate
│   ├── Error Rate by Type
│   ├── Auto-Processed Rate
│   ├── Manual Intervention Required
│   └── Data Completeness Score
│
├── Integration Metrics
│   ├── OncoEMR Writeback Success Rate
│   ├── FHIR Sync Status
│   ├── Email Attachment Processing Rate
│   └── API Response Time (ms)
│
├── SLA Metrics
│   ├── PAs Within SLA
│   ├── PAs Breaching SLA
│   ├── Average Turnaround Time
│   └── SLA Compliance Rate (%)
│
└── Trend Comparison
    ├── vs Yesterday
    ├── vs Last Week Same Day
    └── vs Monthly Average
```

---

## Metric Definitions & Usage

### 1. Volume Metrics

#### 1.1 Total Submissions Received
```
Definition: All PA requests received by Astera in a 24-hour period
Source: RPA event log, Astera API webhook
Formula: COUNT(submissions WHERE receivedAt >= startOfDay AND < nextDayStart)
Frequency: Real-time, reported hourly
```

**Usage:**
- Capacity planning: Determines staffing needs
- Trend analysis: Identifies volume patterns by day/time
- Client SLA tracking: Baseline for compliance calculations

**Chart Type:** Area chart showing submissions by hour + cumulative line

---

#### 1.2 Total Submissions Processed
```
Definition: PAs that completed processing (sent to payer or reached terminal state)
Source: RPA execution log
Formula: COUNT(submissions WHERE completedAt >= startOfDay)
Terminal States: approved, denied, pended, cancelled
```

**Usage:**
- Operational throughput measurement
- Resource utilization tracking
- Bottleneck identification

---

#### 1.3 Submissions by Source
```
Definition: Breakdown of how PAs entered the system
Categories:
- Email: Fax/email submissions processed via email connector
- API: Direct API submissions from EHR/EMR
- Manual: Dashboard-created orders
- Batch: Bulk file uploads (SFTP or upload)
```

**Chart Type:** Donut chart with percentages

---

#### 1.4 Submissions by Drug/Therapy Class
```
Definition: Volume distribution by medication category
Categories (example):
- Specialty (Oncology, Biologics)
- Chronic Disease (Diabetes, Cholesterol)
- Mental Health
- Pain Management
- Antibiotics/Acute
```

**Usage:**
- Identify high-volume drugs for automation focus
- Payer mix analysis
- Revenue correlation by drug class

---

### 2. Processing Metrics

#### 2.1 Processing Rate (PAs/Hour)
```
Definition: Number of PAs processed per hour
Formula: totalProcessed / hoursElapsed
Target: >60 PAs/hour sustained
```

**Chart Type:** Line chart showing hourly rate + target threshold line

```
HOURLY PROCESSING RATE
─────────────────────────────────────────────────────────────────────
120 ┤                                    ═════ Target
    │                    ╭─────╮
100 ┤              ╭─────╯      ╰─────╮
    │         ╭──╯                    ╰──╮
 80 ┤    ╭──╮╯                           ╰──╮
    │ ╭──╯                                  ╰────
 60 ┤──╯════════════════════════════════════════════
    │
 40 ┤
    └──────────────────────────────────────────────────
     8AM   10AM   12PM   2PM   4PM   6PM   8PM   10PM

    ████████ Processing Rate    ═══ Target (60/hr)
```

---

#### 2.2 Average Processing Time
```
Definition: Mean time from submission to completion
Formula: AVG(completedAt - receivedAt) for all PAs completed today
Target: <90 seconds for auto-processed, <5 minutes for manual review
```

**Breakdown:**
- Auto-processed average: Target <90s
- Manual review average: Target <5min
- Batch processing average: Target <2min per PA

---

#### 2.3 Queue Depth Over Time
```
Definition: Number of PAs waiting to be processed at each hour
Formula: COUNT(submissions WHERE received but not completed)
```

**Chart Type:** Stacked area chart showing pending + in-progress over time

```
QUEUE DEPTH
─────────────────────────────────────────────────────────────────────
 50 ┤     ████
    │   ████████
 40 ┤ ████████████
    │████████████████
 30 ┤████████████████████
    │████████████████████████
 20 ┤████████████████████████████
    │████████████████████████████████
 10 ┤████████████████████████████████████
    │████████████████████████████████████████
  0 ┼─────────────────────────────────────────────────────
    8AM   10AM   12PM   2PM   4PM   6PM   8PM

    ░░░ Pending    ████ In Progress
```

---

### 3. Outcome Metrics

#### 3.1 Approval Rate
```
Definition: Percentage of submitted PAs that received approval
Formula: (approvedCount / totalCompleted) * 100
Target: >75% for Astera (pharmacy focus)
```

**Usage:**
- Quality indicator: High approval rate = good documentation
- Payer performance: Compare approval rates by payer
- Patient outcome: Track time-to-therapy

---

#### 3.2 Denial Analysis
```
Definition: Breakdown of denial reasons
Categories:
- Prior auth required (submitted wrong)
- Step therapy not completed
- Clinical criteria not met
- Formulary restrictions
- Quantity limit exceeded
- Other
```

**Chart Type:** Pareto chart (denial count by reason, sorted descending)

```
DENIAL REASONS
─────────────────────────────────────────────────────────────────────
 80 ┤ █
    │ █ █
 60 ┤ █ █ █
    │ █ █ █ █
 40 ┤ █ █ █ █ █
    │ █ █ █ █ █ █
 20 ┤ █ █ █ █ █ █ █
    │ █ █ █ █ █ █ █ █
  0 ┼───────────────────────────────────────────────
    Prior   Step    Clinical  Formulary Quantity Other
    Auth    Therapy  Criteria

    █ Count    ─── Cumulative %
```

---

#### 3.3 Outcomes by Payer
```
Definition: Approval/denial rates broken down by insurance payer
Purpose: Identify payer-specific issues, optimize documentation
```

---

### 4. Quality Metrics

#### 4.1 First-Pass Success Rate
```
Definition: PAs processed without any errors or manual intervention
Formula: (cleanCompletions / totalCompletions) * 100
Target: >95%
```

**Error Types That Fail First-Pass:**
- Data validation errors
- Missing required fields
- API timeout/retries
- FHIR writeback failures

---

#### 4.2 Auto-Processed Rate
```
Definition: Percentage of PAs processed fully automatically (no human touch)
Formula: (autoProcessedCount / totalProcessed) * 100
Target: >80% for Astera
```

**Breakdown:**
- Straight-through processing (STP): No human intervention
- Semi-automated: Started auto, required manual completion
- Manual: Entirely manual processing

---

#### 4.3 Data Completeness Score
```
Definition: Percentage of PA orders with all required fields populated
Formula: (completeOrders / totalOrders) * 100
Target: >98%
```

**Required Fields for Astera:**
- Patient name, DOB, member ID
- Prescriber name, NPI
- Drug name, NDC
- Diagnosis code (ICD-10)
- Clinical documentation reference

---

### 5. Integration Metrics

#### 5.1 OncoEMR Writeback Success Rate
```
Definition: Percentage of PA outcomes successfully written to OncoEMR via FHIR
Formula: (writebackSuccessCount / writebackAttemptedCount) * 100
Target: >99%
```

**Writeback Types:**
- Approval: DocumentReference with approval letter
- Denial: Communication with denial note
- Status update: ServiceRequest status change

**Chart Type:** Gauge chart showing success rate vs target

```
FHIR WRITEBACK SUCCESS RATE
─────────────────────────────────────────────────────────────────────

          ████████████████████████ 99.2%

     95%  ──── Target

      [█████████████░░░░░░░░░░░] 99.2%
```

---

#### 5.2 Email Attachment Processing
```
Definition: Metrics for email-submitted PAs (Astera primary intake channel)
Components:
- Emails received
- Attachments extracted
- Attachments parsed successfully
- PAs auto-created from emails
```

**Target Metrics:**
- Extraction rate: >98%
- Parsing success: >95%
- Auto-creation rate: >90%

---

#### 5.3 API Response Time
```
Definition: Average response time for Astera API calls
Breakdown by Endpoint:
- POST /pa-requests: <500ms
- GET /status/{id}: <200ms
- POST /bulk-submit: <2s per PA
```

**Chart Type:** Box plot or histogram of response times

---

### 6. SLA Metrics

#### 6.1 SLA Compliance
```
Definition: Percentage of PAs completed within SLA
Astera SLA Targets:
- Standard PA: <24 hours
- Urgent PA: <4 hours
- STAT PA: <1 hour

Formula: (completedWithinSLA / totalCompleted) * 100
Target: >95% for standard, >99% for urgent
```

---

#### 6.2 Turnaround Time by Priority
```
Definition: Average completion time broken down by priority level
Categories:
- STAT (immediate): Target <60 min
- Urgent: Target <4 hours
- Standard: Target <24 hours
- Low: Target <48 hours
```

**Chart Type:** Bar chart showing avg time vs target for each priority

```
TURNAROUND TIME BY PRIORITY
─────────────────────────────────────────────────────────────────────
 25 ┤                        ████████
    │                        ████████
 20 ┤                        ████████
    │           ████████
 15 ┤           ████████      ████████
    │           ████████      ████████
 10 ┤ ████████ ████████      ████████
    │ ████████ ████████      ████████
  5 ┤ ████████ ████████      ████████
    └──────────────────────────────────────
      STAT       URGENT      STANDARD     LOW

      █ Actual   ─── Target line
```

---

## Daily Report Template

### Morning Handoff Report (8:00 AM ET)

```markdown
# Astera Daily Operations Report
**Date:** {DATE}
**Report Time:** {GENERATED_AT}
**Analyst:** {NAME}

---

## Executive Summary

| Metric | Yesterday | 7-Day Avg | Status |
|--------|-----------|-----------|--------|
| Total PAs | 847 | 823 | ✅ +3% |
| Approval Rate | 89.2% | 87.5% | ✅ +1.7pp |
| Auto-Process Rate | 94.1% | 92.8% | ✅ +1.3pp |
| SLA Compliance | 97.3% | 96.1% | ✅ +1.2pp |
| Writeback Success | 99.4% | 99.2% | ✅ +0.2pp |

**Overall Status:** 🟢 Green - All metrics within targets

---

## Yesterday's Highlights

### Volume
- Peak hour: 2:00 PM (127 PAs processed)
- Lowest hour: 6:00 AM (12 PAs)
- Most common drug: Wegovy (12.3% of volume)
- Most common payer: Express Scripts (23.1%)

### Quality
- First-pass success: 96.8% (target: 95%)
- Data completeness: 99.1% (target: 98%)
- Zero critical errors

### Issues Resolved
1. ✉️ Email parsing issue with PDF attachments (2:45 AM - resolved 3:15 AM)
2. 🔄 Temporary FHIR endpoint latency (11:30 AM - resolved 11:45 AM)

---

## Watch List for Today

1. ⚠️ Payer "MedicineCare" showing 12% denial rate (avg: 8%)
   - Root cause: Step therapy documentation missing
   - Action: Working with clinical team on documentation template

2. ⚠️ Queue depth building after 4 PM
   - Pattern: Last 3 Thursdays show +30% volume 4-6 PM
   - Action: Pre-positioning staff, batch optimization

---

## Actions Required

| Action | Owner | Due | Status |
|--------|-------|-----|--------|
| Review denial pattern for MedicineCare | Clinical | Today 12 PM | 🟡 |
| Deploy email parser hotfix | Engineering | Today 10 AM | 🔵 |
| Weekly client report prep | PM | Today 3 PM | 🔵 |

---
```

---

## Weekly Trend Report

```markdown
# Astera Weekly Trend Report
**Week Ending:** {DATE}
**Prepared by:** {NAME}

---

## Week-over-Week Comparison

| Metric | This Week | Last Week | Change | Trend |
|--------|-----------|-----------|--------|-------|
| Total Volume | 5,847 | 5,623 | +4.0% | 📈 |
| Daily Avg | 835 | 803 | +4.0% | → |
| Approval Rate | 88.7% | 86.2% | +2.5pp | 📈 |
| Auto-Process | 93.8% | 91.4% | +2.4pp | 📈 |
| SLA Compliance | 96.8% | 95.2% | +1.6pp | 📈 |
| Error Rate | 0.8% | 1.2% | -0.4pp | 📈 |

---

## Volume by Day

| Day | Volume | Approval | Auto% | SLA% |
|-----|--------|----------|-------|------|
| Monday | 892 | 87.2% | 92.1% | 95.8% |
| Tuesday | 945 | 89.1% | 94.3% | 97.2% |
| Wednesday | 923 | 88.8% | 93.9% | 96.9% |
| Thursday | 1,012 | 90.2% | 95.1% | 98.1% |
| Friday | 879 | 87.9% | 92.8% | 95.4% |
| Saturday | 623 | 88.5% | 93.2% | 96.2% |
| Sunday | 573 | 89.1% | 94.1% | 97.8% |

---

## Drug Class Breakdown

| Therapy Class | Volume | % of Total | Approval Rate |
|---------------|--------|------------|---------------|
| GLP-1/Weight Loss | 1,847 | 31.6% | 85.2% |
| Oncology | 1,234 | 21.1% | 91.8% |
| Diabetes | 987 | 16.9% | 92.4% |
| Cardiology | 756 | 12.9% | 88.1% |
| Mental Health | 534 | 9.1% | 87.3% |
| Other | 489 | 8.4% | 89.5% |

---

## Issues & Resolutions

| Issue | Days Active | Impact | Resolution |
|-------|-------------|--------|------------|
| Email attachment parsing timeout | 2 | ~50 PAs delayed | Deployed timeout fix |
| FHIR writeback retry loop | 1 | 12 PAs failed writeback | Fixed endpoint auth |
| Payer rejection surge (MedicineCare) | 3 | +4% denial rate | Added doc checklist |

---

## Recommendations for Next Week

1. **Increase capacity for Thursday**: Historical data shows Thursday is highest volume day
2. **Focus on GLP-1 documentation**: Approval rate 5% below average, opportunity for improvement
3. **Proactive MedicineCare outreach**: Schedule call with payer rep about documentation requirements

---
```

---

## Google Sheets Implementation

### Sheet Structure

```
Tab 1: DAILY_STATS (Today's metrics, auto-populated)
Tab 2: HISTORICAL (All daily stats, for trend analysis)
Tab 3: TRENDS (Charts and visualizations)
Tab 4: ALERTS (Threshold breaches, anomalies)
Tab 5: ADMIN (Settings, thresholds, recipients)
```

### Key Formulas

```javascript
// ========================
// DAILY_STATS Sheet
// ========================

// Total Volume
=COUNTIFS(HISTORICAL!A:A, TODAY(), HISTORICAL!B:B, "<>")

// Approval Rate
=SUMIFS(HISTORICAL!D:D, HISTORICAL!A:A, TODAY()) /
 SUMIFS(HISTORICAL!C:C, HISTORICAL!A:A, TODAY())

// Auto-Process Rate
=SUMIFS(HISTORICAL!E:E, HISTORICAL!A:A, TODAY()) /
 SUMIFS(HISTORICAL!C:C, HISTORICAL!A:A, TODAY())

// SLA Compliance
=SUMIFS(HISTORICAL!F:F, HISTORICAL!A:A, TODAY()) /
 SUMIFS(HISTORICAL!C:C, HISTORICAL!A:A, TODAY())

// Week-over-Week Change
=(THIS_WEEK_AVG - LAST_WEEK_AVG) / LAST_WEEK_AVG

// ========================
// TRENDS Sheet
// ========================

// 7-Day Moving Average
=AVERAGE(OFFSET(TODAY(), -6, 0, 7, 1))

// Month-over-Month Growth
=(SUM(ThisMonth) - SUM(LastMonth)) / SUM(LastMonth)

// Forecasted Volume
=TREND(HISTORICAL!B2:B30, HISTORICAL!A2:A30, TODAY()+7)

// Standard Deviation
=STDEV.P(HISTORICAL!B2:B30)

// Upper/Lower Control Limits
=AVERAGE(HISTORICAL!B2:B30) + (3 * STDEV.P(HISTORICAL!B2:B30))
=AVERAGE(HISTORICAL!B2:B30) - (3 * STDEV.P(HISTORICAL!B2:B30))

// ========================
// ALERTS Sheet
// ========================

// Check for SLA breach
=IF(SLA_COMPLIANCE < 0.95, "🚨 SLA BREACH", "✅ OK")

// Check for approval rate drop
=IF(APPROVAL_RATE < AVERAGE(HISTORICAL!D:D) - (2 * STDEV(HISTORICAL!D:D)),
    "⚠️ APPROVAL RATE ANOMALY", "✅ OK")

// Check for error rate spike
=IF(ERROR_RATE > 0.02, "🔴 ERROR RATE HIGH", "✅ OK")
```

---

## Dashboard Visualizations

### Primary Dashboard (Real-time)

```
┌─────────────────────────────────────────────────────────────────────┐
│  🏥 Astera Operations — Live Dashboard           Last Update: 2:45 PM│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐           │
│  │   TODAY   │ │ APPROVAL  │ │   AUTO    │ │    SLA    │           │
│  │    847    │ │   89.2%   │ │   94.1%   │ │   97.3%   │           │
│  │  PAs      │ │  ▲ +1.2%  │ │  ▲ +0.8%  │ │  ▲ +0.5%  │           │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘           │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 📊 Hourly Processing Rate                                     │   │
│  │                                                             │   │
│  │ 100 ┤         ╭───╮                                          │   │
│  │     │    ╭───╯   ╰───╮        ╭───╮                          │   │
│  │  75 ┤───╯             ╰────────╯   ╰───╮                     │   │
│  │     │                              ╭──╯                      │   │
│  │  50 ┤                              ╯                          │   │
│  │     └────────────────────────────────────────────────────   │   │
│  │      8AM  10AM  12PM   2PM   4PM   6PM                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────┐  ┌────────────────────────────────────┐  │
│  │ 📁 Outcome Mix       │  │ 📈 Approval Trend (7 days)         │  │
│  │                      │  │                                     │  │
│  │  ████ Approved 89%   │  │  90%┤ ═══════╮                      │  │
│  │  ██ Denied   8%      │  │     │       ╰────╮                  │  │
│  │  ░ Pend    3%        │  │  85%┤            ╰──╮               │  │
│  │                      │  │     └───────────────╯              │  │
│  │                      │  │      M  T  W  T  F  S  S            │  │
│  └──────────────────────┘  └────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────┐  ┌────────────────────────────────────┐  │
│  │ 🏥 Payer Mix          │  │ ✅ Writeback Status                │  │
│  │                      │  │                                     │  │
│  │ Express Scripts 23%  │  │  ████████████████████████ 99.4%    │  │
│  │ OptumRx        19%  │  │                                     │  │
│  │ CVS Caremark   17%  │  │  Failed: 3  │  Success: 492        │  │
│  │ MedicineCare   14%  │  │                                     │  │
│  │ Other          27%  │  │  [View Failed]                    │  │
│  └──────────────────────┘  └────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ ⏱️ SLA Status                          ⚠️  3 PAs at risk      │   │
│  │                                                             │   │
│  │ 🟢 On Track: 844  │  🟡 At Risk: 2  │  🔴 Breached: 1       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Quality Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 Quality Metrics — Astera                          Apr 27, 2026   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ FIRST-PASS SUCCESS RATE                                      │   │
│  │                                                             │   │
│  │      ████████████████████████████████░░░░  96.8%            │   │
│  │      Target: 95%  │  Trend: +1.2% vs last week             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│  │ DATA COMPLETE   │ │ ERROR RATE       │ │ MANUAL INTERV   │     │
│  │    99.1%        │ │    0.8%          │ │     5.9%         │     │
│  │  Target: 98%   │ │  Target: <1%    │ │  Target: <10%   │     │
│  │  ✅ Above      │ │  ✅ Below        │ │  ✅ Below        │     │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 📋 Error Breakdown Today                                    │   │
│  │                                                             │   │
│  │ Validation Error        ████████████████████░░░░░  45       │   │
│  │ FHIR Writeback Failure  ███████████████░░░░░░░░░░  28       │   │
│  │ API Timeout             ████████░░░░░░░░░░░░░░░░░  15       │   │
│  │ Data Missing            ████░░░░░░░░░░░░░░░░░░░░░   8       │   │
│  │ Other                   ██░░░░░░░░░░░░░░░░░░░░░░░   4       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🔄 Processing Time Distribution                               │   │
│  │                                                             │   │
│  │ 0-30s    ████████████████████████████████████████████ 78%   │   │
│  │ 30-60s   ████████████████████░░░░░░░░░░░░░░░░░░░░░░░  12%   │   │
│  │ 1-5min   ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   6%    │   │
│  │ 5-15min  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   3%    │   │
│  │ >15min   ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   1%    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Automation Setup

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ASTERA STATS AUTOMATION                         │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  RPA Logs    │────▶│  Data Loader │────▶│  BigQuery    │
│  (Firestore) │     │  (Python)    │     │              │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Reports     │◀────│  Scheduler   │◀────│  Aggregate   │
│  (Email)     │     │  (Cron)      │     │  Tables      │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│  Dashboard   │
│  (GSheets)   │
└──────────────┘
```

### Python Data Loader

```python
# astera_stats_loader.py

from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud import firestore
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class AsteraStatsLoader:
    """Load daily statistics for Astera operations."""

    def __init__(self, project_id: str, dataset: str):
        self.bq = bigquery.Client(project=project_id)
        self.dataset = dataset

    def calculate_daily_stats(self, date: datetime.date) -> dict:
        """Calculate all daily statistics for Astera."""

        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)

        return {
            'date': date.isoformat(),
            'volume': self._get_volume_stats(start_of_day, end_of_day),
            'processing': self._get_processing_stats(start_of_day, end_of_day),
            'outcomes': self._get_outcome_stats(start_of_day, end_of_day),
            'quality': self._get_quality_stats(start_of_day, end_of_day),
            'integration': self._get_integration_stats(start_of_day, end_of_day),
            'sla': self._get_sla_stats(start_of_day, end_of_day)
        }

    def _get_volume_stats(self, start: datetime, end: datetime) -> dict:
        """Get volume metrics."""
        query = """
        SELECT
            COUNT(*) as total_submissions,
            COUNTIF(status IN ('approved', 'denied', 'pended')) as processed,
            COUNTIF(status = 'pending') as pending,
            COUNTIF(source = 'email') as email_count,
            COUNTIF(source = 'api') as api_count,
            COUNTIF(source = 'manual') as manual_count,
            COUNTIF(source = 'batch') as batch_count
        FROM `rpa.astera_submissions`
        WHERE received_at >= @start AND received_at < @end
        """
        results = self.bq.query(query, params={
            'start': start.isoformat(),
            'end': end.isoformat()
        }).result()

        row = next(results)
        return {
            'total': row.total_submissions,
            'processed': row.processed,
            'pending': row.pending,
            'by_source': {
                'email': row.email_count,
                'api': row.api_count,
                'manual': row.manual_count,
                'batch': row.batch_count
            }
        }

    def _get_outcome_stats(self, start: datetime, end: datetime) -> dict:
        """Get outcome breakdown."""
        query = """
        SELECT
            COUNTIF(outcome = 'approved') as approved,
            COUNTIF(outcome = 'denied') as denied,
            COUNTIF(outcome = 'pended') as pended,
            COUNTIF(outcome = 'cancelled') as cancelled
        FROM `rpa.astera_submissions`
        WHERE completed_at >= @start AND completed_at < @end
        """
        results = self.bq.query(query, params={
            'start': start.isoformat(),
            'end': end.isoformat()
        }).result()

        row = next(results)
        total = row.approved + row.denied + row.pended + row.cancelled

        return {
            'approved': row.approved,
            'denied': row.denied,
            'pended': row.pended,
            'cancelled': row.cancelled,
            'approval_rate': row.approved / total if total > 0 else 0
        }

    def _get_quality_stats(self, start: datetime, end: datetime) -> dict:
        """Get quality metrics."""
        query = """
        SELECT
            AVG(TIMESTAMP_DIFF(completed_at, received_at, SECOND)) as avg_processing_time,
            COUNTIF(error_occurred = TRUE) / COUNT(*) as error_rate,
            COUNTIF(first_pass_success = TRUE) / COUNT(*) as first_pass_rate,
            COUNTIF(auto_processed = TRUE) / COUNT(*) as auto_process_rate,
            COUNTIF(data_complete = TRUE) / COUNT(*) as data_completeness
        FROM `rpa.astera_submissions`
        WHERE received_at >= @start AND received_at < @end
        """
        results = self.bq.query(query, params={
            'start': start.isoformat(),
            'end': end.isoformat()
        }).result()

        row = next(results)
        return {
            'avg_processing_time_seconds': row.avg_processing_time or 0,
            'error_rate': row.error_rate or 0,
            'first_pass_rate': row.first_pass_rate or 0,
            'auto_process_rate': row.auto_process_rate or 0,
            'data_completeness': row.data_completeness or 0
        }

    def _get_sla_stats(self, start: datetime, end: datetime) -> dict:
        """Get SLA compliance metrics."""
        query = """
        SELECT
            COUNT(*) as total,
            COUNTIF(TIMESTAMP_DIFF(completed_at, received_at, MINUTE) <= sla_minutes) as within_sla,
            COUNTIF(TIMESTAMP_DIFF(completed_at, received_at, MINUTE) > sla_minutes) as breached,
            AVG(TIMESTAMP_DIFF(completed_at, received_at, MINUTE)) as avg_turnaround_minutes
        FROM `rpa.astera_submissions`
        WHERE completed_at >= @start AND completed_at < @end
        """
        results = self.bq.query(query, params={
            'start': start.isoformat(),
            'end': end.isoformat()
        }).result()

        row = next(results)
        return {
            'total_completed': row.total,
            'within_sla': row.within_sla,
            'breached': row.breached,
            'sla_compliance_rate': row.within_sla / row.total if row.total > 0 else 0,
            'avg_turnaround_minutes': row.avg_turnaround_minutes or 0
        }

    def load_to_google_sheets(self, stats: dict, spreadsheet_id: str):
        """Load calculated stats to Google Sheets."""

        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        sheets = build('sheets', 'v4', credentials=self._get_credentials())

        # Update daily stats tab
        range_name = 'DAILY_STATS!A1:Z100'

        values = self._format_stats_for_sheets(stats)

        body = {
            'values': values
        }

        sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()

        logger.info(f"Updated daily stats for {stats['date']}")
```

---

## Alerts & Notifications

### Threshold Configuration

```python
ALERT_THRESHOLDS = {
    'volume': {
        'min_daily': 500,          # Alert if below 500 PAs
        'max_hourly': 150,         # Alert if >150 PAs in one hour
    },
    'approval_rate': {
        'warning': 0.85,           # Alert if below 85%
        'critical': 0.80,          # Escalate if below 80%
    },
    'auto_process_rate': {
        'warning': 0.90,           # Alert if below 90%
        'critical': 0.85,          # Escalate if below 85%
    },
    'sla_compliance': {
        'warning': 0.95,           # Alert if below 95%
        'critical': 0.90,          # Escalate if below 90%
    },
    'error_rate': {
        'warning': 0.015,          # Alert if above 1.5%
        'critical': 0.02,          # Escalate if above 2%
    },
    'writeback_success': {
        'warning': 0.98,           # Alert if below 98%
        'critical': 0.95,          # Escalate if below 95%
    }
}
```

### Alert Rules

| Alert | Condition | Action | Recipients |
|-------|-----------|--------|------------|
| Volume Drop | Today < 70% of 7-day avg | Email + Slack | PM, Ops Lead |
| Approval Rate Drop | Rate < threshold | Email + Slack | PM, Clinical |
| SLA Breach | Any PA breaches SLA | Slack | Ops Lead, PM |
| Error Spike | Error rate > 2x avg | Pager | Engineering |
| Writeback Failure | >5 consecutive failures | Pager + Email | Engineering, PM |

---

## Setup Checklist

### Day 1: Initial Setup
- [ ] Create Google Sheets template
- [ ] Set up BigQuery dataset and tables
- [ ] Deploy data loader script
- [ ] Configure service account permissions
- [ ] Set up alert thresholds
- [ ] Test end-to-end data flow

### Day 2: Validation
- [ ] Verify data accuracy against source systems
- [ ] Confirm alert thresholds are appropriate
- [ ] Test email notification delivery
- [ ] Train on-call team on alert response

### Week 1: Refinement
- [ ] Adjust thresholds based on observed patterns
- [ ] Add any Astera-specific drug categories
- [ ] Customize reports for Astera stakeholders
- [ ] Schedule automated report delivery

---

## Appendix: Astera vs NYCBS Comparison

| Metric | Astera | NYCBS | Notes |
|--------|--------|-------|-------|
| Primary Channel | Email/API | SFTP Batch | Different ingestion |
| Volume Pattern | Consistent | Spiky (batches) | Astera needs real-time |
| Approval Focus | Pharmacy | Health System | Different outcome focus |
| Writeback | OncoEMR (FHIR) | EHR Integration | Similar tech, different scope |
| SLA | 24hr standard | 48hr standard | Astera needs faster turnaround |
| Reporting | Daily detailed | Weekly summary | Astera benefits from intraday |

---

*Document Version: 1.0*
*Last Updated: April 27, 2026*
*Author: Kulraj Sabharwal, Technical PM*
*Review Cycle: Monthly*