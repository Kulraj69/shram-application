# Phase 2 PRD: Feature Completeness (Week 3-6)

## Summary

Complete visibility gaps, approval workflows, and client-specific operational features.

---

## 2.1 Planned Task Incorporation

### README

**Problem**: Planned/queued tasks not visible in dashboard.
**Solution**: Dashboard queue view for scheduled submissions, retry queue, exception routing.
**Impact**: Complete task visibility, zero "did I submit that?" questions.

### SPEC.md

#### Planned Task Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PLANNED TASK PIPELINE                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SCHEDULED │    │    READY    │    │   EXECUTING │    │  COMPLETED  │
│    TASKS    │───▶│    QUEUE    │───▶│    ACTIVE   │───▶│    TASKS     │
│             │    │             │    │             │    │             │
│ Future dates │    │ Due now     │    │ RPA running │    │ Success     │
│ Cron-based   │    │ Auto-promote│    │ Real-time   │    │ Failed       │
│ Hold states  │    │ Pre-flight  │    │ Progress    │    │ Retry        │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Schedule   │    │  Retry      │    │  Exception  │    │  Audit      │
│  Dashboard  │    │  Queue      │    │  Handler    │    │  Log        │
│  View       │    │  (3 attempts│    │  (IRC/Pager)│    │  (Firestore)│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

#### Task Types

```typescript
interface PlannedTask {
  id: string;
  type: TaskType;
  status: TaskStatus;
  createdAt: string;
  scheduledAt: string;
  attemptedAt?: string;
  completedAt?: string;

  payload: TaskPayload;
  constraints: TaskConstraints;
  retryPolicy: RetryPolicy;
  auditTrail: AuditEntry[];
}

type TaskType =
  | 'scheduled_pa_submission'    // Time-based PA submission
  | 'retry_submission'           // Failed task retry
  | 'exception_route'           // Manual intervention needed
  | 'scheduled_check'           // Status check at interval
  | 'bulk_operations';          // Batch job

type TaskStatus =
  | 'held'                       // Waiting for schedule
  | 'queued'                     // Ready to execute
  | 'executing'                  // Currently running
  | 'completed'                  // Successfully finished
  | 'failed'                     // Failed after all retries
  | 'cancelled';                // Manually cancelled

interface TaskPayload {
  orderId?: string;
  clientId?: string;
  batchId?: string;
  endpoint: string;
  method: 'POST' | 'GET' | 'PATCH';
  headers: Record<string, string>;
  body?: Record<string, unknown>;
  expectedResponseTimeMs: number;
}

interface TaskConstraints {
  allowedWindows: TimeWindow[];
  maxExecutionTimeMs: number;
  requiredApprovals: string[];
  dependencyTaskIds: string[];
}

interface RetryPolicy {
  maxAttempts: number;
  backoffMultiplier: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryableErrors: string[];
}
```

#### Scheduled PA Submission Flow

```python
# Task scheduler service: scheduled_tasks.py

from datetime import datetime, timedelta
from typing import Optional
import asyncio

class TaskScheduler:
    """Manages scheduled and planned tasks."""

    def __init__(self, db: FirestoreClient, rpa_queue: RabbitMQClient):
        self.db = db
        self.queue = rpa_queue
        self._running = False

    async def start(self):
        """Start the task scheduler."""
        self._running = True
        await self._run_scheduler_loop()

    async def _run_scheduler_loop(self):
        """Main scheduler loop - runs every 30 seconds."""
        while self._running:
            try:
                await self._process_due_tasks()
                await self._promote_ready_tasks()
                await self._check_retry_queue()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(30)

    async def _process_due_tasks(self):
        """Find and execute tasks that are due."""
        now = datetime.utcnow()
        query = self.db.collection('planned_tasks').where(
            'status', '==', 'held'
        ).where(
            'scheduledAt', '<=', now.isoformat()
        ).where(
            'constraints.allowedWindows', 'array_contains', self._current_window()
        )

        tasks = query.get()
        for task_doc in tasks:
            await self._queue_task(task_doc.id, task_doc.to_dict())

    async def _queue_task(self, task_id: str, task: dict):
        """Move task to ready queue and enqueue for RPA."""
        task_ref = self.db.collection('planned_tasks').document(task_id)

        # Update status to queued
        task_ref.update({
            'status': 'queued',
            'queuedAt': datetime.utcnow().isoformat()
        })

        # Enqueue to RPA
        await self.queue.publish('task_queue', {
            'taskId': task_id,
            'type': task['type'],
            'payload': task['payload'],
            'retryPolicy': task['retryPolicy']
        })

    async def schedule_pa_submission(
        self,
        order_id: str,
        scheduled_time: datetime,
        window: str = 'business_hours'
    ) -> str:
        """Schedule a PA submission for future execution."""
        task_data = {
            'type': 'scheduled_pa_submission',
            'status': 'held',
            'createdAt': datetime.utcnow().isoformat(),
            'scheduledAt': scheduled_time.isoformat(),
            'payload': {
                'orderId': order_id,
                'endpoint': f'/api/v1/pa-orders/{order_id}/submit',
                'method': 'POST'
            },
            'constraints': {
                'allowedWindows': [window],
                'maxExecutionTimeMs': 30000
            },
            'retryPolicy': {
                'maxAttempts': 3,
                'backoffMultiplier': 2,
                'baseDelayMs': 1000,
                'maxDelayMs': 60000,
                'retryableErrors': ['timeout', 'rate_limit', 'service_unavailable']
            },
            'auditTrail': [{
                'action': 'created',
                'timestamp': datetime.utcnow().isoformat(),
                'userId': 'system'
            }]
        }

        doc_ref = await self.db.collection('planned_tasks').add(task_data)
        return doc_ref.id
```

#### Retry Queue Implementation

```python
# Retry handler: retry_queue.py

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class FailedTask:
    task_id: str
    error_type: str
    error_message: str
    attempt_count: int
    next_retry_at: datetime
    payload: dict

class RetryQueue:
    """Priority queue for failed tasks with exponential backoff."""

    def __init__(self, db: FirestoreClient, max_attempts: int = 3):
        self.db = db
        self.max_attempts = max_attempts
        self._heap: list[FailedTask] = []

    def calculate_next_retry(
        self,
        attempt_count: int,
        base_delay_ms: int,
        multiplier: float,
        max_delay_ms: int
    ) -> datetime:
        """Calculate next retry time with exponential backoff."""
        delay_ms = min(
            base_delay_ms * (multiplier ** attempt_count),
            max_delay_ms
        )
        return datetime.utcnow() + timedelta(milliseconds=delay_ms)

    def add_failed_task(self, task: dict, error: Exception):
        """Add a failed task to the retry queue."""
        attempt_count = task.get('attemptCount', 0) + 1

        if attempt_count >= self.max_attempts:
            # Move to dead letter queue
            self._move_to_dead_letter(task, error)
            return

        failed_task = FailedTask(
            task_id=task['id'],
            error_type=type(error).__name__,
            error_message=str(error),
            attempt_count=attempt_count,
            next_retry_at=self.calculate_next_retry(
                attempt_count,
                base_delay_ms=1000,
                multiplier=2.0,
                max_delay_ms=60000
            ),
            payload=task['payload']
        )

        # Persist to Firestore
        self.db.collection('retry_queue').add({
            'taskId': task['id'],
            'errorType': failed_task.error_type,
            'errorMessage': failed_task.error_message,
            'attemptCount': attempt_count,
            'nextRetryAt': failed_task.next_retry_at.isoformat(),
            'payload': failed_task.payload
        })

    async def process_due_retries(self) -> list[str]:
        """Process all tasks that are due for retry."""
        now = datetime.utcnow()
        query = self.db.collection('retry_queue').where(
            'nextRetryAt', '<=', now.isoformat()
        )

        task_ids = []
        for doc in query.get():
            task_ids.append(doc.id)
            await self._retry_task(doc.id, doc.to_dict())

        return task_ids

    def _move_to_dead_letter(self, task: dict, error: Exception):
        """Move permanently failed task to dead letter queue."""
        self.db.collection('dead_letter_queue').add({
            'originalTaskId': task['id'],
            'failedAt': datetime.utcnow().isoformat(),
            'errorType': type(error).__name__,
            'errorMessage': str(error),
            'totalAttempts': self.max_attempts,
            'payload': task['payload'],
            'requiresManualReview': True
        })

        # Trigger alert
        self._alert_on_failure(task, error)
```

### API.md

```yaml
GET /api/v1/planned-tasks
  Query:
    status: TaskStatus[]
    type: TaskType[]
    from: timestamp
    to: timestamp
    limit: number (default 50)
    offset: number (default 0)
  Response:
    tasks: PlannedTask[]
    total: number
    byStatus: Record<TaskStatus, number>

GET /api/v1/planned-tasks/scheduled
  Response:
    tasks: ScheduledTask[]
    nextScheduled: timestamp
    todayCount: number

GET /api/v1/planned-tasks/retry-queue
  Response:
    tasks: RetryTask[]
    totalRetries: number
    estimatedProcessingTime: number

POST /api/v1/planned-tasks
  Body:
    type: TaskType
    scheduledAt: timestamp
    payload: TaskPayload
    constraints: TaskConstraints
  Response:
    taskId: string
    status: 'held'

POST /api/v1/planned-tasks/{taskId}/cancel
  Response:
    success: boolean
    cancelledAt: timestamp

GET /api/v1/planned-tasks/{taskId}/audit
  Response:
    auditTrail: AuditEntry[]
```

### UI.md

#### Task Dashboard View

```
┌─────────────────────────────────────────────────────────────────────┐
│  📋 Planned Tasks                                           [Refresh]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Scheduled] [Retry Queue] [Exception Route] [Completed]          │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 📅 SCHEDULED (12)                           Next: 2:30 PM     │  │
│  │                                                               │  │
│  │ ┌───────────────────────────────────────────────────────────┐ │  │
│  │ │ 🕐 2:30 PM — NYCBS Batch #4532 (45 PA submissions)       │ │  │
│  │ │    Window: Business Hours | Status: Held                 │ │  │
│  │ │    [View Details] [Modify] [Cancel]                     │ │  │
│  │ └───────────────────────────────────────────────────────────┘ │  │
│  │                                                               │  │
│  │ ┌───────────────────────────────────────────────────────────┐ │  │
│  │ │ 🕐 4:00 PM — Astera Individual: Smith, John (Enbrel)     │ │  │
│  │ │    Window: Urgent | Status: Held                         │ │  │
│  │ └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 🔄 RETRY QUEUE (3)                        Processing...      │  │
│  │                                                               │  │
│  │ ┌───────────────────────────────────────────────────────────┐ │  │
│  │ │ ⚠️ Attempt 2/3 — PA-2026-0412-0891                       │  │
│  │ │    Error: rate_limit (429) | Next retry: 3:15 PM         │  │
│  │ │    [View Error] [Force Retry] [Cancel]                   │ │  │
│  │ └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 🚨 EXCEPTION ROUTING (1)                   Requires Action   │  │
│  │                                                               │  │
│  │ ┌───────────────────────────────────────────────────────────┐ │  │
│  │ │ ❌ PA-2026-0412-0156 — NYCBS Denial Letter Missing        │  │
│  │ │    Plan requires appeal within 14 days                     │  │
│  │ │    [Review] [Upload Letter] [Route to Specialist]         │  │
│  │ └───────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2.2 Approval Systems

### README

**Problem**: Approvals require email/Slack/handoff.
**Solution**: In-dashboard approval workflow with audit trail.
**Impact**: Full audit trail, faster approvals, zero email threads.

### SPEC.md

#### Approval Workflow States

```
                    ┌─────────────────┐
                    │   PENDING      │
                    │   APPROVAL     │
                    └────────┬───────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
      ┌───────────┐   ┌───────────┐   ┌───────────┐
      │ APPROVED  │   │ REJECTED  │   │ ESCALATED │
      └───────────┘   └───────────┘   └─────┬─────┘
                                            │
                                      ┌─────┴─────┐
                                      ▼           ▼
                               ┌──────────┐ ┌──────────┐
                               │ APPROVED │ │ REJECTED │
                               └──────────┘ └──────────┘
```

#### Approval Types

```typescript
interface ApprovalRequest {
  id: string;
  type: ApprovalType;
  status: ApprovalStatus;

  // Requestor info
  requestedBy: string;
  requestedAt: string;

  // Target info
  taskId: string;
  taskType: string;
  taskDescription: string;

  // Financial threshold
  estimatedValue: number;
  currency: string;

  // Decision
  decidedBy?: string;
  decidedAt?: string;
  decision?: 'approved' | 'rejected' | 'escalated';
  notes?: string;

  // Metadata
  priority: 'low' | 'normal' | 'high' | 'urgent';
  dueAt?: string;
  slaMinutes?: number;
}

type ApprovalType =
  | 'high_value_pa'         // PA > $500 value
  | 'denial_escalation'     // Denial appeal
  | 'manual_override'       // Manual data correction
  | 'exception_route'       // Non-standard workflow
  | 'bulk_approval';        // Batch operation

type ApprovalStatus =
  | 'pending'               // Awaiting decision
  | 'approved'             // Approved
  | 'rejected'             // Rejected
  | 'escalated'            // Escalated to higher authority
  | 'cancelled';           // Cancelled by requestor
```

#### Approval Service

```python
# approval_service.py

from typing import Optional
from datetime import datetime, timedelta
from enum import Enum

class ApprovalService:
    """Handles approval workflows and escalations."""

    HIGH_VALUE_THRESHOLD = 500  # dollars

    def __init__(
        self,
        db: FirestoreClient,
        notification_service: NotificationService,
        audit_logger: AuditLogger
    ):
        self.db = db
        self.notifications = notification_service
        self.audit = audit_logger

    async def create_approval_request(
        self,
        approval_type: ApprovalType,
        task_id: str,
        requestor_id: str,
        priority: str = 'normal'
    ) -> str:
        """Create a new approval request."""

        # Determine if auto-escalation needed
        auto_approve = await self._check_auto_approve(task_id, approval_type)

        approval_data = {
            'type': approval_type,
            'status': 'approved' if auto_approve else 'pending',
            'requestedBy': requestor_id,
            'requestedAt': datetime.utcnow().isoformat(),
            'taskId': task_id,
            'priority': priority,
            'slaMinutes': self._get_sla_minutes(approval_type)
        }

        if auto_approve:
            approval_data['decidedBy'] = 'system'
            approval_data['decidedAt'] = datetime.utcnow().isoformat()
            approval_data['decision'] = 'approved'
            approval_data['notes'] = 'Auto-approved: meets criteria'

        doc_ref = await self.db.collection('approval_requests').add(approval_data)

        if not auto_approve:
            await self._notify_approvers(doc_ref.id, approval_type)

        return doc_ref.id

    async def process_approval_decision(
        self,
        approval_id: str,
        decision: str,
        approver_id: str,
        notes: Optional[str] = None
    ) -> bool:
        """Process an approval decision."""

        approval_doc = self.db.collection('approval_requests').document(approval_id)
        approval = approval_doc.get().to_dict()

        if approval['status'] != 'pending':
            raise ValueError(f"Approval {approval_id} is not pending")

        if not self._can_approve(approver_id, approval['type']):
            raise PermissionError(f"User {approver_id} cannot approve {approval['type']}")

        # Update approval
        approval_doc.update({
            'status': 'approved' if decision == 'approve' else 'rejected',
            'decidedBy': approver_id,
            'decidedAt': datetime.utcnow().isoformat(),
            'decision': decision,
            'notes': notes
        })

        # Notify requestor
        await self.notifications.send(
            user_id=approval['requestedBy'],
            title=f"Approval {decision}d",
            message=f"Your request for {approval['type']} has been {decision}d",
            actions=[{
                'label': 'View Details',
                'action': 'navigate',
                'payload': {'page': f'/approvals/{approval_id}'}
            }]
        )

        # Execute approved action
        if decision == 'approve':
            await self._execute_approved_action(approval)

        # Audit log
        await self.audit.log(
            action='approval_decision',
            approval_id=approval_id,
            decision=decision,
            approver_id=approver_id
        )

        return True

    def _get_sla_minutes(self, approval_type: ApprovalType) -> int:
        """Get SLA for approval type in minutes."""
        sla_map = {
            'high_value_pa': 30,      # 30 minutes
            'denial_escalation': 60,   # 1 hour
            'manual_override': 15,      # 15 minutes
            'exception_route': 120,     # 2 hours
            'bulk_approval': 240       # 4 hours
        }
        return sla_map.get(approval_type, 60)

    async def _execute_approved_action(self, approval: dict):
        """Execute the action after approval."""
        # This would trigger the actual workflow action
        await self._dispatch_action(approval['taskId'], approval['type'])
```

### API.md

```yaml
POST /api/v1/approvals
  Body:
    taskId: string
    approvalType: ApprovalType
    priority?: 'low' | 'normal' | 'high' | 'urgent'
    notes?: string
  Response:
    approvalId: string
    status: 'pending' | 'approved'

GET /api/v1/approvals
  Query:
    status?: ApprovalStatus[]
    type?: ApprovalType[]
    requestedBy?: string
    page: number
    pageSize: number
  Response:
    approvals: ApprovalRequest[]
    total: number

GET /api/v1/approvals/pending
  Response:
    approvals: ApprovalRequest[]
    countByType: Record<ApprovalType, number>
    oldestPending: timestamp

GET /api/v1/approvals/{approvalId}
  Response:
    approval: ApprovalRequest
    auditTrail: AuditEntry[]

POST /api/v1/approvals/{approvalId}/decide
  Body:
    decision: 'approve' | 'reject' | 'escalate'
    notes?: string
  Response:
    success: boolean

POST /api/v1/approvals/{approvalId}/escalate
  Body:
    reason: string
    escalateTo: string (role or user id)
  Response:
    approvalId: string
    newStatus: 'escalated'

GET /api/v1/approvals/sla
  Response:
    atRisk: ApprovalRequest[]   # Within 10 min of SLA
    breached: ApprovalRequest[]  # Past SLA
```

### UI.md

#### Approval Queue UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  ✅ Approvals                                                 [⚙️]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Pending (5)    Approved (127)    Rejected (12)    All (144)       │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 🚨 URGENT — High Value PA Approval                           │  │
│  │                                                               │  │
│  │ ┌─────────────────────────────────────────────────────────┐ │  │
│  │ │                                                           │ │  │
│  │ │  Patient: Martinez, Rosa                                  │ │  │
│  │ │  Drug: Opdivo 240mg (Nivolumab)                          │ │  │
│  │ │  Estimated Value: $12,450/month                          │ │  │
│  │ │  Plan: Aetna Medicare                                    │  │
│  │ │                                                           │ │  │
│  │ │  Requested by: jsmith@risa.ai (2 hours ago)             │ │  │
│  │ │  SLA: 28 minutes remaining                               │  │
│  │ │                                                           │ │  │
│  │ │  ┌─────────────────────────────────────────────────────┐│ │  │
│  │ │  │ Reason: Patient has failed 2 prior biologics.       ││ │  │
│  │ │  │ Oncologist recommends Opdivo per NCCN guidelines.  ││ │  │
│  │ │  └─────────────────────────────────────────────────────┘│ │  │
│  │ │                                                           │ │  │
│  │ │  [Reject]  [Escalate]  [────────── Approve ──────────] │ │  │
│  │ │                                                           │ │  │
│  │ └─────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ ⚠️ Denial Escalation                                         │  │
│  │                                                               │  │
│  │ Order: PA-2026-0412-0156                                     │  │
│  │ Plan: CVS Caremark                                           │  │
│  │ Deadline: April 30, 2026 (10 days remaining)               │  │
│  │                                                           │  │
│  │ [View Denial] [Prepare Appeal] [Approve] [Reject]          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2.3 Client Operational Gaps

### README

**Problem**: Client-specific operations have visibility gaps.
**Solution**: NYCBS and Astera-specific dashboards and integrations.
**Impact**: Client self-service for status questions.

### SPEC.md

#### NYCBS Integration Requirements

```python
# nycbs_integration.py

class NYCBSIntegration:
    """NYCBS-specific integrations and visibility."""

    def __init__(self, sftp_client: SFTPClient, db: FirestoreClient):
        self.sftp = sftp_client
        self.db = db

    async def get_batch_file_status(self, batch_id: str) -> dict:
        """Get status of NYCBS batch file submission."""

        # Query NYCBS SFTP for file status
        files = await self.sftp.list_directory('/outbound/batches/')

        batch_files = [
            f for f in files
            if f.startswith(f'BATCH_{batch_id}')
        ]

        statuses = []
        for file in batch_files:
            file_info = await self.sftp.stat(f'/outbound/batches/{file}')
            statuses.append({
                'filename': file,
                'size': file_info.st_size,
                'modified': datetime.fromtimestamp(file_info.st_mtime),
                'status': await self._check_processing_status(file)
            })

        return {
            'batchId': batch_id,
            'files': statuses,
            'totalFiles': len(statuses),
            'processedFiles': sum(1 for s in statuses if s['status'] == 'processed'),
            'pendingFiles': sum(1 for s in statuses if s['status'] == 'pending')
        }

    async def get_denial_letter_confirmation(self, order_id: str) -> dict:
        """Check if denial letter was received for an order."""

        # Check NYCBS system for letter attachment
        letter = await self._fetch_from_nycbs_api(
            endpoint=f'/orders/{order_id}/denial-letter'
        )

        return {
            'orderId': order_id,
            'letterReceived': letter is not None,
            'letterDate': letter.get('receivedAt') if letter else None,
            'documentId': letter.get('documentId'),
            'verifiedBy': letter.get('verifiedBy') if letter else None
        }

    async def monitor_sftp_push_pull(self, operation_id: str) -> dict:
        """Monitor SFTP push/pull status for an operation."""

        operation = self.db.collection('sftp_operations').document(operation_id)
        op_data = operation.get().to_dict()

        return {
            'operationId': operation_id,
            'type': op_data['type'],  # 'push' or 'pull'
            'status': op_data['status'],
            'filesTransferred': op_data.get('filesTransferred', 0),
            'totalFiles': op_data.get('totalFiles', 0),
            'bytesTransferred': op_data.get('bytesTransferred', 0),
            'startedAt': op_data.get('startedAt'),
            'completedAt': op_data.get('completedAt'),
            'errors': op_data.get('errors', [])
        }
```

#### Astera Integration Requirements

```python
# astera_integration.py

class AsteraIntegration:
    """Astera-specific integrations and visibility."""

    def __init__(self, email_client: IMAPClient, api_client: httpx.AsyncClient):
        self.email = email_client
        self.api = api_client

    async def get_email_attachment_status(self, order_id: str) -> dict:
        """Check status of email attachment processing."""

        # Query Astera email inbox
        emails = await self.email.search(
            f'FROM astera-system AND SUBJECT "Attachment: {order_id}"'
        )

        statuses = []
        for email_id in emails:
            email_data = await self.email.fetch(email_id, 'BODY[]')
            statuses.append({
                'emailId': email_id,
                'receivedAt': email_data['date'],
                'attachmentFound': self._has_attachment(email_data),
                'processed': self._check_processing(email_id)
            })

        return {
            'orderId': order_id,
            'emailStatuses': statuses,
            'allProcessed': all(s['processed'] for s in statuses)
        }

    async def get_bulk_submission_progress(self, submission_id: str) -> dict:
        """Track progress of bulk PA submission to Astera."""

        # Poll Astera API for bulk submission status
        response = await self.api.get(
            f'https://api.astera.com/bulk-submissions/{submission_id}'
        )

        data = response.json()

        return {
            'submissionId': submission_id,
            'status': data['status'],
            'totalCount': data['totalCount'],
            'processedCount': data['processedCount'],
            'successCount': data['successCount'],
            'failureCount': data['failureCount'],
            'progress': data['processedCount'] / data['totalCount'] * 100,
            'startedAt': data['startedAt'],
            'estimatedCompletion': data.get('estimatedCompletion')
        }

    async def get_single_pa_confirmation(self, pa_request_id: str) -> dict:
        """Get confirmation for single PA submission."""

        response = await self.api.get(
            f'https://api.astera.com/pa-requests/{pa_request_id}'
        )

        return {
            'requestId': pa_request_id,
            'submittedAt': response['submittedAt'],
            'confirmationNumber': response['confirmationNumber'],
            'status': response['status'],
            'nextSteps': response.get('nextSteps', [])
        }

    async def get_oncoemr_writeback_status(self, order_id: str) -> dict:
        """Check OncoEMR FHIR writeback status."""

        # Query OncoEMR for writeback status
        writeback = await self._fetch_oncoemr(
            f'/fhir/writeback/status?orderId={order_id}'
        )

        return {
            'orderId': order_id,
            'writebackAttempted': writeback.get('attempted', False),
            'lastAttempt': writeback.get('lastAttemptAt'),
            'status': writeback.get('status'),  # 'success', 'failed', 'pending'
            'fhirResourceId': writeback.get('resourceId'),
            'errorMessage': writeback.get('errorMessage')
        }
```

### UI.md

#### NYCBS Operations Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│  🏥 NYCBS Operations                            [SFTP] [Batches]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 📁 Batch Status Overview                   Last sync: 2min ago│  │
│  │                                                               │  │
│  │ Active Batches: 3    Processed Today: 12    Pending: 1       │  │
│  │                                                               │  │
│  │ ┌─────────────────────────────────────────────────────────┐ │  │
│  │ │ BATCH-2026-0412-4532                                    │ │  │
│  │ │ Status: ✅ Complete | Files: 45/45 | Errors: 0         │ │  │
│  │ │ Started: 9:15 AM | Completed: 10:32 AM (1h 17m)        │ │  │
│  │ │ [View Details] [Download Report] [Re-run]               │ │  │
│  │ └─────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 📋 SFTP Activity                                             │  │
│  │                                                               │  │
│  │ Push Operations: 12   Pull Operations: 8   Failed: 0           │  │
│  │                                                               │  │
│  │ Recent:                                                       │  │
│  │ • OUT: BATCH-2026-0412-4532.csv (23MB) — Complete            │  │
│  │ • IN:  responses_2026-04-12.par (1.2MB) — Complete            │  │
│  │ • OUT: BATCH-2026-0412-4533.csv (18MB) — In Progress         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ ⚠️ Error Log (Last 24h)                                      │  │
│  │                                                               │  │
│  │ 0 errors in last 24 hours                                     │  │
│  │ ✓ All systems operational                                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

#### Astera Operations Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔬 Astera Operations                              [Email] [Submit]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 📧 Email Processing                         24 pending        │  │
│  │                                                               │  │
│  │ Processed Today: 156   Failed: 3   Avg Processing: 45s        │  │
│  │                                                               │  │
│  │ Recent Activity:                                               │  │
│  │ • PA-2026-0412-0901 — Attachment received, processing...      │  │
│  │ • PA-2026-0412-0900 — ✅ Processed (23s)                     │  │
│  │ • PA-2026-0412-0899 — ✅ Processed (18s)                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 📊 Bulk Submissions                                           │  │
│  │                                                               │  │
│  │ Active: BATCH-0412 — 89% complete (890/1000 PAs)             │  │
│  │ ████████████████████░░░░░░░░░░░░░                             │  │
│  │ ETA: 11:45 AM (23 minutes)                                   │  │
│  │                                                               │  │
│  │ Completed Today: 3 batches (2,847 total PAs)                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 💾 OncoEMR Writeback Status                                  │  │
│  │                                                               │  │
│  │ Successful Today: 145   Pending: 2   Failed: 0              │  │
│  │                                                               │  │
│  │ Recent:                                                       │  │
│  │ • PA-2026-0412-0891 — ✅ DocumentReference created (DR-4567) │  │
│  │ • PA-2026-0412-0892 — ⏳ Pending FHIR writeback              │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Success Metrics

| Feature | Target | Measurement |
|---------|--------|-------------|
| Task visibility | 100% coverage | No "did I submit?" questions |
| Approval time | -60% | Avg time from request to decision |
| NYCBS self-service | 80% reduction | Client support tickets |
| Astera operations | Zero manual checks | Automated status tracking |

---

*Author: Kulraj Sabharwal, Technical PM*
*Phase 2 Timeline: Week 3-6*