import os
from dotenv import load_dotenv
import pymysql
from fastapi import FastAPI
from pydantic import BaseModel
import praw
import json
import time
import requests

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "whatthehack")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # Hugging Face API Token

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

print("🔑 Checking environment...")
if HF_API_TOKEN:
    print("✅ Hugging Face API key loaded")
else:
    raise ValueError("❌ HF_API_TOKEN not found. Check your .env file.")

# ---------------------------
# Init FastAPI
# ---------------------------
app = FastAPI()

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
# Helper: Reframe problem using Hugging Face Inference API
# ---------------------------
HF_MODEL = "google/flan-t5-large"  # use small/base/large only


def reframe_with_hf(text):
    prompt = f"""
Reframe this raw user problem into a hackathon challenge.
Also classify its domain and difficulty.

Problem: {text}

Return JSON with keys 'reframed', 'domain', 'difficulty'.
"""
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": prompt}

    max_retries = 3
    wait_seconds = 5

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{HF_MODEL}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            output_text = response.json()[0]["generated_text"].strip()
            return json.loads(output_text)
        except Exception as e:
            print(f"⚠️ Hugging Face error / JSON parse issue: {e}")
            time.sleep(wait_seconds)
            wait_seconds *= 2

    # fallback if parsing fails
    return {"reframed": text, "domain": "Unknown", "difficulty": "Unknown"}

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

    result = reframe_with_hf(req.text)
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

    # 🔹 Limit to first 10 posts
    raw_posts = raw_posts[:10]

    system_prompt = """
You are an assistant that extracts real problems from Reddit posts.
Keep any post that clearly describes a challenge, bug, question, or obstacle.
Even if small or casual, keep it.
Discard memes, vague discussions, or irrelevant posts.
Return a JSON object with a key 'problems' containing an array of problem statements.
    """

    user_content = "\n".join(raw_posts)
    
    max_retries = 3
    wait_seconds = 5
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            # parse JSON
            filtered = json.loads(response.choices[0].message.content)
            problems = filtered.get("problems", [])
            break
        except Exception as e:
            print(f"⚠️ OpenAI error / JSON parse issue: {e}. Retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)
            wait_seconds *= 2  # exponential backoff
            problems = []

    return {"problems": problems}


@app.get("/problems")
def list_problems():
    cursor.execute("SELECT * FROM problems ORDER BY id DESC")
    return cursor.fetchall()
