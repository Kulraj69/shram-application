# Phase 1 PRD: Quick Wins (Week 1-2)

## Summary

Four high-impact, low-effort features to immediately improve dashboard adoption and reduce manual work.

---

## 1.1 Feature Discovery Overlay

### README

**Problem**: Users don't know what the dashboard can do.
**Solution**: Contextual tooltips + "New Features" notification banner.
**Impact**: +15% adoption among occasional users.

### SPEC.md

#### User Experience

1. **First-Time User Tour**
   - Triggered on first login
   - 5-step carousel highlighting key features
   - Skip option always visible
   - Progress indicator (1/5, 2/5...)

2. **Feature Discovery Tooltips**
   - Appear on hover over feature icons
   - 150ms delay before showing
   - Include keyboard shortcut if applicable
   - Dismiss on click outside

3. **"New in Dashboard" Banner**
   - Shows for 7 days after new feature added
   - Dismissible per user
   - Links to feature documentation
   - Max 1 banner at a time

#### Visual Design

```
┌─────────────────────────────────────────────────────────┐
│  ✨ New Feature: Status Comment Fetch                  │
│  Now see CoverMyMeds responses directly in dashboard.   │
│  [Learn More] [Dismiss]                                 │
└─────────────────────────────────────────────────────────┘
```

#### Component States

| State | Background | Border | Icon |
|-------|------------|--------|------|
| Default | `#F8F9FA` | `#E5E7EB` | `#6B7280` |
| Hover | `#EFF6FF` | `#3B82F6` | `#3B82F6` |
| Active | `#DBEAFE` | `#2563EB` | `#2563EB` |
| New (7 days) | `#FEF3C7` | `#F59E0B` | `#F59E0B` |

### API.md

```yaml
POST /api/v1/users/{userId}/onboarding-tour
  Body:
    completed: boolean
    skippedAtStep: number?
    completedAt: timestamp

GET /api/v1/features/announcements
  Query:
    userId: string
    limit: number (default 5)
  Response:
    announcements: Announcement[]
    totalUnread: number

POST /api/v1/features/announcements/{id}/dismiss
  Body:
    userId: string

GET /api/v1/features/search?q={query}
  Response:
    results: FeatureResult[]
    suggestions: string[]
```

### UI.md

#### Tooltip Component

```typescript
interface TooltipProps {
  content: string;
  featureId: string;
  shortcut?: string;
  placement: 'top' | 'bottom' | 'left' | 'right';
  children: React.ReactNode;
}
```

**Styling (Tailwind)**:
```css
.tooltip-container { position: relative; display: inline-flex; }
.tooltip-bubble {
  @apply absolute z-50 px-3 py-2 text-sm bg-gray-900 text-white
         rounded-lg shadow-lg max-w-xs;
  @apply opacity-0 pointer-events-none transition-opacity duration-200;
}
.tooltip-container:hover .tooltip-bubble {
  @apply opacity-100 pointer-events-auto;
}
.tooltip-bubble::after {
  content: '';
  @apply absolute border-8 border-transparent;
}
.tooltip-bubble.top::after {
  @apply top-full left-1/2 -translate-x-1/2 border-t-gray-900;
}
```

#### Banner Component

```typescript
interface BannerProps {
  announcement: Announcement;
  onDismiss: () => void;
  onLearnMore: () => void;
}
```

**Design Tokens**:
- Banner height: 48px
- Icon size: 20px
- Font: Inter, 14px medium
- Padding: 16px horizontal, 12px vertical
- Animation: slideIn 300ms ease-out

---

## 1.2 Status Comment Fetch from CMM

### README

**Problem**: Status shows "Sent to Plan" but no plan response details.
**Solution**: Auto-fetch CoverMyMeds status comments on status page.
**Impact**: Eliminates manual CMM login for status checks.

### SPEC.md

#### Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Dashboard   │────▶│  RPA Service │────▶│ CoverMyMeds │
│  Status Page │     │  /cmm-fetch  │     │     API     │
└──────────────┘     └──────────────┘     └──────────────┘
       ▲                    │
       │                    ▼
       │            ┌──────────────┐
       └────────────│  Firestore   │
                    │   Cache      │
                    └──────────────┘
```

#### CMM API Integration

```python
# RPA Service: cmm_status_fetcher.py

import httpx
from datetime import datetime, timedelta
import asyncio

class CoverMyMedsClient:
    """Client for CoverMyMeds API integration."""

    BASE_URL = "https://api.covermymeds.com/api/v1"

    def __init__(self, api_key: str, rpa_user: str):
        self.api_key = api_key
        self.rpa_user = rpa_user
        self._session = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-RPA-User": rpa_user,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    async def get_request_status(self, request_id: str) -> dict:
        """Fetch full status including plan comments."""
        response = await self._session.get(
            f"{self.BASE_URL}/requests/{request_id}"
        )
        response.raise_for_status()
        return response.json()

    async def get_status_comments(self, request_id: str) -> list[dict]:
        """Fetch all status comments for a request."""
        response = await self._session.get(
            f"{self.BASE_URL}/requests/{request_id}/comments"
        )
        return response.json().get("comments", [])

    async def poll_for_updates(
        self,
        request_ids: list[str],
        interval_seconds: int = 300
    ) -> dict[str, list[dict]]:
        """Poll multiple requests for status updates."""
        results = {}
        for req_id in request_ids:
            comments = await self.get_status_comments(req_id)
            results[req_id] = comments
            await asyncio.sleep(0.5)  # Rate limit
        return results
```

#### Caching Strategy

```python
# Firestore cache schema
CACHE_COLLECTION = "cmm_status_cache"

def cache_key(request_id: str, user_id: str) -> str:
    return f"{request_id}_{user_id}"

def cache_entry(
    request_id: str,
    status: str,
    comments: list[dict],
    fetched_at: datetime
) -> dict:
    return {
        "request_id": request_id,
        "status": status,
        "comments": comments,
        "fetched_at": fetched_at,
        "ttl": fetched_at + timedelta(hours=1)
    }

async def get_cached_or_fetch(
    db: firestore.Client,
    client: CoverMyMedsClient,
    request_id: str,
    user_id: str
) -> dict:
    """Get from cache if fresh, otherwise fetch from CMM."""
    cache_ref = db.collection(CACHE_COLLECTION).document(cache_key(request_id, user_id))
    cached = cache_ref.get()

    if cached.exists:
        entry = cached.to_dict()
        if datetime.now() < entry["ttl"]:
            return entry  # Cache hit

    # Cache miss - fetch from CMM
    status_data = await client.get_request_status(request_id)
    comments = await client.get_status_comments(request_id)

    entry = cache_entry(request_id, status_data["status"], comments, datetime.now())
    cache_ref.set(entry)

    return entry
```

### DATA-MODELS.md

```typescript
// CoverMyMeds Response Mapping

interface CMMRequest {
  id: string;
  createdAt: string;
  updatedAt: string;
  status: CMMPayerStatus;
  planName: string;
  planId: string;
  drugName: string;
  drugNdc: string;
  patientDob: string;
  prescriberNpi: string;
  comments: CMMComment[];
  attachments: CMMAttachment[];
}

type CMMPayerStatus =
  | 'pending'           // 1-2 days
  | 'sent'              // Submitted
  | 'pdd_received'      // Plan received PADD
  | 'pdd_approved'      // Plan approved
  | 'pdd_denied'        // Plan denied
  | 'pdd_pended'        // Plan needs more info
  | 'appealed'          // Appealed
  | 'override'          // Override requested
  | 'closed';           // Request closed

interface CMMComment {
  id: string;
  author: string;
  authorType: 'plan' | 'user' | 'system';
  content: string;
  createdAt: string;
  isInternal: boolean;
  attachments: CMMAttachment[];
}

