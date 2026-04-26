# Phase 3 PRD: Write-back & Integration (Week 7-10)

## Summary

Complete EMR integrations, fax workflow, calling workflow, and external system sync.

---

## 3.1 FHIR Write-back Completion

### README

**Problem**: Partial writeback to OncoEMR.
**Solution**: Complete FHIR-compliant writeback for all outcomes.
**Impact**: Complete EMR integration, zero manual documentation.

### SPEC.md

#### FHIR R4 Resource Mapping

```python
# fhir_writeback_service.py

from typing import Optional
from datetime import datetime
import httpx
from fhir.resources.R4B import (
    DocumentReference,
    CommunicationRequest,
    Communication,
    Annotation,
    Reference,
    CodeableConcept,
    Coding
)

class FHIRWritebackService:
    """FHIR R4 compliant writeback to OncoEMR."""

    FHIR_BASE_URL = "https://fhir.oncoemr.example.com/r4"

    def __init__(self, auth_token: str, db: FirestoreClient):
        self.auth_token = auth_token
        self.db = db
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/fhir+json",
                "Accept": "application/fhir+json"
            },
            timeout=30.0
        )

    async def write_approval(
        self,
        patient_mrn: str,
        order_id: str,
        approval_data: dict
    ) -> dict:
        """Create FHIR DocumentReference for PA approval."""

        # Build DocumentReference resource
        document = DocumentReference.parse_obj({
            "resourceType": "DocumentReference",
            "status": "current",
            "docStatus": "final",
            "type": CodeableConcept.parse_obj({
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "34117-2",
                    "display": "History and physical note"
                }]
            }).dict(),
            "subject": {
                "reference": f"Patient/{patient_mrn}"
            },
            "date": datetime.utcnow().isoformat(),
            "author": [{
                "reference": "Practitioner/rpa-service",
                "display": "RISA RPA Service"
            }],
            "description": f"Prior Authorization Approval for Order {order_id}",
            "content": [{
                "attachment": {
                    "contentType": "application/pdf",
                    "url": approval_data["approval_letter_url"],
                    "title": f"PA_Approval_{order_id}.pdf"
                }
            }],
            "context": {
                "related": [{
                    "ref": f"ServiceRequest/prior-auth-{order_id}",
                    "display": f"Prior Authorization Request {order_id}"
                }]
            }
        })

        # Post to FHIR server
        response = await self._client.post(
            f"{self.FHIR_BASE_URL}/DocumentReference",
            json=document.dict(exclude_none=True)
        )

        if response.status_code >= 400:
            raise FHIRError(f"Failed to create DocumentReference: {response.text}")

        result = response.json()

        # Log to Firestore
        await self._log_writeback(
            order_id=order_id,
            resource_type="DocumentReference",
            resource_id=result["id"],
            outcome="success"
        )

        return result

    async def write_denial(
        self,
        patient_mrn: str,
        order_id: str,
        denial_data: dict
    ) -> dict:
        """Create FHIR Communication + DocumentReference for PA denial."""

        # 1. Create DocumentReference for denial letter
        denial_doc = DocumentReference.parse_obj({
            "resourceType": "DocumentReference",
            "status": "current",
            "docStatus": "final",
            "type": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "34117-2",
                    "display": "History and physical note"
                }]
            },
            "subject": {"reference": f"Patient/{patient_mrn}"},
            "date": datetime.utcnow().isoformat(),
            "author": [{
                "reference": "Practitioner/rpa-service"
            }],
            "description": f"Prior Authorization Denial - Order {order_id}",
            "content": [{
                "attachment": {
                    "contentType": "application/pdf",
                    "url": denial_data["denial_letter_url"],
                    "title": f"PA_Denial_{order_id}.pdf"
                }
            }],
            "context": {
                "related": [{
                    "ref": f"ServiceRequest/prior-auth-{order_id}"
                }]
            }
        })

        doc_response = await self._client.post(
            f"{self.FHIR_BASE_URL}/DocumentReference",
            json=denial_doc.dict(exclude_none=True)
        )

        # 2. Create Communication for clinical note
        communication = Communication.parse_obj({
            "resourceType": "Communication",
            "status": "completed",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystemCommunicationCategory",
                    "code": "notification",
                    "display": "Notification"
                }]
            }],
            "subject": {"reference": f"Patient/{patient_mrn}"},
            "sent": datetime.utcnow().isoformat(),
            "payload": [{
                "contentString": self._build_denial_note(order_id, denial_data)
            }]
        })

        comm_response = await self._client.post(
            f"{self.FHIR_BASE_URL}/Communication",
            json=communication.dict(exclude_none=True)
        )

        # Log both
        await self._log_writeback(order_id, "DocumentReference", doc_response.json()["id"], "success")
        await self._log_writeback(order_id, "Communication", comm_response.json()["id"], "success")

        return {
            "documentReferenceId": doc_response.json()["id"],
            "communicationId": comm_response.json()["id"]
        }

    async def subscribe_to_status_updates(
        self,
        patient_mrn: str,
        order_id: str,
        callback_url: str
    ) -> dict:
        """Create FHIR Subscription for real-time status updates."""

        subscription = {
            "resourceType": "Subscription",
            "status": "active",
            "channelType": {
                "system": "http://terminology.hl7.org/CodeSystem/subscription-channel-type",
                "code": "rest-hook"
            },
            "endpoint": callback_url,
            "criteria": f"ServiceRequest?subject=Patient/{patient_mrn}",
            "payload": "application/fhir+json",
            "filter": {
                "modifier": "text",
                "value": f"PriorAuth-{order_id}"
            }
        }

        response = await self._client.post(
            f"{self.FHIR_BASE_URL}/Subscription",
            json=subscription
        )

        return response.json()

    def _build_denial_note(self, order_id: str, denial_data: dict) -> str:
        """Build human-readable denial note for Communication payload."""
        return f"""
Prior Authorization Denial - Order {order_id}
-------------------------------------------
Denied by: {denial_data.get('plan_name', 'Unknown')}
Denial Reason: {denial_data.get('reason', 'Not specified')}
 Denial Date: {denial_data.get('denial_date', datetime.utcnow().date())}
Appeal Deadline: {denial_data.get('appeal_deadline', 'Not specified')}

Clinical Rationale: {denial_data.get('clinical_rationale', 'Not provided')}

Action Required: {'Appeal' if denial_data.get('requires_appeal') else 'None'}

This is an automated notification from RISA prior authorization system.
""".strip()

    async def _log_writeback(
        self,
        order_id: str,
        resource_type: str,
        resource_id: str,
        outcome: str
    ):
        """Log FHIR writeback attempt to Firestore."""
        await self.db.collection('fhir_writeback_log').add({
            'orderId': order_id,
            'resourceType': resource_type,
            'resourceId': resource_id,
            'outcome': outcome,
            'createdAt': datetime.utcnow().isoformat()
        })


class FHIRError(Exception):
    """FHIR API error."""
    pass
```

