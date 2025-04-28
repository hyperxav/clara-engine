# Clara Engine

Clara Engine is a multi-tenant AI bot platform that enables the deployment of personalized GPT-powered Twitter bots for multiple clients from a single, centralized codebase.

## Features

- Multi-client support for managing multiple Twitter bots
- Per-client prompt customization
- Dynamic posting schedule
- Full data logging
- Centralized deployment
- Optional knowledge base integration

## Requirements

- Python 3.10+
- Docker (for deployment)
- OpenAI API Key
- Twitter Developer Account
- Supabase Account
- Render Account (for deployment)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/clara-engine.git
cd clara-engine
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Development Setup

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

## Project Structure

```
clara_engine/
├── clara_engine/          # Main package directory
│   ├── __init__.py
│   ├── core/             # Core functionality
│   ├── clients/          # Client management
│   ├── twitter/          # Twitter integration
│   ├── openai/           # OpenAI integration
│   └── utils/            # Utility functions
├── tests/                # Test directory
├── config/               # Configuration files
├── docs/                 # Documentation
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
└── README.md            # This file
```

## Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and update the values:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo

# Twitter API Configuration
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## Running Tests

```bash
pytest
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 