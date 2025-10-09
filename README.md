# Google Agent

A powerful AI-powered agent system for managing Google Workspace services including Gmail, Google Calendar, Google Tasks, and Google Drive.

## Overview

Google Agent is a hierarchical multi-agent system that acts as a supervisor coordinating specialized agents for different Google Workspace services. It can understand natural language requests and automatically delegate tasks to the appropriate specialized agents, making it easy to perform complex cross-domain operations.

### Key Features

- **Multi-Agent Architecture**: Hierarchical system with a supervisor agent coordinating specialized sub-agents
- **Gmail Management**: Search, organize, summarize, and compose emails
- **Calendar Operations**: Schedule events, check availability, manage meetings
- **Task Management**: Create, update, and organize Google Tasks
- **Drive Operations**: Search, organize, and manage files and folders
- **Cross-Domain Intelligence**: Automatically coordinates between services (e.g., creating tasks from emails, scheduling based on email content)
- **Natural Language Interface**: Conversational interface powered by Google's Gemini models

## Architecture

The project follows a hierarchical agent structure:

```
GoogleAgent (Supervisor)
├── GmailAgent
│   ├── SearchAndRetrievalAgent
│   ├── SummaryAndAnalyticsAgent
│   ├── OrganizationAgent
│   └── WriterAgent
├── CalendarAgent
├── TasksAgent
└── DriveAgent
    ├── SearchAndRetrievalAgent
    ├── OrganizationAgent
    └── WriterAgent
```

### Agent Responsibilities

**GoogleAgent (Supervisor)**
- Routes requests to appropriate service agents
- Coordinates cross-domain operations
- Synthesizes responses from multiple agents

**GmailAgent**
- Delegates email-related tasks to specialized sub-agents
- Coordinates email search, organization, analytics, and composition

**CalendarAgent**
- Manages calendar events and scheduling
- Checks availability and meeting conflicts

**TasksAgent**
- Handles Google Tasks operations
- Creates, updates, and organizes tasks

**DriveAgent**
- Manages Google Drive files and folders
- Handles file search, organization, and sharing

## Installation

### Prerequisites

- Python 3.8 or higher
- A Google Cloud Project with the following APIs enabled:
  - Gmail API
  - Google Calendar API
  - Google Tasks API
  - Google Drive API
- OAuth 2.0 credentials for the project

### Setup

1. Clone the repository:
```bash
git clone https://github.com/dsmolla/google-agent.git
cd google-agent
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:

Create a `.env` file in the project root:
```env
TOKEN_PATH=path/to/your/token.json
CREDS_PATH=path/to/your/credentials.json
GOOGLE_API_KEY=your_google_api_key for Gemini
```

5. Obtain Google OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail, Calendar, Tasks, and Drive APIs
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials JSON file and save it as specified in `CREDS_PATH`

## Usage

### Basic Usage

Run the interactive agent:

```bash
python test.py
```

This starts an interactive session where you can type natural language commands.

### Example Commands

**Gmail Operations**
```
Human: Find all emails from Sarah about the project deadline
Human: Summarize my emails from last week
Human: Delete all my user-created labels
Human: Organize my inbox from today into personal, work, and shopping categories
```

**Calendar Operations**
```
Human: What meetings do I have tomorrow?
Human: Schedule a team standup every Monday at 9am
Human: Check my availability this Friday afternoon
```

**Tasks Operations**
```
Human: Show me all my overdue tasks
Human: Create a task to review the Q4 budget by Friday
Human: List all high-priority tasks due this week
```

**Drive Operations**
```
Human: Find all my presentation files from last month
Human: Create a folder called "Project Alpha" and share it with the team
Human: Organize all my documents from this year into folders by month
```

**Cross-Domain Operations**
```
Human: Find emails from Sarah about the client presentation and add a task to prepare slides
Human: What's on my schedule today and what tasks are due?
Human: Block 1 hour on my calendar for each high priority task this week
Human: Save all email attachments from this week's project emails to a Drive folder
```

### Command Line Options

```bash
# Enable debug mode to see agent steps
python test.py --print_steps True
```

### Programmatic Usage

```python
from dotenv import load_dotenv
from google_agent.agent import GoogleAgent
from google_client.user_client import UserClient
from langchain_core.messages import HumanMessage
from google_agent.shared.llm_models import LLM_FLASH
import os

load_dotenv()

# Initialize the Google service client
token_path = os.getenv("TOKEN_PATH")
creds_path = os.getenv("CREDS_PATH")
google_service = UserClient.from_file(token_path, creds_path)

# Create the agent
agent = GoogleAgent(google_service, LLM_FLASH, print_steps=False)

