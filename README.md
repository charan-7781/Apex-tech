# 🛡️ SAVE KAROO — Public Safety Platform

> **Tagline:** REPORT. TRACK. ESCALATE. STAY SAFE.  
> **Category:** Public Safety / Transit Protection / Citizen Grievance Management  
> **Status:** Fully Functional Full-Stack Platform Prototype

---

## 🌟 Executive Overview
**SAVE KAROO** is a complete, production-ready, full-stack public safety complaint management and citizen protection platform. It bridges citizens, authorized police officers, and precinct administrators through a transparent, audited complaint tracking and escalation architecture.

### 🛡️ Foundational Principle:
> **Essential public safety complaint filing, real-time tracking, police updates, and emergency directory access are 100% FREE for all citizens forever.**  
> Optional subscriptions apply strictly to convenience features: certified PDF transcripts for insurance/court, danger-zone heatmaps, and enterprise fleet compliance audits.

---

## 🏢 Four Role-Based Portals

| Role | Access & Key Features | Demo Credentials |
| :--- | :--- | :--- |
| **Citizen** | 6-step complaint wizard, 10-stage timeline stepper, certified transcripts, notification center, free/pro plans. | `priya.sharma@gmail.com` / `Citizen@123` |
| **Police Officer** | Assigned case queue, evidence inspector, official action logger (ANPR, Section 91, summons, challans). | `officer.sharma@police.gov.in` / `Officer@123` |
| **Police Admin** | Precinct KPIs, officer workload assignment, escalation monitor, SLA breach alerts, CSV register export. | `policeadmin.blr@savekaroo.org` / `PoliceAdmin@123` |
| **Super Admin** | Platform governance, police account approval queue, configurable escalation rules & SLA hours, immutable audit log. | `superadmin@savekaroo.org` / `Admin@123` |

*Note: For testing convenience, a **One-Click Quick Role Switcher** is embedded in the application sidebar.*

---

## 🏗️ Relational Database Architecture (`save_karoo.db`)
SAVE KAROO is backed by an SQLite relational database utilizing WAL mode and foreign key constraints:
1. `users` — Citizens, Police Officers, Admins, Super Admins.
2. `districts` — Jurisdictional zones and localized emergency helplines.
3. `police_departments` — Police stations and contact dispatchers.
4. `police_officers` — Verified badge numbers, ranks, active case limits.
5. `complaint_categories` — 9 transit and safety categories with priority tiers.
6. `complaints` — Core complaints with unique IDs (`SK-2026-XXXXXX`).
7. `complaint_evidence` — Secure file attachments, screenshots, telemetry.
8. `complaint_assignments` — Officer assignment audit records.
9. `complaint_status_history` — 10-stage lifecycle audit timeline.
10. `complaint_actions` — Official actions taken (summons, challans, notices).
11. `escalation_records` — Automatic triggers for repeat violations & SLA breaches.
12. `notifications` — In-app alerts with read/unread statuses.
13. `subscription_plans` — Free Citizen, Citizen Pro (₹199/mo), Enterprise (₹4999/mo).
14. `subscriptions` — Citizen active plans and billing cycles.
15. `payments` — Razorpay test mode transactions and status.
16. `invoices` — Tax invoices with unique numbers and PDF references.
17. `support_tickets` — Citizen support and technical feedback.
18. `audit_logs` — Immutable platform security and compliance trail.
19. `system_settings` — Dynamic thresholds, SLA hours, emergency numbers.

---

## ⚡ The SAVE KAROO Escalation Concept
To prevent public safety complaints from stalling:
- **Repeat Offender Rule:** If **5 or more complaints** accumulate against the same vehicle or commercial driver without closure, the Escalation Engine flags the entity for immediate Administrative Review.
- **SLA Breach Rule:** If an assigned high-priority complaint remains without an official recorded action for **48 hours**, it is escalated in red on precinct dashboards.

---

## 🤖 KAROO AI — The Public Safety Assistant
- Assists citizens in structuring incident details, selecting categories, and identifying crucial evidence (GPS deviations, trip invoices).
- **Strict Guardrails:** Never claims to be police, never determines guilt, and immediately routes life-threatening emergencies to **112** (National Emergency) and **1091** (Women's Safety).

---

## 🚀 Running the Application Locally

### 1. Ensure Python Virtual Environment is Activated
```powershell
.\venv\Scripts\activate
```

### 2. Run the Automated Test Suite (9 Test Suites, 100% Green)
```powershell
python -m unittest test_save_karoo.py -v
```

### 3. Launch the Platform
```powershell
python -m streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🌐 Production Deployment Guide

### Deployment on Linux / Cloud Server (Docker / Systemd)
1. **Dockerfile:**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   EXPOSE 8501
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```
2. **Build and Run:**
   ```bash
   docker build -t save-karoo .
   docker run -d -p 8501:8501 -v savekaroo_data:/app/data --name savekaroo save-karoo
   ```

---

## ⚖️ Legal & Safety Disclaimer
*SAVE KAROO is an independent public-safety software platform prototype. It is not an official government agency and does not replace emergency 112 services. In case of imminent danger, citizens must dial 112 or 1091 immediately.*
