# Phase 5 PRD: Stack Mapping (Week 15-16)

## Summary

Sales capability mapping and ops feature catalog for complete dashboard transparency.

---

## 5.1 Sales Team Capability Map

### README

**Problem**: "If a client asks, what can we build?"
**Solution**: Complete capability map with status for sales team.
**Impact**: Sales knows what's possible before promising.

### SPEC.md

#### Capability Matrix Structure

```python
# capability_map.py

from dataclasses import dataclass
from typing import Optional
from enum import Enum

class CapabilityStatus(Enum):
    LIVE = "live"              # Production ready
    PARTIAL = "partial"        # Limited availability
    PLANNED = "planned"        # In development
    GAP = "gap"               # Not available
    DEPRECATED = "deprecated"  # Being phased out

class ClientSegment(Enum):
    HEALTH_SYSTEM = "health_system"
    PAYER = "payer"
    PHARMACY = "pharmacy"
    SPECIALTY = "specialty"
    ONCOLOGY = "oncology"

@dataclass
class Capability:
    id: str
    name: str
    category: str
    status: CapabilityStatus
    clients: list[ClientSegment]
    description: str
    dependencies: list[str]
    limitations: Optional[str]
    roadmap: Optional[str]

class CapabilityMap:
    """RISA capability mapping for sales and operations."""

    CAPABILITIES = [
        # Prior Authorization
        Capability(
            id="pa-automation",
            name="Prior Authorization Automation",
            category="Core Workflow",
            status=CapabilityStatus.LIVE,
            clients=[ClientSegment.HEALTH_SYSTEM, ClientSegment.PAYER],
            description="Automated PA submission, tracking, and writeback",
            dependencies=["CoverMyMeds integration"],
            roadmap=None
        ),
        Capability(
            id="pa-bulk",
            name="Bulk PA Processing",
            category="Core Workflow",
            status=CapabilityStatus.LIVE,
            clients=[ClientSegment.PAYER, ClientSegment.PHARMACY],
            description="CSV batch processing with SFTP integration",
            dependencies=["SFTP credentials"],
            roadmap=None
        ),
        Capability(
            id="pa-cmm-integration",
            name="CoverMyMeds Integration",
            category="Integration",
            status=CapabilityStatus.LIVE,
            clients=[ClientSegment.HEALTH_SYSTEM],
            description="Direct API integration with CMM for status and comments",
            dependencies=None,
            roadmap=None
        ),

        # Clinical Decision Support
        Capability(
            id="clinical-rules",
            name="Clinical Rules Engine",
            category="AI/ML",
            status=CapabilityStatus.LIVE,
            clients=[ClientSegment.HEALTH_SYSTEM],
            description="Medical necessity checking, step therapy enforcement",
            dependencies=["Clinical knowledge base"],
            roadmap=None
        ),
        Capability(
            id="ai-document-extraction",
            name="AI Document Extraction",
            category="AI/ML",
            status=CapabilityStatus.LIVE,
            clients=[ClientSegment.HEALTH_SYSTEM, ClientSegment.PHARMACY],
            description="PDF/text extraction for prior auth forms",
            dependencies=["ML models"],
            roadmap=None
        ),

        # EHR Integration
        Capability(
            id="fhir-writeback",
            name="FHIR R4 Writeback",
            category="Integration",
            status=CapabilityStatus.LIVE,
            clients=[ClientSegment.ONCOLOGY],
            description="Complete FHIR-compliant writeback to OncoEMR",
            dependencies=["FHIR endpoint access"],
            roadmap=None
        ),
        Capability(
            id="ehr-integration",
            name="EHR Integration",
            category="Integration",
            status=CapabilityStatus.PARTIAL,
            clients=[ClientSegment.HEALTH_SYSTEM],
            description="Bidirectional data exchange with major EHRs",
            dependencies=["EHR credentials, VPN"],
            limitations="Limited to Epic, Cerner, and Meditech",
            roadmap="Full HL7 support Q3 2026"
        ),

        # Fax Workflow
        Capability(
            id="fax-inbound",
            name="Inbound Fax Processing",
            category="Core Workflow",
            status=CapabilityStatus.LIVE,
            clients=[ClientSegment.HEALTH_SYSTEM, ClientSegment.PAYER],
            description="Fax-to-PA auto-creation with OCR",
            dependencies=["Fax service (RingCentral)"],
            roadmap=None
        ),
        Capability(
            id="fax-outbound",
            name="Outbound Fax",
            category="Core Workflow",
            status=CapabilityStatus.LIVE,
            clients=[ClientSegment.HEALTH_SYSTEM, ClientSegment.PAYER],
            description="Fax sending with tracking and confirmation",
            dependencies=["Fax service (RingCentral)"],
            roadmap=None
        ),

        # Calling
        Capability(
            id="patient-outreach",
            name="Patient Outreach",
            category="Communication",
            status=CapabilityStatus.PARTIAL,
            clients=[ClientSegment.HEALTH_SYSTEM],
            description="Automated patient calling for follow-up",
            dependencies=["Twilio integration"],
            limitations="Voice only, no SMS",
            roadmap="SMS and email integration Q4 2026"
        ),

        # Reporting
        Capability(
            id="analytics-dashboard",
            name="Analytics Dashboard",
            category="Reporting",
            status=CapabilityStatus.PARTIAL,
            clients=[ClientSegment.HEALTH_SYSTEM, ClientSegment.PAYER],
            description="Real-time dashboard with drill-down capabilities",
            dependencies=["BigQuery"],
            limitations="Currently 80% feature complete",
            roadmap="100% feature coverage by Week 16"
        ),

        # Client-Specific
        Capability(
            id="nycbs-sftp",
            name="NYCBS SFTP Integration",
            category="Client-Specific",
            status=CapabilityStatus.LIVE,
            clients=[ClientSegment.PAYER],
            description="Batch file push/pull for NYCBS",
            dependencies=["NYCBS SFTP credentials"],
            roadmap=None
        ),
        Capability(
            id="astera-api",
            name="Astera API Integration",
            category="Client-Specific",
            status=CapabilityStatus.LIVE,
            clients=[ClientSegment.PHARMACY],
            description="Astera platform API integration",
            dependencies=["Astera API credentials"],
            roadmap=None
        ),

        # Gaps
        Capability(
            id="mobile-access",
            name="Mobile App",
            category="Access",
            status=CapabilityStatus.GAP,
            clients=[],
            description="Native iOS/Android app for on-the-go access",
            dependencies=None,
            roadmap="Mobile app in roadmap for 2027"
        ),
        Capability(
            id="white-label",
            name="White Label",
            category="Branding",
            status=CapabilityStatus.GAP,
            clients=[],
            description="Custom branding and domain for clients",
            dependencies=None,
            roadmap="White-label offering Q1 2027"
        ),
        Capability(
            id="client-portal",
            name="Client Self-Service Portal",
            category="Access",
            status=CapabilityStatus.GAP,
            clients=[],
            description="Separate client-facing portal for status tracking",
            dependencies=None,
            roadmap="Client portal in roadmap"
        )
    ]

    def get_capability(self, capability_id: str) -> Optional[Capability]:
        """Get a specific capability by ID."""
        return next(
            (c for c in self.CAPABILITIES if c.id == capability_id),
            None
        )

    def get_by_status(self, status: CapabilityStatus) -> list[Capability]:
        """Get all capabilities with a specific status."""
        return [c for c in self.CAPABILITIES if c.status == status]

    def get_by_client(self, client: ClientSegment) -> list[Capability]:
        """Get all capabilities available for a client segment."""
        return [c for c in self.CAPABILITIES if client in c.clients]

    def can_deliver(
        self,
        requirements: list[str]
    ) -> dict[str, any]:
        """Check if RISA can deliver a set of requirements."""
        delivered = []
        gaps = []
        partial = []

        for req in requirements:
            capability = self._match_requirement(req)
            if capability:
                if capability.status == CapabilityStatus.LIVE:
                    delivered.append(capability)
                elif capability.status == CapabilityStatus.PARTIAL:
                    partial.append(capability)
                else:
                    gaps.append(capability)
            else:
                gaps.append(req)

        return {
            'can_deliver': len(gaps) == 0,
            'delivered': delivered,
            'partial': partial,
            'gaps': gaps
        }
```

