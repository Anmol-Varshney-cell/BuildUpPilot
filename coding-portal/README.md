# Coding Portal (React + Node + Judge)

This module adds an interactive coding challenges portal with:
- Session-based auth (email/password)
- Problem catalog with filters/search
- Problem detail with Monaco code editor
- Run on sample tests + Submit on hidden tests
- Verdicts: `ACCEPTED`, `WRONG_ANSWER`, `RUNTIME_ERROR`, `COMPILATION_ERROR`, `TIME_LIMIT_EXCEEDED`
- Submission history and profile stats
- DSA journeys with progress bars
- Admin APIs for CRUD on problems/test cases

## Stack
- Frontend: React + TypeScript + React Query + Monaco
- Backend: Node.js + Express + TypeScript + Prisma
- DB: PostgreSQL
- Judge: separate Node.js microservice that executes user code in Docker sandboxes

## Folder Structure
- `frontend/` React app
- `backend/` API + Prisma schema/seed
- `judge/` isolated execution service
- `docker-compose.yml` orchestration

## Quick Start (Docker)
From `coding-portal/`:

```bash
docker compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:4000/api
- Judge: http://localhost:5001
- Postgres: localhost:5433

Default seeded admin:
- email: `admin@coding.local`
- password: `admin123`

## Local Dev (Without Docker)
### Backend
```bash
cd backend
cp .env.example .env
npm install
npx prisma generate
npx prisma db push
npm run seed
npm run dev
```

### Judge
```bash
cd judge
cp .env.example .env
npm install
npm run dev
```

### Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## API Overview
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/problems`
- `GET /api/problems/:slug`
- `POST /api/submissions/execute` (`mode=run|submit`)
- `GET /api/submissions/me`
- `GET /api/profile/me`
- `GET /api/journeys`
- `POST /api/admin/problems` (admin)
- `PUT /api/admin/problems/:id` (admin)
- `DELETE /api/admin/problems/:id` (admin)
- `POST /api/admin/problems/:id/test-cases` (admin)

## Add a New Problem
Use admin API `POST /api/admin/problems` with body:
- metadata: title, slug, difficulty, tags
- statement sections
- supported languages
- `starterCodes`
- `testCases` array with `{ input, output, isHidden }`

You can also add examples in `backend/prisma/seed.ts` and rerun:

```bash
cd backend
npm run seed
```

## Add a New Language
1. Update enums in `backend/prisma/schema.prisma`.
2. Add starter code mapping in seed/admin payloads.
3. Extend judge request schema + compile/run logic in `judge/src/index.ts`.
4. Add language option in frontend selectors.

## Security Notes
- Judge runs code via Docker containers and enforces timeout.
- Backend does not run untrusted code directly.
- Keep this architecture and run judge in isolated infra for production.
