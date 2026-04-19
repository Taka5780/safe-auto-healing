# Safe Auto-Healing System (AWS × Python)

## ■ Overview

This project is an incident response automation system built on AWS.
Its primary goal is to reduce MTTR (Mean Time To Recovery) by optimizing the response process after alert detection.

Rather than fully automating everything, this system focuses on **safe and controlled automation**, while preserving human decision-making where necessary.

---

## ■ Background

In real-world operations, the following issues are common:

* Delayed response due to missed email alerts
* Lack of visibility in incident handling
* Inconsistent recovery time depending on the operator

To address these problems, this system redesigns the workflow from detection to response and provides a **faster and more reliable incident handling process**.

---

## ■ Concept

* Do not eliminate alerts (failures are inevitable)
* Reduce MTTR instead of suppressing incidents
* Automate only safe and repeatable operations
* Keep human-in-the-loop where necessary

---

## ■ Architecture

* EC2 (target instance)
* Amazon CloudWatch (monitoring and alerting)
* AWS Lambda (auto-healing and decision logic)
* AWS Systems Manager (SSM) (remote command execution)
* Slack (notification)

---

## ■ Flow

CloudWatch Alarm
↓
Lambda (Python)
↓
Action or Decision Support
↓
Slack Notification

---

# ■ Scenario 1: Auto-Healing (L1)

## ■ Description

Automatically recovers from minor and well-understood failures.

---

## ■ Workflow

1. CloudWatch detects an anomaly (e.g., CPU spike or HTTP failure)
2. Lambda function is triggered
3. Nginx is restarted via SSM
4. HTTP health check verifies recovery
5. Result is sent to Slack

---

## ■ Slack Notification Example

```text
[Auto-Healing SUCCESS]

Time: 2026-04-17 17:52:05 (JST)
Instance: safe-auto-healing-web-server (i-xxxxxxxxxxxx)
Alarm: safe-auto-healing-nginx-down
Action: Nginx Restart (L1)
Result: OK
Detail: Nginx is back online and responding to HTTP 200.
```

---

## ■ Key Features

### 1. Safe Target Control (Tag-based)

```
auto-healing=true
```

Only instances with this tag are eligible for auto-healing.

---

### 2. SSM Execution Verification

Handles intermediate states such as:

```
Pending / InProgress
```

Ensures actions are executed only after completion.

---

### 3. Retry Mechanism

```
Up to 5 health check attempts
```

Improves resilience against transient failures.

---

### 4. Result Visibility

* Success / Failure notifications via Slack
* Error trace is included on failure

---

# ■ Scenario 2: Human-in-the-Loop Decision (L2)

## ■ Description

Handles incidents that cannot be safely auto-recovered.
Instead of executing actions automatically, the system **assists human decision-making** by providing contextual information and recommended actions.

---

## ■ Workflow

1. CloudWatch detects an anomaly (e.g., CPU spike)
2. Lambda function is triggered
3. Diagnostic data is collected via SSM (e.g., top CPU processes)
4. A structured alert is sent to Slack
5. Human operator reviews and takes appropriate action

---

## ■ Slack Notification Example

```text
🚨 [ALERT] Service Impact Suspected

Instance: safe-auto-healing-web-server (i-xxxxxxxxxxxx)
Alarm: CPU High
Value: Over 30% (As detected)

Additional Info:
- Current status: running
- Triggered at: 2026-04-20 02:08:21 (JST)
- Recovery action: None (Investigation only)

Suggested Actions:
1. Check the process list below
2. Reboot instance if necessary
3. Check application logs

Status: [UNRESOLVED]

---

Current Top Processes:
PID   USER   %CPU   COMMAND
...
```

---

## ■ Key Features

### 1. Human-Centric Design

* No automatic recovery for uncertain scenarios
* Designed to support rapid human decision-making

---

### 2. Context-Aware Alerts

* Includes instance state and timestamp
* Provides real-time process-level insights

---

### 3. Built-in Investigation Support

* Retrieves top CPU-consuming processes via SSM
* Eliminates the need for immediate SSH access

---

### 4. Actionable Guidance

* Suggested next steps included in alerts
* Reduces decision-making time during incidents

---

## ■ Design Rationale

Not all failures should be automated.

For cases such as CPU spikes:

* Root cause may vary (application bug, traffic spike, batch processing, etc.)
* Blind automation (e.g., restart) may worsen the situation

Therefore, this scenario prioritizes:

* Safety over automation
* Decision speed over blind execution

---

## ■ Comparison Between Scenarios

| Aspect      | Scenario 1 (L1)    | Scenario 2 (L2)  |
| ----------- | ------------------ | ---------------- |
| Recovery    | Automatic          | Manual           |
| Purpose     | Immediate recovery | Decision support |
| Risk        | Low                | Medium           |
| Lambda Role | Execute action     | Provide context  |

---

## ■ Directory Structure

```
safe-auto-healing/
├── infra/
│   ├── terraform/
│   └── ansible/
├── app/
│   └── lambda/
├── config/
├── docs/
└── README.md
```

---

## ■ Tech Stack

* Python
* AWS Lambda
* Amazon CloudWatch
* AWS Systems Manager (SSM)
* Terraform
* Ansible
* Slack Webhook

---

## ■ Future Improvements

* Scenario 3: Safe blocking (non-automatable cases)
* Cooldown mechanism
* Incident history tracking
* Automated escalation

---

## ■ Summary

This system achieves:

* Faster incident response
* Reduced MTTR
* Safe and controlled automation

The key idea is:

> "Do not automate everything. Design what should and should not be automated."

---

