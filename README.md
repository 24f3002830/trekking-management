# Trekking Management Application (TMA) - V2

---

## 📌 Project Overview

The **Trekking Management Application (TMA)** is a multi-role web platform designed for adventure organizations to streamline and digitize trekking operations. It replaces manual coordination, spreadsheets, and phone calls with an automated system for managing trek approvals, slot availability, participant registrations, and booking tracking.

---

## 👥 User Roles & Core Capabilities

### 1. 🛡️ Admin (Pre-existing Superuser)
- Created programmatically upon database initialization (no public registration).
- Dashboard with high-level analytics: total treks, active users, staff, and bookings.
- Create, update, and manage trekking routes and schedules.
- Add and manage trek staff, and assign staff to specific treks.
- Search, view, and moderate (deactivate/blacklist) users and staff.
- View trekking statistics and automated monthly performance reports.

### 2. 🥾 Trek Staff
- Log in using credentials provisioned by the Admin.
- Dedicated staff dashboard displaying assigned treks and participant counts.
- Manage trek capacity and real-time status (`Open`, `Closed`, `Started`, `Completed`).
- View and manage registered participants per assigned trek.

### 3. 🎒 User (Trekker)
- Self-registration, profile management, and authentication.
- Browse, search, and filter treks by difficulty (*Easy*, *Moderate*, *Hard*), location, and duration.
- Book open treks with real-time slot checking (prevents duplicate bookings and overbooking).
- View personal booking statuses, upcoming itineraries, and trekking history.
- Trigger asynchronous CSV export of booking and trekking history.

---

## ⚙️ Technology Stack

| Layer | Framework / Technology | Purpose |
| :--- | :--- | :--- |
| **Backend API** | Flask (Python) | RESTful API backend, business logic, and RBAC authentication |
| **Frontend UI** | Vue.js + Bootstrap | Reactive single-page user interface and responsive styling |
| **Database** | SQLite | Programmatically initialized relational database storage |
| **Caching** | Redis | Caching frequently accessed trek details with TTL expiration |
| **Batch Processing** | Redis + Celery | Scheduled reminders, monthly reports, and async CSV exports |

---

## 📂 Project Directory Structure

```text
trekking-management/
├── backend/
│   ├── models/            # SQLAlchemy / Database models
│   ├── routes/            # Flask API route blueprints
│   └── app.py             # Flask application entry point
├── frontend/
│   └── src/
│       └── components/    # Vue.js reusable UI components
├── .gitignore             # Git ignore configuration
└── README.md              # Project documentation & setup guide
```

---

## 🔄 Celery & Background Jobs

1. **Daily Reminders (Scheduled Job):** Sends daily notifications/reminders to users regarding upcoming trek schedules and guidelines via email or webhooks.
2. **Monthly Activity Report (Scheduled Job):** Generates and emails a monthly activity and analytics summary to the Admin on the first day of each month.
3. **Async CSV Export (User-Triggered Job):** Allows users to export their complete trekking and booking history as a downloadable CSV.

---

## 🚀 Milestone Progress

- [x] **Milestone 0:** GitHub Repository Setup, initial directory structure, `.gitignore`, and `README.md`.
- [x] **Milestone 1:** Database models (SQLite), programmatic schema initialization, pre-seeded Admin, and JWT RBAC authentication APIs.
- [ ] **Milestone 2:** Admin, Staff, and User API endpoints and Redis caching.
- [ ] **Milestone 3:** Celery asynchronous tasks and scheduled periodic jobs.
- [ ] **Milestone 4:** Vue.js + Bootstrap reactive frontend integration.
- [ ] **Milestone 5:** End-to-end testing, validation, and final polish.

---

## 💻 Running the Backend & Verification

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Run Automated Verification Tests
```bash
python backend/test_milestone1.py
```

### 3. Start the Flask Backend Server
```bash
python backend/app.py
```
Default superuser credentials (seeded programmatically):
- **Email:** `admin@trekking.com` (or username: `admin`)
- **Password:** `Admin@123`
