FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download required NLTK data during build
RUN python -m nltk.downloader -d /usr/local/nltk_data punkt_tab

# Copy project files
COPY . .

# Expose the port Django will run on
EXPOSE 8000

# Set environment variables (optional, can also be set in docker-compose.yml)
# ENV DB_URL=postgres://fastapiuser:password@db:5432/fastapidb
# ENV DB_USER=fastapiuser
# ENV DB_PASSWORD=password
# ENV DB_HOST=db
# ENV DB_PORT=5432
# ENV DB_NAME=fastapidb
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]

# Run the Django development server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]