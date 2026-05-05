import json, os, requests

BASE_URL = "https://taboracademy.myschoolapp.com"
STUDENT_ID = "7493993"
MARKING_PERIOD_ID = "19936"
GRADES_FILE = "last_grades.json"

SECTIONS = {
    "Algebra 2": "115175645",
    "Courage & Conviction": "115172678",
    "Honors Chemistry": "115175893",
    "Honors Spanish 3": "115180406",
    "Honors US History": "115173126"
}

def send_text(message):
    bot_token = os.environ["DISCORD_TOKEN"]
    user_id = os.environ["DISCORD_USER_ID"]
    r = requests.post(
        "https://discord.com/api/v10/users/@me/channels",
        headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"},
        json={"recipient_id": user_id}
    )
    channel_id = r.json()["id"]
    requests.post(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"},
        json={"content": message}
    )

def get_session():
    with open("cookie.txt") as f:
        cookie_string = f.read().strip()
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        "Cookie": cookie_string,
        "Referer": BASE_URL
    })
    return session

def get_course_grades(session):
    r = session.get(BASE_URL + f"/api/datadirect/ParentStudentUserClassesGet?userId={STUDENT_ID}&schoolYearLabel=2025%20-%202026&memberLevel=3&persona=2&durationList=173822&markingPeriodId=")
    try:
        data = r.json()
        grades = {}
        if isinstance(data, list):
            for course in data:
                name = course.get("sectionidentifier", "")
                grade = course.get("cumgrade") or course.get("CumulativeDisplay") or "N/A"
                if name:
                    grades[name] = str(grade)
        return grades
    except:
        return {}

def get_assignments(session):
    assignments = {}
    for course_name, section_id in SECTIONS.items():
        r = session.get(BASE_URL + f"/api/gradebook/AssignmentPerformanceStudent?sectionId={section_id}&markingPeriodId={MARKING_PERIOD_ID}&studentId={STUDENT_ID}")
        try:
            data = r.json()
            for a in data:
                assignment_id = str(a.get("AssignmentId", ""))
                name = a.get("AssignmentShortDescription", "").replace("<br />", "").strip()
                points = a.get("Points")
                max_points = a.get("MaxPoints")
                if assignment_id and name and points is not None and max_points:
                    pct = round((points / max_points) * 100, 1)
                    assignments[assignment_id] = {
                        "course": course_name,
                        "name": name,
                        "grade": f"{points}/{max_points} ({pct}%)"
                    }
        except:
            continue
    return assignments

def check_for_changes():
    session = get_session()
    current_grades = get_course_grades(session)
    current_assignments = get_assignments(session)

    if not current_grades:
        print("No grades found — login may have failed.")
        send_text("Grade tracker: login failed, check your credentials.")
        return

    print("Grades found:", current_grades)
    print(f"Assignments found: {len(current_assignments)}")

    if os.path.exists(GRADES_FILE):
        with open(GRADES_FILE) as f:
            previous = json.load(f)

        prev_grades = previous.get("grades", {})
        prev_assignments = previous.get("assignments", {})
        messages = []

        # Check course grade changes
        for subject, grade in current_grades.items():
            if subject in prev_grades and prev_grades[subject] != grade:
                messages.append(f"📊 {subject}: {prev_grades[subject]} -> {grade}")

        # Check new assignments
        for assignment_id, info in current_assignments.items():
            if assignment_id not in prev_assignments:
                messages.append(f"📝 New grade in {info['course']}:\n    {info['name']}: {info['grade']}")

        if messages:
            send_text("Tabor Update!\n" + "\n".join(messages))
            print("Sent:", messages)
        else:
            print("No changes.")
    else:
        send_text("Grade tracker is live! You'll get Discord DMs when grades change.")
        print("First run done.")

    with open(GRADES_FILE, "w") as f:
        json.dump({"grades": current_grades, "assignments": current_assignments}, f)
        print(f"Saved {len(current_grades)} grades and {len(current_assignments)} assignments.")

check_for_changes()
