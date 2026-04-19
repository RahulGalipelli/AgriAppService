python -m venv venv
venv\Scripts\activate
python -m pip install dotenv fastapi uvicorn pydantic python-multipart openai pillow twilio
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
python -m pip install -r requirements.txt

# Database (PostgreSQL)
# Default local URL: postgresql+asyncpg://postgres:postgres@localhost:5432/agricure
# 1. Install PostgreSQL and ensure it is running.
# 2. Create the database:  createdb agricure   (or set POSTGRES_DB in .env)
# 3. Override in .env if needed: DATABASE_URL or POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
# Tables are auto-created on startup when ENV=local or DEBUG=true.
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head