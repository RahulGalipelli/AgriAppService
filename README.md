python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn pydantic python-multipart
uvicorn main:app --reload --host 0.0.0.0 --port 8000


pip install fastapi uvicorn openai pillow