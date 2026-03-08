README.md Template
Markdown
全体的に必要な情報が網羅されていて、非常に分かりやすいREADMEになっています！ハッカソンの審査員も、この手順通りに進めれば動かせるはずです。

ただ、情報の重複（Prerequisitesが2回出てくるなど）を整理し、Markdownのコードブロック（黒い背景の枠）を正しく閉じることで、よりプロフェッショナルな見た目になります。

最終版として、きれいに整えたものを以下にまとめました。これをコピーして使ってください！

🌍 TripWeave: AI-Powered Personalized Travel Planner
TripWeave simplifies travel planning by instantly weaving together your unique preferences into a seamless journey. No more juggling a dozen tabs—just tell us where you're headed and what you love, and let our AI do the rest.

✨ Key Features
Intelligent Personalization: Leverages user profiles stored in SurrealDB to tailor every recommendation.

Dynamic Itinerary Generation: Uses LangGraph to manage complex, multi-step planning workflows.

Context-Aware Suggestions: Adapts to constraints like budget, walking preferences, and specific interests.

🛠 Tech Stack
AI/LLM: Google Gemini 1.5 Flash (via LangChain/LangGraph)

Backend: Python, FastAPI

Database: SurrealDB (Multi-model database for flexible travel data)

Frontend: Node.js

🚀 Getting Started
1. Prerequisites
Node.js (for Frontend)

Python 3.10+ (for AI Backend)

SurrealDB (Installed and running on your machine)

2. Environment Setup
Create a .env file in the python-ai directory and add your credentials:

GOOGLE_API_KEY=AIzaSyCdAZ9p8aG8YKrH-DrpWce67VEukZ2-hj8
SURREAL_DB_URL=ws://127.0.0.1:8001/rpc
SURREAL_USER=root
SURREAL_PASS=root
SURREAL_NS=tripweave_ns
SURREAL_DB=trip
3. Execution Steps
To run TripWeave, you need to start three separate processes in different terminal tabs:

Tab 1: Database (SurrealDB)
Bash
surreal start --bind 127.0.0.1:8001 --user root --pass root rocksdb:tripweave.db
Tab 2: AI Backend (Python)
Bash
cd python-ai
# Setup virtual environment (Optional but recommended)
python3 -m venv tripweave_env
source tripweave_env/bin/activate

# Install dependencies and start
pip install -r requirements.txt
python3 main.py
Tab 3: Frontend (Node.js)
Bash
# From the project root
node app.js
4. Database Initialization (Important!) ⚠️
Since the AI requires a user profile to generate personalized plans, please initialize the required data. Run the following command:

Bash
surreal sql --endpoint http://127.0.0.1:8001 --user root --pass root --ns tripweave_ns --db trip
Then, execute this SQL query in the shell:

SQL
-- Create a default traveler profile
CREATE traveller:idiots SET
    name = "The Weekend Group",
    preferences = {
        interests: ["Budget-friendly dining", "Historical landmarks", "Local markets"],
        walking_preference: "prefers public transport over walking"
    };

-- Initialize an active trip
CREATE trip SET
    traveller_id = traveller:idiots,
    destination = "London",
    status = "active",
    updated_at = time::now();
🏗 System Architecture
TripWeave uses a Graph-based workflow (LangGraph) to ensure that the AI doesn't just "chat," but actually executes logic:

Extraction: Identifies user intent and destination.

Context Retrieval: Fetches history and preferences from SurrealDB.

Plan Weaving: Generates and formats the final itinerary.

👥 Contributors
Injoo Moon/Backend & AI Workflow Lead
Jigar Polra/Software Engineer
Harena Toyokawa/Frontend Developer | UI/UX Design