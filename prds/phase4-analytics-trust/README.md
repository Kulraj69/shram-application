# Phase 4 PRD: Analytics & Trust (Week 11-14)

## Summary

Systematic data reliability improvements, executive reporting, and feature analytics.

---

## 4.1 RISA Pharma Analytics — Trust Recovery

### README

**Problem**: Analytics gave wrong values, PMs lost trust.
**Solution**: Systematic data reliability pass with verification framework.
**Impact**: Data trust restored, zero manual BigQuery queries.

### SPEC.md

#### Analytics Data Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ANALYTICS DATA FLOW                              │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    Source    │    │   Extract    │    │  Transform   │    │    Load      │
│   Systems    │───▶│    (RPA)     │───▶│   (ETL)      │───▶│  (BigQuery)  │
│              │    │              │    │              │    │              │
│ • CoverMyMeds│    │ • Real-time  │    │ • Validation │    │ • Aggregated │
│ • NYCBS SFTP │    │ • Batch      │    │ • Cleansing  │    │ • Partitioned│
│ • Astera API │    │ • Webhook    │    │ • Enrichment │    │ • Indexed    │
│ • OncoEMR    │    │              │    │ • Dedup      │    │ • Cached      │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │                                      │                     │
       ▼                                      ▼                     ▼
┌──────────────┐                      ┌──────────────┐      ┌──────────────┐
│  Raw Audit   │                      │  Data        │      │  Dashboard   │
│  (Firestore) │                      │  Quality     │      │  (Frontend)  │
│              │                      │  Checks      │      │              │
│ • All events │                      │ • Threshold  │      │ • Real-time  │
│ • Immutable  │                      │ • Anomaly    │      │ • Accurate   │
│ • Full trace │                      │ • Completeness│    │ • Trusted    │
└──────────────┘                      └──────────────┘      └──────────────┘
```

#### Analytics Query Validation

```python
# analytics_validator.py

from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    is_valid: bool
    expected_value: float
    actual_value: float
    variance_percent: float
    errors: list[str]
    warnings: list[str]

