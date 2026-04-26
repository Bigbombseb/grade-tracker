import json, os, requests

# --- SECRETS (loaded from GitHub) ---
COOKIE_STRING = os.environ["COOKIE_STRING"].replace("\n", "").replace("\r", "").strip()

BASE_URL = "https://taboracademy.myschoolapp.com"
STUDENT_ID = "7493993"
GRADES_FILE = "last_grades.json"

def send_text(message):
    bot_token = os.environ["DISCORD_TOKEN"]
    user_id = os.environ["DISCORD_USER_ID"]

    # Open a DM channel
    r = requests.post(
        "https://discord.com/api/v10/users/@me/channels",
        headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"},
        json={"recipient_id": user_id}
    )
    channel_id = r.json()["id"]

    # Send the message
    requests.post(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"},
        json={"content": message}
    )

def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        "Cookie": COOKIE_STRING,
        "Referer": BASE_URL
    })
    return session

def get_grades(session):
    r = session.get(BASE_URL + "/api/datadirect/ParentStudentUserClassesGet?userId=7493993&schoolYearLabel=2025%20-%202026&memberLevel=3&persona=2&durationList=173822&markingPeriodId=")
    print("Status:", r.status_code)

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
    except Exception as e:
        print("Error parsing grades:", e)
        return {}

def check_for_changes():
    session = get_session()
    current = get_grades(session)

    if not current:
        print("No grades found — cookie may have expired.")
        send_text("Grade tracker: session expired, please update your cookie.")
        return

    print("Grades found:", current)

    if os.path.exists(GRADES_FILE):
        with open(GRADES_FILE) as f:
            previous = json.load(f)

        changes = []
        for subject, grade in current.items():
            if subject in previous and previous[subject] != grade:
                changes.append(f"{subject}: {previous[subject]} -> {grade}")
            elif subject not in previous:
                changes.append(f"New grade posted: {subject}: {grade}")

        if changes:
            send_text("Tabor Grade Update!\n" + "\n".join(changes))
            print("Sent:", changes)
        else:
            print("No changes.")
    else:
        send_text("Grade tracker is live! You'll get Discord DMs when grades change.")
        print("First run done.")

    with open(GRADES_FILE, "w") as f:
        json.dump(current, f)
        print(f"Saved {len(current)} grades.")

check_for_changes()