interface CMMAttachment {
  id: string;
  filename: string;
  contentType: string;
  url: string;
  uploadedAt: string;
}
```

### UI.md

#### Status Page Enhancement

```
┌────────────────────────────────────────────────────────────────┐
│  Order #PA-2026-0412-0001                                      │
│  ──────────────────────────────────────────────────────────── │
│                                                                │
│  Status:  🟡 Payer Review (3 days)                            │
│  Plan:    CVS Caremark                                         │
│  Drug:    Enbrel 50mg Auto-Injector                            │
│                                                                │
│  ──────────────────────────────────────────────────────────── │
│  📋 Plan Response (from CoverMyMeds)                         │
│  ──────────────────────────────────────────────────────────── │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 📅 Apr 24, 2026 — CVS Caremark                         │   │
│  │ "Prior authorization approved. member may receive      │   │
│  │  medication at participating pharmacy. Valid for        │   │
│  │  12 months."                                            │   │
│  │                                                        │   │
│  │ 📎 Attachment: Approval_Letter_2026-04-24.pdf          │   │
│  │           [Download] [View]                            │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 📅 Apr 22, 2026 — System                                │   │
│  │ "Request received and routed to clinical review."      │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  [View Full CMM History] [Refresh Status]                      │
└────────────────────────────────────────────────────────────────┘
```

---

## 1.3 Dev/Prod Environment Toggle

### README

**Problem**: PMs confused about which dashboard to use.
**Solution**: Clear environment indicator + prominent switch.
**Impact**: Prevents prod accidents from dev testing.

### SPEC.md

#### Environment Indicator Design

```
┌────────────────────────────────────────────────────────────────────┐
│ 🟡 DEV                                    [💻 Dev] [🚀 Prod]  [👤] │
└────────────────────────────────────────────────────────────────────┘

Header background color by environment:
- Development:  #FEF3C7 (amber-100)
- Staging:       #DBEAFE (blue-100)
- Production:    #DCFCE7 (green-100)
```

#### Environment Badge Component

```typescript
interface EnvBadgeProps {
  environment: 'development' | 'staging' | 'production';
  onSwitch: () => void;
}

// Styling
const envStyles = {
  development: {
    bg: 'bg-amber-100',
    text: 'text-amber-800',
    border: 'border-amber-300',
    icon: '⚠️'
  },
  staging: {
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    border: 'border-blue-300',
    icon: '🔵'
  },
  production: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-300',
    icon: '🚀'
  }
};
```

#### Switch Confirmation Modal

```typescript
interface SwitchConfirmationProps {
  targetEnv: Environment;
  onConfirm: () => void;
  onCancel: () => void;
}

// Logic: Require confirmation when switching TO production
// Show warning: "You are about to switch to PRODUCTION environment"
```

### API.md

```yaml
GET /api/v1/system/environment
  Response:
    current: 'development' | 'staging' | 'production'
    version: string
    lastDeploy: timestamp
    switchAvailable: boolean
    allowedEnvironments: string[]

POST /api/v1/system/environment/switch
  Body:
    targetEnvironment: 'development' | 'staging' | 'production'
    reason: string
    acknowledged: boolean (must be true for prod switch)
  Response:
    success: boolean
    redirectUrl: string
    sessionToken: string (new token for target env)
```

---

## 1.4 Missing Data Pre-Filter

### README

**Problem**: Users scan entire list looking for actionable items.
**Solution**: One-click "Show only items with missing data" filter.
**Impact**: -50% time to find actionable items.

### SPEC.md

#### Filter Logic

```typescript
interface MissingDataFilter {
  enabled: boolean;
  fields: MissingField[];
  mode: 'any' | 'all';  // Match any field OR all fields missing
}

type MissingField =
  | 'prescriber_npi'
  | 'patient_dob'
  | 'drug_ndc'
  | 'diagnosis_code'
  | 'chart_note'
  | 'prior_auth_history'
  | 'plan_response';