### Capability Matrix Visualization

```
┌─────────────────────────────────────────────────────────────────────┐
│  📋 RISA CAPABILITY MAP                          [Export] [Filter] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CATEGORY         │ LIVE        │ PARTIAL    │ PLANNED   │ GAP     │
│  ─────────────────┼─────────────┼────────────┼───────────┼─────────│
│  Core Workflow    │            │            │           │         │
│  ├─ PA Automation │     ✅      │            │           │         │
│  ├─ Bulk Process  │     ✅      │            │           │         │
│  ├─ Fax Workflow  │     ✅      │            │           │         │
│  └─ Calling       │             │     🟡     │           │         │
│  ─────────────────┼─────────────┼────────────┼───────────┼─────────│
│  Integration      │            │            │           │         │
│  ├─ CMM           │     ✅      │            │           │         │
│  ├─ FHIR Writeback│     ✅      │            │           │         │
│  ├─ EHR           │             │     🟡     │           │         │
│  └─ External API  │     ✅      │            │           │         │
│  ─────────────────┼─────────────┼────────────┼───────────┼─────────│
│  AI/ML            │            │            │           │         │
│  ├─ Clinical Rules│     ✅      │            │           │         │
│  └─ Doc Extraction│     ✅      │            │           │         │
│  ─────────────────┼─────────────┼────────────┼───────────┼─────────│
│  Access           │            │            │           │         │
│  ├─ Dashboard     │     ✅      │            │           │         │
│  ├─ Mobile App    │             │            │           │    🔴   │
│  └─ Client Portal │             │            │           │    🔴   │
│  ─────────────────┼─────────────┼────────────┼───────────┼─────────│
│  Branding         │            │            │           │         │
│  └─ White Label   │             │            │           │    🔴   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5.2 Ops Team Feature Catalog

### README

**Problem**: "Does feature X exist?"
**Solution**: Complete feature catalog with locations and docs.
**Impact**: Zero "does X exist?" questions.

### SPEC.md

#### Feature Catalog Structure

```python
# feature_catalog.py

