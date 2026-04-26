# RISA Dashboard PRD — Shared Components & Templates

## PRD Template

Every PRD follows this structure:

```
PRD-[Phase]-[Feature]
├── README.md                 # One-page summary
├── SPEC.md                   # Detailed specification
├── API.md                    # API endpoints
├── UI.md                     # UI/UX specifications
├── DATA-MODELS.md            # Data structures
├── TESTING.md                # Test cases
└── assets/
    ├── mockups/              # UI mockups
    └── diagrams/             # Architecture diagrams
```

---

## Shared API Response Format

```typescript
// Standard API Response Wrapper
interface APIResponse<T> {
  success: boolean;
  data: T;
  meta: {
    timestamp: string;
    requestId: string;
    page?: number;
    pageSize?: number;
    totalCount?: number;
  };
  errors?: APIError[];
}

interface APIError {
  code: string;
  message: string;
  field?: string;
  details?: Record<string, unknown>;
}
```

---

## Shared Authentication Headers

```http
Authorization: Bearer {NOTION_API_TOKEN}
X-RISA-Version: 2024-01
X-Request-ID: {uuid}
Content-Type: application/json
```

---

## Notification System Specification

```typescript
interface Notification {
  id: string;
  type: 'info' | 'warning' | 'success' | 'error';
  category: 'status' | 'approval' | 'error' | 'reminder';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  actions?: NotificationAction[];
  createdAt: string;
  readAt?: string;
  expiresAt?: string;
}

interface NotificationAction {
  label: string;
  action: 'navigate' | 'api_call' | 'dismiss';
  payload: Record<string, unknown>;
}
```

---

## Dashboard Metrics Schema

```typescript
interface DashboardMetrics {
  utilizationScore: number;           // 0-100
  activeUsers: {
    daily: number;
    weekly: number;
    monthly: number;
  };
  featureAdoption: FeatureUsage[];
  manualReductionPercent: number;
  errorRatePerThousand: number;
  avgResolutionTimeMs: number;
  clientEscalations: number;
}

interface FeatureUsage {
  featureId: string;
  featureName: string;
  usageCount: number;
  uniqueUsers: number;
  avgTimeSpentSeconds: number;
  abandonmentRate: number;
}
```

---

## Event Logging Schema

```typescript
interface DashboardEvent {
  id: string;
  timestamp: string;
  userId: string;
  sessionId: string;
  action: DashboardAction;
  resource: {
    type: 'order' | 'document' | 'report' | 'approval';
    id: string;
  };
  metadata: Record<string, unknown>;
  performance: {
    loadTimeMs: number;
    renderTimeMs: number;
  };
}
```

---

*Last Updated: April 2026*
*Author: Kulraj Sabharwal, Technical PM*