#### FHIR Data Models

```typescript
// fhir.resources.ts

// Core FHIR R4 Types for PA Writeback

interface DocumentReference {
  resourceType: 'DocumentReference';
  id?: string;
  status: 'current' | 'superseded' | 'entered-in-error';
  docStatus?: 'final' | 'amended' | 'preliminary';
  type?: CodeableConcept;
  subject: Reference;
  date?: string;
  author?: Reference[];
  description?: string;
  content: DocumentContent[];
  context?: DocumentContext;
}

interface DocumentContent {
  attachment: Attachment;
  format?: Coding;
}

interface Attachment {
  contentType?: string;
  language?: string;
  data?: string;          // base64 encoded
  url?: string;           // URL to external content
  size?: number;
  hash?: string;
  title?: string;
  creation?: string;
}

interface DocumentContext {
  event?: CodeableConcept[];
  period?: Period;
  facilityType?: CodeableConcept;
  related?: RelatedResource[];
}

interface Communication {
  resourceType: 'Communication';
  id?: string;
  status: 'in-progress' | 'completed' | 'entered-in-error';
  category?: CodeableConcept[];
  subject?: Reference;
  sent?: string;
  received?: string;
  payload?: CommunicationPayload[];
}

interface CommunicationPayload {
  contentString?: string;
  contentAttachment?: Attachment;
  contentReference?: Reference;
}

interface ServiceRequest {
  resourceType: 'ServiceRequest';
  id?: string;
  status: 'active' | 'completed' | 'cancelled';
  intent: 'order' | 'plan' | 'proposal';
  subject: Reference;
  code?: CodeableConcept;
  orderDetail?: CodeableConcept[];
}

interface Subscription {
  resourceType: 'Subscription';
  id?: string;
  status: 'active' | 'inactive' | 'requested';
  channelType: Coding;
  endpoint: string;
  criteria: string;
  payload?: string;
}
```

