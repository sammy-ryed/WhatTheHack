import os
import json
import pymysql
import praw
from dotenv import load_dotenv
from fastapi import FastAPI
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
# Connect to MySQL
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
    """Scrape hot posts from given subreddits if they match keywords"""
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
# Request body schema
# ---------------------------
class ProblemRequest(BaseModel):
    text: str

# ---------------------------
# Routes
# ---------------------------
@app.post("/reframe")
def reframe_problem(req: ProblemRequest):
    """Reframe a single user problem into hackathon format"""
    print(f"📩 Received problem: {req.text}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that reframes raw user problems into hackathon-style challenges. Also classify into domain and difficulty."
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
                            "reframed": {"type": "string"},
                            "domain": {"type": "string"},
                            "difficulty": {"type": "string"}
                        },
                        "required": ["reframed", "domain", "difficulty"]
                    }
                }
            }
        )

        # Safer: use content instead of `.parsed`
        result = json.loads(response.choices[0].message.content)

        cursor.execute(
            "INSERT INTO problems (text, reframed, domain, difficulty) VALUES (%s, %s, %s, %s)",
            (req.text, result["reframed"], result["domain"], result["difficulty"])
        )
        db.commit()
        print(f"✨ Reframed: {result['reframed']} | Domain: {result['domain']} | Difficulty: {result['difficulty']}")
        return result

    except Exception as e:
        print(f"❌ OpenAI/DB error: {e}")
        return {"error": "Failed to process problem"}

@app.get("/fetch")
def fetch_route():
    """Scrape Reddit, reframe posts, and save to DB"""
    subreddits = [
        "techsupport", "learnprogramming", "webdev", "Entrepreneur",
        "cscareerquestions", "AskProgramming",
        "buildapc", "linuxquestions", "applehelp"
    ]
    keywords = [
        "how", "why", "error", "issue", "problem", "can't", "cannot",
        "doesn't", "won't", "help", "stuck", "crash", "bug", "fail", "broken"
    ]

    # Scrape max 10 posts
    raw_posts = scrape_reddit(subreddits, keywords)[:10]
    if not raw_posts:
        return {"problems": []}

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
You are an assistant that reframes Reddit posts into hackathon-style problems.
For each input post, return JSON with:
- reframed: problem statement
- domain: choose from [AI/ML, FinTech, Blockchain, HealthTech, WebDev, General Tech]
- difficulty: Easy, Medium, or Hard
Return {"problems": [ ... ]}.
"""
                },
                {"role": "user", "content": json.dumps(raw_posts)}
            ],
            response_format={"type": "json_object"}
        )

        parsed = json.loads(response.choices[0].message.content)
        problems = parsed.get("problems", [])

        # Save each problem into DB
        for idx, p in enumerate(problems):
            try:
                cursor.execute(
                    "INSERT INTO problems (text, reframed, domain, difficulty) VALUES (%s, %s, %s, %s)",
                    (
                        raw_posts[idx],
                        p.get("reframed", ""),
                        p.get("domain", ""),
                        p.get("difficulty", "")
                    )
                )
            except Exception as e:
                print(f"⚠️ DB insert failed: {e}")
        db.commit()

        return {"problems": problems}

    except Exception as e:
        print(f"❌ Error in batch OpenAI processing: {e}")
        return {"problems": []}

@app.get("/problems")
def list_problems():
    """List all problems stored in DB"""
    cursor.execute("SELECT * FROM problems ORDER BY id DESC")
    return cursor.fetchall()