class AnalyticsValidator:
    """Validates analytics queries against source of truth."""

    def __init__(self, rpa_db: FirestoreClient, bigquery_client):
        self.rpa_db = rpa_db
        self.bq = bigquery_client

    async def validate_pa_counts(
        self,
        date_range: tuple[datetime, datetime],
        granularity: str = 'daily'
    ) -> ValidationResult:
        """Validate PA count analytics against RPA logs."""

        start_date, end_date = date_range

        # Get ground truth from RPA logs
        rpa_counts = await self._count_rpa_submissions(start_date, end_date)

        # Get BigQuery analytics
        bq_counts = await self._query_bigquery_pa_counts(
            start_date, end_date, granularity
        )

        # Compare
        variance = abs(bq_counts - rpa_counts) / max(rpa_counts, 1) * 100

        result = ValidationResult(
            is_valid=variance <= 0.1,  # 0.1% tolerance
            expected_value=rpa_counts,
            actual_value=bq_counts,
            variance_percent=variance,
            errors=[],
            warnings=[f"Variance: {variance:.2f}%"] if variance > 0.1 else []
        )

        if not result.is_valid:
            logger.error(
                f"PA count mismatch: RPA={rpa_counts}, BQ={bq_counts}, "
                f"variance={variance:.2f}%"
            )
            await self._alert_analytics_mismatch('pa_counts', result)

        return result

    async def validate_error_rates(
        self,
        date_range: tuple[datetime, datetime]
    ) -> ValidationResult:
        """Validate error rate analytics."""

        start_date, end_date = date_range

        # Count total submissions
        total = await self._count_rpa_submissions(start_date, end_date)

        # Count errors
        errors = await self._count_rpa_errors(start_date, end_date)

        # Calculate true error rate
        true_rate = errors / total * 100 if total > 0 else 0

        # Query BigQuery for reported error rate
        reported_rate = await self._query_bigquery_error_rate(
            start_date, end_date
        )

        variance = abs(reported_rate - true_rate)

        return ValidationResult(
            is_valid=variance <= 0.5,  # 0.5% tolerance for rates
            expected_value=true_rate,
            actual_value=reported_rate,
            variance_percent=variance,
            errors=[],
            warnings=[]
        )

    async def validate_dashboard_refresh_lag(
        self,
        max_lag_seconds: int = 300
    ) -> dict:
        """Check if dashboard data is fresh enough."""

        # Get latest record timestamp in BigQuery
        latest_bq = await self._get_latest_bq_timestamp()

        # Get latest source event
        latest_source = await self._get_latest_source_timestamp()

        lag_seconds = (latest_source - latest_bq).total_seconds()

        return {
            'is_fresh': lag_seconds <= max_lag_seconds,
            'lag_seconds': lag_seconds,
            'max_allowed': max_lag_seconds,
            'latest_bq_record': latest_bq.isoformat(),
            'latest_source_event': latest_source.isoformat(),
            'alerts_triggered': lag_seconds > max_lag_seconds
        }

    async def run_full_validation(self) -> dict:
        """Run all validation checks."""

        yesterday = datetime.utcnow() - timedelta(days=1)
        week_ago = datetime.utcnow() - timedelta(days=7)

        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'pa_counts_daily': await self.validate_pa_counts(
                    (yesterday, yesterday), 'daily'
                ),
                'pa_counts_weekly': await self.validate_pa_counts(
                    (week_ago, yesterday), 'weekly'
                ),
                'error_rate': await self.validate_error_rates((week_ago, yesterday)),
                'refresh_lag': await self.validate_dashboard_refresh_lag()
            },
            'overall_valid': all(
                r.is_valid for r in results['checks'].values()
                if isinstance(r, ValidationResult)
            )
        }

        # Log validation run
        await self._log_validation_run(results)

        return results

    async def _count_rpa_submissions(
        self,
        start: datetime,
        end: datetime
    ) -> int:
        """Count actual PA submissions from RPA logs."""

        query = self.db.collection('rpa_events').where(
            'eventType', '==', 'pa_submitted'
        ).where(
            'timestamp', '>=', start.isoformat()
        ).where(
            'timestamp', '<=', end.isoformat()
        )

        return len(query.get())

    async def _count_rpa_errors(
        self,
        start: datetime,
        end: datetime
    ) -> int:
        """Count actual errors from RPA logs."""

        query = self.db.collection('rpa_events').where(
            'eventType', '==', 'error'
        ).where(
            'timestamp', '>=', start.isoformat()
        ).where(
            'timestamp', '<=', end.isoformat()
        )

        return len(query.get())
```

#### Data Quality Framework

```python
# data_quality.py

from enum import Enum
from dataclasses import dataclass
from typing import Callable
from datetime import datetime

class DataQualityScore(Enum):
    EXCELLENT = "excellent"  # 95-100%
    GOOD = "good"           # 85-94%
    FAIR = "fair"           # 70-84%
    POOR = "poor"           # <70%

@dataclass
class QualityCheck:
    name: str
    description: str
    check_fn: Callable
    threshold: float
    severity: str  # 'critical', 'warning', 'info'

