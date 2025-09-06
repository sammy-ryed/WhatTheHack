import os
from dotenv import load_dotenv
import pymysql
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import praw
import requests
import json

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
        reframed TEXT,
        domain VARCHAR(255),
        difficulty VARCHAR(255)
    )
""")
print("✅ Table 'problems' is ready")

# ---------------------------
# Helper: Scrape Reddit
# ---------------------------
def scrape_reddit(subreddit_list, keywords):
    problems = []
    for name in subreddit_list:
        try:
            for submission in reddit.subreddit(name).hot(limit=15):
                if submission.stickied:
                    continue

                text = submission.title
                if submission.selftext:
                    text += " " + submission.selftext
                text = text.strip()

                if len(text.split()) <= 8:
                    continue

                if any(kw in text.lower() for kw in keywords):
                    problems.append(text)
        except Exception as e:
            print(f"⚠️ Skipping {name}: {e}")
    return problems

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

    cursor.execute(
        "INSERT INTO problems (text, reframed, domain, difficulty) VALUES (%s, %s, %s, %s)",
        (req.text, reframed, domain, difficulty)
    )
    db.commit()
    print("💾 Saved to database")

    return result

@app.get("/fetch")
def fetch_route():
    subreddits = [
        "techsupport", "learnprogramming", "webdev", "Entrepreneur",
        "cscareerquestions", "CSStudents", "AskProgramming",
        "buildapc", "linuxquestions", "applehelp"
    ]

    keywords = [
        "how", "why", "error", "issue", "problem", "can't", "cannot",
        "doesn't", "won't", "help", "stuck", "crash", "bug", "fail", "broken"
    ]

    raw_posts = scrape_reddit(subreddits, keywords)

    if not raw_posts:
        return {"problems": []}

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """
You are an assistant that extracts real problems from Reddit posts.
Keep any post that clearly describes a challenge, bug, question, or obstacle.
Even if small or casual, keep it.
Discard memes, vague discussions, or irrelevant posts.
Return a JSON object with a key 'problems' containing an array of problem statements.
            """},
            {"role": "user", "content": "\n".join(raw_posts)}
        ],
        response_format={"type": "json_object"}
    )

    try:
        filtered = json.loads(response.choices[0].message.content)
        problems = filtered.get("problems", [])
    except Exception as e:
        print("❌ JSON parse error:", e)
        problems = []

    return {"problems": problems}

@app.get("/problems")
def list_problems():
    cursor.execute("SELECT * FROM problems ORDER BY id DESC")
    return cursor.fetchall()
