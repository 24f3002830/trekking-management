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
- [x] **Milestone 2:** Admin, Staff, and User API endpoints, slot management, and Redis caching.
- [x] **Milestone 3:** Celery asynchronous tasks, periodic daily reminders, monthly reports, and CSV export.
- [x] **Milestone 4:** Vue.js + Bootstrap reactive frontend integration (SFC Single Page Application).
- [x] **Milestone 5:** End-to-end testing, realistic demo seeding, packaging, and final polish.
- [x] **Milestone 6:** Payment simulation, in-app notification center, Chart.js analytics, and comprehensive user manual.

---

## 💻 Running the Application & Verification

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Populate Realistic Demo Data (Optional but Recommended)
```bash
python backend/seed_data.py
```
Pre-populates the database with Himalayan treks across Uttarakhand, Himachal & Ladakh, certified staff members, sample trekkers, and bookings.

### 3. Run All Automated Verification Tests Consecutively
```bash
python run_all_tests.py
```
*(Runs all milestone test suites: test_milestone1.py through test_milestone6.py consecutively).*

### 4. Start the Full-Stack Web Application
```bash
python backend/app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000/`**

Default superuser credentials (seeded programmatically):
- **Email:** `admin@trekking.com` (or username: `admin`)
- **Password:** `Admin@123`

### 5. Packaging the Project for Submission
```bash
python package_submission.py
```
Generates `trekking_management_24f3002830.zip` adhering strictly to the folder structure required for MAD-2 evaluation.

### 6. Full Documentation & User Manual
Refer to [`USER_MANUAL.md`](USER_MANUAL.md) for step-by-step role guides, screenshots/workflow overviews, and developer reference.

---

## 🖥️ Frontend Architecture & UI Components

The frontend is a reactive Single Page Application (SPA) built using **Vue 3**, **Vue Router 4**, and styled exclusively with **Bootstrap 5**:

| Component | Path | Description |
| :--- | :--- | :--- |
| **Navbar** | `frontend/src/components/Navbar.vue` | Responsive navbar with role-based navigation and profile badge |
| **LoginView** | `frontend/src/components/LoginView.vue` | Unified login with demo quick-fill buttons for Admin, Staff, & Trekker |
| **RegisterView**| `frontend/src/components/RegisterView.vue` | Self-registration form for Trekkers with client-side validation |
| **TrekkerDashboard** | `frontend/src/components/TrekkerDashboard.vue`| Explore & filter treks, slot booking modal, booking history, & CSV export |
| **StaffDashboard** | `frontend/src/components/StaffDashboard.vue` | Manage assigned treks, update status/slots, & view participant lists |
| **AdminDashboard** | `frontend/src/components/AdminDashboard.vue` | High-level metrics, trek CRUD, staff provisioning, user moderation, & reports |
| **ProfileView** | `frontend/src/components/ProfileView.vue` | View and update profile details (name, phone) |

### 4. Running Celery Worker & Beat (Optional for Background Batch Processing)
```bash
# Start Celery Worker
celery -A backend.celery_app.celery worker --loglevel=info

# Start Celery Beat (Periodic Scheduler)
celery -A backend.celery_app.celery beat --loglevel=info
```
*(Note: If Redis or Celery is offline, TMA automatically executes background batch jobs via built-in synchronous fallbacks so that local evaluation and demonstrations run without external services).*

---

## 🔌 API Endpoints Summary

| Blueprint | Method | Endpoint | Access | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/auth/register` | Public | Trekker self-registration |
| | `POST` | `/api/auth/login` | Public | Unified login (Admin, Staff, Trekker) |
| | `GET` | `/api/auth/profile` | Authenticated | View current profile |
| | `PUT` | `/api/auth/profile` | Authenticated | Update current profile |
| **Treks** | `GET` | `/api/treks` | Public | List & search/filter treks (Cached) |
| | `GET` | `/api/treks/<id>` | Public | View single trek details |
| | `POST` | `/api/treks` | Admin | Create trekking route |
| | `PUT` | `/api/treks/<id>` | Admin | Update trek details |
| | `DELETE` | `/api/treks/<id>` | Admin | Remove trek route |
| **Bookings**| `POST` | `/api/bookings` | Trekker | Book slots (prevents duplicate/overbooking) |
| | `GET` | `/api/bookings/my-bookings` | Trekker | View personal booking history |
| | `PUT` | `/api/bookings/<id>/cancel`| Owner/Admin | Cancel booking & return slots |
| **Staff** | `GET` | `/api/staff/dashboard` | Staff | View assigned treks & participant counts |
| | `GET` | `/api/staff/treks/<id>/participants` | Staff/Admin | View participants for assigned trek |
| | `PUT` | `/api/staff/treks/<id>/status` | Staff/Admin | Update status (Open/Started/Completed) |
| | `PUT` | `/api/staff/treks/<id>/slots` | Staff/Admin | Update available slot capacity |
| **Admin** | `GET` | `/api/admin/dashboard` | Admin | Overall metrics & recent activity |
| | `GET` | `/api/admin/users` | Admin | Search users & filter by role/status |
| | `PUT` | `/api/admin/users/<id>/status` | Admin | Deactivate / blacklist / reactivate user |
| | `POST` | `/api/admin/staff` | Admin | Add new Trek Staff with profile |
| | `GET` | `/api/admin/staff` | Admin | List all staff & assigned trek counts |
| | `PUT` | `/api/admin/treks/<id>/assign-staff` | Admin | Assign staff to a trek |
| | `GET` | `/api/admin/bookings` | Admin | View all system-wide bookings |
| | `GET` | `/api/admin/reports` | Admin | Aggregated trekking statistics |
