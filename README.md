# Safe Auto-Healing System (AWS × Python)

## ■ Overview

This project is an incident response automation system built on AWS.
Its primary goal is to reduce MTTR (Mean Time To Recovery) by automating the recovery process after alert detection.

Rather than fully automating everything, this system focuses on **safe and controlled automation**, while preserving human decision-making where necessary.

---

## ■ Background

In real-world operations, the following issues are common:

* Delayed response due to missed email alerts
* Lack of visibility in incident handling
* Inconsistent recovery time depending on the operator

To address these problems, this system redesigns the workflow from detection to recovery and provides a **faster and more reliable response process**.

---

## ■ Concept

* Do not eliminate alerts (failures are inevitable)
* Reduce MTTR instead of suppressing incidents
* Automate only safe and repeatable operations
* Keep human-in-the-loop where necessary

---

## ■ Architecture

* EC2 (target instance)
* CloudWatch (monitoring and alerting)
* Lambda (auto-healing logic)
* Systems Manager (SSM) (remote command execution)
* Slack (notification)

---

## ■ Flow

CloudWatch Alarm
↓
Lambda (Python)
↓
Restart Nginx via SSM
↓
HTTP health check
↓
Slack notification

---

## ■ Scenario 1: Auto-Healing (L1)

### ■ Description

Automatically recovers from minor and well-understood failures.

### ■ Workflow

1. CloudWatch detects an anomaly (e.g., CPU spike or HTTP failure)
2. Lambda function is triggered
3. Nginx is restarted via SSM
4. HTTP health check verifies recovery
5. Result is sent to Slack

---

### ■ Slack Notification Example

```id="m4w1u5"
[Auto-Healing SUCCESS]

Time: 2026-04-17 17:52:05
Instance: i-xxxxxxxxxxxx
Alarm: safe-auto-healing-nginx-down
Action: Nginx Restart
Result: OK
```

---

## ■ Key Features

### 1. Safe Target Control (Tag-based)

```id="1zz0t2"
auto-healing=true
```

Only instances with this tag are eligible for auto-healing.

---

### 2. SSM Execution Verification

Handles intermediate states such as:

```id="jbbf8v"
Pending / InProgress
```

Ensures actions are executed only after completion.

---

### 3. Retry Mechanism

```id="mcl20b"
Up to 5 health check attempts
```

Improves resilience against transient failures.

---

### 4. Result Visibility

* Success / Failure notifications via Slack
* Error trace is included on failure

---

## ■ Directory Structure

```id="0zixmp"
safe-auto-healing/
├── infra/
│   ├── terraform/
│   └── ansible/
├── app/
│   └── lambda/
├── config/
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

* Scenario 2: Human-in-the-loop response
* Scenario 3: Safe blocking (non-automatable cases)
* Cooldown mechanism
* Incident history tracking

---

## ■ Summary

This system achieves:

* Faster incident response
* Reduced MTTR
* Safe and controlled automation

The key idea is:

> "Do not automate everything. Design what should and should not be automated."

---
