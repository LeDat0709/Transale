FROM python:3.10-slim

WORKDIR /app

# Copy requirements if we have them, otherwise install directly
# Since the project might not have a requirements.txt, let's install what we know we need
RUN pip install --no-cache-dir fastapi uvicorn sse-starlette pydantic google-api-python-client google-auth-httplib2 google-auth-oauthlib deep-translator

# Copy backend files and root python scripts that are needed
COPY ./web_app/backend /app/backend
COPY ./translate_sheet_range.py /app/
COPY ./token.json /app/

WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
