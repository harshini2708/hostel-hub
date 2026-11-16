import os
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.config import settings
from backend.auth import hash_password

# Path for local SQLite fallback
DB_PATH = Path(__file__).resolve().parent.parent / "hostelhub_local.db"

class DatabaseManager:
    def __init__(self):
        self.use_supabase = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY and "supabase.co" in settings.SUPABASE_URL)
        self.supabase = None
        if self.use_supabase:
            try:
                from supabase import create_client
                self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                print("Connected to Supabase PostgreSQL.")
                self._seed_supabase_if_empty()
            except Exception as e:
                print(f"Supabase connection warning: {e}. Falling back to persistent local storage.")
                self.use_supabase = False

        if not self.use_supabase:
            self._init_local_db()

    def _seed_supabase_if_empty(self):
        """Seed default demo accounts and items into Supabase if empty."""
        try:
            users_res = self.supabase.table("users").select("id").limit(1).execute()
            if not users_res.data:
                now = datetime.now(timezone.utc).isoformat()
                admin_id = str(uuid.uuid4())
                self.supabase.table("users").insert({
                    "id": admin_id,
                    "email": "admin@hostel.edu",
                    "hashed_password": hash_password("Hostel@123"),
                    "full_name": "Hostel Warden",
                    "room_number": "Warden Office",
                    "role": "warden",
                    "created_at": now
                }).execute()

                student_id = str(uuid.uuid4())
                self.supabase.table("users").insert({
                    "id": student_id,
                    "email": "student@hostel.edu",
                    "hashed_password": hash_password("Student@123"),
                    "full_name": "Harshini (Student)",
                    "room_number": "Room 304",
                    "role": "student",
                    "created_at": now
                }).execute()

                self.supabase.table("menu_settings").upsert({"id": 1, "is_locked": False, "updated_at": now}).execute()

                menu_dishes = [
                    {"day": "Mon", "dish": "Paneer Butter Masala", "created_at": now},
                    {"day": "Mon", "dish": "Chole Bhature", "created_at": now},
                    {"day": "Wed", "dish": "Veg Biryani", "created_at": now},
                    {"day": "Wed", "dish": "Rajma Chawal", "created_at": now},
                    {"day": "Fri", "dish": "Dosa & Sambhar", "created_at": now}
                ]
                self.supabase.table("menu_items").insert(menu_dishes).execute()

                fb_data = [
                    {"user_id": student_id, "meal": "Lunch", "stars": 2, "comment": "Rice was cold and the curry had too much oil today.", "tags": ["quality"], "created_at": now},
                    {"user_id": student_id, "meal": "Dinner", "stars": 3, "comment": "Same paneer dish as last two Fridays, a bit repetitive.", "tags": ["repetition"], "created_at": now},
                    {"user_id": student_id, "meal": "Breakfast", "stars": 5, "comment": "Loved the poha, portion was just right.", "tags": ["positive"], "created_at": now}
                ]
                self.supabase.table("food_feedback").insert(fb_data).execute()

                comp_data = [
                    {"user_id": student_id, "category": "Water", "description": "No water supply on the 3rd floor since morning, urgent.", "priority": "High", "viewed": True, "resolved": False, "created_at": now, "updated_at": now},
                    {"user_id": student_id, "category": "WiFi", "description": "WiFi has been slow in Block B every evening this week.", "priority": "Medium", "viewed": True, "resolved": False, "created_at": now, "updated_at": now},
                    {"user_id": student_id, "category": "Cleanliness", "description": "Washroom on 2nd floor needs cleaning, minor issue but recurring.", "priority": "Low", "viewed": False, "resolved": False, "created_at": now, "updated_at": now},
                    {"user_id": student_id, "category": "Electricity", "description": "Room 214 fan not working, sparking sound when switched on.", "priority": "High", "viewed": True, "resolved": True, "created_at": now, "updated_at": now},
                    {"user_id": student_id, "category": "Maintenance", "description": "Cupboard door in room 108 is broken.", "priority": "Medium", "viewed": False, "resolved": False, "created_at": now, "updated_at": now}
                ]
                self.supabase.table("complaints").insert(comp_data).execute()

                p1 = self.supabase.table("polls").insert({"question": "Should Sunday breakfast start 30 minutes later?", "created_by": admin_id, "is_active": True, "created_at": now}).execute()
                if p1.data:
                    self.supabase.table("poll_options").insert([
                        {"poll_id": p1.data[0]["id"], "label": "Yes, shift to 8:30 AM", "created_at": now},
                        {"poll_id": p1.data[0]["id"], "label": "No, keep 8:00 AM", "created_at": now}
                    ]).execute()

                p2 = self.supabase.table("polls").insert({"question": "Preferred snack for evening mess?", "created_by": admin_id, "is_active": True, "created_at": now}).execute()
                if p2.data:
                    self.supabase.table("poll_options").insert([
                        {"poll_id": p2.data[0]["id"], "label": "Samosa", "created_at": now},
                        {"poll_id": p2.data[0]["id"], "label": "Sandwich", "created_at": now},
                        {"poll_id": p2.data[0]["id"], "label": "Fruit chaat", "created_at": now}
                    ]).execute()

                sugg_data = [
                    {"user_id": student_id, "text": "Add a water purifier on the 3rd floor near the common room.", "group_tag": "Water", "created_at": now},
                    {"user_id": student_id, "text": "Extend WiFi router range to cover Block C fully.", "group_tag": "WiFi", "created_at": now},
                    {"user_id": student_id, "text": "A weekly laundry slot booking system would help avoid queues.", "group_tag": "Laundry", "created_at": now},
                    {"user_id": student_id, "text": "More water coolers needed near the mess entrance.", "group_tag": "Water", "created_at": now}
                ]
                self.supabase.table("suggestions").insert(sugg_data).execute()
                print("Seeded initial demo data to Supabase successfully.")
        except Exception as e:
            print(f"Notice during Supabase initial seed check: {e}")

    def _get_sqlite(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_local_db(self):
        """Initialize local SQLite tables and initial seed data if Supabase is not yet configured."""
        with self._get_sqlite() as conn:
            c = conn.cursor()
            # Users
            c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                room_number TEXT,
                role TEXT NOT NULL DEFAULT 'student',
                created_at TEXT
            )
            """)
            # Menu Items
            c.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT NOT NULL,
                dish TEXT NOT NULL,
                created_at TEXT
            )
            """)
            # Menu Settings (lock status)
            c.execute("""
            CREATE TABLE IF NOT EXISTS menu_settings (
                id INTEGER PRIMARY KEY,
                is_locked INTEGER DEFAULT 0,
                updated_at TEXT
            )
            """)
            c.execute("INSERT OR IGNORE INTO menu_settings (id, is_locked, updated_at) VALUES (1, 0, datetime('now'))")

            # Menu Votes (Unique user_id + menu_item_id)
            c.execute("""
            CREATE TABLE IF NOT EXISTS menu_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                menu_item_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                created_at TEXT,
                UNIQUE(menu_item_id, user_id)
            )
            """)

            # Food Feedback
            c.execute("""
            CREATE TABLE IF NOT EXISTS food_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                meal TEXT NOT NULL,
                stars INTEGER NOT NULL,
                comment TEXT,
                tags TEXT,
                created_at TEXT
            )
            """)

            # Complaints
            c.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'Medium',
                viewed INTEGER DEFAULT 0,
                resolved INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
            """)

            # Polls
            c.execute("""
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                created_by TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
            """)

            # Poll Options
            c.execute("""
            CREATE TABLE IF NOT EXISTS poll_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                created_at TEXT
            )
            """)

            # Poll Votes (Unique user_id + poll_id)
            c.execute("""
            CREATE TABLE IF NOT EXISTS poll_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                option_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                created_at TEXT,
                UNIQUE(poll_id, user_id)
            )
            """)

            # Suggestions
            c.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                text TEXT NOT NULL,
                group_tag TEXT DEFAULT 'General',
                created_at TEXT
            )
            """)

            conn.commit()

            # Seed default demo users and data if empty
            c.execute("SELECT COUNT(*) as count FROM users")
            if c.fetchone()["count"] == 0:
                self._seed_default_data(conn)

    def _seed_default_data(self, conn):
        c = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        # Seed admin user (Password: Hostel@123)
        admin_id = str(uuid.uuid4())
        c.execute("""
        INSERT INTO users (id, email, hashed_password, full_name, room_number, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (admin_id, "admin@hostel.edu", hash_password("Hostel@123"), "Hostel Warden", "Warden Office", "warden", now))

        # Seed demo student user (Password: Student@123)
        student_id = str(uuid.uuid4())
        c.execute("""
        INSERT INTO users (id, email, hashed_password, full_name, room_number, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, "student@hostel.edu", hash_password("Student@123"), "Harshini (Student)", "Room 304", "student", now))

        # Seed menu items
        menu_items = [
            ("Mon", "Paneer Butter Masala"),
            ("Mon", "Chole Bhature"),
            ("Wed", "Veg Biryani"),
            ("Wed", "Rajma Chawal"),
            ("Fri", "Dosa & Sambhar")
        ]
        for day, dish in menu_items:
            c.execute("INSERT INTO menu_items (day, dish, created_at) VALUES (?, ?, ?)", (day, dish, now))

        # Seed some dummy votes
        c.execute("SELECT id FROM menu_items")
        item_ids = [r["id"] for r in c.fetchall()]
        if item_ids:
            # Add initial votes for dish 1 and 2
            for i in range(14):
                c.execute("INSERT OR IGNORE INTO menu_votes (menu_item_id, user_id, created_at) VALUES (?, ?, ?)", (item_ids[0], f"mock_user_{i}", now))
            for i in range(21):
                c.execute("INSERT OR IGNORE INTO menu_votes (menu_item_id, user_id, created_at) VALUES (?, ?, ?)", (item_ids[1], f"mock_user_{i+20}", now))
            for i in range(27):
                c.execute("INSERT OR IGNORE INTO menu_votes (menu_item_id, user_id, created_at) VALUES (?, ?, ?)", (item_ids[2], f"mock_user_{i+50}", now))

        # Seed feedback
        feedback_list = [
            (student_id, "Lunch", 2, "Rice was cold and the curry had too much oil today.", json.dumps(["quality"])),
            (student_id, "Dinner", 3, "Same paneer dish as last two Fridays, a bit repetitive.", json.dumps(["repetition"])),
            (student_id, "Breakfast", 5, "Loved the poha, portion was just right.", json.dumps(["positive"]))
        ]
        for uid, meal, stars, comment, tags in feedback_list:
            c.execute("INSERT INTO food_feedback (user_id, meal, stars, comment, tags, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (uid, meal, stars, comment, tags, now))

        # Seed complaints
        complaints_list = [
            (student_id, "Water", "No water supply on the 3rd floor since morning, urgent.", "High", 1, 0),
            (str(uuid.uuid4()), "WiFi", "WiFi has been slow in Block B every evening this week.", "Medium", 1, 0),
            (str(uuid.uuid4()), "Cleanliness", "Washroom on 2nd floor needs cleaning, minor issue but recurring.", "Low", 0, 0),
            (str(uuid.uuid4()), "Electricity", "Room 214 fan not working, sparking sound when switched on.", "High", 1, 1),
            (str(uuid.uuid4()), "Maintenance", "Cupboard door in room 108 is broken.", "Medium", 0, 0),
        ]
        for uid, cat, desc, pri, viewed, resolved in complaints_list:
            c.execute("""
            INSERT INTO complaints (user_id, category, description, priority, viewed, resolved, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (uid, cat, desc, pri, viewed, resolved, now, now))

        # Seed polls
        c.execute("INSERT INTO polls (question, created_by, is_active, created_at) VALUES (?, ?, ?, ?)",
                  ("Should Sunday breakfast start 30 minutes later?", admin_id, 1, now))
        poll1_id = c.lastrowid
        c.execute("INSERT INTO poll_options (poll_id, label, created_at) VALUES (?, ?, ?)", (poll1_id, "Yes, shift to 8:30 AM", now))
        opt1_id = c.lastrowid
        c.execute("INSERT INTO poll_options (poll_id, label, created_at) VALUES (?, ?, ?)", (poll1_id, "No, keep 8:00 AM", now))
        opt2_id = c.lastrowid

        for i in range(31):
            c.execute("INSERT INTO poll_votes (poll_id, option_id, user_id, created_at) VALUES (?, ?, ?, ?)",
                      (poll1_id, opt1_id, f"mock_voter_{i}", now))
        for i in range(19):
            c.execute("INSERT INTO poll_votes (poll_id, option_id, user_id, created_at) VALUES (?, ?, ?, ?)",
                      (poll1_id, opt2_id, f"mock_voter_{i+100}", now))

        c.execute("INSERT INTO polls (question, created_by, is_active, created_at) VALUES (?, ?, ?, ?)",
                  ("Preferred snack for evening mess?", admin_id, 1, now))
        poll2_id = c.lastrowid
        c.execute("INSERT INTO poll_options (poll_id, label, created_at) VALUES (?, ?, ?)", (poll2_id, "Samosa", now))
        s_opt1 = c.lastrowid
        c.execute("INSERT INTO poll_options (poll_id, label, created_at) VALUES (?, ?, ?)", (poll2_id, "Sandwich", now))
        s_opt2 = c.lastrowid
        c.execute("INSERT INTO poll_options (poll_id, label, created_at) VALUES (?, ?, ?)", (poll2_id, "Fruit chaat", now))
        s_opt3 = c.lastrowid

        for i in range(22):
            c.execute("INSERT INTO poll_votes (poll_id, option_id, user_id, created_at) VALUES (?, ?, ?, ?)", (poll2_id, s_opt1, f"pv1_{i}", now))
        for i in range(14):
            c.execute("INSERT INTO poll_votes (poll_id, option_id, user_id, created_at) VALUES (?, ?, ?, ?)", (poll2_id, s_opt2, f"pv2_{i}", now))
        for i in range(9):
            c.execute("INSERT INTO poll_votes (poll_id, option_id, user_id, created_at) VALUES (?, ?, ?, ?)", (poll2_id, s_opt3, f"pv3_{i}", now))

        # Seed suggestions
        suggestions_list = [
            (student_id, "Add a water purifier on the 3rd floor near the common room.", "Water"),
            (str(uuid.uuid4()), "Extend WiFi router range to cover Block C fully.", "WiFi"),
            (str(uuid.uuid4()), "A weekly laundry slot booking system would help avoid queues.", "Laundry"),
            (str(uuid.uuid4()), "More water coolers needed near the mess entrance.", "Water")
        ]
        for uid, text, tag in suggestions_list:
            c.execute("INSERT INTO suggestions (user_id, text, group_tag, created_at) VALUES (?, ?, ?, ?)",
                      (uid, text, tag, now))

        conn.commit()

    # ========================== USER OPERATIONS ==========================
    def get_user_by_email(self, email: str) -> Optional[dict]:
        if self.use_supabase:
            res = self.supabase.table("users").select("*").eq("email", email.lower()).execute()
            return res.data[0] if res.data else None
        else:
            with self._get_sqlite() as conn:
                r = conn.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()
                return dict(r) if r else None

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        if self.use_supabase:
            res = self.supabase.table("users").select("*").eq("id", user_id).execute()
            return res.data[0] if res.data else None
        else:
            with self._get_sqlite() as conn:
                r = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
                return dict(r) if r else None

    def create_user(self, email: str, hashed_password: str, full_name: str, room_number: Optional[str], role: str = "student") -> dict:
        now = datetime.now(timezone.utc).isoformat()
        user_id = str(uuid.uuid4())
        data = {
            "id": user_id,
            "email": email.lower(),
            "hashed_password": hashed_password,
            "full_name": full_name,
            "room_number": room_number or "",
            "role": role,
            "created_at": now
        }
        if self.use_supabase:
            res = self.supabase.table("users").insert(data).execute()
            return res.data[0]
        else:
            with self._get_sqlite() as conn:
                conn.execute("""
                INSERT INTO users (id, email, hashed_password, full_name, room_number, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, data["email"], hashed_password, full_name, data["room_number"], role, now))
                conn.commit()
            return data

    # ========================== MENU OPERATIONS ==========================
    def get_menu_items(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        if self.use_supabase:
            items_res = self.supabase.table("menu_items").select("*").order("id").execute()
            items = items_res.data or []
            votes_res = self.supabase.table("menu_votes").select("menu_item_id, user_id").execute()
            votes = votes_res.data or []
            settings_res = self.supabase.table("menu_settings").select("is_locked").eq("id", 1).execute()
            is_locked = bool(settings_res.data[0]["is_locked"]) if settings_res.data else False
        else:
            with self._get_sqlite() as conn:
                items = [dict(r) for r in conn.execute("SELECT * FROM menu_items ORDER BY id").fetchall()]
                votes = [dict(r) for r in conn.execute("SELECT menu_item_id, user_id FROM menu_votes").fetchall()]
                s = conn.execute("SELECT is_locked FROM menu_settings WHERE id = 1").fetchone()
                is_locked = bool(s["is_locked"]) if s else False

        # Aggregate votes
        vote_counts = {}
        user_voted_items = set()
        for v in votes:
            mid = v["menu_item_id"]
            vote_counts[mid] = vote_counts.get(mid, 0) + 1
            if user_id and str(v["user_id"]) == str(user_id):
                user_voted_items.add(mid)

        enriched_items = []
        for item in items:
            enriched_items.append({
                "id": item["id"],
                "day": item["day"],
                "dish": item["dish"],
                "votes": vote_counts.get(item["id"], 0),
                "voted": item["id"] in user_voted_items
            })

        return {
            "menuLocked": is_locked,
            "menuItems": enriched_items
        }

    def add_menu_item(self, day: str, dish: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        if self.use_supabase:
            res = self.supabase.table("menu_items").insert({"day": day, "dish": dish, "created_at": now}).execute()
            # If menu was locked, reopen it when a new item is added
            self.supabase.table("menu_settings").update({"is_locked": False, "updated_at": now}).eq("id", 1).execute()
            return res.data[0]
        else:
            with self._get_sqlite() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO menu_items (day, dish, created_at) VALUES (?, ?, ?)", (day, dish, now))
                item_id = cur.lastrowid
                conn.execute("UPDATE menu_settings SET is_locked = 0, updated_at = ? WHERE id = 1", (now,))
                conn.commit()
                return {"id": item_id, "day": day, "dish": dish, "votes": 0, "voted": False}

    def toggle_menu_vote(self, menu_item_id: int, user_id: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        if self.use_supabase:
            # Check existing vote
            existing = self.supabase.table("menu_votes").select("id").eq("menu_item_id", menu_item_id).eq("user_id", user_id).execute()
            if existing.data:
                self.supabase.table("menu_votes").delete().eq("id", existing.data[0]["id"]).execute()
                voted = False
            else:
                self.supabase.table("menu_votes").insert({"menu_item_id": menu_item_id, "user_id": user_id, "created_at": now}).execute()
                voted = True
        else:
            with self._get_sqlite() as conn:
                r = conn.execute("SELECT id FROM menu_votes WHERE menu_item_id = ? AND user_id = ?", (menu_item_id, user_id)).fetchone()
                if r:
                    conn.execute("DELETE FROM menu_votes WHERE id = ?", (r["id"],))
                    voted = False
                else:
                    conn.execute("INSERT INTO menu_votes (menu_item_id, user_id, created_at) VALUES (?, ?, ?)", (menu_item_id, user_id, now))
                    voted = True
                conn.commit()
        return {"menu_item_id": menu_item_id, "voted": voted}

    def set_menu_locked(self, locked: bool) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        if self.use_supabase:
            self.supabase.table("menu_settings").upsert({"id": 1, "is_locked": locked, "updated_at": now}).execute()
        else:
            with self._get_sqlite() as conn:
                conn.execute("UPDATE menu_settings SET is_locked = ?, updated_at = ? WHERE id = 1", (1 if locked else 0, now))
                conn.commit()
        return locked

    # ========================== FEEDBACK OPERATIONS ==========================
    def get_feedback(self) -> List[dict]:
        if self.use_supabase:
            res = self.supabase.table("food_feedback").select("*").order("id", desc=True).limit(50).execute()
            feedbacks = res.data or []
            for f in feedbacks:
                if isinstance(f.get("tags"), str):
                    try: f["tags"] = json.loads(f["tags"])
                    except: f["tags"] = []
            return feedbacks
        else:
            with self._get_sqlite() as conn:
                rows = conn.execute("SELECT * FROM food_feedback ORDER BY id DESC LIMIT 50").fetchall()
                out = []
                for r in rows:
                    d = dict(r)
                    try: d["tags"] = json.loads(d["tags"]) if d["tags"] else []
                    except: d["tags"] = []
                    out.append(d)
                return out

    def add_feedback(self, user_id: str, meal: str, stars: int, comment: str, tags: List[str]) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "user_id": user_id,
            "meal": meal,
            "stars": stars,
            "comment": comment or "",
            "tags": json.dumps(tags),
            "created_at": now
        }
        if self.use_supabase:
            res = self.supabase.table("food_feedback").insert(data).execute()
            ret = res.data[0]
            ret["tags"] = tags
            return ret
        else:
            with self._get_sqlite() as conn:
                cur = conn.cursor()
                cur.execute("""
                INSERT INTO food_feedback (user_id, meal, stars, comment, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, meal, stars, comment or "", json.dumps(tags), now))
                conn.commit()
                return {"id": cur.lastrowid, "user_id": user_id, "meal": meal, "stars": stars, "comment": comment, "tags": tags, "created_at": now}

    # ========================== COMPLAINTS OPERATIONS ==========================
    def get_complaints(self, current_user: dict) -> List[dict]:
        """
        Students ONLY see their own complaints.
        Warden sees all complaints across the hostel.
        """
        is_warden = current_user.get("role") == "warden"
        user_id = current_user.get("id")

        if self.use_supabase:
            try:
                query = self.supabase.table("complaints").select("*, users(full_name, room_number)")
                if not is_warden:
                    query = query.eq("user_id", user_id)
                res = query.order("id", desc=True).execute()
                data = res.data or []
                for item in data:
                    u = item.pop("users", None) or {}
                    if isinstance(u, list) and len(u) > 0: u = u[0]
                    item["studentName"] = u.get("full_name", "Student")
                    item["roomNumber"] = u.get("room_number", "")
                    item["desc"] = item.get("description", "")
                return data
            except Exception:
                query = self.supabase.table("complaints").select("*")
                if not is_warden:
                    query = query.eq("user_id", user_id)
                res = query.order("id", desc=True).execute()
                data = res.data or []
                for item in data:
                    item["studentName"] = "Student"
                    item["roomNumber"] = ""
                    item["desc"] = item.get("description", "")
                return data
        else:
            with self._get_sqlite() as conn:
                if is_warden:
                    rows = conn.execute("""
                    SELECT c.*, u.full_name as studentName, u.room_number as roomNumber
                    FROM complaints c
                    LEFT JOIN users u ON c.user_id = u.id
                    ORDER BY c.id DESC
                    """).fetchall()
                else:
                    rows = conn.execute("""
                    SELECT c.*, u.full_name as studentName, u.room_number as roomNumber
                    FROM complaints c
                    LEFT JOIN users u ON c.user_id = u.id
                    WHERE c.user_id = ?
                    ORDER BY c.id DESC
                    """, (user_id,)).fetchall()

                out = []
                for r in rows:
                    d = dict(r)
                    d["desc"] = d.get("description", "")
                    d["viewed"] = bool(d["viewed"])
                    d["resolved"] = bool(d["resolved"])
                    out.append(d)
                return out

    def add_complaint(self, user_id: str, category: str, description: str, priority: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "user_id": user_id,
            "category": category,
            "description": description,
            "priority": priority,
            "viewed": False,
            "resolved": False,
            "created_at": now,
            "updated_at": now
        }
        if self.use_supabase:
            res = self.supabase.table("complaints").insert(data).execute()
            ret = res.data[0]
            ret["desc"] = ret.get("description", "")
            return ret
        else:
            with self._get_sqlite() as conn:
                cur = conn.cursor()
                cur.execute("""
                INSERT INTO complaints (user_id, category, description, priority, viewed, resolved, created_at, updated_at)
                VALUES (?, ?, ?, ?, 0, 0, ?, ?)
                """, (user_id, category, description, priority, now, now))
                conn.commit()
                return {"id": cur.lastrowid, **data, "desc": description}

    def mark_complaint_viewed(self, complaint_id: int) -> Optional[dict]:
        now = datetime.now(timezone.utc).isoformat()
        if self.use_supabase:
            res = self.supabase.table("complaints").update({"viewed": True, "updated_at": now}).eq("id", complaint_id).execute()
            return res.data[0] if res.data else None
        else:
            with self._get_sqlite() as conn:
                conn.execute("UPDATE complaints SET viewed = 1, updated_at = ? WHERE id = ?", (now, complaint_id))
                conn.commit()
                r = conn.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
                if not r: return None
                d = dict(r)
                d["viewed"] = bool(d["viewed"])
                d["resolved"] = bool(d["resolved"])
                return d

    def mark_complaint_resolved(self, complaint_id: int) -> Optional[dict]:
        now = datetime.now(timezone.utc).isoformat()
        if self.use_supabase:
            res = self.supabase.table("complaints").update({"viewed": True, "resolved": True, "updated_at": now}).eq("id", complaint_id).execute()
            return res.data[0] if res.data else None
        else:
            with self._get_sqlite() as conn:
                conn.execute("UPDATE complaints SET viewed = 1, resolved = 1, updated_at = ? WHERE id = ?", (now, complaint_id))
                conn.commit()
                r = conn.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
                if not r: return None
                d = dict(r)
                d["viewed"] = bool(d["viewed"])
                d["resolved"] = bool(d["resolved"])
                return d

    # ========================== POLLS OPERATIONS ==========================
    def get_polls(self, user_id: Optional[str] = None) -> List[dict]:
        if self.use_supabase:
            polls_res = self.supabase.table("polls").select("*").eq("is_active", True).order("id", desc=True).execute()
            polls = polls_res.data or []
            if not polls: return []
            poll_ids = [p["id"] for p in polls]
            options_res = self.supabase.table("poll_options").select("*").in_("poll_id", poll_ids).execute()
            votes_res = self.supabase.table("poll_votes").select("*").in_("poll_id", poll_ids).execute()

            options_by_poll = {}
            for opt in (options_res.data or []):
                options_by_poll.setdefault(opt["poll_id"], []).append(opt)

            votes = votes_res.data or []
        else:
            with self._get_sqlite() as conn:
                polls = [dict(r) for r in conn.execute("SELECT * FROM polls WHERE is_active = 1 ORDER BY id DESC").fetchall()]
                if not polls: return []
                options = [dict(r) for r in conn.execute("SELECT * FROM poll_options ORDER BY id").fetchall()]
                votes = [dict(r) for r in conn.execute("SELECT * FROM poll_votes").fetchall()]

                options_by_poll = {}
                for opt in options:
                    options_by_poll.setdefault(opt["poll_id"], []).append(opt)

        out = []
        for p in polls:
            pid = p["id"]
            opts = options_by_poll.get(pid, [])
            # Count votes per option
            opt_votes = {}
            user_voted = False
            for v in votes:
                if v["poll_id"] == pid:
                    opt_votes[v["option_id"]] = opt_votes.get(v["option_id"], 0) + 1
                    if user_id and str(v["user_id"]) == str(user_id):
                        user_voted = True

            enriched_opts = []
            for opt in opts:
                enriched_opts.append({
                    "id": opt["id"],
                    "label": opt["label"],
                    "votes": opt_votes.get(opt["id"], 0)
                })

            out.append({
                "id": pid,
                "q": p["question"],
                "options": enriched_opts,
                "userVoted": user_voted
            })
        return out

    def create_poll(self, question: str, options: List[str], created_by: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        if self.use_supabase:
            p_res = self.supabase.table("polls").insert({"question": question, "created_by": created_by, "is_active": True, "created_at": now}).execute()
            poll = p_res.data[0]
            poll_id = poll["id"]
            opt_data = [{"poll_id": poll_id, "label": opt, "created_at": now} for opt in options]
            o_res = self.supabase.table("poll_options").insert(opt_data).execute()
            return {"id": poll_id, "q": question, "options": [{"id": o["id"], "label": o["label"], "votes": 0} for o in o_res.data], "userVoted": False}
        else:
            with self._get_sqlite() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO polls (question, created_by, is_active, created_at) VALUES (?, ?, 1, ?)", (question, created_by, now))
                poll_id = cur.lastrowid
                created_opts = []
                for opt in options:
                    cur.execute("INSERT INTO poll_options (poll_id, label, created_at) VALUES (?, ?, ?)", (poll_id, opt, now))
                    created_opts.append({"id": cur.lastrowid, "label": opt, "votes": 0})
                conn.commit()
                return {"id": poll_id, "q": question, "options": created_opts, "userVoted": False}

    def vote_poll(self, poll_id: int, option_id: int, user_id: str) -> dict:
        """Vote on a poll option with strict duplicate vote prevention."""
        now = datetime.now(timezone.utc).isoformat()
        if self.use_supabase:
            # Check if user already voted in this poll
            existing = self.supabase.table("poll_votes").select("id").eq("poll_id", poll_id).eq("user_id", user_id).execute()
            if existing.data:
                raise ValueError("You have already voted in this poll.")
            self.supabase.table("poll_votes").insert({
                "poll_id": poll_id,
                "option_id": option_id,
                "user_id": user_id,
                "created_at": now
            }).execute()
        else:
            with self._get_sqlite() as conn:
                r = conn.execute("SELECT id FROM poll_votes WHERE poll_id = ? AND user_id = ?", (poll_id, user_id)).fetchone()
                if r:
                    raise ValueError("You have already voted in this poll.")
                conn.execute("""
                INSERT INTO poll_votes (poll_id, option_id, user_id, created_at)
                VALUES (?, ?, ?, ?)
                """, (poll_id, option_id, user_id, now))
                conn.commit()
        return {"poll_id": poll_id, "option_id": option_id, "userVoted": True}

    # ========================== SUGGESTIONS OPERATIONS ==========================
    def get_suggestions(self) -> List[dict]:
        if self.use_supabase:
            res = self.supabase.table("suggestions").select("*").order("id", desc=True).execute()
            return res.data or []
        else:
            with self._get_sqlite() as conn:
                return [dict(r) for r in conn.execute("SELECT * FROM suggestions ORDER BY id DESC").fetchall()]

    def add_suggestion(self, user_id: str, text: str, group_tag: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        if self.use_supabase:
            res = self.supabase.table("suggestions").insert({
                "user_id": user_id,
                "text": text,
                "group_tag": group_tag,
                "created_at": now
            }).execute()
            return res.data[0]
        else:
            with self._get_sqlite() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO suggestions (user_id, text, group_tag, created_at) VALUES (?, ?, ?, ?)",
                            (user_id, text, group_tag, now))
                conn.commit()
                return {"id": cur.lastrowid, "user_id": user_id, "text": text, "group_tag": group_tag, "created_at": now}

    # ========================== ADMIN DASHBOARD ANALYTICS ==========================
    def get_dashboard_analytics(self) -> dict:
        """Calculate aggregated analytics across all hostel data."""
        # 1. Complaints breakdown
        complaints = self.get_complaints({"role": "warden"})
        cat_counts = {}
        unresolved = 0
        for c in complaints:
            cat = c.get("category", "General")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            if not c.get("resolved"):
                unresolved += 1

        top_cat = max(cat_counts.items(), key=lambda x: x[1])[0] if cat_counts else "None"

        # 2. Menu vote stats
        menu_data = self.get_menu_items()
        menu_items = menu_data.get("menuItems", [])
        top_food = max(menu_items, key=lambda x: x["votes"]) if menu_items else {"dish": "None", "votes": 0}

        # 3. Feedback avg rating
        feedbacks = self.get_feedback()
        if feedbacks:
            avg_rating = round(sum(f["stars"] for f in feedbacks) / len(feedbacks), 1)
        else:
            avg_rating = 0.0

        # 4. Suggestions breakdown
        suggestions = self.get_suggestions()
        sugg_counts = {}
        for s in suggestions:
            g = s.get("group_tag") or "General"
            sugg_counts[g] = sugg_counts.get(g, 0) + 1

        top_sugg = max(sugg_counts.items(), key=lambda x: x[1])[0] if sugg_counts else "General"

        # Trend (last 7 days dummy/trend baseline)
        trend = [3.6, 3.8, 3.4, 3.9, 4.1, 3.7, float(avg_rating) if avg_rating > 0 else 4.0]

        ai_insight = (
            f"{top_cat} complaints are this week's top category ({cat_counts.get(top_cat, 0)} logged), "
            f"with {unresolved} still unresolved. '{top_food.get('dish')}' is the most-requested dish "
            f"with {top_food.get('votes')} votes, and the average meal rating stands at {avg_rating}/5. "
            f"The most repeated student suggestions relate to '{top_sugg}' — recommended to prioritize for the upcoming week."
        )

        return {
            "topCat": top_cat,
            "unresolved": unresolved,
            "topFood": top_food,
            "avgRating": str(avg_rating),
            "topSugg": top_sugg,
            "catCounts": cat_counts,
            "suggCounts": sugg_counts,
            "trend": trend,
            "aiInsight": ai_insight
        }

db = DatabaseManager()
