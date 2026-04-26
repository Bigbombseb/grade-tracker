import json, os, smtplib, requests
from email.mime.text import MIMEText

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
MY_SMS_EMAIL = os.environ["MY_SMS_EMAIL"]
COOKIE_STRING = os.environ["COOKIE_STRING"]

BASE_URL = "https://taboracademy.myschoolapp.com"
STUDENT_ID = "7493993"
GRADES_FILE = "last_grades.json"

def send_text(message):
    msg = MIMEText(message)
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = MY_SMS_EMAIL
    msg["Subject"] = ""
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, MY_SMS_EMAIL, msg.as_string())

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
            print("Text sent:", changes)
        else:
            print("No changes.")
    else:
        send_text("Grade tracker is live! You'll get texts when grades change.")
        print("First run done.")

    with open(GRADES_FILE, "w") as f:
        json.dump(current, f)
        print(f"Saved {len(current)} grades.")

check_for_changes()