from dataclasses import dataclass
from typing import Optional, list
from enum import Enum

class FeatureCategory(Enum):
    PA_ORDERS = "PA Orders"
    STATUS_TRACKING = "Status Tracking"
    DOCUMENTS = "Documents"
    ANALYTICS = "Analytics"
    SFTP = "SFTP Operations"
    VALIDATOR = "Coverage Validator"
    FAX = "Fax"
    REPORTS = "Reports"
    ADMIN = "Administration"

class FeatureMaturity(Enum):
    STABLE = "stable"
    BETA = "beta"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"

@dataclass
class FeatureEntry:
    feature_id: str
    name: str
    category: FeatureCategory
    description: str
    dashboard_location: str
    api_endpoint: str
    maturity: FeatureMaturity
    added_in_version: str
    docs_url: Optional[str]
    related_features: list[str]
    example_usage: str

class FeatureCatalog:
    """Complete feature catalog for RISA dashboard."""

    FEATURES = [
        # PA Orders
        FeatureEntry(
            feature_id="pa-create",
            name="Create PA Order",
            category=FeatureCategory.PA_ORDERS,
            description="Create a new prior authorization order",
            dashboard_location="Worklists → New Order",
            api_endpoint="/api/v1/pa-orders/create",
            maturity=FeatureMaturity.STABLE,
            added_in_version="1.0",
            docs_url="/docs/pa-orders#create",
            related_features=["pa-submit", "pa-track"],
            example_usage="POST /api/v1/pa-orders/create { patient, medication, prescriber }"
        ),
        FeatureEntry(
            feature_id="pa-view",
            name="View PA Order",
            category=FeatureCategory.PA_ORDERS,
            description="View details of a specific PA order",
            dashboard_location="Worklists → Search",
            api_endpoint="/api/v1/pa-orders/{id}",
            maturity=FeatureMaturity.STABLE,
            added_in_version="1.0",
            docs_url="/docs/pa-orders#view",
            related_features=["pa-create", "pa-edit"],
            example_usage="GET /api/v1/pa-orders/PA-2026-0412-0001"
        ),
        FeatureEntry(
            feature_id="pa-submit",
            name="Submit to Payer",
            category=FeatureCategory.PA_ORDERS,
            description="Submit PA order to insurance plan",
            dashboard_location="Order → Send to Plan",
            api_endpoint="/api/v1/pa-orders/{id}/submit",
            maturity=FeatureMaturity.STABLE,
            added_in_version="1.0",
            docs_url="/docs/pa-orders#submit",
            related_features=["pa-create", "pa-track"],
            example_usage="POST /api/v1/pa-orders/PA-2026-0412-0001/submit"
        ),
        FeatureEntry(
            feature_id="pa-track",
            name="Track PA Status",
            category=FeatureCategory.STATUS_TRACKING,
            description="Track status changes of PA order",
            dashboard_location="Status Page",
            api_endpoint="/api/v1/status/{id}",
            maturity=FeatureMaturity.STABLE,
            added_in_version="1.0",
            docs_url="/docs/status#track",
            related_features=["cmm-comments"],
            example_usage="GET /api/v1/status/PA-2026-0412-0001"
        ),

        # Documents
        FeatureEntry(
            feature_id="doc-upload",
            name="Upload Document",
            category=FeatureCategory.DOCUMENTS,
            description="Upload supporting document to order",
            dashboard_location="Order → Upload",
            api_endpoint="/api/v1/documents/upload",
            maturity=FeatureMaturity.STABLE,
            added_in_version="1.2",
            docs_url="/docs/documents#upload",
            related_features=["doc-download", "doc-view"],
            example_usage="POST /api/v1/documents/upload { orderId, file, type }"
        ),
        FeatureEntry(
            feature_id="doc-download",
            name="Download Document",
            category=FeatureCategory.DOCUMENTS,
            description="Download attached document",
            dashboard_location="Order → Documents",
            api_endpoint="/api/v1/documents/{id}/download",
            maturity=FeatureMaturity.STABLE,
            added_in_version="1.0",
            docs_url="/docs/documents#download",
            related_features=["doc-upload"],
            example_usage="GET /api/v1/documents/DOC-123/download"
        ),

        # Analytics
        FeatureEntry(
            feature_id="analytics-kpi",
            name="View KPIs",
            category=FeatureCategory.ANALYTICS,
            description="View key performance indicators",
            dashboard_location="Summary Page",
            api_endpoint="/api/v1/summary-stats",
            maturity=FeatureMaturity.STABLE,
            added_in_version="1.0",
            docs_url="/docs/analytics#kpis",
            related_features=["analytics-detailed"],
            example_usage="GET /api/v1/summary-stats"
        ),
        FeatureEntry(
            feature_id="analytics-export",
            name="Export Analytics",
            category=FeatureCategory.ANALYTICS,
            description="Export analytics data to CSV/Excel",
            dashboard_location="Summary → Export",
            api_endpoint="/api/v1/analytics/export",
            maturity=FeatureMaturity.BETA,
            added_in_version="2.1",
            docs_url="/docs/analytics#export",
            related_features=["analytics-kpi"],
            example_usage="POST /api/v1/analytics/export { format, dateRange }"
        ),

        # SFTP
        FeatureEntry(
            feature_id="sftp-upload",
            name="Upload Batch File",
            category=FeatureCategory.SFTP,
            description="Upload batch file to SFTP for processing",
            dashboard_location="SFTP Page → Upload",
            api_endpoint="/api/v1/sftp/upload",
            maturity=FeatureMaturity.STABLE,
            added_in_version="1.5",
            docs_url="/docs/sftp#upload",
            related_features=["sftp-status"],
            example_usage="POST /api/v1/sftp/upload { file, clientId }"
        ),
        FeatureEntry(
            feature_id="sftp-status",
            name="SFTP Status",
            category=FeatureCategory.SFTP,
            description="Monitor SFTP batch processing status",
            dashboard_location="SFTP Page → Status",
            api_endpoint="/api/v1/sftp/{operationId}/status",
            maturity=FeatureMaturity.STABLE,
            added_in_version="1.5",
            docs_url="/docs/sftp#status",
            related_features=["sftp-upload"],
            example_usage="GET /api/v1/sftp/OP-123/status"
        ),

        # Validator
        FeatureEntry(
            feature_id="validator-check",
            name="Coverage Check",
            category=FeatureCategory.VALIDATOR,
            description="Verify patient coverage and benefits",
            dashboard_location="Validator Page",
            api_endpoint="/api/v1/coverage/check",
            maturity=FeatureMaturity.STABLE,
            added_in_version="1.3",
            docs_url="/docs/coverage#check",
            related_features=["validator-eligibility"],
            example_usage="POST /api/v1/coverage/check { patientId, drugNdc, payerId }"
        ),

        # Fax
        FeatureEntry(
            feature_id="fax-send",
            name="Send Fax",
            category=FeatureCategory.FAX,
            description="Send outbound fax for PA order",
            dashboard_location="Fax Page → Compose",
            api_endpoint="/api/v1/fax/send",
            maturity=FeatureMaturity.STABLE,
            added_in_version="2.0",
            docs_url="/docs/fax#send",
            related_features=["fax-inbox", "fax-track"],
            example_usage="POST /api/v1/fax/send { orderId, recipientFax, documentUrl }"
        ),
        FeatureEntry(
            feature_id="fax-inbox",
            name="View Fax Inbox",
            category=FeatureCategory.FAX,
            description="View received faxes",
            dashboard_location="Fax Page → Inbox",
            api_endpoint="/api/v1/fax/inbox",
            maturity=FeatureMaturity.STABLE,
            added_in_version="2.0",
            docs_url="/docs/fax#inbox",
            related_features=["fax-send", "fax-route"],
            example_usage="GET /api/v1/fax/inbox"
        ),
        FeatureEntry(
            feature_id="fax-route",
            name="Route Fax to Order",
            category=FeatureCategory.FAX,
            description="Link received fax to existing PA order",
            dashboard_location="Fax Inbox → Route",
            api_endpoint="/api/v1/fax/{faxId}/route-to-pa",
            maturity=FeatureMaturity.STABLE,
            added_in_version="2.0",
            docs_url="/docs/fax#route",
            related_features=["fax-inbox"],
            example_usage="POST /api/v1/fax/FAX-123/route-to-pa { orderId }"
        ),

        # Reports
        FeatureEntry(
            feature_id="report-daily",
            name="Daily Report",
            category=FeatureCategory.REPORTS,
            description="Generate daily operations summary",
            dashboard_location="Reports → Daily",
            api_endpoint="/api/v1/reports/daily",
            maturity=FeatureMaturity.STABLE,
            added_in_version="1.8",
            docs_url="/docs/reports#daily",
            related_features=["report-weekly", "report-executive"],
            example_usage="GET /api/v1/reports/daily"
        ),
        FeatureEntry(
            feature_id="report-executive",
            name="Executive Report",
            category=FeatureCategory.REPORTS,
            description="Generate executive summary for leadership",
            dashboard_location="Reports → Executive",
            api_endpoint="/api/v1/reports/executive/daily",
            maturity=FeatureMaturity.STABLE,
            added_in_version="2.0",
            docs_url="/docs/reports#executive",
            related_features=["report-daily"],
            example_usage="GET /api/v1/reports/executive/daily"
        )
    ]

    def get_feature(self, feature_id: str) -> Optional[FeatureEntry]:
        """Get a specific feature by ID."""
        return next(
            (f for f in self.FEATURES if f.feature_id == feature_id),
            None
        )

    def get_by_category(self, category: FeatureCategory) -> list[FeatureEntry]:
        """Get all features in a category."""
        return [f for f in self.FEATURES if f.category == category]

    def search(self, query: str) -> list[FeatureEntry]:
        """Search features by name or description."""
        query_lower = query.lower()
        return [
            f for f in self.FEATURES
            if query_lower in f.name.lower() or query_lower in f.description.lower()
        ]