### API.md

```yaml
POST /api/v1/fhir/writeback
  Body:
    resourceType: 'DocumentReference' | 'Communication'
    patientMrn: string
    orderId: string
    outcome: 'approved' | 'denied' | 'pended' | 'appealed'
    documentUrl?: string
    clinicalNote?: string
    author: string (system or user id)
  Response:
    fhirResourceId: string
    resourceType: string
    createdAt: timestamp

POST /api/v1/fhir/writeback/batch
  Body:
    writebacks: WritebackRequest[]
  Response:
    results: WritebackResult[]
    successCount: number
    failureCount: number

GET /api/v1/fhir/writeback/status/{orderId}
  Response:
    orderId: string
    writebacks: FHIRWritebackRecord[]
    lastWriteback: timestamp
    errors: WritebackError[]

POST /api/v1/fhir/subscription
  Body:
    patientMrn: string
    orderId: string
    callbackUrl: string
    eventTypes: string[]
  Response:
    subscriptionId: string
    status: 'active'

GET /api/v1/fhir/subscription/{subscriptionId}
  Response:
    subscriptionId: string
    status: string
    createdAt: timestamp
    lastNotification: timestamp

DELETE /api/v1/fhir/subscription/{subscriptionId}
  Response:
    success: boolean
```

---

## 3.2 Fax Workflow Integration

### README

**Problem**: Fax handled separately from main dashboard.
**Solution**: Fax integrated into main dashboard workflow.
**Impact**: Fax no longer a separate workflow.

### SPEC.md

#### Fax Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FAX WORKFLOW                                 │
└─────────────────────────────────────────────────────────────────────┘

INBOUND FAX                                         OUTBOUND FAX
────────────                                        ─────────────
                                                                │
    Fax Server                                                  │
    (RingCentral)                                               │
        │                                                       │
        ▼                                                       ▼
┌─────────────────┐                                    ┌─────────────────┐
│  Fax Parser     │                                    │  Fax Compose   │
│  - OCR/Text     │                                    │  - Template     │
│  - Data Extract │                                    │  - PDF Generate │
│  - Route Logic  │                                    │  - Cover Sheet  │
└────────┬────────┘                                    └────────┬────────┘
         │                                                      │
         ▼                                                      ▼
┌─────────────────┐                                    ┌─────────────────┐
│  PA Order Auto  │                                    │  Fax Delivery   │
│  Creation       │                                    │  - Track Status │
│  - Parse fields │                                    │  - Confirm      │
│  - Match patient│                                    │  - Retry        │
│  - Create order │                                    └────────┬────────┘
└────────┬────────┘                                             │
         │                                                      │
         ▼                                                      ▼
┌─────────────────┐                                    ┌─────────────────┐
│  Dashboard      │                                    │  Dashboard      │
│  Notification   │                                    │  Status View   │
│  - New fax      │                                    │  - Sent        │
│  - Linked to PA │                                    │  - Delivered   │
└─────────────────┘                                    │  - Failed      │
                                                       └─────────────────┘
```

#### Fax Service Implementation

```python
# fax_service.py

from typing import Optional
from enum import Enum
import httpx
from datetime import datetime
import asyncio

