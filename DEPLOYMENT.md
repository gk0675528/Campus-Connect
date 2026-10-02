# Pathzeo Hosting Guide

## Recommended architecture

- Cloudflare Pages serves the static site in `frontend/`.
- Render or Railway runs the FastAPI service in `backend/` using Docker.
- Managed PostgreSQL and Redis provide application data and runtime services.

Do not deploy this backend to Cloudflare Workers as-is. It depends on PostgreSQL, Redis, and Python packages that need a separate compatibility assessment for the Workers runtime.

## 1. Deploy the API on Render

1. Push the repository to GitHub.
2. In Render, create a Blueprint and select this repository. Render reads the root `render.yaml`, which configures the API service with `backend/` as its root directory.
3. Create or attach managed PostgreSQL and Redis services. Make sure both are reachable from the API service.
4. Add these API environment variables in Render:

   ```text
   ENVIRONMENT=production
   APP_NAME=Pathzeo
   DEBUG=False
   SECRET_KEY=<long-random-secret>
   DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/<database>
   REDIS_URL=redis://<user>:<password>@<host>:<port>/<database>
   CORS_ORIGINS=https://<your-pages-site>.pages.dev
   ```

   Use the database provider's internal connection URL when available, and ensure the scheme is `postgresql+asyncpg`. Never commit real secrets to Git.
5. Deploy the service and confirm `https://<your-api-host>/health` responds successfully.
6. Run database migrations from the backend service environment with `alembic upgrade head` before using the application.

The existing Render blueprint uses `python main.py` and `/health`. Supply all five required production values (`ENVIRONMENT`, `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, and `CORS_ORIGINS`) before deploying.

## 2. Deploy the frontend to Cloudflare Pages

1. In Cloudflare, create a Pages project connected to the same GitHub repository.
2. Set the root directory to `frontend`.
3. Set the build output directory to `.` and add the Pages environment variable `PATHZEO_API_URL=https://<your-api-host>` for production and preview deployments.
4. Set the build command to `sed -i "s|__PATHZEO_API_URL__|${PATHZEO_API_URL}|g" js/config.js`.
5. Commit and push that configuration, then allow Cloudflare Pages to deploy it.
6. Copy the Pages URL, then set `CORS_ORIGINS` on the API to that exact origin, without a trailing slash, and redeploy the API if needed.

For a custom frontend domain, use that exact HTTPS origin in `CORS_ORIGINS` instead of, or in addition to, the `pages.dev` URL.

## 3. Railway alternative

The repository includes `railway.json` and `backend/Dockerfile`. Import the repository into Railway, add PostgreSQL and Redis services, and provide the same environment variables as above. The Railway configuration builds with `backend/` as the Docker context.

## Required and optional settings

Required:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `ENVIRONMENT=production`
- `DEBUG=False`

Optional integrations:

- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
- `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET`
- `STRIPE_SECRET_KEY` / `STRIPE_PUBLIC_KEY`
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`
- `OPENAI_API_KEY`

## Release checks

- Confirm `/health` returns HTTP 200.
- Confirm the frontend can register, log in, and call `/api/auth/me`.
- Exercise mentor search, bookings, communities, messaging, notifications, and payments.
- Check browser developer tools for CORS errors and failed requests.
- Keep production secrets in the hosting provider's secret manager, not in frontend files or Git.