```

### Feature Catalog UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔍 Search features...                              [All] [Filter ▼] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CATEGORIES                                                         │
│  ├── [📋] PA Orders (4)                                            │
│  ├── [📍] Status Tracking (1)                                      │
│  ├── [📄] Documents (2)                                           │
│  ├── [📊] Analytics (2)                                            │
│  ├── [📁] SFTP (2)                                                  │
│  ├── [✅] Validator (1)                                            │
│  ├── [📠] Fax (3)                                                   │
│  └── [📈] Reports (2)                                              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 📋 PA Orders                                                    │  │
│  │                                                               │  │
│  │ ┌───────────────────────────────────────────────────────────┐ │  │
│  │ │ Create PA Order                          [STABLE] [Docs]   │ │  │
│  │ │────────────────────────────────────────────────────────── │ │  │
│  │ │ Location: Worklists → New Order                           │ │  │
│  │ │ API: POST /api/v1/pa-orders/create                        │ │  │
│  │ │ Since: v1.0 | Related: View Order, Submit                 │ │  │
│  │ │                                                           │ │  │
│  │ │ Example:                                                  │ │  │
│  │ │ ┌─────────────────────────────────────────────────────┐ │ │  │
│  │ │ │ POST /api/v1/pa-orders/create                       │ │ │  │
│  │ │ │ {                                                    │ │ │  │
│  │ │ │   "patient": { "name": "...", "dob": "..." },       │ │ │  │
│  │ │ │   "medication": { "name": "...", "ndc": "..." },    │ │ │  │
│  │ │ │   "prescriber": { "npi": "..." }                    │ │ │  │
│  │ │ │ }                                                    │ │ │  │
│  │ │ └─────────────────────────────────────────────────────┘ │ │  │
│  │ │                                                           │ │  │
│  │ │ [Copy API] [View Docs]                                   │ │  │
│  │ └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Success Metrics

| Feature | Target | Measurement |
|---------|--------|-------------|
| Capability map accuracy | 100% | Sales can accurately describe capabilities |
| Feature catalog completeness | 100% | No "feature not found" issues |
| Sales discovery time | <2 min | Time to find capability answer |

---

*Author: Kulraj Sabharwal, Technical PM*
*Phase 5 Timeline: Week 15-16*