#!/usr/bin/env python3
"""
Create detailed PRD child pages in Notion
"""

import httpx
import time
import os

NOTION_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
PARENT_PAGE_ID = os.environ.get("NOTION_PAGE_ID", "34e8fc2d-8618-81d9-9d2c-e6091d7db672")

if not NOTION_TOKEN:
    raise ValueError("Please set NOTION_API_TOKEN environment variable")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

BASE_URL = "https://api.notion.com/v1"

def create_page(parent_id: str, title: str, emoji: str = "📋", content: list = None) -> str:
    """Create a new page and optionally add content"""
    response = httpx.post(f"{BASE_URL}/pages", headers=HEADERS, json={
        "parent": {"page_id": parent_id},
        "icon": {"emoji": emoji},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        }
    }, timeout=30.0)

    if 'error' in response.json():
        print(f"  ❌ Error creating {title}: {response.json()['message']}")
        return None

    page_id = response.json()['id']
    print(f"  ✅ Created: {title} ({page_id})")

    if content:
        time.sleep(0.5)
        add_blocks(page_id, content)

    return page_id

def add_blocks(page_id: str, blocks: list, chunk_size: int = 50):
    """Add blocks to a page"""
    for i in range(0, len(blocks), chunk_size):
        chunk = blocks[i:i+chunk_size]
        httpx.post(f"{BASE_URL}/blocks/{page_id}/children", headers=HEADERS,
                   json={"children": chunk}, timeout=60.0)
        time.sleep(0.3)

