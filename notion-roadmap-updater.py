#!/usr/bin/env python3
"""
Notion API Helper for RISA Dashboard Roadmap
Adds charts, code, and PRDs to Notion page
"""

import httpx
import json
import time
from datetime import datetime

# Configuration - Set via environment variables
import os
NOTION_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
PAGE_ID = os.environ.get("NOTION_PAGE_ID", "34e8fc2d-8618-81d9-9d2c-e6091d7db672")

if not NOTION_TOKEN:
    raise ValueError("Please set NOTION_API_TOKEN environment variable")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

BASE_URL = "https://api.notion.com/v1"

def create_block(block_type: str, content: dict) -> dict:
    """Create a block based on type"""
    return {
        "object": "block",
        "type": block_type,
        block_type: content
    }

def add_heading(text: str, level: int = 1) -> dict:
    """Add a heading block"""
    heading_key = f"heading_{level}"
    return create_block(heading_key, {"rich_text": [{"type": "text", "text": {"content": text}}]})

def add_paragraph(text: str) -> dict:
    """Add a paragraph block"""
    return create_block("paragraph", {"rich_text": [{"type": "text", "text": {"content": text}}]})

def add_bullet(text: str) -> dict:
    """Add a bullet point"""
    return create_block("bulleted_list_item", {"rich_text": [{"type": "text", "text": {"content": text}}]})

def add_numbered(text: str) -> dict:
    """Add a numbered list item"""
    return create_block("numbered_list_item", {"rich_text": [{"type": "text", "text": {"content": text}}]})

def add_todo(text: str, checked: bool = False) -> dict:
    """Add a to-do item"""
    return create_block("to_do", {"rich_text": [{"type": "text", "text": {"content": text}}], "checked": checked})

def add_code(content: str, language: str = "python") -> dict:
    """Add a code block"""
    return create_block("code", {
        "rich_text": [{"type": "text", "text": {"content": content}}],
        "language": language
    })

def add_callout(emoji: str, text: str) -> dict:
    """Add a callout block"""
    return create_block("callout", {
        "rich_text": [{"type": "text", "text": {"content": text}}],
        "icon": {"emoji": emoji}
    })

def add_divider() -> dict:
    """Add a divider"""
    return create_block("divider", {})

def add_table_header(columns: list[str]) -> list[dict]:
    """Create table header rows"""
    return [{
        "object": "block",
        "type": "table_row",
        "table_row": {
            "cells": [[{"type": "text", "text": {"content": col}}] for col in columns]
        }
    }]

def add_table_row(columns: list[str]) -> dict:
    """Create a table row"""
    return {
        "object": "block",
        "type": "table_row",
        "table_row": {
            "cells": [[{"type": "text", "text": {"content": col}}] for col in columns]
        }
    }

def append_blocks(page_id: str, blocks: list[dict]) -> dict:
    """Append blocks to a page"""
    url = f"{BASE_URL}/blocks/{page_id}/children"
    response = httpx.post(url, headers=HEADERS, json={"children": blocks}, timeout=60.0)
    return response.json()

def create_child_page(parent_id: str, title: str) -> dict:
    """Create a child page"""
    url = f"{BASE_URL}/pages"
    response = httpx.post(url, headers=HEADERS, json={
        "parent": {"page_id": parent_id},
        "icon": {"emoji": "📋"},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        }
    }, timeout=60.0)
    return response.json()

def add_image_from_url(page_id: str, url: str, caption: str = "") -> dict:
    """Add an image block (via external URL)"""
    url_endpoint = f"{BASE_URL}/blocks/{page_id}/children"
    blocks = [{
        "object": "block",
        "type": "image",
        "image": {
            "type": "external",
            "external": {"url": url}
        },
        "image": {
            "caption": [{"type": "text", "text": {"content": caption}}] if caption else []
        }
    }]
    return httpx.post(url_endpoint, headers=HEADERS, json={"children": blocks}, timeout=60.0).json()

def clear_page(page_id: str):
    """Clear all blocks from a page"""
    url = f"{BASE_URL}/blocks/{page_id}/children"
    response = httpx.get(url, headers=HEADERS, timeout=30.0)
    blocks = response.json().get("results", [])
    for block in blocks:
        httpx.delete(f"{BASE_URL}/blocks/{block['id']}", headers=HEADERS, timeout=30.0)
    time.sleep(0.5)