class DataQualityFramework:
    """Automated data quality monitoring and alerting."""

    def __init__(self, db, bigquery_client):
        self.db = db
        self.bq = bigquery_client

    def _get_checks(self) -> list[QualityCheck]:
        """Define all quality checks."""

        return [
            # Completeness checks
            QualityCheck(
                name="null_check",
                description="Check for unexpected null values in key fields",
                check_fn=self._check_null_values,
                threshold=0.01,  # Max 1% nulls
                severity="critical"
            ),
            QualityCheck(
                name="missing_data_indicator",
                description="Check for records with missing critical data",
                check_fn=self._check_missing_data,
                threshold=0.05,
                severity="warning"
            ),

            # Accuracy checks
            QualityCheck(
                name="value_range",
                description="Check values are within expected ranges",
                check_fn=self._check_value_ranges,
                threshold=0.0,
                severity="critical"
            ),
            QualityCheck(
                name="cross_reference",
                description="Verify cross-references between tables",
                check_fn=self._check_cross_references,
                threshold=0.001,
                severity="warning"
            ),

            # Timeliness checks
            QualityCheck(
                name="freshness",
                description="Check data is within acceptable lag",
                check_fn=self._check_data_freshness,
                threshold=300,  # 5 minutes
                severity="critical"
            ),

            # Consistency checks
            QualityCheck(
                name="duplicate_check",
                description="Check for duplicate records",
                check_fn=self._check_duplicates,
                threshold=0.001,
                severity="warning"
            ),
            QualityCheck(
                name="calculation_accuracy",
                description="Verify calculated fields are correct",
                check_fn=self._check_calculations,
                threshold=0.0,
                severity="critical"
            )
        ]

    async def run_all_checks(self) -> dict:
        """Run all quality checks and return report."""

        results = []
        for check in self._get_checks():
            try:
                result = await check.check_fn()
                results.append({
                    'check': check.name,
                    'passed': result['score'] >= check.threshold,
                    'score': result['score'],
                    'details': result.get('details', [])
                })
            except Exception as e:
                results.append({
                    'check': check.name,
                    'passed': False,
                    'score': 0,
                    'error': str(e)
                })

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_score': self._calculate_overall_score(results),
            'checks': results
        }

    async def _check_null_values(self) -> dict:
        """Check for unexpected nulls in key fields."""
        # Implementation
        pass

    async def _check_duplicates(self) -> dict:
        """Check for duplicate records."""
        # Implementation
        pass

    async def _check_data_freshness(self) -> dict:
        """Check if data is fresh."""
        # Implementation
        pass
```

### Metrics Dashboard

#### Utilization Score Card

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 DASHBOARD UTILIZATION SCORE                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐  ┌─────────────────────┐                   │
│  │                     │  │                     │                   │
│  │      ████           │  │      ██████         │                   │
│  │     ████            │  │     ███████         │                   │
│  │    ████             │  │    ████████         │                   │
│  │   ████              │  │   █████████         │                   │
│  │  ████               │  │  ██████████         │                   │
│  │ ████                │  │ ███████████        │                   │
│  │                     │  │                     │                   │
│  │     78 / 100        │  │      92 / 100       │                   │
│  │                     │  │                     │                   │
│  │   WEEK 4            │  │    WEEK 12          │                   │
│  │   Target: 85        │  │    Target: 100      │                   │
│  └─────────────────────┘  └─────────────────────┘                   │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Key Metrics Timeline                                          │  │
│  │                                                               │  │
│  │ Feature Adoption          ████████████████████░░░░░  85%      │  │
│  │ Manual Reduction          ████████████████████████░  92%      │  │
│  │ Analytics Errors          ██████████████████████████  0       │  │
│  │ Client Escalations        █████████████████████░░░░  80%      │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4.2 Executive Reports in Astera

### README

**Problem**: Leadership pulls raw data.
**Solution**: Automated executive reports in dashboard.
**Impact**: Zero raw data pulls.

### SPEC.md

#### Report Generation Service

```python
# executive_report_service.py

from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

@dataclass
class ReportConfig:
    report_type: str
    refresh_interval_hours: int
    recipients: list[str]
    format: str  # 'html', 'pdf', 'email'

