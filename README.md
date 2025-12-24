python -m venv venv
venv\Scripts\activate
python -m pip install dotenv fastapi uvicorn pydantic python-multipart openai pillow twilio
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
python -m pip install -r requirements.txt