def main():
    print("🚀 Starting Notion content update...")

    # Clear existing content
    print("  Clearing existing content...")
    clear_page(PAGE_ID)
    time.sleep(1)

    blocks = []

    # ===== HEADER SECTION =====
    blocks.append(add_callout("📊", "RISA Dashboard Roadmap | 16-Week Plan to Achieve 100% Utilization"))
    blocks.append(add_divider())

    # Stats Overview
    blocks.append(add_heading("📈 Current State", 2))
    blocks.append(add_bullet("13,509+ PA Orders Tracked"))
    blocks.append(add_bullet("80% Current Automation"))
    blocks.append(add_bullet("20% Manual Gap — High-Value Opportunities"))
    blocks.append(add_bullet("4 User Teams: PM, Ops, CS, Leadership"))
    blocks.append(add_divider())

    # ===== PHASE 1: QUICK WINS =====
    blocks.append(add_heading("🎯 Phase 1: Quick Wins (Week 1-2)", 2))

    # Feature Discovery
    blocks.append(add_heading("1.1 Feature Discovery Overlay", 3))
    blocks.append(add_callout("⚠️", "Problem: Users don't know what the dashboard can do."))
    blocks.append(add_callout("💡", "Solution: In-app tooltips + \"New Features\" notification banner + first-time user tour."))
    blocks.append(add_bullet("Impact: +15% adoption among occasional users"))
    blocks.append(add_bullet("Effort: Low (frontend overlay)"))
    blocks.append(add_bullet("Timeline: 1 Week"))
    blocks.append(add_divider())

    # CMM Status Fetch
    blocks.append(add_heading("1.2 Status Comment Fetch from CMM", 3))
    blocks.append(add_callout("⚠️", "Problem: Status shows \"Sent to Plan\" but no plan response details."))
    blocks.append(add_callout("💡", "Solution: Auto-fetch CoverMyMeds status comments on status page with Firestore caching."))
    blocks.append(add_bullet("Impact: Eliminates manual CMM login for status checks"))
    blocks.append(add_bullet("Effort: Medium (new API integration)"))
    blocks.append(add_bullet("Timeline: 2 Weeks"))
    blocks.append(add_divider())

    # Env Toggle
    blocks.append(add_heading("1.3 Dev/Prod Environment Toggle", 3))
    blocks.append(add_callout("⚠️", "Problem: PMs confused about which dashboard to use."))
    blocks.append(add_callout("💡", "Solution: Clear environment indicator (color-coded header) + prominent switch with confirmation."))
    blocks.append(add_bullet("Impact: Prevents prod accidents from dev testing"))
    blocks.append(add_bullet("Effort: Low (UI change)"))
    blocks.append(add_bullet("Timeline: 1 Week"))
    blocks.append(add_divider())

    # Missing Data Filter
    blocks.append(add_heading("1.4 Missing Data Pre-Filter", 3))
    blocks.append(add_callout("⚠️", "Problem: Users scan entire list looking for actionable items."))
    blocks.append(add_callout("💡", "Solution: One-click \"Show only items with missing data\" filter with field selection."))
    blocks.append(add_bullet("Impact: -50% time to find actionable items"))
    blocks.append(add_bullet("Effort: Low (filter logic)"))
    blocks.append(add_bullet("Timeline: 1 Week"))
    blocks.append(add_divider())

    # ===== PHASE 2: FEATURE COMPLETENESS =====
    blocks.append(add_heading("🎯 Phase 2: Feature Completeness (Week 3-6)", 2))

    blocks.append(add_heading("2.1 Planned Task Incorporation", 3))
    blocks.append(add_bullet("Scheduled PA Submission Queue — Dashboard view for time-based PA submissions"))
    blocks.append(add_bullet("Retry Queue Visibility — Visible retry dashboard instead of hidden logs"))
    blocks.append(add_bullet("Exception Routing — Dashboard alerts + queue for IRC/chat notifications"))

    blocks.append(add_heading("2.2 Approval Systems", 3))
    blocks.append(add_bullet("High-Value PA Approval Modal — In-dashboard approval instead of email chains"))
    blocks.append(add_bullet("Denial Escalation Queue — Dashboard queue + approve instead of IRC ping"))
    blocks.append(add_bullet("Manual Override Audit Trail — Dashboard approve + audit instead of direct DB write"))

    blocks.append(add_heading("2.3 Client Operational Gaps", 3))

    blocks.append(add_heading("🛡️ NYCBS Gaps", 4))
    blocks.append(add_todo("Batch File Status Visibility"))
    blocks.append(add_todo("Denial Letter Attachment Confirmation"))
    blocks.append(add_todo("SFTP Push/Pull Status Dashboard"))
    blocks.append(add_todo("Error Log Visibility Per Batch"))

    blocks.append(add_heading("🔬 Astera Gaps", 4))
    blocks.append(add_todo("Email Attachment Fetch Status"))
    blocks.append(add_todo("Bulk Submission Progress Tracking"))
    blocks.append(add_todo("Single PA Submission Confirmation"))
    blocks.append(add_todo("OncoEMR Writeback Status"))
    blocks.append(add_divider())

    # ===== PHASE 3: WRITE-BACK & INTEGRATION =====
    blocks.append(add_heading("🎯 Phase 3: Write-back & Integration (Week 7-10)", 2))

    blocks.append(add_heading("3.1 FHIR Write-back Completion", 3))
    blocks.append(add_bullet("Approval Note: Text note created → Structured FHIR DocumentReference"))
    blocks.append(add_bullet("Denial Letter: Manual upload → Auto-upload + FHIR attachment"))
    blocks.append(add_bullet("Status Update: Manual IRC → Auto-FHIR subscription"))

    blocks.append(add_heading("3.2 Fax Workflow Sync", 3))
    blocks.append(add_bullet("Inbound fax queue with dashboard notification"))
    blocks.append(add_bullet("Fax-to-PA routing with auto-creation"))
    blocks.append(add_bullet("Fax status tracking: Sent/failed/delivered"))
    blocks.append(add_bullet("Fax attachment linking to related PA order"))

    blocks.append(add_heading("3.3 Calling Workflow Integration", 3))
    blocks.append(add_bullet("Call queue: Patients requiring call → dashboard"))
    blocks.append(add_bullet("Call status: Attempted/completed/failed logged"))
    blocks.append(add_bullet("Callback scheduling: Schedule follow-up call from dashboard"))
    blocks.append(add_divider())

    # ===== PHASE 4: ANALYTICS & TRUST =====
    blocks.append(add_heading("🎯 Phase 4: Analytics & Trust (Week 11-14)", 2))

    blocks.append(add_heading("4.1 RISA Pharma Analytics — Trust Recovery", 3))
    blocks.append(add_bullet("Re-validate BigQuery queries against RPA logs"))
    blocks.append(add_bullet("Tune alert thresholds with 30-day stable run"))
    blocks.append(add_bullet("Fix ETL pipeline with daily reconciliation"))
    blocks.append(add_bullet("Real-time dashboard refresh (<5 min lag)"))
    blocks.append(add_callout("🎯", "Target: Dashboard value vs source-of-truth match rate 99.9%"))

    blocks.append(add_heading("4.2 Executive Reports in Astera", 3))
    blocks.append(add_bullet("Daily Ops Summary: Refresh every 4 hours — volume, approval rate, errors"))
    blocks.append(add_bullet("Weekly Trend Report: Monday AM — WoW comparison, anomaly flags"))
    blocks.append(add_bullet("Client Health Score: Daily per-client SLA adherence"))
    blocks.append(add_bullet("FTE Efficiency Report: Weekly PAs per FTE, automation rate"))
    blocks.append(add_divider())

    # ===== PHASE 5: STACK MAPPING =====
    blocks.append(add_heading("🎯 Phase 5: Stack Mapping (Week 15-16)", 2))

    blocks.append(add_heading("5.1 Sales Team Capability Map", 3))
    blocks.append(add_paragraph("\"If a client comes, what can we build?\""))

    blocks.append(add_heading("Capability Status", 4))
    blocks.append(add_todo("Prior auth automation — PA Order Pipeline ✅ Live"))
    blocks.append(add_todo("Eligibility verification — EV-BV Service ✅ Live"))
    blocks.append(add_todo("EHR integration — OncoEMR writeback ✅ Live"))
    blocks.append(add_todo("Fax-based workflows — Fax API ✅ Live"))
    blocks.append(add_todo("AI document processing — PDF extraction + Medical necessity ✅ Live"))
    blocks.append(add_todo("Multi-payer support — 50+ payer configs ✅ Live"))
    blocks.append(add_todo("Custom reporting — BigQuery + Dashboard 🟡 Partial"))
    blocks.append(add_todo("Mobile access — None 🔴 Gap"))
    blocks.append(add_todo("White-label — None 🔴 Gap"))
    blocks.append(add_todo("Client portal — None 🔴 Gap"))

    blocks.append(add_heading("5.2 Ops Team Feature Catalog", 3))
    blocks.append(add_paragraph("\"Does feature X exist?\" — Complete feature catalog with locations and docs."))
    blocks.append(add_divider())

    # ===== API SPECIFICATIONS =====
    blocks.append(add_heading("🔧 API Specifications", 2))

    blocks.append(add_heading("Planned Tasks API", 3))
    blocks.append(add_code("""GET /api/v1/planned-tasks
Response: {
  "tasks": [...],
  "scheduled": [...],
  "retry_queue": [...],
  "exception_routes": [...]
}""", "yaml"))

    blocks.append(add_heading("Approvals API", 3))
    blocks.append(add_code("""POST /api/v1/approvals
{
  "task_id": "...",
  "approval_type": "high_value_pa",
  "approved_by": "user_id",
  "notes": "..."
}""", "json"))

    blocks.append(add_heading("FHIR Writeback API", 3))
    blocks.append(add_code("""POST /api/v1/fhir/writeback
{
  "resourceType": "DocumentReference",
  "patientMrn": "...",
  "outcome": "approved",
  "documentUrl": "...",
  "author": "rpa-service"
}""", "json"))
    blocks.append(add_divider())

    # ===== SUCCESS CRITERIA =====
    blocks.append(add_heading("🎯 Success Criteria — Week 16", 2))

    blocks.append(add_heading("Operational Metrics", 3))
    blocks.append(add_todo("Zero PM manual BigQuery queries for operational decisions", True))
    blocks.append(add_todo("Zero client escalations due to \"can't see status\"", True))
    blocks.append(add_todo("Analytics errors: zero for 30+ consecutive days", True))
    blocks.append(add_todo("Feature adoption: 100% of available features used weekly", True))
    blocks.append(add_todo("Executive reports: zero raw data pulls", True))
    blocks.append(add_todo("Approval workflows: 100% in-dashboard", True))

    blocks.append(add_heading("Business Impact", 3))
    blocks.append(add_todo("NYCBS volume growth sustainable without proportional FTE increase", True))
    blocks.append(add_todo("Client retention improved via transparency", True))
    blocks.append(add_todo("Leadership decision speed: -70%", True))
    blocks.append(add_todo("Operational trust score: >4.5/5", True))
    blocks.append(add_divider())

    # ===== RISKS =====
    blocks.append(add_heading("⚠️ Risks & Mitigations", 2))

    blocks.append(add_heading("Feature Overload", 3))
    blocks.append(add_callout("📋", "Mitigation: Phase rollout with feedback loops between phases"))

    blocks.append(add_heading("Analytics Trust Takes Time", 3))
    blocks.append(add_callout("📊", "Mitigation: Start trust recovery Week 1, show progress weekly"))

    blocks.append(add_heading("Scope Creep", 3))
    blocks.append(add_callout("📅", "Mitigation: Strict phase gates with change control"))
    blocks.append(add_divider())

    # ===== MEASUREMENT FRAMEWORK =====
    blocks.append(add_heading("📊 Measurement Framework", 2))

    blocks.append(add_heading("Dashboard Utilization Score Formula", 3))
    blocks.append(add_code("""UTILIZATION_SCORE = (
  Active_Users / Total_Users × 25% +
  Feature_Adoption_Rate × 25% +
  Decision_queries_Via_Dashboard / Total_Decision_Queries × 25% +
  Manual_Steps_Eliminated / Total_Pre_Dashboard_Steps × 25%
)""", "python"))

    blocks.append(add_heading("Key Metrics Timeline", 3))
    blocks.append(add_bullet("Active daily users: +20% by Week 4, +80% by Week 16"))
    blocks.append(add_bullet("Feature adoption: 60% → 75% → 85% → 95% → 100%"))
    blocks.append(add_bullet("Manual query reduction: 80% → 85% → 92% → 97% → 100%"))
    blocks.append(add_bullet("Analytics error rate: -50% by Week 4, 0% by Week 16"))
    blocks.append(add_bullet("Client escalations: -20% by Week 4, -80% by Week 16"))
    blocks.append(add_divider())

    # ===== FOOTER =====
    blocks.append(add_callout("📅", "Document Version: 1.0 | Last Updated: April 2026 | Author: Kulraj Sabharwal, Technical PM"))

    print(f"  Adding {len(blocks)} blocks to Notion page...")

    # Batch append in chunks of 50
    chunk_size = 50
    for i in range(0, len(blocks), chunk_size):
        chunk = blocks[i:i+chunk_size]
        result = append_blocks(PAGE_ID, chunk)
        if 'error' in result:
            print(f"  ⚠️ Error at chunk {i}: {result.get('message', 'Unknown error')}")
        else:
            print(f"  ✅ Added blocks {i+1}-{min(i+chunk_size, len(blocks))}")
        time.sleep(0.5)

    print("✨ Notion page updated successfully!")
    print(f"  View at: https://www.notion.so/RISA-Dashboard-Roadmap-100-Utilization-Plan-{PAGE_ID}")

if __name__ == "__main__":
    main()