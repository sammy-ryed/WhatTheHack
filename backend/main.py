import os
import json
import random
import requests
import pymysql
import praw
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import numpy as np
#from bertopic import BERTopic
# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "whatthehack")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY not found. Check your .env file.")
print("✅ OpenAI API key loaded")

# ---------------------------
# Init FastAPI + OpenAI
# ---------------------------
app = FastAPI()
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------
# Init Reddit client
# ---------------------------
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

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

# --- Auto-migrate: check and add 'description' if missing ---
cursor.execute("SHOW COLUMNS FROM problems LIKE 'description'")
if not cursor.fetchone():
    cursor.execute("ALTER TABLE problems ADD COLUMN description TEXT AFTER reframed")
    db.commit()
    print("⚡ Added missing column 'description'")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
problem_queries = [
    "I need help",
    "This is not working",
    "I found a bug",
    "I wish there was a solution",
    "I am struggling with something",
    "Looking for advice",
    "Facing an issue",
    'how can i implement',
    "what's the code for",
    "it was working before but"
]

# Pre-compute embeddings for speed
problem_embeddings = embedder.encode(problem_queries)
def is_problem_post(text, threshold=0.35):
    """
    Returns True if the text is semantically close to a 'problem' intent.
    """
    text_emb = embedder.encode([text])[0]
    sims = [cosine_similarity(text_emb, ref_emb) for ref_emb in problem_embeddings]
    best_score = max(sims)
    
    return best_score >= threshold


sources = {
    "github": {
        "Developer Tools": [
            {"name": "getfider/fider", "description": "Feedback platform for collecting and prioritizing ideas"},
            {"name": "atom/atom", "description": "Hackable text editor for the 21st century"},
            {"name": "instill-ai/community", "description": "Open-source community for AI tooling"},
            {"name": "isaacs/github", "description": "Meta repo for GitHub issues discussions"}
        ],
        "Frontend/Web": [
            {"name": "facebook/react", "description": "A JavaScript library for building user interfaces"},
            {"name": "angular/angular", "description": "Framework for building scalable web applications"}
        ],
        "Finance/Crypto": [
            {"name": "MetaMask/metamask-extension", "description": "Crypto wallet and gateway to blockchain apps"},
            {"name": "ledgerhq/ledger-live-desktop", "description": "Ledger Live desktop app for crypto management"}
        ],
        "Communication/Productivity": [
            {"name": "signalapp/Signal-Android", "description": "Private messaging app with end-to-end encryption"},
            {"name": "obsidianmd/obsidian-releases", "description": "Knowledge base and note-taking app"}
        ]
    },
    "reddit": {
        "AI/ML": [
            {"name": "MachineLearning", "description": "Discussions and news about artificial intelligence and machine learning"},
            {"name": "datascience", "description": "Everything data science: questions, projects, learning"},
            {"name": "deeplearning", "description": "Deep learning discussions and research"}
        ],
        "Blockchain": [
            {"name": "ethereum", "description": "The hub for Ethereum and blockchain technology"},
            {"name": "CryptoTechnology", "description": "Advanced discussions about crypto and blockchain"},
            {"name": "Solana", "description": "Subreddit for the Solana blockchain"},
            {"name": "web3", "description": "Everything related to Web3 and decentralized apps"},
            {"name": "NFT", "description": "Non-fungible token news, projects and culture"}
        ],
        "HealthTech": [
            {"name": "DigitalHealth", "description": "Tech and innovation in healthcare and wellbeing"},
            {"name": "Healthcare", "description": "General discussions about healthcare"},
            {"name": "medtech", "description": "Medical technologies and devices"},
            {"name": "Bioinformatics", "description": "Computational biology and bioinformatics"},
            {"name": "mentalhealth", "description": "Discussions and support around mental health"}
        ],
        "WebDev": [
            {"name": "webdev", "description": "Web development help, tools, and community"},
            {"name": "learnprogramming", "description": "Help and resources for learning programming"},
            {"name": "linuxquestions", "description": "Q&A for Linux users"},
            {"name": "buildapc", "description": "Advice for building PCs"},
            {"name": "applehelp", "description": "Technical help for Apple devices"},
            {"name": "Productivity", "description": "Tips and tricks for productivity"}
        ],
        "Rant": [
            {"name": "rant", "description": "A place to vent frustrations"},
            {"name": "offmychest", "description": "Get things off your chest"},
            {"name": "findapath", "description": "Life guidance and career struggles"},
            {"name": "TrueAskReddit", "description": "Ask genuine questions, get real answers"},
            {"name": "NoStupidQuestions", "description": "Ask anything without judgment"}
        ],
        "General Tech": [
            {"name": "techsupport", "description": "Get help with tech support issues"},
            {"name": "Entrepreneur", "description": "Startup and entrepreneur discussions"},
            {"name": "startups", "description": "Community for startup founders"},
            {"name": "IoT", "description": "Internet of Things projects and ideas"},
            {"name": "cscareerquestions", "description": "Career advice for computer science students"},
            {"name": "LifeProTips", "description": "Tips to improve everyday life"},
            {"name": "antiwork", "description": "Discussions about work, labor and alternatives"}
        ],
        "Misc": [
            {"name": "india", "description": "Discussions about India"},
            {"name": "indiaspeaks", "description": "Indian current affairs and culture"},
            {"name": "unitedstatesofindia", "description": "Humor and memes about Indian politics"},
            {"name": "indianteenagers", "description": "Teenagers in India sharing experiences"}
        ]
    }
}

