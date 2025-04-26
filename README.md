# LLM Translator

A multilingual translation application powered by advanced LLM technology via OpenRouter API.

## Features

- Translate text between multiple languages
- User-friendly interface built with Streamlit
- Backend API powered by FastAPI
- Container-based deployment with Docker and Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose installed on your system
- An OpenRouter API key

### Setup

1. Clone this repository
2. Add your OpenRouter API key to the `.env` file:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   SITE_URL=your_site_url_here
   SITE_NAME=LLM Translator
   ```
3. Build and start the containers:
   ```
   docker-compose up -d
   ```
4. Access the translator at http://localhost:8501

## Architecture

- **Frontend**: Streamlit application that provides the user interface
- **Backend**: FastAPI service that handles translation requests via OpenRouter API

## Development

To run the application locally for development:

1. Install Python 3.9+ and pip
2. Install backend requirements: `pip install -r backend/requirements.txt`
3. Install frontend requirements: `pip install -r frontend/requirements.txt`
4. Run the backend: `cd backend && uvicorn app:app --reload`
5. Run the frontend: `cd frontend && streamlit run app.py`

## License

See the LICENSE file for details.