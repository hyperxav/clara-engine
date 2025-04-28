# Installation Guide

This guide will walk you through the process of installing and configuring Clara Engine.

## Prerequisites

Before installing Clara Engine, ensure you have the following:

### System Requirements
- Python 3.10 or higher
- Redis 6.0 or higher
- Docker (optional, for containerized deployment)
- Node.js 18+ (for dashboard)

### Required Accounts
1. **OpenAI Account**
   - API key with access to GPT models
   - Sufficient quota for your usage

2. **Twitter Developer Account**
   - Elevated access level
   - API key and secret
   - Access token and secret

3. **Supabase Account**
   - Project created
   - Database credentials
   - Service role key

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/clara-engine.git
cd clara-engine
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# For development, also install dev dependencies
pip install -r requirements-dev.txt
```

### 4. Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your configuration:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo

# Twitter API Configuration
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### 5. Initialize Database

Run the database migration script:

```bash
python scripts/apply_migrations.py
```

### 6. Install Pre-commit Hooks (Development)

```bash
pre-commit install
```

## Verification

1. Run the test suite:
```bash
pytest
```

2. Test the connection:
```bash
python test_connection.py
```

3. Start the CLI:
```bash
python -m clara_engine.cli status
```

## Docker Installation (Alternative)

1. Build the Docker image:
```bash
docker build -t clara-engine .
```

2. Run with Docker Compose:
```bash
docker-compose up -d
```

## Common Issues

### Database Migration Fails
- Ensure Supabase credentials are correct
- Check if the database exists and is accessible
- Verify you have the necessary permissions

### Twitter API Authentication Fails
- Verify Twitter API credentials
- Ensure you have Elevated access level
- Check if the tokens are still valid

### OpenAI API Issues
- Verify API key is valid
- Check if you have sufficient quota
- Ensure the selected model is available for your account

## Next Steps

After successful installation:

1. Follow the [Quick Start Guide](./quickstart.md) to create your first client
2. Review the [Configuration Guide](./configuration.md) for detailed settings
3. Check the [Architecture Overview](../concepts/architecture.md) to understand the system

## Support

If you encounter any issues during installation:

1. Check the [Troubleshooting Guide](../troubleshooting/common-issues.md)
2. Search existing [GitHub Issues](https://github.com/yourusername/clara-engine/issues)
3. Create a new issue with:
   - Your system information
   - Steps to reproduce
   - Error messages
   - Logs (with sensitive information removed) 