# Execute a task
messages = [HumanMessage("Find all emails from last week about the project")]
response = agent.execute(messages)

print(response.messages[-1].content)
```

## Project Structure

```
google-agent/
├── google_agent/
│   ├── agent.py              # Main GoogleAgent supervisor
│   ├── tools.py              # Tool definitions for service agents
│   ├── gmail/                # Gmail agent and sub-agents
│   │   ├── agent.py
│   │   ├── tools.py
│   │   ├── search_and_retrieval/
│   │   ├── summary_and_analytics/
│   │   ├── organization/
│   │   ├── writer/
│   │   └── shared/
│   ├── calendar/             # Calendar agent
│   │   ├── agent.py
│   │   └── tools.py
│   ├── tasks/                # Tasks agent
│   │   ├── agent.py
│   │   └── tools.py
│   ├── drive/                # Drive agent and sub-agents
│   │   ├── agent.py
│   │   ├── tools.py
│   │   ├── search_and_retrieval/
│   │   ├── organization/
│   │   ├── writer/
│   │   └── shared/
│   └── shared/               # Shared utilities
│       ├── base_agent.py
│       ├── llm_models.py
│       ├── response.py
│       └── exceptions.py
├── test.py                   # Interactive CLI interface
├── requirements.txt          # Project dependencies
└── .env                      # Environment variables (not tracked)
```

## Dependencies

- **python-dotenv**
- **google-api-client-wrapper**
- **langgraph**
- **langchain-core**
- **langchain-google-genai**
- **langchain**
- **textwrap3**
- **Pydantic**

## How It Works

1. **User Input**: You provide a natural language request through the CLI or API
2. **Supervisor Analysis**: The GoogleAgent analyzes the request and creates a plan
3. **Task Delegation**: The supervisor delegates to appropriate specialized agents:
   - Gmail operations → GmailAgent
   - Calendar operations → CalendarAgent
   - Task operations → TasksAgent
   - Drive operations → DriveAgent
4. **Sub-Agent Processing**: Each specialized agent may further delegate to their own sub-agents
5. **Response Synthesis**: The supervisor collects all responses and provides a comprehensive answer

### Agent Communication

Agents communicate through structured tool calls and responses. The supervisor maintains conversation context and ensures proper sequencing of operations, especially for cross-domain tasks that require coordination between multiple services.

### LLM Models

The project uses Google's Gemini models:
- **LLM_FLASH**: Primary model for most agents (faster, cost-effective)
- **LLM_LITE**: Used for simpler tasks like email composition

Models are configured in `google_agent/shared/llm_models.py`.

## Features in Detail

### Gmail Agent Capabilities

- **Search & Retrieval**: Find emails by sender, subject, date, labels, etc.
- **Summary & Analytics**: Summarize email threads, extract action items, classify emails
- **Organization**: Create/delete labels, move emails, archive, mark as read/unread
- **Writer**: Compose and send emails with attachments

### Calendar Agent Capabilities

- Create single and recurring events
- Check availability and schedule conflicts
- List events by date range
- Update and delete events

### Tasks Agent Capabilities

- Create tasks with due dates and priorities
- List tasks by status, priority, or due date
- Update task details
- Mark tasks as complete

### Drive Agent Capabilities

- **Search & Retrieval**: Find files and folders by name, type, date
- **Organization**: Create folders, move files, organize hierarchies
- **Writer**: Upload files, update file metadata, manage sharing permissions

### Cross-Domain Intelligence

The supervisor agent can automatically:
- Create tasks from email action items
- Schedule calendar events based on email content
- Save email attachments to Drive
- Check calendar availability when scheduling from emails
- Link related items across services

## Configuration

### Environment Variables

- `TOKEN_PATH`: Path to Google OAuth token file
- `CREDS_PATH`: Path to Google OAuth credentials file
- `GOOGLE_API_KEY`: Google API key for Generative AI

### Debug Mode

Enable verbose logging to see agent decision-making:
```bash
python test.py --print_steps True
```

Or in code:
```python
agent = GoogleAgent(google_service, LLM_FLASH, print_steps=True)
```

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:
1. Ensure your `credentials.json` file is valid
2. Delete the `token.json` file and re-authenticate
3. Verify all required APIs are enabled in Google Cloud Console

### API Quota Limits

Google APIs have usage quotas. If you hit limits:
- Check your quota usage in Google Cloud Console
- Request quota increases if needed
- Implement rate limiting in your application

### Agent Errors

If agents fail to execute tasks:
- Enable debug mode (`print_steps=True`) to see detailed execution
- Enable langchain's detailed debug mode (`from langhain.globals import set_debug; set_debug(True)`)
- Check that the LLM models are properly configured
- Verify your Google API key is valid

