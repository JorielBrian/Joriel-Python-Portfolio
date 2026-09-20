# Joriel Portfolio API

FastAPI backend for the portfolio, backed by Neon (Postgres). Serves projects,
qualifications, skills, and bio text ("content blocks") that used to be
hardcoded in `app/data/*.ts` in the Next.js repo.

## 1. Create the Neon database

1. Go to https://neon.tech, sign in, create a new project (any region close to
   where your Vercel/backend deploy will run).
2. In the project dashboard, copy the **pooled connection string** (Neon shows
   both a direct and a pooled one — use the pooled one for a deployed app so
   you don't run out of connections).
3. It looks like: `postgresql://user:password@ep-xxxx-pooler.region.aws.neon.tech/neondb?sslmode=require`

## 2. Local setup

```bash
cd portfolio-backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: paste your real DATABASE_URL, set ADMIN_API_KEY to something random
```

## 3. Create tables and load your real data

The `scripts/seed_data.json` file was exported directly from your existing
`app/data/*.ts` files, so it's an exact copy of what's live right now — 7
projects, 14 qualifications, 56 skills, and your bio text.

```bash
set -a; source .env; set +a     # loads DATABASE_URL etc. into the shell
python -m scripts.seed
```

Re-running it is safe — it skips any table that already has rows, so it
won't duplicate data.

## 4. Run the API locally

```bash
set -a; source .env; set +a
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for interactive Swagger docs — you can try
every endpoint from the browser.

Quick checks:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/projects
curl http://localhost:8000/content/ABOUT
```

Write endpoints (POST/PUT/DELETE) need the admin header:
```bash
curl -X PUT http://localhost:8000/content/ABOUT \
  -H "X-Admin-Key: $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"paragraphs": ["Updated paragraph one.", "Updated paragraph two."]}'
```

## 5. Deploy the backend

Recommended: **Railway** (simplest for a small FastAPI service) or **Render**.
Either works fine; here's Railway:

1. Push this `portfolio-backend/` folder to its own GitHub repo (keep it
   separate from the Next.js repo — different language, different deploy).
2. In Railway: New Project → Deploy from GitHub repo → pick the repo.
3. Set environment variables in Railway's dashboard: `DATABASE_URL`,
   `CORS_ORIGINS`, `ADMIN_API_KEY` (same values as your local `.env`).
4. Set the start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Once deployed, Railway gives you a URL like
   `https://your-service.up.railway.app`. That's your `NEXT_PUBLIC_API_URL` /
   backend base URL for the Next.js side.
6. Update `CORS_ORIGINS` to include your real Vercel domain (it already does:
   `https://jorielbriansudario.vercel.app`) plus `http://localhost:3000` for
   local dev.

## 6. Wiring this into Next.js (next step)

On the Next.js side, replace the static imports in `app/data/*.ts` with fetch
calls to this API, e.g.:

```ts
// app/lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL!; // e.g. https://your-service.up.railway.app

export async function getProjects() {
  const res = await fetch(`${API_URL}/projects`, { next: { revalidate: 3600 } });
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}
```

Then in a server component:
```ts
const projects = await getProjects();
```

`{ next: { revalidate: 3600 } }` caches the response for an hour and
re-fetches after that — so editing data later through the dashboard shows up
on the live site without a full redeploy. We'll wire this up for real in the
next phase, once the backend is deployed and you've confirmed the data reads
correctly.

## API reference

| Method | Path                    | Auth | Notes |
|--------|--------------------------|------|-------|
| GET    | `/health`                | none | uptime check |
| GET    | `/projects`              | none | list, ordered |
| GET    | `/projects/{id}`         | none | |
| POST   | `/projects`              | X-Admin-Key | |
| PUT    | `/projects/{id}`         | X-Admin-Key | partial update |
| DELETE | `/projects/{id}`         | X-Admin-Key | |
| GET    | `/qualifications`        | none | same pattern as projects |
| GET    | `/skills`                | none | same pattern as projects |
| GET    | `/content`               | none | all bio blocks |
| GET    | `/content/{key}`         | none | e.g. `ABOUT`, `STORY`, `GOALS` |
| PUT    | `/content/{key}`         | X-Admin-Key | replaces paragraph list |

The `X-Admin-Key` header is a stopgap so the write endpoints aren't wide open
on the public internet while there's no dashboard yet. Phase 2 replaces this
with real session-based login for the admin dashboard.
# Joriel-Python-Portfolio