const missingDataPatterns = {
  prescriber_npi: (order) => !order.prescriber?.npi,
  patient_dob: (order) => !order.patient?.dateOfBirth,
  drug_ndc: (order) => !order.medication?.ndc,
  diagnosis_code: (order) => !order.diagnosis?.icd10,
  chart_note: (order) => !order.documents?.find(d => d.type === 'chart_note'),
  prior_auth_history: (order) => order.priorAuthCount === 0,
  plan_response: (order) => order.statusResponse === null
};
```

#### Filter UI

```
┌────────────────────────────────────────────────────────────────────┐
│  Filters: [All ▼] [Prescriber NPI ▼] [Patient DOB ▼]              │
│           [Drug NDC ▼] [Diagnosis ▼] [Documents ▼]                │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ ☐ Show only items with MISSING DATA                        │  │
│  │                                                             │  │
│  │ Missing: [Prescriber NPI] [Patient DOB]                    │  │
│  │          [Chart Note]         [Plan Response]              │  │
│  │                                                             │  │
│  │ [Select fields to filter]                                   │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Result: 127 of 13,509 orders have missing data                  │
└────────────────────────────────────────────────────────────────────┘
```

### API.md

```yaml
GET /api/v1/pa-orders
  Query:
    missingFields: string[]  # comma-separated
    missingMode: 'any' | 'all'
    page: number
    pageSize: number (max 100)
  Response:
    orders: PAOrder[]
    missingDataSummary: MissingDataSummary
    pagination: PaginationInfo

GET /api/v1/pa-orders/missing-data-summary
  Response:
    byField: Record<MissingField, {count: number; percentage: number}>
    totalAffected: number
    estimatedFixTime: number  # minutes
```

### TESTING.md

```python
# test_missing_data_filter.py

import pytest
from datetime import datetime

class TestMissingDataFilter:
    """Test cases for missing data filtering."""

    def test_filter_any_field_missing(self):
        """When mode='any', orders missing ANY selected field appear."""
        order = create_order(prescriber_npi=None, patient_dob="1990-01-01")
        filter_config = FilterConfig(
            enabled=True,
            fields=['prescriber_npi'],
            mode='any'
        )
        assert matches_filter(order, filter_config) == True

    def test_filter_all_fields_missing(self):
        """When mode='all', only orders missing ALL fields appear."""
        order = create_order(prescriber_npi=None, patient_dob=None)
        filter_config = FilterConfig(
            enabled=True,
            fields=['prescriber_npi', 'patient_dob'],
            mode='all'
        )
        assert matches_filter(order, filter_config) == True

    def test_filter_no_fields_missing(self):
        """Orders with no missing fields don't match filter."""
        order = create_order(
            prescriber_npi="1234567890",
            patient_dob="1990-01-01"
        )
        filter_config = FilterConfig(
            enabled=True,
            fields=['prescriber_npi'],
            mode='any'
        )
        assert matches_filter(order, filter_config) == False

    def test_empty_filter_returns_all(self):
        """When no fields selected, all orders match."""
        filter_config = FilterConfig(enabled=True, fields=[], mode='any')
        assert matches_filter(any_order, filter_config) == True

    @pytest.mark.asyncio
    async def test_api_returns_summary(self):
        """API returns count summary for each field."""
        response = await client.get("/api/v1/pa-orders/missing-data-summary")
        assert response.status == 200
        data = response.json()
        assert 'byField' in data
        assert all(f in data['byField'] for f in MissingField)
```

---

## Success Metrics

| Feature | Target | Measurement |
|---------|--------|-------------|
| Onboarding tour completion | >80% | Tour completion rate |
| Feature tooltips usage | >3 per session | Avg tooltips shown |
| CMM comment fetch | >500/day | API call count |
| Env switch accuracy | 0 accidents | Prod switch confirmations |
| Missing data filter | -50% search time | User timing studies |

---

*Author: Kulraj Sabharwal, Technical PM*
*Phase 1 Timeline: Week 1-2*