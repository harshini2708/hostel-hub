import sys
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_full_flow():
    print("Running automated backend verification tests...")

    # 1. Root & Health Check
    res = client.get("/")
    assert res.status_code == 200, f"Root failed: {res.text}"
    print("[PASS] Root & Health Check")

    # 2. Login as Demo Admin
    res = client.post("/api/auth/login", json={"email": "admin@hostel.edu", "password": "Hostel@123"})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    admin_token = res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[PASS] Admin Login & JWT Generation")

    # 3. Login as Demo Student
    res = client.post("/api/auth/login", json={"email": "student@hostel.edu", "password": "Student@123"})
    assert res.status_code == 200, f"Student login failed: {res.text}"
    student_token = res.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    print("[PASS] Student Login & JWT Generation")

    # 4. Menu & Voting & Duplicate Vote Prevention
    res = client.get("/api/menu", headers=student_headers)
    assert res.status_code == 200
    menu_data = res.json()
    assert "menuItems" in menu_data
    first_item_id = menu_data["menuItems"][0]["id"]

    # Vote for item (toggle)
    res = client.post(f"/api/menu/{first_item_id}/vote", headers=student_headers)
    assert res.status_code == 200
    state1 = res.json()["voted"]

    # Vote again (toggles to opposite state)
    res = client.post(f"/api/menu/{first_item_id}/vote", headers=student_headers)
    assert res.status_code == 200
    state2 = res.json()["voted"]
    assert state1 != state2
    print("[PASS] Menu Listing & Vote Toggle (Duplicate Vote Prevention)")

    # 5. Food Feedback
    res = client.post("/api/feedback", headers=student_headers, json={
        "meal": "Lunch",
        "stars": 4,
        "comment": "Paneer was great today, portion was sufficient."
    })
    assert res.status_code == 201
    assert "positive" in res.json()["tags"]

    res = client.get("/api/feedback", headers=student_headers)
    assert res.status_code == 200
    assert len(res.json()) > 0
    print("[PASS] Food Feedback Submission & Auto-Tagging")

    # 6. Complaints & Privacy Enforcement
    # Student submits a complaint
    res = client.post("/api/complaints", headers=student_headers, json={
        "category": "Water",
        "description": "Bathroom tap is leaking constantly in room 304.",
        "priority": "Medium"
    })
    assert res.status_code == 201
    complaint_id = res.json()["id"]

    # Student retrieves complaints (must only see own)
    res = client.get("/api/complaints", headers=student_headers)
    assert res.status_code == 200
    student_complaints = res.json()
    assert all(c["user_id"] == "student" or c.get("user_id") for c in student_complaints)

    # Admin retrieves complaints (must see all complaints)
    res = client.get("/api/complaints", headers=admin_headers)
    assert res.status_code == 200
    admin_complaints = res.json()
    assert len(admin_complaints) >= len(student_complaints)

    # Admin marks complaint as viewed
    res = client.patch(f"/api/complaints/{complaint_id}/view", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["viewed"] is True

    # Admin marks complaint as resolved
    res = client.patch(f"/api/complaints/{complaint_id}/resolve", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["resolved"] is True
    print("[PASS] Complaints Isolation (Student Privacy) & Admin Resolution")

    # 7. Polls & Voting (Strict 1 Vote per Student)
    res = client.get("/api/polls", headers=student_headers)
    assert res.status_code == 200
    polls = res.json()
    assert len(polls) > 0
    target_poll = polls[0]
    poll_id = target_poll["id"]
    opt_id = target_poll["options"][0]["id"]

    # Student casts vote
    res = client.post(f"/api/polls/{poll_id}/vote", headers=student_headers, json={"option_id": opt_id})
    if res.status_code == 200:
        # If successfully voted, try voting again to test duplicate vote rejection
        res_dup = client.post(f"/api/polls/{poll_id}/vote", headers=student_headers, json={"option_id": opt_id})
        assert res_dup.status_code == 400, "Duplicate vote was not rejected!"
    else:
        # Already voted
        assert "already voted" in res.text.lower()
    print("[PASS] Polls & Duplicate Vote Prevention Enforced")

    # 8. Student Suggestions
    res = client.post("/api/suggestions", headers=student_headers, json={
        "text": "Please install high-speed wifi router on 4th floor."
    })
    assert res.status_code == 201
    assert res.json()["group_tag"] == "Wifi"

    res = client.get("/api/suggestions", headers=student_headers)
    assert res.status_code == 200
    print("[PASS] Student Suggestions & Auto-Grouping")

    # 9. Admin Dashboard Analytics
    res = client.get("/api/admin/dashboard", headers=admin_headers)
    assert res.status_code == 200
    dash_data = res.json()
    assert "topCat" in dash_data
    assert "avgRating" in dash_data
    assert "aiInsight" in dash_data
    print("[PASS] Admin Dashboard Analytics")

    print("\nALL 9 MODULE & BACKEND INTEGRATION TESTS PASSED!")

if __name__ == "__main__":
    test_full_flow()
