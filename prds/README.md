# RISA Dashboard PRD Documentation

Comprehensive Product Requirements Documents for the RISA Dashboard 100% Utilization Roadmap.

---

## Structure

```
prds/
├── README.md                    # This file
├── shared/
│   └── SHARED-COMPONENTS.md     # Shared API schemas, data models, and components
├── phase1-quick-wins/
│   └── README.md                # Phase 1: Feature Discovery, CMM Fetch, Env Toggle, Missing Data Filter
├── phase2-feature-completeness/
│   └── README.md                # Phase 2: Planned Tasks, Approvals, NYCBS/Astera Gaps
├── phase3-writeback/
│   └── README.md                # Phase 3: FHIR Writeback, Fax, Calling, GG Sync
├── phase4-analytics-trust/
│   └── README.md                # Phase 4: Analytics Recovery, Executive Reports, Feature Tracking
├── phase5-stack-mapping/
│   └── README.md                # Phase 5: Sales Capability Map, Feature Catalog
├── ASTERA_DAILY_STATS.md        # Astera daily stats reporting spec (NEW)
└── assets/
    ├── charts/                  # Chart mockups and specifications
    ├── diagrams/                # Architecture diagrams
    └── code/                    # Code snippets and implementations
```

---

## Quick Reference

### Phase 1: Quick Wins (Week 1-2)

| Feature | Description | Impact |
|---------|-------------|--------|
| Feature Discovery Overlay | In-app tooltips + "New Features" banner | +15% adoption |
| CMM Status Fetch | Auto-fetch CoverMyMeds comments | Eliminates manual login |
| Dev/Prod Toggle | Clear environment indicator | Prevents prod accidents |
| Missing Data Filter | One-click filter for incomplete orders | -50% search time |

### Phase 2: Feature Completeness (Week 3-6)

| Feature | Description | Impact |
|---------|-------------|--------|
| Planned Task Visibility | Dashboard queue view | Zero "did I submit?" |
| Approval Workflow | In-dashboard approval modal | Zero email threads |
| NYCBS Operations | SFTP, batch, denial letter tracking | Client self-service |
| Astera Operations | Email, bulk, OncoEMR writeback | Client self-service |

### Phase 3: Write-back & Integration (Week 7-10)

| Feature | Description | Impact |
|---------|-------------|--------|
| FHIR Writeback | Complete FHIR-compliant writeback | Zero manual docs |
| Fax Workflow | Fax in main dashboard | Single workflow |
| Calling Workflow | Call outcomes in dashboard | Complete hub |
| GG Sync | External system visibility | Integration status |

### Phase 4: Analytics & Trust (Week 11-14)

| Feature | Description | Impact |
|---------|-------------|--------|
| Analytics Trust Recovery | Data reliability pass | PM trust restored |
| Executive Reports | Daily/weekly automated reports | Zero raw pulls |
| Feature Tracking | Dashboard usage analytics | Data-driven improvement |

### Phase 5: Stack Mapping (Week 15-16)

| Feature | Description | Impact |
|---------|-------------|--------|
| Sales Capability Map | "What can we build?" | Sales clarity |
| Ops Feature Catalog | "Does feature X exist?" | Zero "does X exist?" |

---

## Astera Daily Stats

New documentation for Astera-specific daily operations reporting:

- **Overview**: Astera operates in high-volume pharmacy environment
- **Metrics**: Volume, Processing, Outcomes, Quality, Integration, SLA
- **Reporting**: Morning handoff reports, weekly trends, Google Sheets automation
- **Comparison**: NYCBS vs Astera differences (batch vs real-time focus)

See `ASTERA_DAILY_STATS.md` for complete documentation.

---

## Usage

### Reading a Phase PRD

1. Navigate to the phase folder (e.g., `phase1-quick-wins/`)
2. Open `README.md`
3. Each feature contains:
   - **README**: One-page summary with problem/solution/impact
   - **SPEC.md**: Detailed specification (embedded in README)
   - **API.md**: API endpoint definitions with examples
   - **UI.md**: UI/UX specifications with mockups
   - **DATA-MODELS.md**: Data structure definitions
   - **TESTING.md**: Test cases and scenarios

### Shared Components

For common schemas, API patterns, and components:
- See `shared/SHARED-COMPONENTS.md`

### Adding a New Phase

1. Create folder: `phaseN-name/`
2. Add `README.md` with structure:
   ```
   # Phase N: [Title]
   ## Summary
   ## [Feature 1]
   ### README
   ### SPEC.md
   ### API.md
   ### UI.md
   ```

---

## Dependencies

- **Python 3.10+** for code examples
- **TypeScript** for API schemas
- **Google Cloud** (BigQuery, Firestore) for data layer
- **CoverMyMeds API** for status fetching
- **FHIR R4** for EMR writeback

---

## Contact

- **Author**: Kulraj Sabharwal, Technical PM
- **Document Status**: Active
- **Last Updated**: April 2026
- **Review Cycle**: Monthly