class ExecutiveReportService:
    """Generate automated executive reports."""

    def __init__(
        self,
        db: FirestoreClient,
        bq_client,
        email_service,
        report_templates: dict
    ):
        self.db = db
        self.bq = bq_client
        self.email = email_service
        self.templates = report_templates

    async def generate_daily_ops_summary(self) -> dict:
        """Generate daily operational summary report."""

        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        # Query BigQuery for daily stats
        stats = await self._query_daily_stats(yesterday)

        # Get anomaly flags
        anomalies = await self._detect_anomalies(stats)

        # Build report
        report_data = {
            'reportDate': yesterday.isoformat(),
            'generatedAt': datetime.utcnow().isoformat(),
            'period': 'Daily',
            'summary': {
                'totalPAVolume': stats['total_submissions'],
                'approvalRate': stats['approval_rate'],
                'automationRate': stats['automation_rate'],
                'errorCount': stats['error_count'],
                'errorRate': stats['error_rate']
            },
            'byClient': await self._get_client_breakdown(yesterday),
            'byPayer': await self._get_payer_breakdown(yesterday),
            'anomalies': anomalies,
            'highlights': self._generate_highlights(stats)
        }

        return report_data

    async def generate_weekly_trend_report(self) -> dict:
        """Generate weekly trend analysis report."""

        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=7)
        prev_start = start_date - timedelta(days=7)

        # Current week stats
        current_stats = await self._query_range_stats(start_date, end_date)

        # Previous week stats for comparison
        prev_stats = await self._query_range_stats(prev_start, start_date)

        report_data = {
            'reportDate': end_date.isoformat(),
            'period': f'{start_date} to {end_date}',
            'generatedAt': datetime.utcnow().isoformat(),
            'currentWeek': current_stats,
            'previousWeek': prev_stats,
            'wowComparison': self._calculate_wow_comparison(
                current_stats, prev_stats
            ),
            'trends': self._analyze_trends(current_stats),
            'topIssues': await self._get_top_issues(start_date, end_date),
            'recommendations': self._generate_recommendations(
                current_stats, prev_stats
            )
        }

        return report_data

    async def generate_client_health_score(self, client_id: str) -> dict:
        """Generate health score for a specific client."""

        # Calculate metrics
        sla_adherence = await self._calculate_sla_adherence(client_id)
        error_rate = await self._calculate_error_rate(client_id)
        response_time = await self._calculate_avg_response_time(client_id)
        escalation_rate = await self._calculate_escalation_rate(client_id)

        # Weighted health score
        health_score = (
            sla_adherence * 0.35 +
            (100 - error_rate) * 0.30 +
            response_time * 0.20 +
            (100 - escalation_rate) * 0.15
        )

        return {
            'clientId': client_id,
            'healthScore': round(health_score, 1),
            'grade': self._score_to_grade(health_score),
            'metrics': {
                'slaAdherence': round(sla_adherence, 1),
                'errorRate': round(error_rate, 1),
                'avgResponseTimeMin': round(response_time, 1),
                'escalationRate': round(escalation_rate, 1)
            },
            'alerts': await self._get_client_alerts(client_id),
            'recommendations': self._generate_client_recommendations(
                client_id, health_score
            )
        }

    async def generate_fte_efficiency_report(self) -> dict:
        """Generate FTE efficiency metrics."""

        users = await self._get_active_users()
        metrics = []

        for user in users:
            user_stats = await self._get_user_stats(user['id'])
            metrics.append({
                'userId': user['id'],
                'userName': user['name'],
                'paPerHour': user_stats['submissions'] / user_stats['hours'],
                'automationRate': user_stats['automated'] / user_stats['total'],
                'errorRate': user_stats['errors'] / user_stats['total']
            })

        return {
            'generatedAt': datetime.utcnow().isoformat(),
            'teamSize': len(users),
            'avgPAPerFTEHour': sum(m['paPerHour'] for m in metrics) / len(metrics),
            'avgAutomationRate': sum(m['automationRate'] for m in metrics) / len(metrics),
            'userMetrics': sorted(metrics, key=lambda x: x['paPerHour'], reverse=True)
        }
```

### API.md

```yaml
GET /api/v1/reports/executive/daily
  Query:
    date?: string (YYYY-MM-DD, default yesterday)
  Response:
    report: DailyReport
    generatedAt: timestamp

GET /api/v1/reports/executive/weekly
  Query:
    weekEndDate?: string (default last week)
  Response:
    report: WeeklyReport
    wowComparison: WoWComparison

GET /api/v1/reports/client-health
  Query:
    clientId: string
  Response:
    healthScore: number
    grade: string
    metrics: HealthMetrics

GET /api/v1/reports/fte-efficiency
  Response:
    teamMetrics: FTEPerformance[]
    avgPAPerFTE: number

POST /api/v1/reports/schedule
  Body:
    reportType: 'daily' | 'weekly' | 'client_health'
    recipients: string[]
    schedule: CronExpression
  Response:
    scheduleId: string
    nextRun: timestamp