class FaxDirection(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class FaxStatus(Enum):
    RECEIVED = "received"
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"

class FaxService:
    """Fax workflow management for PA orders."""

    FAX_PROVIDER = "ringcentral"  # or "twilio_fax", "zipwire"
    FAX_API_URL = "https://platform.ringcentral.com/restapi/v1.0"

    def __init__(self, api_key: str, db: FirestoreClient):
        self.api_key = api_key
        self.db = db
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0
        )

    async def receive_fax_webhook(self, webhook_data: dict) -> str:
        """Handle incoming fax webhook from provider."""

        fax_id = webhook_data["faxId"]
        caller = webhook_data["from"]
        recipient = webhook_data["to"]
        page_count = webhook_data["pageCount"]
        attachment_url = webhook_data["pages"][0]["url"]

        # Download fax content
        fax_content = await self._download_fax(attachment_url)

        # Parse fax content for PA data
        parsed_data = await self._parse_fax_for_pa(fax_content)

        # Create PA order if valid
        if parsed_data and self._is_valid_pa_request(parsed_data):
            pa_order_id = await self._create_pa_order_from_fax(parsed_data)

            # Link fax to order
            await self._link_fax_to_order(fax_id, pa_order_id)

            # Notify dashboard users
            await self._notify_new_fax(pa_order_id, parsed_data)

            return pa_order_id

        # Fax received but couldn't create order
        await self._create_fax_received_record(
            fax_id=fax_id,
            direction=FaxDirection.INBOUND,
            caller=caller,
            parsed_data=parsed_data,
            status=FaxStatus.RECEIVED
        )

        return None

    async def send_fax(
        self,
        order_id: str,
        recipient_fax: str,
        document_url: str,
        cover_sheet_data: dict
    ) -> dict:
        """Send outbound fax for PA order."""

        # Generate cover sheet PDF
        cover_pdf = await self._generate_cover_sheet(order_id, cover_sheet_data)

        # Merge with document
        merged_pdf = await self._merge_documents([cover_pdf, document_url])

        # Upload to fax provider
        upload_response = await self._upload_fax_document(merged_pdf)

        # Send fax
        fax_response = await self._client.post(
            f"{self.FAX_API_URL}/fax",
            json={
                "to": [{"phoneNumber": recipient_fax}],
                "attachments": [{"id": upload_response["id"]}],
                "coverPageText": f"PA Order: {order_id}"
            }
        )

        fax_data = fax_response.json()

        # Track fax
        await self._create_outbound_fax_record(
            fax_id=fax_data["id"],
            order_id=order_id,
            recipient=recipient_fax,
            status=FaxStatus.SENDING
        )

        return {
            "faxId": fax_data["id"],
            "status": FaxStatus.SENDING.value,
            "estimatedPages": fax_data["pageCount"]
        }

    async def get_fax_status(self, fax_id: str) -> dict:
        """Get current status of a fax."""

        response = await self._client.get(f"{self.FAX_API_URL}/fax/{fax_id}")
        fax_data = response.json()

        return {
            "faxId": fax_id,
            "status": self._map_fax_status(fax_data["completionStatus"]),
            "pagesSent": fax_data.get("sentPageCount", 0),
            "totalPages": fax_data.get("pageCount", 0),
            "duration": fax_data.get("duration", 0),
            "result": fax_data.get("result", "pending")
        }

    async def route_fax_to_pa_order(
        self,
        fax_id: str,
        target_order_id: str
    ) -> bool:
        """Link an existing fax to a PA order."""

        fax_ref = self.db.collection('faxes').document(fax_id)
        fax_ref.update({
            'linkedOrderId': target_order_id,
            'linkedAt': datetime.utcnow().isoformat(),
            'linkedBy': 'user'  # or 'system'
        })

        # Add fax to order's document list
        order_ref = self.db.collection('pa_orders').document(target_order_id)
        order_doc = order_ref.get().to_dict()

        documents = order_doc.get('documents', [])
        documents.append({
            'type': 'fax',
            'faxId': fax_id,
            'addedAt': datetime.utcnow().isoformat()
        })
        order_ref.update({'documents': documents})

        return True

    async def _parse_fax_for_pa(self, fax_content: bytes) -> dict:
        """Parse fax content to extract PA request data."""

        # Use OCR + NLP to extract structured data
        extracted_text = await self._ocr_fax(fax_content)

        # Parse extracted text for PA fields
        pa_data = {
            'patientName': self._extract_field(extracted_text, ['patient name', 'patient']),
            'patientDob': self._extract_field(extracted_text, ['dob', 'date of birth']),
            'drugName': self._extract_field(extracted_text, ['medication', 'drug', 'drug name']),
            'prescriberName': self._extract_field(extracted_text, ['prescriber', 'doctor']),
            'prescriberNpi': self._extract_field(extracted_text, ['npi']),
            'diagnosisCode': self._extract_field(extracted_text, ['icd', 'diagnosis code'])
        }

        return pa_data

    def _is_valid_pa_request(self, parsed_data: dict) -> bool:
        """Validate parsed data has minimum required fields."""
        required_fields = ['patientName', 'drugName', 'prescriberNpi']
        return all(parsed_data.get(field) for field in required_fields)
```

### API.md

```yaml
GET /api/v1/fax/inbox
  Query:
    status?: FaxStatus[]
    fromDate?: timestamp
    toDate?: timestamp
    page: number
    pageSize: number
  Response:
    faxes: Fax[]
    unreadCount: number

