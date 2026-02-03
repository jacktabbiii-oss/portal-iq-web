# Portal IQ Dashboard - Streamlit
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy dashboard code
COPY dashboard/ ./dashboard/

# Copy data files
COPY ml-engine/data/processed/on3_all_nil_rankings.csv ./ml-engine/data/processed/
COPY ml-engine/data/processed/on3_transfer_portal.csv ./ml-engine/data/processed/
COPY ml-engine/data/processed/on3_team_portal_rankings.csv ./ml-engine/data/processed/

# Copy and setup start script
COPY start.sh .
RUN chmod +x start.sh

# Railway sets PORT env var - default to 8501
ENV PORT=8501

# Expose port
EXPOSE 8501

# Run via start script
CMD ["./start.sh"]
