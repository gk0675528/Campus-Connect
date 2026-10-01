# CampusConnect deployment guide

## 1) Render

1. Push this repository to GitHub.
2. In Render, create a new Web Service and connect this repo.
3. Set the root directory to `backend`.
4. Use the default Python environment or set `PYTHON_VERSION=3.11`.
5. Set startup command: `python main.py`.
6. Add environment variables from `backend/.env`.
7. Add a Postgres and Redis service if needed.
8. Set `CORS_ORIGINS` to your frontend URL.
9. Deploy.

## 2) Railway

1. Import the repo into Railway.
2. Set the root directory to the repository root.
3. Railway will use `railway.json` and the existing `backend/Dockerfile`.
4. Add environment variables from `backend/.env`.
5. Add a PostgreSQL and Redis plugin.
6. Deploy the project.

## 3) Azure App Service

1. Install Azure Developer CLI (`azd`) if needed.
2. Run:
   - `azd auth login`
   - `azd init -t` if starting fresh
3. Use `azure.yaml` in the repository root.
4. Set environment values in the Azure app configuration.
5. Deploy with:
   - `azd up`

## Required environment values

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` (optional)
- `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` (optional)
- `STRIPE_SECRET_KEY` / `STRIPE_PUBLIC_KEY` (optional)
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` (optional)
- `OPENAI_API_KEY` (optional)

## Health check

The service exposes `/health` and should return `200 OK` once database and Redis are reachable.