GET /api/v1/fax/{faxId}
  Response:
    fax: Fax
    linkedOrder?: OrderSummary
    history: FaxStatusHistory[]

GET /api/v1/fax/{faxId}/route-to-pa
  Body:
    targetOrderId: string
  Response:
    success: boolean
    linkedOrderId: string

POST /api/v1/fax/{faxId}/attach-to-order
  Body:
    orderId: string
    documentType: 'fax'
  Response:
    success: boolean

POST /api/v1/fax/send
  Body:
    orderId: string
    recipientFax: string
    documentUrl: string
    coverSheet: CoverSheetData
  Response:
    faxId: string
    status: FaxStatus
    estimatedPages: number

GET /api/v1/fax/sent
  Query:
    orderId?: string
    status?: FaxStatus[]
  Response:
    faxes: OutboundFax[]

GET /api/v1/fax/{faxId}/status
  Response:
    faxId: string
    status: FaxStatus
    pagesSent: number
    totalPages: number
    result: string
```

### UI.md

#### Fax Dashboard UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  📠 Fax Center                              [Inbox] [Sent] [Compose]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 📥 INBOX (3 new)                        [Mark All Read] [Filter]│  │
│  │                                                               │  │
│  │ ┌───────────────────────────────────────────────────────────┐ │  │
│  │ │ 🆕 Fax #4451 — Received 5 minutes ago                      │ │  │
│  │ │                                                             │ │  │
│  │ │ From: (555) 123-4567 — Dr. Williams Office                  │ │  │
│  │ │ Pages: 3 | Status: New — Auto-creating PA Order...          │ │  │
│  │ │                                                             │ │  │
│  │ │ Patient: Martinez, Rosa | Drug: Opdivo 240mg               │ │  │
│  │ │ [View Fax] [View Created Order] [Link to Existing]         │ │  │
│  │ └───────────────────────────────────────────────────────────┘ │  │
│  │                                                               │  │
│  │ ┌───────────────────────────────────────────────────────────┐ │  │
│  │ │ Fax #4450 — Today 2:30 PM                                  │ │  │
│  │ │ From: (555) 987-6543                                      │ │  │
│  │ │ [Link to Order PA-2026-0412-0891 ▼]                      │ │  │
│  │ └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 📤 SENT (12 today)                                           │  │
│  │                                                               │  │
│  │ ┌───────────────────────────────────────────────────────────┐ │  │
│  │ │ Fax #4455 — PA-2026-0412-0891 → (555) 246-8135           │ │  │
│  │ │ Status: ✅ Delivered | Pages: 5 | Sent: 3:15 PM          │ │  │
│  │ └───────────────────────────────────────────────────────────┘ │  │
│  │                                                               │  │
│  │ ┌───────────────────────────────────────────────────────────┐ │  │
│  │ │ Fax #4454 — PA-2026-0412-0890 → (555) 135-7924           │ │  │
│  │ │ Status: ⏳ Sending (2/4 pages) | Retrying...              │ │  │
│  │ └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3.3 Calling Workflow Integration

### README

**Problem**: Calling workflow not in dashboard.
**Solution**: Call outcomes visible and actionable in dashboard.
**Impact**: Complete patient communication hub.

### SPEC.md

#### Calling Service Implementation

```python
# calling_workflow_service.py

from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

@dataclass
class CallRecord:
    call_id: str
    patient_phone: str
    patient_name: str
    order_id: str
    purpose: str
    outcome: CallOutcome
    duration_seconds: int
    recording_url: Optional[str]
    notes: str
    called_at: datetime
    called_by: str

class CallOutcome(Enum):
    CONNECTED = "connected"           # Patient answered
    VOICEMAIL = "voicemail"           # Left voicemail
    NO_ANSWER = "no_answer"          # Ring, no answer
    WRONG_NUMBER = "wrong_number"    # Number disconnected
    BUSY = "busy"                    # Line busy
    CALL_BACK_SCHEDULED = "callback_scheduled"

