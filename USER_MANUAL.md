# Trekking Management Application (TMA) - User & Developer Manual

**Student ID:** `24f3002830`  
**Course:** Modern Application Development II (MAD-2)  
**Version:** 2.0 (Milestone 6 Final Release)

---

## 📖 Table of Contents
1. [Overview & Architecture](#1-overview--architecture)
2. [Mandatory Frameworks & Standards](#2-mandatory-frameworks--standards)
3. [User Roles & Key Capabilities](#3-user-roles--key-capabilities)
4. [Quick Start & Installation](#4-quick-start--installation)
5. [Step-by-Step User Workflows](#5-step-by-step-user-workflows)
   - [Superuser Admin Guide](#51-superuser-admin-guide)
   - [Trek Staff Guide](#52-trek-staff-guide)
   - [Trekker (User) Guide](#53-trekker-user-guide)
6. [Payment Simulation & In-App Notifications](#6-payment-simulation--in-app-notifications)
7. [Celery Batch Jobs & Caching](#7-celery-batch-jobs--caching)
8. [Automated Verification Suites](#8-automated-verification-suites)
9. [Packaging for Submission](#9-packaging-for-submission)

---

## 1. Overview & Architecture

The **Trekking Management Application (TMA)** is a multi-role, responsive web platform designed to streamline and automate trekking operations for adventure organizations. It connects organizers (Admin), certified mountain guides (Trek Staff), and participants (Trekkers) on a unified digital platform.

### Directory Structure
```text
trekking-management/
├── backend/
│   ├── models/            # SQLAlchemy unified models & SQLite initialization
│   ├── routes/            # Blueprint API endpoints (auth, admin, staff, treks, bookings)
│   ├── templates/         # Jinja2 entry point for Vue 3 SPA mounting
│   ├── app.py             # Main Flask server entry point
│   ├── cache.py           # Redis caching with graceful fallback
│   ├── celery_app.py      # Celery app & Celery Beat periodic scheduler
│   ├── tasks.py           # Batch tasks (reminders, monthly reports, CSV export)
│   └── seed_data.py       # Realistic Himalayan demo data seeder
├── frontend/
│   ├── src/
│   │   ├── components/    # Vue.js Single File Components (.vue)
│   │   │   ├── Navbar.vue
│   │   │   ├── LoginView.vue
│   │   │   ├── RegisterView.vue
│   │   │   ├── TrekkerDashboard.vue
│   │   │   ├── StaffDashboard.vue
│   │   │   ├── AdminDashboard.vue
│   │   │   └── ProfileView.vue
│   │   └── app.js         # Frontend controller, router & SFC loader
│   └── index.html         # Frontend static entry
├── run_all_tests.py       # Master automated test suite (Milestones 1–6)
├── package_submission.py  # Submission packager producing zip archive
├── README.md              # Project documentation
└── requirements.txt       # Project dependencies
```

---

## 2. Mandatory Frameworks & Standards

* **Backend API:** Python Flask (RESTful JSON APIs, RBAC authentication).
* **Frontend UI:** Vue.js 3 Single Page Application (SPA) with Vue Router 4.
* **Styling & Layout:** Bootstrap 5 & Bootstrap Icons (no other CSS frameworks).
* **Entry Point:** Jinja2 template (`backend/templates/index.html`) used exclusively as the CDN entry point.
* **Database:** SQLite initialized programmatically (manual DB creation strictly prohibited).
* **Caching:** Redis for frequently accessed trek routes with automatic fallback.
* **Batch Jobs:** Redis + Celery for scheduled reminders, monthly activity reports, and async CSV exports.

---

## 3. User Roles & Key Capabilities

| Capability | Admin (Superuser) | Trek Staff | Trekker (User) |
| :--- | :---: | :---: | :---: |
| Self-Registration | ❌ (Pre-seeded only) | ❌ (Created by Admin) | ✅ |
| Browse & Search Treks | ✅ | ✅ | ✅ |
| Book Open Treks | ❌ | ❌ | ✅ |
| Overbooking Safeguard | Enforced | Enforced | Enforced |
| Payment Simulation & Receipt | — | — | ✅ |
| Download Trek History (CSV) | ✅ | — | ✅ |
| Manage Assigned Treks | ✅ (All) | ✅ (Assigned only) | ❌ |
| Update Slots & Status | ✅ | ✅ | ❌ |
| View Participant Contact Lists| ✅ | ✅ (Assigned only) | ❌ |
| Deactivate / Blacklist Users | ✅ | ❌ | ❌ |
| View Aggregated Analytics | ✅ (Chart.js) | ❌ | ❌ |
| In-App Notification Center | ✅ | ✅ | ✅ |

---

## 4. Quick Start & Installation

### Step 1: Install Python Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 2: Seed Realistic Demonstration Data
```bash
python backend/seed_data.py
```

### Step 3: Start the Web Application
```bash
python backend/app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000/`**

### Pre-Configured Accounts for Demonstration:
* **Admin:** `admin@trekking.com` / `Admin@123`
* **Staff Guide:** `staff_arjun` / `StaffPassword123`
* **Trekker:** `trekker_rahul` / `Password123`
*(Convenient one-click quick-fill buttons are available on the Login screen).*

---

## 5. Step-by-Step User Workflows

### 5.1 Superuser Admin Guide
1. **Login:** Log in using `admin@trekking.com` and password `Admin@123`.
2. **Dashboard Metrics:** View real-time cards showing total treks, active users, certified staff, total bookings, and overall revenue.
3. **Manage Treks:**
   - Click **Add New Trek** to configure route name, difficulty (*Easy*, *Moderate*, *Hard*), duration, slots, pricing, and assigned staff.
   - Edit or delete existing routes (protected against deleting routes with active bookings).
4. **Manage Staff:**
   - Click **Add Staff Member** to provision certified staff credentials, experience years, and bio.
   - One-click button to deactivate or reactivate staff accounts.
5. **Moderate Users:**
   - Search trekkers by name, email, or username.
   - Click **Blacklist / Reactivate** to immediately prevent deactivated users from logging in.
6. **Reports & Analytics:**
   - View the interactive **Chart.js slot utilization chart**.
   - Trigger the **Monthly HTML Report** or **Daily Reminders** on demand.

### 5.2 Trek Staff Guide
1. **Login:** Log in with staff credentials provisioned by the Admin (`staff_arjun`).
2. **Assigned Treks:** The dashboard displays only the expeditions assigned to your account.
3. **Status Updates:** Use the dropdown to update trek status to `Open`, `Closed`, `Started`, or `Completed`.
4. **Slot Management:** Adjust available slot capacity in real time.
5. **Participant Lists:** Click **Participants** to view the full roster (name, email, phone number, slots booked) for your trek.

### 5.3 Trekker (User) Guide
1. **Explore Treks:** Browse open expeditions using real-time keyword search, difficulty filter, and location filters.
2. **Booking & Checkout Simulation:**
   - Click **Book Now** on any open trek.
   - Choose slot count and select your preferred payment simulation method (UPI, Card, Net Banking).
   - Click **Confirm & Book**; an instant transaction reference (`TXN_...`) is generated and slots are deducted.
3. **Notifications:** Check the notification bell in the top navbar to view the instant booking confirmation alert.
4. **My Bookings & Cancellation:**
   - View your upcoming and historical treks.
   - Cancel any active booking with one click to release the slots back to the trek.
5. **CSV History Export:**
   - Click **Export History (CSV)** to trigger an asynchronous export task and automatically download your trekking history file.

---

## 6. Payment Simulation & In-App Notifications

* **Payment Simulation:**
  * Supports test checkout simulation across UPI (*GooglePay / PhonePe*), Credit/Debit Card, and Net Banking.
  * Every successful reservation generates a unique transaction reference (e.g. `TXN_1794915696_111`) and marks `payment_status = 'Paid'`.
* **In-App Notification Center:**
  * Real-time notification badge displayed on the navigation bell.
  * Automatic alerts generated on booking confirmation, cancellations, and upcoming trek reminders.
  * Includes one-click "Mark all read" and individual read-state management.

---

## 7. Trek Reviews, Ratings & Progressive Web App (PWA)

### Star Ratings & Trekker Reviews
* Trekkers can view aggregate star ratings (1 to 5 stars) and feedback on every trek card.
* Clicking **View Reviews** opens an interactive modal with full review histories and submission capabilities:
  * Select star rating (1 to 5).
  * Provide trail feedback comments.
  * Real-time calculation and display of average trek rating.

### Progressive Web App (PWA) & "Add to Desktop"
* The application conforms to modern PWA specifications with a Web App Manifest (`manifest.json`) and a dedicated Service Worker (`sw.js`).
* Users can install the TMA application directly to their Desktop or Mobile home screen:
  * In Chrome / Edge: Click the **Install** or **Add to Desktop** icon in the browser address bar.
  * Launches as a standalone native window without browser address bar clutter.
  * Static shell caching ensures fast startup.

---

## 8. Celery Batch Jobs & Caching

### Redis Caching
* Frequently browsed treks (`GET /api/treks`) are cached in Redis with a 5-minute TTL.
* Modifying, creating, or booking a trek automatically clears `treks:*` cache keys.
* Built-in fallback gracefully handles offline Redis servers without crashing.

### Celery Background Processing
1. **Scheduled Daily Reminders:** Dispatches gear preparation guidelines (shoes, warm clothing, hydration) to trekkers with treks starting within 3 days.
2. **Scheduled Monthly Activity Report:** Generates an HTML report on the 1st of every month summarizing performance and revenue.
3. **Async CSV Export:** Generates downloadable CSV records of user booking history asynchronously.

```bash
# Optional: To start Celery Worker and Beat manually
celery -A backend.celery_app.celery worker --loglevel=info
celery -A backend.celery_app.celery beat --loglevel=info
```

---

## 9. Automated Verification Suites

Run the complete test suite across all 7 milestones:
```bash
python run_all_tests.py
```

Or run individual milestone suites:
* `python backend/test_milestone1.py` — Database Models & Authentication
* `python backend/test_milestone2.py` — Core CRUD APIs, Slot Management & Redis Caching
* `python backend/test_milestone3.py` — Celery Batch Jobs & Async CSV Export
* `python backend/test_milestone4.py` — Vue.js 3 + Bootstrap 5 Single Page Application
* `python backend/test_milestone5.py` — Master End-to-End System Integration Checks
* `python backend/test_milestone6.py` — Payment Simulation, Notifications & Analytics
* `python backend/test_milestone7.py` — Reviews, 5-Star Ratings & PWA Add to Desktop

---

## 10. Packaging for Submission

Run the submission packager to create the exact archive required by the course:
```bash
python package_submission.py
```
This produces `trekking_management_24f3002830.zip` ready for evaluation upload.
