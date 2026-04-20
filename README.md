# Sprout — Backend

FastAPI backend for Sprout, a daily habit tracker for kids and guardians.

## Tech Stack

- **FastAPI** — Python web framework
- **PostgreSQL** — Relational database
- **SQLAlchemy** — ORM
- **Supabase Auth** — Authentication
- **APScheduler** — Midnight task reset scheduler
- **Railway** — Deployment

## Project Structure

    sprout-backend/
    ├── routers/
    │   ├── __init__.py
    │   ├── children.py
    │   ├── daily.py
    │   ├── guardian.py
    │   ├── rewards.py
    │   └── tasks.py
    ├── auth.py
    ├── database.py
    ├── dependencies.py
    ├── main.py
    ├── models.py
    ├── scheduler.py
    ├── requirements.txt
    └── .env

## Local Setup

**1. Clone the repo**

```bash
git clone https://github.com/mkjabed/sprout-backend
cd sprout-backend
```

**2. Create and activate virtual environment**

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate       # Mac/Linux
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Create `.env` file**

DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/sprout_db

SECRET_KEY=your_secret_key

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=10080

**5. Run the server**

```bash
uvicorn main:app --reload
```

**6. Open API docs**

http://127.0.0.1:8000/docs

## API Overview

| Method | Route                  | Description              |
| ------ | ---------------------- | ------------------------ |
| POST   | /auth/signup           | Guardian registration    |
| POST   | /auth/login            | Guardian login           |
| GET    | /guardian/me           | Get current guardian     |
| GET    | /children              | Get all children         |
| POST   | /children              | Create a child           |
| GET    | /tasks/:childId        | Get tasks for child      |
| POST   | /tasks                 | Create a task            |
| PATCH  | /tasks/:id/toggle      | Toggle task active state |
| GET    | /daily/:childId        | Get today's scorecard    |
| POST   | /daily/:logId/complete | Complete a task          |
| GET    | /rewards/:childId      | Get rewards for child    |
| POST   | /rewards               | Create a reward          |
| PATCH  | /rewards/:id/deliver   | Mark reward as delivered |

## Database Schema

8 tables: `guardians`, `children`, `tasks`, `daily_logs`,
`streaks`, `rewards`, `badges`, `parenting_tips`

## Deployment

Deployed on Railway with PostgreSQL plugin.
Auto-deploys on push to `main` branch.

## Environment Variables (Production)

Set these in Railway dashboard:

DATABASE_URL

SECRET_KEY

ALGORITHM

ACCESS_TOKEN_EXPIRE_MINUTES
