# HostelHub — Smart Hostel Management System

HostelHub is a full-stack smart hostel operations platform featuring weekly mess menu voting, food ratings, private complaints with warden status tracking, hostel polls, student suggestions, and an admin analytics dashboard.

---

## Tech Stack
- **Frontend**: Responsive HTML5, CSS3, Vanilla JavaScript (REST API integration).
- **Backend**: Python 3 (FastAPI, Pydantic, Uvicorn, PyJWT).
- **Database**: Supabase PostgreSQL (with automatic local persistent fallback for offline development).

---

## 6 Modules Overview

1. **Weekly Mess Menu & Voting**:
   - Wardens can add dishes and lock/publish or reopen the menu.
   - Students can cast votes; database unique constraints prevent duplicate voting.
2. **Food Feedback & Ratings**:
   - Students rate meals (1–5 stars) with optional comments.
   - Automatic keyword scanning detects tags (`quality`, `taste`, `quantity`, `repetition`, `positive`).
3. **Student Complaints with Admin Tracking**:
   - **Privacy Guard**: Students can only access their own private complaints and receive status updates.
   - **Warden View**: Wardens see all complaints hostel-wide, filtered by `unviewed`, `viewed`, and `resolved`.
   - Wardens can mark complaints as "Admin viewed" or "Resolved".
4. **Hostel Polls & Voting**:
   - Wardens can publish polls with 2 to 4 options.
   - Students vote; the backend strictly enforces one vote per student per poll.
5. **Student Suggestions**:
   - Permanent suggestion box grouped by topic (`Water`, `WiFi`, `Laundry`, `General`, etc.).
6. **Admin Dashboard with Analytics**:
   - Real-time aggregation of most-reported complaint categories, unresolved count, most-voted dishes, and average satisfaction ratings.
   - 7-day satisfaction trend chart.
   - Generated weekly AI insight summarizing key operational highlights.

---

## Quick Start (Local)

### 1. Start the FastAPI Backend
Open a terminal in the project folder and run:
```bash
python -m backend.main
```
The backend server will start at `http://localhost:8000`.
- API Documentation (Swagger UI): `http://localhost:8000/docs`
- Interactive ReDoc: `http://localhost:8000/redoc`

### 2. Open the Frontend
Simply double-click or open `index.html` in any web browser!

---

## Connecting to Supabase PostgreSQL

HostelHub works out of the box with persistent local storage, and connects to Supabase PostgreSQL whenever you are ready:

1. **Create a Supabase Project**:
   - Sign up or log in at [supabase.com](https://supabase.com).
   - Create a new project.
2. **Run Database Migration**:
   - Go to the **SQL Editor** in your Supabase dashboard.
   - Open `supabase_schema.sql` from this folder, paste its contents into the SQL Editor, and click **Run**.
   - This creates all 8 tables, unique constraints, and indexes.
3. **Set Environment Variables**:
   - In Supabase, go to **Project Settings** -> **API**.
   - Copy your **Project URL** and **anon / service_role API Key**.
   - Open the `.env` file in this project and paste them:
     ```env
     SUPABASE_URL=https://your-project.supabase.co
     SUPABASE_KEY=your-supabase-key-here
     ```
4. Restart the backend server. HostelHub will now read and write directly to your cloud Supabase database!

---

## Default Demo Credentials

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Student** | `student@hostel.edu` | `Student@123` | Menu voting, ratings, private complaints, poll votes |
| **Warden / Admin** | `admin@hostel.edu` | `Hostel@123` | Menu locking/adding, complaint management, poll creation, dashboard analytics |