class CallingWorkflowService:
    """Manage calling workflow for PA follow-ups."""

    def __init__(
        self,
        db: FirestoreClient,
        call_provider: 'CallProvider',  # Twilio, Bandwidth, etc.
        notification_service: NotificationService
    ):
        self.db = db
        self.provider = call_provider
        self.notifications = notification_service

    async def get_call_queue(self, user_id: str) -> list[dict]:
        """Get patients requiring callback for a user."""

        # Query for orders needing calls
        query = self.db.collection('pa_orders').where(
            'status', '==', 'needs_callback'
        ).where(
            'assignedTo', '==', user_id
        )

        orders = query.get()

        queue = []
        for order in orders:
            order_data = order.to_dict()

            # Check if already called today
            recent_call = await self._get_recent_call(order.id, user_id)
            if recent_call:
                continue  # Skip if already called

            queue.append({
                'orderId': order.id,
                'patientName': order_data['patient']['name'],
                'patientPhone': order_data['patient']['phone'],
                'callPurpose': order_data['callbackReason'],
                'priority': order_data.get('priority', 'normal'),
                'attempts': order_data.get('callAttempts', 0),
                'lastAttempt': order_data.get('lastCallAttempt')
            })

        return sorted(queue, key=lambda x: (
            x['priority'] != 'urgent',
            x['lastAttempt'] is None,
            x['attempts']
        ))

    async def initiate_call(
        self,
        user_id: str,
        order_id: str,
        call_purpose: str
    ) -> dict:
        """Initiate outbound call to patient."""

        order_doc = self.db.collection('pa_orders').document(order_id)
        order_data = order_doc.get().to_dict()

        if not order_data.get('patient', {}).get('phone'):
            raise ValueError(f"No phone number for order {order_id}")

        # Make the call via provider
        call_result = await self.provider.make_call(
            to=order_data['patient']['phone'],
            from_=self._get_available_line(),
            recording=True,
            webhook_url=f"https://rpa.risalabs.com/calls/webhook/{order_id}"
        )

        # Log call attempt
        call_record = {
            'callId': call_result['callId'],
            'orderId': order_id,
            'userId': user_id,
            'purpose': call_purpose,
            'status': 'in_progress',
            'startedAt': datetime.utcnow().isoformat(),
            'patientPhone': order_data['patient']['phone']
        }

        await self.db.collection('call_records').add(call_record)

        # Update order call attempts
        order_doc.update({
            'callAttempts': (order_data.get('callAttempts', 0)) + 1,
            'lastCallAttempt': datetime.utcnow().isoformat()
        })

        return {
            'callId': call_result['callId'],
            'status': 'connecting',
            'patientPhone': self._mask_phone(order_data['patient']['phone'])
        }

    async def record_call_outcome(
        self,
        call_id: str,
        outcome: CallOutcome,
        notes: str = "",
        callback_scheduled: Optional[datetime] = None
    ) -> bool:
        """Record the outcome of a call."""

        call_doc = self.db.collection('call_records').document(call_id)
        call_data = call_doc.get().to_dict()

        # Update call record
        call_doc.update({
            'outcome': outcome.value,
            'notes': notes,
            'completedAt': datetime.utcnow().isoformat(),
            'durationSeconds': self._calculate_duration(
                call_data['startedAt']
            )
        })

        # If callback scheduled, create follow-up task
        if callback_scheduled:
            await self._schedule_callback(
                order_id=call_data['orderId'],
                scheduled_time=callback_scheduled,
                user_id=call_data['userId']
            )

        # Update order status based on outcome
        await self._update_order_after_call(
            order_id=call_data['orderId'],
            outcome=outcome
        )

        # Create activity log
        await self._log_call_activity(call_data, outcome, notes)

        return True

    async def schedule_callback(
        self,
        order_id: str,
        user_id: str,
        scheduled_time: datetime,
        patient_phone: str,
        callback_reason: str
    ) -> str:
        """Schedule a callback for a later time."""

        task_data = {
            'type': 'scheduled_callback',
            'orderId': order_id,
            'patientPhone': patient_phone,
            'scheduledAt': scheduled_time.isoformat(),
            'userId': user_id,
            'reason': callback_reason,
            'status': 'pending',
            'createdBy': user_id,
            'createdAt': datetime.utcnow().isoformat()
        }

        doc_ref = await self.db.collection('scheduled_callbacks').add(task_data)

        # Schedule the actual call
        await self._schedule_call_task(doc_ref.id, scheduled_time)

        return doc_ref.id

    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for display."""
        if len(phone) == 10:
            return f"(***) ***-{phone[-4:]}"
        return phone

    async def _schedule_call_task(self, callback_id: str, scheduled_time: datetime):
        """Internal: Schedule RPA task to make the call."""
        # This would integrate with the planned task scheduler
        pass

    async def _update_order_after_call(
        self,
        order_id: str,
        outcome: CallOutcome
    ):
        """Update PA order based on call outcome."""

        status_map = {
            CallOutcome.CONNECTED: 'callback_completed',
            CallOutcome.VOICEMAIL: 'voicemail_left',
            CallOutcome.CALL_BACK_SCHEDULED: 'callback_pending',
            CallOutcome.NO_ANSWER: 'callback_needed',
            CallOutcome.WRONG_NUMBER: 'contact_info_invalid'
        }

        order_ref = self.db.collection('pa_orders').document(order_id)
        order_ref.update({
            'callStatus': outcome.value,
            'lastCallOutcome': outcome.value,
            'lastCallAt': datetime.utcnow().isoformat()
        })
```

### API.md

```yaml
GET /api/v1/calls/queue
  Query:
    userId: string
    limit: number
  Response:
    queue: CallQueueItem[]
    totalWaiting: number

POST /api/v1/calls/initiate
  Body:
    orderId: string
    purpose: string
  Response:
    callId: string
    status: 'connecting'
    patientPhoneMasked: string

POST /api/v1/calls/{callId}/outcome
  Body:
    outcome: 'connected' | 'voicemail' | 'no_answer' | 'wrong_number' | 'busy' | 'callback_scheduled'
    notes?: string
    callbackScheduledAt?: timestamp
  Response:
    success: boolean
    orderUpdated: boolean

GET /api/v1/calls/history
  Query:
    orderId?: string
    userId?: string
    from: timestamp
    to: timestamp
    page: number
  Response:
    calls: CallRecord[]
    total: number

POST /api/v1/calls/schedule
  Body:
    orderId: string
    scheduledTime: timestamp
    reason: string
  Response:
    callbackId: string
    scheduledAt: timestamp

GET /api/v1/calls/scheduled
  Query:
    userId: string
    date: string
  Response:
    callbacks: ScheduledCallback[]
```

### UI.md

#### Calling Dashboard UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  📞 Patient Calls                                [Queue] [History]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 📋 Call Queue — 8 patients waiting                          │  │
│  │                                                               │  │
│  │ Sort: [Priority ▼] [Last Attempt ▼] [Patient Name ▼]        │  │
│  │                                                               │  │
│  │ ┌───────────────────────────────────────────────────────────┐ │  │
│  │ │ 🚨 URGENT — Martinez, Rosa                                │ │  │
│  │ │    Phone: (555) 123-4567                                  │ │  │
│  │ │    Order: PA-2026-0412-0891 | Opdivo approval needed     │ │  │
│  │ │    Attempts: 0 | Last: Never                              │ │  │
│  │ │    [📞 Call Now]                                         │ │  │
│  │ └───────────────────────────────────────────────────────────┘ │  │
│  │                                                               │  │
│  │ ┌───────────────────────────────────────────────────────────┐ │  │
│  │ │ ⚡ Johnson, Michael                                        │ │  │
│  │ │    Phone: (555) 987-6543                                  │ │  │
│  │ │    Order: PA-2026-0412-0889 | Denial appeal follow-up    │ │  │
│  │ │    Attempts: 2 | Last: Yesterday 4:30 PM (voicemail)     │ │  │
│  │ │    [📞 Call Now] [Schedule] [Skip]                       │ │  │
│  │ └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 📊 Call Outcomes Today                                         │  │
│  │                                                               │  │
│  │ Connected: 12  │  Voicemail: 8  │  No Answer: 3  │  Other: 2  │  │
│  │ ████████████   █████████         ███              ██            │  │
│  │                                                               │  │
│  │ Avg Call Duration: 2m 34s | Total Time: 1h 12m               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ ⏰ Scheduled Callbacks                                        │  │
│  │                                                               │  │
│  │ • 3:00 PM — Thompson, Lisa (PA-2026-0412-0892)                │  │
│  │ • 4:30 PM — Garcia, Carlos (PA-2026-0412-0887)                │  │
│  │ • Tomorrow 9:00 AM — Williams, John (PA-2026-0412-0885)       │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Success Metrics

| Feature | Target | Measurement |
|---------|--------|-------------|
| FHIR writeback | 100% of outcomes | Auto-documentation rate |
| Fax integration | <5 min to route | Avg fax-to-order time |
| Calling workflow | 90% callback rate | Contact success rate |

---

*Author: Kulraj Sabharwal, Technical PM*
*Phase 3 Timeline: Week 7-10*