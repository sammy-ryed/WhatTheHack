import os
import json
import random
import pymysql
import praw
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "whatthehack")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---------------------------
# Init Reddit client
# ---------------------------
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY not found. Check your .env file.")
print("✅ OpenAI API key loaded")

# ---------------------------
# Init FastAPI + OpenAI
# ---------------------------
app = FastAPI()
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------
# DB connection helper
# ---------------------------
def get_cursor():
    """Get a live MySQL cursor with auto-reconnect."""
    global db, cursor
    try:
        db.ping(reconnect=True)
    except Exception as e:
        print("⚠️ Reconnecting to MySQL:", e)
        db = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
    return db.cursor()

# Init DB
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

# Ensure table exists (with title column)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        text TEXT,
        reframed TEXT,
        domain VARCHAR(255),
        difficulty VARCHAR(255)
    )
""")
db.commit()
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
            print(f"⚠️ Skipping subreddit {name}: {e}")
    return problems

# ---------------------------
# Random subreddit selection per domain
# ---------------------------
domain_subreddits = {
    "AI/ML": ["MachineLearning", "datascience", "deeplearning"],
    "FinTech": ["FinTech", "personalfinance", "financialindependence", "cryptocurrency"],
    "Blockchain": ["ethereum", "CryptoTechnology", "Solana", "web3", "NFT"],
    "HealthTech": ["healthIT", "DigitalHealth", "medtech", "Bioinformatics", "Healthcare"],
    "WebDev": ["webdev", "learnprogramming", "linuxquestions", "buildapc", "applehelp"],
    "General Tech": ["techsupport", "Entrepreneur", "startups", "IoT", "cscareerquestions"]
}

def get_random_subreddits_per_domain(n_per_domain=2):
    selected = []
    for domain, subs in domain_subreddits.items():
        selected += random.sample(subs, min(n_per_domain, len(subs)))
    return selected

# ---------------------------
# Request body schema
# ---------------------------
class ProblemRequest(BaseModel):
    text: str

# ---------------------------
# Routes
# ---------------------------
@app.post("/reframe")
def reframe_problem(req: ProblemRequest):
    """Reframe a single user problem into hackathon format and generate title"""
    cursor = get_cursor()
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
You are an assistant that reframes raw user problems into hackathon-style challenges.
Also, generate a very short catchy title (max 5 words) for the problem.
Classify the problem into domain and difficulty.
"""
                },
                {"role": "user", "content": req.text}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "reframed_problem",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "reframed": {"type": "string"},
                            "domain": {"type": "string"},
                            "difficulty": {"type": "string"}
                        },
                        "required": ["title", "reframed", "domain", "difficulty"]
                    }
                }
            }
        )

        result = json.loads(response.choices[0].message.content)

        cursor.execute(
            "INSERT INTO problems (title, text, reframed, domain, difficulty) VALUES (%s, %s, %s, %s, %s)",
            (result["title"], req.text, result["reframed"], result["domain"], result["difficulty"])
        )
        db.commit()
        return result

    except Exception as e:
        print(f"❌ Error in /reframe: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/fetch")
def fetch_route():
    """Scrape Reddit, generate titles, reframe posts, save to DB, and show debug info"""
    subreddits = get_random_subreddits_per_domain(n_per_domain=2)
    print("🔹 Selected subreddits for this fetch:", subreddits)

    keywords = [
        "how", "why", "error", "issue", "problem", "can't", "cannot",
        "doesn't", "won't", "help", "stuck", "crash", "bug", "fail", "broken"
    ]

    raw_posts = scrape_reddit(subreddits, keywords)[:10]

    print("🔹 Raw Reddit posts being scraped:")
    for idx, post in enumerate(raw_posts, 1):
        print(f"{idx}: {post}\n")

    if not raw_posts:
        return {"raw_posts": [], "problems": []}

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
You are an assistant that reframes Reddit posts into hackathon-style problems.
For each post, generate:
- title: a very short catchy title (max 5 words)
- reframed: problem statement
- domain: choose from [AI/ML, FinTech, Blockchain, HealthTech, WebDev, General Tech]
- difficulty: Easy, Medium, or Hard
Return the result as a JSON object like:
{"problems": [ ... ]}
"""
                },
                {
                    "role": "user",
                    "content": f"Please convert the following posts to JSON format:\n{json.dumps(raw_posts)}"
                }
            ],
            response_format={"type": "json_object"}
        )

        parsed = json.loads(response.choices[0].message.content)
        problems = parsed.get("problems", [])

        cursor = get_cursor()
        for idx, p in enumerate(problems):
            try:
                cursor.execute(
                    "INSERT INTO problems (title, text, reframed, domain, difficulty) VALUES (%s, %s, %s, %s, %s)",
                    (
                        p.get("title", ""),
                        raw_posts[idx],
                        p.get("reframed", ""),
                        p.get("domain", ""),
                        p.get("difficulty", "")
                    )
                )
            except Exception as e:
                print(f"⚠️ DB insert failed: {e}")
        db.commit()

        return {"raw_posts": raw_posts, "problems": problems}

    except Exception as e:
        print(f"❌ Error in /fetch: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/problems")
def list_problems():
    """List all problems stored in DB"""
    try:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM problems ORDER BY id DESC")
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error in /problems: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