# ---------------------------
# GitHub Issues Fetcher
# ---------------------------
def fetch_github_issues(repos, state="open", per_repo=10):
    issues = []
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    
    for repo in repos:
        url = f"https://api.github.com/repos/{repo}/issues"
        params = {"state": state, "per_page": per_repo}
        
        try:
            resp = requests.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            for issue in data:
                if "pull_request" in issue:  # skip PRs
                    continue
                
                text = f"{issue['title']}\n{issue.get('body', '')}".strip()
                
                if len(text.split()) <= 10:  # avoid junk
                    continue
                
                if is_problem_post(text):   # ✅ semantic filter
                    issues.append(text)
        
        except Exception as e:
            print(f"⚠️ Failed to fetch from {repo}: {e}")
    
    return issues

# ---------------------------
# Random GitHub repo selection
# ---------------------------
github_repos_by_domain = {
    "Developer Tools": [
        "getfider/fider",
        "atom/atom",
        "instill-ai/community",
        "isaacs/github"
    ],
    "Frontend/Web": [
        "facebook/react",
        "angular/angular"
    ],
    "Finance/Crypto": [
        "MetaMask/metamask-extension",
        "ledgerhq/ledger-live-desktop"
    ],
    "Communication/Productivity": [
        "signalapp/Signal-Android",
        "obsidianmd/obsidian-releases"
    ]
}

def get_random_github_repos(min_per_group=1, max_per_group=2):
    """
    Returns a shuffled list of GitHub repos, picking a random number per category.
    Ensures diversity across categories.
    """
    selected = []

    # Shuffle groups to randomize order
    groups = list(github_repos_by_domain.keys())
    random.shuffle(groups)

    for group in groups:
        repos = github_repos_by_domain[group]
        count = random.randint(min_per_group, min(max_per_group, len(repos)))
        selected += random.sample(repos, count)

    # Shuffle final list so order isn't predictable
    random.shuffle(selected)
    return selected

# ---------------------------
# Reddit Scraper
# ---------------------------
def scrape_reddit(subreddit_list):
    problems = []
    for name in subreddit_list:
        try:
            for submission in reddit.subreddit(name).hot(limit=15):
                if submission.stickied:
                    continue
                text = (submission.title + " " + submission.selftext).strip()
                if len(text.split()) <= 8:
                    continue
                if is_problem_post(text):   # ✅ semantic filter instead of keywords
                    problems.append(text)
        except Exception as e:
            print(f"⚠️ Skipping subreddit {name}: {e}")
    return problems


domain_subreddits = {
    "AI/ML": ["MachineLearning", "datascience", "deeplearning"],
    "Rant": ["rant", "offmychest", "findapath", "TrueAskReddit", "NoStupidQuestions"],
    "Blockchain": ["ethereum", "CryptoTechnology", "Solana", "web3", "NFT"],
    "HealthTech": ["SocialSkills", "DigitalHealth", "medtech", "Bioinformatics", "Healthcare", "mentalhealth" ],
    "WebDev": ["webdev", "learnprogramming", "linuxquestions", "buildapc", "applehelp", "Productivity"],
    "General Tech": ["techsupport", "Entrepreneur", "startups", "IoT", "cscareerquestions", "LifeProTips", "TrueAskReddit", "antiwork"],
    "Mis.": ["india", "indiaspeaks", "unitedstatesofindia", "indianteenagers"]
}

def get_random_subreddits_per_domain(min_per_domain=1, max_per_domain=2):
    """
    Returns a shuffled list of subreddits, picking 1–2 subreddits per domain.
    Ensures all domains are represented.
    """
    selected = []

    # Shuffle domains for randomness
    domains = list(domain_subreddits.keys())
    random.shuffle(domains)

    for domain in domains:
        subs = domain_subreddits[domain]
        count = random.randint(min_per_domain, min(max_per_domain, len(subs)))
        selected += random.sample(subs, count)

    # Shuffle the final list to mix domains
    random.shuffle(selected)
    return selected