def h(text: str, level: int = 2) -> dict:
    """Heading"""
    return {"object": "block", "type": f"heading_{level}",
            f"heading_{level}": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

def p(text: str) -> dict:
    """Paragraph"""
    return {"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

def b(text: str) -> dict:
    """Bullet"""
    return {"object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

def todo(text: str, checked: bool = False) -> dict:
    """To-do"""
    return {"object": "block", "type": "to_do",
            "to_do": {"rich_text": [{"type": "text", "text": {"content": text}}], "checked": checked}}

def code(content: str, language: str = "python") -> dict:
    """Code block"""
    return {"object": "block", "type": "code",
            "code": {"rich_text": [{"type": "text", "text": {"content": content}}], "language": language}}

def callout(emoji: str, text: str) -> dict:
    """Callout"""
    return {"object": "block", "type": "callout",
            "callout": {"rich_text": [{"type": "text", "text": {"content": text}}], "icon": {"emoji": emoji}}}

def div() -> dict:
    """Divider"""
    return {"object": "block", "type": "divider", "divider": {}}

def main():
    print("🚀 Creating Notion PRD pages...")

    # ===== PHASE 1: QUICK WINS =====
    phase1_content = [
        callout("📊", "High-impact, low-effort features for immediate improvement"),
        div(),
        h("1.1 Feature Discovery Overlay", 2),
        callout("⚠️", "Problem: Users don't know what the dashboard can do."),
        callout("💡", "Solution: In-app tooltips + \"New Features\" notification banner + first-time user tour."),
        h("User Experience", 3),
        b("First-Time User Tour — Triggered on first login, 5-step carousel, skip option"),
        b("Feature Discovery Tooltips — Appear on hover, 150ms delay, keyboard shortcuts"),
        b("\"New in Dashboard\" Banner — Shows 7 days after new feature, max 1 at a time"),
        div(),
        h("1.2 Status Comment Fetch from CMM", 2),
        callout("⚠️", "Problem: Status shows \"Sent to Plan\" but no plan response details."),
        callout("💡", "Solution: Auto-fetch CoverMyMeds status comments on status page with Firestore caching."),
        h("Data Flow", 3),
        code("""# RPA Service: cmm_status_fetcher.py
class CoverMyMedsClient:
    async def get_status_comments(self, request_id: str) -> list:
        response = await self._session.get(
            f"/api/v1/requests/{request_id}/comments"
        )
        return response.json().get("comments", [])""", "python"),
        div(),
        h("1.3 Dev/Prod Environment Toggle", 2),
        callout("⚠️", "Problem: PMs confused about which dashboard to use."),
        callout("💡", "Solution: Color-coded environment indicator + prominent switch with confirmation."),
        div(),
        h("1.4 Missing Data Pre-Filter", 2),
        callout("⚠️", "Problem: Users scan entire list looking for actionable items."),
        callout("💡", "Solution: One-click filter for incomplete orders with field selection."),
        div(),
        h("API Endpoints", 2),
        code("""POST /api/v1/users/{userId}/onboarding-tour
GET /api/v1/features/announcements
GET /api/v1/pa-orders?missingFields=prescriber_npi,patient_dob""", "yaml"),
        div(),
        h("Success Metrics", 2),
        todo("Onboarding tour completion: >80%", True),
        todo("CMM comment fetch: >500/day", True),
        todo("Env switch accuracy: 0 accidents", True),
        todo("Missing data filter: -50% search time", True),
    ]
    create_page(PARENT_PAGE_ID, "Phase 1: Quick Wins PRD", "⚡", phase1_content)

    # ===== PHASE 2: FEATURE COMPLETENESS =====
    phase2_content = [
        callout("📊", "Complete visibility gaps, approval workflows, and client-specific features"),
        div(),
        h("2.1 Planned Task Incorporation", 2),
        b("Scheduled PA Submission Queue — Dashboard view for time-based PA submissions"),
        b("Retry Queue Visibility — Visible retry dashboard instead of hidden logs"),
        b("Exception Routing — Dashboard alerts + queue for IRC/chat notifications"),
        h("Architecture", 3),
        code("""PLANNED TASK PIPELINE:
Scheduled → Ready Queue → Executing → Completed
     ↓            ↓           ↓          ↓
  Hold       Auto-       RPA        Success
           promote      running     Failed
                                  Retry""", "text"),
        div(),
        h("2.2 Approval Systems", 2),
        b("High-Value PA Approval Modal — In-dashboard approval instead of email chains"),
        b("Denial Escalation Queue — Dashboard queue + approve instead of IRC ping"),
        b("Manual Override Audit Trail — Dashboard approve + audit instead of direct DB write"),
        h("Approval Types", 3),
        code("""type ApprovalType =
  | 'high_value_pa'    // PA > $500 value
  | 'denial_escalation' // Denial appeal
  | 'manual_override'  // Manual data correction
  | 'exception_route'   // Non-standard workflow
  | 'bulk_approval'     // Batch operation""", "typescript"),
        div(),
        h("2.3 Client Operational Gaps", 2),
        h("🛡️ NYCBS Gaps", 3),
        todo("Batch File Status Visibility"),
        todo("Denial Letter Attachment Confirmation"),
        todo("SFTP Push/Pull Status Dashboard"),
        todo("Error Log Visibility Per Batch"),
        h("🔬 Astera Gaps", 3),
        todo("Email Attachment Fetch Status"),
        todo("Bulk Submission Progress Tracking"),
        todo("Single PA Submission Confirmation"),
        todo("OncoEMR Writeback Status"),
    ]
    create_page(PARENT_PAGE_ID, "Phase 2: Feature Completeness PRD", "🎯", phase2_content)

    # ===== PHASE 3: WRITE-BACK & INTEGRATION =====
    phase3_content = [
        callout("📊", "Complete EMR integrations, fax workflow, calling workflow, and external sync"),
        div(),
        h("3.1 FHIR Write-back Completion", 2),
        callout("⚠️", "Current: Partial writeback to OncoEMR."),
        callout("💡", "Target: Complete FHIR-compliant writeback for all outcomes."),
        h("FHIR R4 Resource Mapping", 3),
        code("""class FHIRWritebackService:
    async def write_approval(self, patient_mrn, order_id, approval_data):
        document = DocumentReference.parse_obj({
            "resourceType": "DocumentReference",
            "status": "current",
            "type": {"coding": [{"code": "34117-2"}]},
            "subject": {"reference": f"Patient/{patient_mrn}"},
            "content": [{"attachment": {"url": approval_data["letter_url"]}}]
        })
        return await self._client.post("/DocumentReference", json=document)""", "python"),
        div(),
        h("3.2 Fax Workflow Integration", 2),
        b("Inbound fax queue with dashboard notification"),
        b("Fax-to-PA routing with auto-creation"),
        b("Fax status tracking: Sent/failed/delivered"),
        h("Fax Service Architecture", 3),
        code("""class FaxService:
    async def receive_fax_webhook(self, webhook_data):
        # Download and parse fax
        fax_content = await self._download_fax(attachment_url)
        parsed_data = await self._parse_fax_for_pa(fax_content)
        # Auto-create PA order if valid
        if self._is_valid_pa_request(parsed_data):
            return await self._create_pa_order_from_fax(parsed_data)""", "python"),
        div(),
        h("3.3 Calling Workflow Integration", 2),
        b("Call queue: Patients requiring call → dashboard"),
        b("Call status: Attempted/completed/failed logged"),
        b("Callback scheduling: Schedule follow-up call from dashboard"),
        h("Call Outcomes", 3),
        code("""class CallOutcome(Enum):
    CONNECTED = "connected"      # Patient answered
    VOICEMAIL = "voicemail"      # Left voicemail
    NO_ANSWER = "no_answer"      # Ring, no answer
    WRONG_NUMBER = "wrong_number"# Number disconnected
    CALL_BACK_SCHEDULED = "callback_scheduled" """, "python"),
    ]
    create_page(PARENT_PAGE_ID, "Phase 3: Write-back Integration PRD", "🔄", phase3_content)

    # ===== PHASE 4: ANALYTICS & TRUST =====
    phase4_content = [
        callout("📊", "Systematic data reliability improvements, executive reporting, and feature analytics"),
        div(),
        h("4.1 RISA Pharma Analytics — Trust Recovery", 2),
        callout("⚠️", "Problem: Analytics gave wrong values, PMs lost trust."),
        callout("💡", "Solution: Systematic data reliability pass with verification framework."),
        h("Analytics Validator", 3),
        code("""class AnalyticsValidator:
    async def validate_pa_counts(self, start, end) -> ValidationResult:
        # Get ground truth from RPA logs
        rpa_counts = await self._count_rpa_submissions(start, end)
        # Get BigQuery analytics
        bq_counts = await self._query_bigquery_pa_counts(start, end)
        # Compare with 0.1% tolerance
        variance = abs(bq_counts - rpa_counts) / max(rpa_counts, 1)
        return ValidationResult(
            is_valid=variance <= 0.001,
            expected=rpa_counts,
            actual=bq_counts
        )""", "python"),
        div(),
        h("4.2 Executive Reports in Astera", 2),
        b("Daily Ops Summary — Refresh every 4 hours: volume, approval rate, errors"),
        b("Weekly Trend Report — Monday AM: WoW comparison, anomaly flags"),
        b("Client Health Score — Daily per-client SLA adherence"),
        b("FTE Efficiency Report — Weekly PAs per FTE, automation rate"),
        h("Report API", 3),
        code("""GET /api/v1/reports/executive/daily
GET /api/v1/reports/executive/weekly
GET /api/v1/reports/client-health?clientId=nycbs
GET /api/v1/reports/fte-efficiency""", "yaml"),
        div(),
        h("4.3 Per-Feature Improvement Tracking", 2),
        b("Feature usage heatmap — Which features used most"),
        b("Time-to-action — How fast users complete tasks"),
        b("Abandonment rate — Where users drop off"),
        b("Search-to-action — Does search find what users need"),
    ]
    create_page(PARENT_PAGE_ID, "Phase 4: Analytics Trust PRD", "📈", phase4_content)

    # ===== PHASE 5: STACK MAPPING =====
    phase5_content = [
        callout("📊", "Sales capability mapping and ops feature catalog for complete transparency"),
        div(),
        h("5.1 Sales Team Capability Map", 2),
        callout("📋", "\"If a client comes, what can we build?\""),
        h("Capability Matrix", 3),
        todo("Prior auth automation — PA Order Pipeline ✅ Live"),
        todo("Eligibility verification — EV-BV Service ✅ Live"),
        todo("EHR integration — OncoEMR writeback ✅ Live"),
        todo("Fax-based workflows — Fax API ✅ Live"),
        todo("AI document processing — PDF extraction ✅ Live"),
        todo("Multi-payer support — 50+ payer configs ✅ Live"),
        todo("Custom reporting — BigQuery + Dashboard 🟡 Partial"),
        todo("Mobile access — None 🔴 Gap"),
        todo("White-label — None 🔴 Gap"),
        div(),
        h("5.2 Ops Team Feature Catalog", 2),
        callout("📋", "\"Does feature X exist?\" — Complete feature catalog with locations and docs."),
        h("Feature Categories", 3),
        b("PA Orders: Create, View, Submit, Track"),
        b("Status Tracking: Real-time status updates"),
        b("Documents: Upload, Download, View"),
        b("Analytics: KPIs, Export, Trends"),
        b("SFTP: Upload, Status, Download"),
        b("Validator: Coverage Check, Eligibility"),
        b("Fax: Send, Inbox, Route to Order"),
        b("Reports: Daily, Weekly, Executive"),
    ]
    create_page(PARENT_PAGE_ID, "Phase 5: Stack Mapping PRD", "🗺️", phase5_content)

    # ===== ASTERA DAILY STATS =====
    astera_content = [
        callout("🔬", "Daily Operations Dashboard for Astera Pharmacy Client"),
        div(),
        h("Overview", 2),
        p("Astera operates in a high-volume pharmacy environment requiring real-time submission tracking and rapid turnaround monitoring. Unlike NYCBS (health system with batch focus), Astera needs intraday visibility."),
        div(),
        h("Volume Metrics", 2),
        b("Total Submissions Received — All PA requests in 24h"),
        b("Total Submissions Processed — PAs that reached terminal state"),
        b("Submissions by Source — Email, API, Manual, Batch"),
        b("Submissions by Drug/Therapy Class — GLP-1, Oncology, Diabetes, etc."),
        div(),
        h("Processing Metrics", 2),
        b("Processing Rate — PAs/hour (target: >60/hr sustained)"),
        b("Average Processing Time — Mean submission to completion"),
        b("Queue Depth Over Time — PAs waiting at each hour"),
        div(),
        h("Outcome Metrics", 2),
        b("Approval Rate — % of submitted PAs that received approval (target: >75%)"),
        b("Denial Rate + Analysis — Breakdown by denial reason"),
        b("Pend Rate — PAs pended for additional info"),
        b("Appeals Filed — Denials that were appealed"),
        div(),
        h("Quality Metrics", 2),
        b("First-Pass Success Rate — PAs processed without errors (target: >95%)"),
        b("Auto-Processed Rate — % processed fully automatically (target: >80%)"),
        b("Data Completeness Score — Orders with all required fields (target: >98%)"),
        div(),
        h("Integration Metrics", 2),
        b("OncoEMR Writeback Success Rate — FHIR writeback success (target: >99%)"),
        b("Email Attachment Processing — Extraction and parsing rates"),
        b("API Response Time — Average response time by endpoint"),
        div(),
        h("SLA Metrics", 2),
        b("SLA Compliance Rate — % of PAs completed within SLA"),
        b("Average Turnaround Time — By priority (STAT <60min, Urgent <4hr, Standard <24hr)"),
        b("PAs Breaching SLA — Count and list of at-risk orders"),
        div(),
        h("Daily Report Template", 2),
        code("""# Astera Daily Operations Report
**Date:** {DATE}
**Total PAs:** {count}
**Approval Rate:** {rate}%

## Highlights
- Peak hour: {peak_hour} ({count} PAs)
- Most common drug: {drug} ({pct}%)
- Most common payer: {payer} ({pct}%)

## Quality
- First-pass success: {fps}%
- SLA compliance: {sla}%
- Writeback success: {wb}%

## Watch List
{issues}""", "markdown"),
        div(),
        h("Automation Setup", 2),
        code("""class AsteraStatsLoader:
    def calculate_daily_stats(self, date) -> dict:
        return {
            'volume': self._get_volume_stats(),
            'processing': self._get_processing_stats(),
            'outcomes': self._get_outcome_stats(),
            'quality': self._get_quality_stats(),
            'integration': self._get_integration_stats(),
            'sla': self._get_sla_stats()
        }""", "python"),
        div(),
        h("Alert Thresholds", 2),
        b("Volume min: 500/day, max per hour: 150"),
        b("Approval rate warning: <85%, critical: <80%"),
        b("Auto-process rate warning: <90%, critical: <85%"),
        b("SLA compliance warning: <95%, critical: <90%"),
        b("Error rate warning: >1.5%, critical: >2%"),
    ]
    create_page(PARENT_PAGE_ID, "Astera Daily Stats Reporting", "📊", astera_content)

    print("\n✅ All PRD pages created!")
    print(f"   View main page: https://www.notion.so/RISA-Dashboard-Roadmap-100-Utilization-Plan-{PARENT_PAGE_ID}")

if __name__ == "__main__":
    main()