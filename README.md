# Mini PostgreSQL Agent

A lightweight AI agent that helps you interact with PostgreSQL databases using natural language. Built with OpenAI's GPT-4 and Python.

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="your_database_name"
export DB_USER="your_database_user"
export DB_PASSWORD="your_database_password"
```

3. Run the agent:
```bash
python db_agent.py
```

## Usage

The agent understands natural language. Try these examples:

```
You: What tables are in the database?
Agent: [Lists all tables]

You: Show me the structure of the orders table
Agent: [Shows table columns and types]

You: How many orders in the table
Agent: [Executes query and shows results]
```

### Commands
- Type your questions in natural language
- `clear` - Clear conversation history
- `exit` or `quit` - End the session

## Project Structure
```
mini-postgres-agent/
├── README.md
├── requirements.txt
├── .gitignore
├── config.py          # Environment configuration
└── db_agent.py        # Main agent implementation
```

## Requirements
- Python 3.9+
- PostgreSQL database
- OpenAI API key

## License
MIT License 