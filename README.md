# Press Release Distribution Agent

An intelligent agent for generating and distributing press releases, built with LangGraph and Streamlit.

## Features

- Press release generation in Italian using Groq
- Smart web search for Italian media contacts using multiple sources:
  - News API with Italian language filter
  - Google search with Italian-specific queries
  - Italian media directories (ODG and FNSI)
- Personalized email distribution
- Social media posting
- Cloud storage for all generated content
- Human-in-the-loop approval process
- Italian user interface

## Requirements

- Python 3.8+
- Groq API key
- News API key (optional, for enhanced media contact search)
- AWS credentials for S3 (optional, for cloud storage)
- SMTP credentials for email sending (optional)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/agent-m.git
cd agent-m
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Then edit the `.env` file with your API keys and configuration values.

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your browser at the provided URL (typically http://localhost:8501)

3. Follow the workflow:
   - Enter your press release topic
   - Review and approve the generated press release
   - Check recipients and email content
   - Approva e Invia Email
   - Verify social media posting status

## Project Structure

```
agent-m/
├── app.py              # Main Streamlit application
├── utils.py            # Utility functions
├── cloud_storage.py    # Cloud storage management
├── requirements.txt    # Project dependencies
├── .env.example       # Example environment variables
├── .env               # Your environment variables (to be created)
└── tests/             # Test files
    ├── __init__.py
    ├── test_app.py    # Tests for main application
    └── test_utils.py  # Tests for utility functions
```

## Notes

- The application requires explicit user approval for each process step
- Press releases are generated in Italian and optimized for the Italian market
- Recipient search uses a multi-source approach to find Italian media contacts:
  1. News API with Italian language filter
  2. Google search with Italian-specific queries
  3. Italian media directories (ODG and FNSI)
- Cloud storage is optional and requires valid AWS credentials
- Email sending is optional and requires valid SMTP credentials

## License

MIT 