```

### UI.md

#### Executive Dashboard UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  📈 Executive Dashboard                    [Daily] [Weekly] [Export]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │  📊 Total PAs   │  │  ✅ Approval    │  │  ⚡ Automation  │    │
│  │     1,247       │  │     89.2%       │  │     94.7%       │    │
│  │   +12% WoW      │  │   +2.1% WoW     │  │   +0.5% WoW     │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Client Health Scores — This Week                              │  │
│  │                                                               │  │
│  │ NYCBS  ████████████████████████░  94.2 (A)  ✅ Excellent      │  │
│  │ Astera ███████████████████████░░  87.6 (B)  ⚠️ Good          │  │
│  │ BlueCross ███████████████████░░░  72.1 (C)  🔴 Fair           │  │
│  │                                                               │  │
│  │ [View Details] [Export Report]                                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Weekly Trend — PA Volume                                      │  │
│  │                                                               │  │
│  │ 1.4k├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─                              │  │
│  │    │     ╭─╮        ╭─╮                                      │  │
│  │  1.2k│ ─╮╭╯╰╮──╮──╭╯╰╮                                      │  │
│  │    │╭╯ │ ╰──╯  ╰──╯  ╰╮                                    │  │
│  │  1.0k├╯              ╰──╯                                    │  │
│  │    └────────────────────────                                │  │
│  │     Mon  Tue  Wed  Thu  Fri  Sat  Sun                        │  │
│  │     847  1,023  1,189  1,201  1,247  203  89                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4.3 Per-Feature Improvement Tracking

### README

**Problem**: No visibility into which features reduce manual work.
**Solution**: Dashboard analytics for dashboard usage.
**Impact**: Data-driven dashboard improvement.

### SPEC.md

#### Feature Analytics Implementation

```python
# feature_analytics.py

from collections import defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class FeatureUsageMetrics:
    feature_id: str
    feature_name: str
    usage_count: int
    unique_users: int
    avg_time_seconds: float
    abandonment_rate: float
    search_to_action_rate: float

class FeatureAnalytics:
    """Track and analyze feature usage patterns."""

    def __init__(self, db: FirestoreClient, bq_client):
        self.db = db
        self.bq = bq_client

    async def track_user_action(
        self,
        user_id: str,
        session_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        metadata: dict
    ):
        """Track a user action in the dashboard."""

        event = {
            'userId': user_id,
            'sessionId': session_id,
            'action': action,
            'resourceType': resource_type,
            'resourceId': resource_id,
            'metadata': metadata,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self.db.collection('feature_events').add(event)

    async def get_feature_heatmap(self) -> list[FeatureUsageMetrics]:
        """Generate feature usage heatmap."""

        # Query feature events
        query = self.db.collection('feature_events')

        events = query.get()

        # Aggregate by feature
        feature_stats = defaultdict(lambda: {
            'count': 0,
            'users': set(),
            'total_time': 0,
            'abandons': 0
        })

        for event in events:
            feature_id = event.get('metadata', {}).get('featureId', 'unknown')
            stats = feature_stats[feature_id]

            stats['count'] += 1
            stats['users'].add(event['userId'])
            stats['total_time'] += event.get('metadata', {}).get('duration', 0)

            if event['action'] == 'abandoned':
                stats['abandons'] += 1

        # Calculate metrics
        results = []
        for feature_id, stats in feature_stats.items():
            total_users = len(stats['users'])
            results.append(FeatureUsageMetrics(
                feature_id=feature_id,
                feature_name=self._get_feature_name(feature_id),
                usage_count=stats['count'],
                unique_users=total_users,
                avg_time_seconds=stats['total_time'] / stats['count'] if stats['count'] > 0 else 0,
                abandonment_rate=stats['abandons'] / stats['count'] if stats['count'] > 0 else 0,
                search_to_action_rate=self._calculate_search_to_action(feature_id)
            ))

        return sorted(results, key=lambda x: x.usage_count, reverse=True)
```

---

*Author: Kulraj Sabharwal, Technical PM*
*Phase 4 Timeline: Week 11-14*