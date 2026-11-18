# Trekking Management Application

A full-stack web application designed for adventure trekking organizations to manage multi-day expeditions, guide assignments, participant registrations, reviews, and safety operations.

Built as a Single Page Application (SPA) using Vue 3 on the frontend and Python Flask on the backend.

---

## Tech Stack

* **Frontend:** Vue 3, Vue Router, Bootstrap 5
* **Backend:** Python 3, Flask, Flask-SQLAlchemy, Flask-CORS, PyJWT
* **Database:** SQLite
* **Caching & Broker:** Redis
* **Async Jobs:** Celery & Celery Beat (with automatic synchronous fallbacks if Redis is offline)

---

## Project Structure

```text
trekking-management/
├── backend/
│   ├── models/            # SQLAlchemy database models
│   ├── routes/            # REST API blueprints (auth, admin, staff, treks, bookings)
│   ├── templates/         # Jinja2 root template (index.html)
│   ├── app.py             # Flask application entry point
│   ├── cache.py           # Redis caching helper
│   ├── celery_app.py      # Celery task configuration
│   ├── tasks.py           # Background tasks (reminders, reports, CSV export)
│   └── seed_data.py       # Realistic sample data seeder
├── frontend/
│   ├── src/
│   │   ├── components/    # Vue Single File Components (.vue)
│   │   └── app.js         # Frontend router and state setup
│   ├── manifest.json      # PWA manifest
│   └── sw.js              # Service worker script
└── README.md
```

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Populate Sample Data (Recommended)
```bash
python backend/seed_data.py
```
This sets up realistic Himalayan treks, certified staff guides, sample trekkers, and existing bookings.

### 3. Start the Web Server
```bash
python backend/app.py
```
Once started, open your browser at: **`http://127.0.0.1:5000/`**

---

## Default Login Credentials

| Role | Username / Email | Password | What They Can Do |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` (or `admin@trekking.com`) | `Admin@123` | Full dashboard metrics, create/edit treks, add staff, manage users, view reports |
| **Trek Staff** | `staff_arjun` | `StaffPassword123` | View assigned expeditions, manage slot capacity, update status, participant check-in |
| **Trekker** | `trekker_rahul` | `Password123` | Search & book treks, cancel bookings, view itinerary & packing gear list, post reviews |

*New trekkers can also self-register directly through the **Register** page.*

---

## Background Tasks (Celery & Redis)

The application includes automated asynchronous jobs:
1. **Daily Reminders:** Dispatches alerts to participants 3 days before their trek starts.
2. **Monthly Activity Report:** Compiles a summary report of bookings and revenue for the admin.
3. **Async CSV Export:** Allows users to download their complete trekking history as a CSV file.

*Note: If Redis or Celery is not running locally, TMA automatically falls back to executing batch operations synchronously so all features remain testable without external services.*

To start Celery manually (optional):
```bash
# In terminal 1 - Worker
celery -A backend.celery_app.celery worker --loglevel=info

# In terminal 2 - Scheduler
celery -A backend.celery_app.celery beat --loglevel=info
```