# ---------------------------
# Combined Fetch Route
# ---------------------------
# ---------------------------
# Combined Fetch Route (Rewritten)
# ---------------------------
@app.get("/fetch_combined")
def fetch_combined_route():
    """Fetch 4 GitHub + 2 Reddit problems, reframe with description, round-robin merge, save to DB."""
    
    github_repos = get_random_github_repos(min_per_group=1, max_per_group=2)


    # ---------------------------
    # Fetch GitHub issues
    # ---------------------------
    raw_github = fetch_github_issues(github_repos, per_repo=10)[:15]

    github_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are an assistant that reframes GitHub issues into **relatable hackathon problems**.

Rules:
- Keep only issues that represent struggles everyday people or developers face.
- Ignore typos, dependency bumps, or internal housekeeping.
- Generalize the problem so it is relatable and hackathon-friendly.

For each valid issue, output:
- title: catchy 3–5 word title
- reframed: a hackathon styly problem statment
- small_description: 1–2 sentence brief explanation
- description: detailed 2–3 sentence explanation + suggested solution idea
- domain: [AI/ML, FinTech, Blockchain, HealthTech, WebDev, General Tech, RAG ]
- difficulty: Easy / Medium / Hard
- text: optional, raw GitHub issue text

Return JSON: {"problems": [ ... ]}
"""
            },
            {"role": "user", "content": f"GitHub issues:\n{json.dumps(raw_github)}"}
        ],
        response_format={"type": "json_object"}
    )

    parsed_github = json.loads(github_response.choices[0].message.content)
    github_problems = parsed_github.get("problems", [])[:4]
    for p in github_problems:
        p["source"] = "github"
        

    # ---------------------------
    # Fetch Reddit posts
    # ---------------------------
    subreddits = get_random_subreddits_per_domain(min_per_domain=1, max_per_domain=2)


    raw_reddit = scrape_reddit(subreddits)[:15]


    reddit_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are an assistant that reframes Reddit posts into **relatable hackathon problems**.

Rules:
- Keep only posts describing real-life struggles (finance, jobs, healthcare, tech frustrations).
- Ignore memes, low-effort rants, trivial issues.
- Generalize the post into a broader problem.
- Ensure it is hackathon-tackleable.

For each valid issue, output:
- title: catchy 3–5 word title
- reframed: hackathon-style problem statement
- small_description: 1–2 sentence brief explanation
- description: detailed 2–3 sentence explanation + suggested solution idea
- domain: [AI/ML, FinTech, Blockchain, HealthTech, WebDev, General Tech, RAG]
- difficulty: Easy / Medium / Hard
- novelty: integer from 1 to 10 (how new/innovative the idea is)
- text: optional, raw GitHub issue text


Return JSON: {"problems": [ ... ]}
"""
            },
            {"role": "user", "content": f"Reddit posts:\n{json.dumps(raw_reddit)}"}
        ],
        response_format={"type": "json_object"}
    )

    parsed_reddit = json.loads(reddit_response.choices[0].message.content)
    reddit_problems = parsed_reddit.get("problems", [])[:2]
    for p in reddit_problems:
        p["source"] = "reddit"

    # ---------------------------
    # Round-robin merge
    # ---------------------------
    final_problems = []
    g_idx, r_idx = 0, 0
    while g_idx < len(github_problems) or r_idx < len(reddit_problems):
        if g_idx < len(github_problems):
            final_problems.append(github_problems[g_idx])
            g_idx += 1
        if r_idx < len(reddit_problems):
            final_problems.append(reddit_problems[r_idx])
            r_idx += 1
        if len(final_problems) >= 6:
            break

    # ---------------------------
    # Save to DB
    # ---------------------------
    cursor = get_cursor()
    for p in final_problems:
        try:
            cursor.execute(
                        """
                        INSERT INTO problems
                        (title, text, reframed, small_description, description, domain, difficulty, source, novelty)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            p.get("title", ""),
                            p.get("text", ""),
                            p.get("reframed", ""),
                            p.get("small_description", ""),
                            p.get("description", ""),
                            p.get("domain", ""),
                            p.get("difficulty", ""),
                            p.get("source", ""),
                            p.get("novelty", 0)
                        )
                    )


        except Exception as e:
            print(f"⚠️ DB insert failed: {e}")
    db.commit()

    return {"problems": final_problems}


# ---------------------------
# List All Problems
# ---------------------------
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

