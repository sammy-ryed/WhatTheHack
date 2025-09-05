import os
from dotenv import load_dotenv
import pymysql
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import praw
import requests


# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "whatthehack")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

print("🔑 Checking environment...")
if OPENAI_API_KEY:
    print("✅ OpenAI API key loaded")
else:
    raise ValueError("❌ OPENAI_API_KEY not found. Check your .env file.")

# ---------------------------
# Init FastAPI + OpenAI
# ---------------------------
app = FastAPI()
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------
# Connect to MySQL with PyMySQL
# ---------------------------
try:
    db = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = db.cursor()
    print(f"✅ Connected to MySQL database '{DB_NAME}' as user '{DB_USER}'")
except Exception as e:
    print("❌ Failed to connect to MySQL:", e)
    raise

# Ensure table exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        id INT AUTO_INCREMENT PRIMARY KEY,
        text TEXT,
        reframed TEXT
    )
""")

print("✅ Table 'problems' is ready")

# ---------------------------
# Request body
# ---------------------------
class ProblemRequest(BaseModel):
    text: str

# ---------------------------
# Routes
# ---------------------------
@app.post("/reframe")
def reframe_problem(req: ProblemRequest):
    print(f"📩 Received problem: {req.text}")
    
    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant that reframes raw user problems into hackathon-style challenges. Also classify into domain and difficulty."},
            {"role": "user", "content": req.text}
        ],
        response_format={ "type": "json_schema", "json_schema": {
            "name": "reframed_problem",
            "schema": {
                "type": "object",
                "properties": {
                    "reframed": {"type": "string"},
                    "domain": {"type": "string"},
                    "difficulty": {"type": "string"}
                },
                "required": ["reframed", "domain", "difficulty"]
            }
        }}
    )

    result = response.choices[0].message.parsed
    reframed = result["reframed"]
    domain = result["domain"]
    difficulty = result["difficulty"]

    print(f"✨ Reframed: {reframed} | Domain: {domain} | Difficulty: {difficulty}")

    # Insert into DB
    cursor.execute(
        "INSERT INTO problems (text, reframed, domain, difficulty) VALUES (%s, %s, %s, %s)",
        (req.text, reframed, domain, difficulty)
    )
    db.commit()
    print("💾 Saved to database")

    return result
@app.get("/fetch")
def fetch_problems():
    problems = []

    # 🔹 Reddit example
    for submission in reddit.subreddit("technology").hot(limit=5):
        problems.append(submission.title)

# 🔹 GitHub Issues example
    """gh_res = requests.get("https://api.github.com/repos/vercel/next.js/issues")
    if gh_res.ok:
        for issue in gh_res.json()[:5]:
            problems.append(issue["title"])"""

    return {"problems": problems}

@app.get("/problems")
def list_problems():
    cursor.execute("SELECT * FROM problems ORDER BY id DESC")
    return cursor.fetchall()
