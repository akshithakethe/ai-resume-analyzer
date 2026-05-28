from flask import Flask, render_template, request, session, make_response
import pdfplumber
import requests
from reportlab.pdfgen import canvas
from io import BytesIO
app = Flask(__name__)
app.secret_key = "ai_resume_final_project"
@app.route('/')
def home():
    return render_template('index.html')
def analyze_resume(text):
    keywords = [
        "python", "html", "css", "javascript", "sql",
        "ai", "machine learning", "flask", "react",
        "java", "c++", "mysql", "project", "internship"
    ]
    skills = []
    suggestions = []
    score = 0
    for k in keywords:
        if k in text.lower():
            score += 10
            skills.append(k)
    if score > 100:
        score = 100
    if "react" not in text.lower():
        suggestions.append("Add React skill to improve frontend profile.")
    if "flask" not in text.lower():
        suggestions.append("Mention Flask/backend projects.")
    if "github" not in text.lower():
        suggestions.append("Add GitHub profile link.")
    if "internship" not in text.lower():
        suggestions.append("Add internship experience section.")
    return score, skills, suggestions
def github_analysis(username):
    data = {"followers": 0, "repos": 0, "following": 0}
    if username:
        try:
            url = f"https://api.github.com/users/{username}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                j = res.json()
                data["followers"] = j.get("followers", 0)
                data["repos"] = j.get("public_repos", 0)
                data["following"] = j.get("following", 0)
        except:
            pass
    github_score = min(data["repos"] * 10 + data["followers"] * 2, 100)
    return data, github_score
@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files['resume']
    github_username = request.form.get('github')
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text()
    score, skills, suggestions = analyze_resume(text)
    gh_data, github_score = github_analysis(github_username)
    selection_score = (score * 0.75) + (github_score * 0.25)
    if github_score == 0:
        selection_score -= 2
    if "react" not in text.lower():
        selection_score -= 3
    if "project" in text.lower():
        selection_score += 3
    if "internship" in text.lower():
        selection_score += 5
    if score >= 75:
        selection_score += 5
    selection_score = max(0, min(100, selection_score))
    if selection_score >= 80:
        recruiter = "Shortlisted ✅"
    elif selection_score >= 60:
        recruiter = "Maybe Selected ⚠️"
    else:
        recruiter = "Rejected ❌"
    reasons = []
    if "python" in text.lower():
        reasons.append("Strong technical skills ✅")
    if "internship" in text.lower():
        reasons.append("Internship experience found ✅")
    if "react" not in text.lower():
        reasons.append("Missing React skill ❌")
    if github_score < 30:
        reasons.append("Low GitHub activity ❌")
    session["data"] = {
        "score": score,
        "skills": skills,
        "github_score": github_score,
        "recruiter": recruiter
    }
    return f"""
<!DOCTYPE html>
<html>
<head>
<title>AI Resume Dashboard</title>
<style>
body {{
    margin: 0;
    font-family: Arial;
    background: linear-gradient(135deg, #141e30, #243b55);
    color: white;
}}
.container {{
    width: 90%;
    margin: auto;
    padding: 30px;
}}
h1 {{
    text-align: center;
}}
.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}}
.card {{
    background: rgba(255,255,255,0.12);
    padding: 20px;
    border-radius: 15px;
    backdrop-filter: blur(10px);
    transition: 0.3s;
}}
.card:hover {{
    transform: scale(1.03);
}}
.score {{
    font-size: 26px;
    font-weight: bold;
    color: #00ff99;
}}

.bar {{
    width: 100%;
    height: 12px;
    background: #222;
    border-radius: 20px;
    margin-top: 10px;
}}
.fill {{
    width: {score}%;
    height: 100%;
    background: #00ff99;
}}
.git {{
    width: {github_score}%;
    height: 100%;
    background: #00d4ff;
}}
.badge {{
    padding: 6px 12px;
    border-radius: 20px;
    font-weight: bold;
}}
.shortlisted {{ background:#00ff88; color:black; }}
.maybe {{ background:orange; color:black; }}
.rejected {{ background:red; }}
.center {{
    text-align:center;
    margin-top:20px;
}}
button {{
    padding: 12px 18px;
    background: #00ff88;
    border: none;
    border-radius: 10px;
    font-weight: bold;
    cursor: pointer;
}}
</style>
</head>
<body>
<div class="container">
<h1>🤖 AI Resume Dashboard</h1>
<div class="grid">
<div class="card">
<h3>ATS Score</h3>
<div class="score">{score}/100</div>
<div class="bar"><div class="fill"></div></div>
</div>

<div class="card">
<h3>GitHub Score</h3>
<div class="score">{github_score}/100</div>
<div class="bar"><div class="git"></div></div>
</div>

<div class="card">
<h3>Recruiter Decision</h3>
<div class="score">
<span class="badge {{
    'shortlisted' if recruiter.startswith('Shortlisted')
    else 'maybe' if recruiter.startswith('Maybe')
    else 'rejected'
}}">
{recruiter}
</span>
</div>
</div>

<div class="card">
<h3>Skills</h3>
<p>{", ".join(skills)}</p>
</div>

<div class="card">
<h3>AI Suggestions</h3>
<ul>
{"".join(f"<li>{s}</li>" for s in suggestions)}
</ul>
</div>

<div class="card">
<h3>Recruiter Reasons</h3>
<ul>
{"".join(f"<li>{r}</li>" for r in reasons)}
</ul>
</div>

</div>

<div class="center">
<a href="/download">
<button>📄 Download PDF Report</button>
</a>
</div>

</div>

</body>
</html>
"""

def create_pdf(score, skills, github_score, recruiter):

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    p.drawString(100, 800, "AI Resume Report")
    p.drawString(100, 760, f"ATS Score: {score}/100")
    p.drawString(100, 740, f"GitHub Score: {github_score}/100")
    p.drawString(100, 720, f"Recruiter: {recruiter}")

    y = 680
    p.drawString(100, 700, "Skills:")

    for s in skills:
        p.drawString(120, y, f"- {s}")
        y -= 20

    p.save()
    buffer.seek(0)
    return buffer

@app.route('/download')
def download():

    data = session.get("data")

    if not data:
        return "No data found"

    pdf = create_pdf(
        data["score"],
        data["skills"],
        data["github_score"],
        data["recruiter"]
    )

    response = make_response(pdf.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=report.pdf"

    return response
    import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)