-- PostgreSQL setup for CampusConnect hosting
-- Run this once on a managed PostgreSQL instance or local PostgreSQL server.

CREATE DATABASE campusconnect;

-- Optional: create an app user
-- CREATE USER campusconnect WITH ENCRYPTED PASSWORD 'CHANGE_ME';
-- GRANT ALL PRIVILEGES ON DATABASE campusconnect TO campusconnect;

-- If you are connecting as the postgres/admin user and creating a schema manually:
-- \c campusconnect;
-- GRANT ALL ON SCHEMA public TO campusconnect;

-- Note:
-- The FastAPI app will automatically create tables when it starts if the database is empty.
-- The app calls init_db() inside backend/main.py, which creates tables from SQLAlchemy models.
