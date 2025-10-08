# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a hierarchical multi-agent system for Google Workspace automation built using LangChain and LangGraph. It uses a ReAct (Reasoning + Acting) architecture where agents delegate tasks to specialized sub-agents.

## Architecture

### Hierarchical Agent Structure

The system follows a 3-tier agent hierarchy:

1. **GoogleAgent** (Top-level supervisor)
   - Coordinates across all Google Workspace services
   - Delegates to: GmailAgent, DriveAgent, CalendarAgent, TasksAgent

2. **Service-level agents** (Gmail, Drive, Calendar, Tasks)
   - Handle complex multi-step operations within their domain
   - Further delegate to specialized sub-agents (e.g., GmailAgent → OrganizationAgent, SearchAndRetrievalAgent, etc.)

3. **Specialized agents** (Organization, Search, Writer, etc.)
   - Execute specific operations using tools
   - Directly interact with Google APIs via service clients

### Key Design Patterns

**ReAct under ReAct**: Agents use LangGraph's `create_react_agent` to build a graph where each node can invoke another ReAct agent. This allows hierarchical task delegation with reasoning at each level.

**Base Agent Pattern**: All agents inherit from `BaseAgent` (in `shared/base_agent.py`) which:
- Manages LLM, config, and tools
- Creates the ReAct agent graph via `_create_agent()`
- Executes via `shared/agent_executor.py`
- Requires subclasses to implement `_get_tools()` and `system_prompt()`

**Agent-as-Tool**: Service agents are wrapped as LangChain tools (see `google-agent/tools.py`, `google-agent/gmail/tools.py`, etc.) allowing them to be invoked by parent agents.

**Caching**:
- `EmailCache` in `google-agent/gmail/shared/email_cache.py` caches fetched emails to avoid redundant API calls
- `TaskListCache` in `google-agent/tasks/task_list_cache.py` caches task list metadata

### Agent Communication

Agents communicate through structured prompts in their `system_prompt()` methods:
- Parent agents break down user requests and delegate to child agents
- Child agents return results which parents synthesize
- Message IDs, thread IDs, event IDs, task IDs, and file IDs are passed between agents
- Full file paths are included when downloading attachments or saving files

## LLM Configuration

LLM tiers defined in `shared/llm_models.py`:
- `LLM_PRO`: Gemini 2.5 Pro (most capable, used for complex operations like Drive writing)
- `LLM_FLASH`: Gemini 2.5 Flash (default for most agents)
- `LLM_LITE`: Gemini 2.5 Flash Lite (fast, used for simple operations like email writing)

All models use an in-memory rate limiter (10 requests per minute).

## Testing and Development

**Running the test agent**:
```bash
python test.py
```

This initializes a `GoogleAgent` with user credentials and runs an interactive loop where you can test queries.

**Environment Setup**:
- Requires `.env` file with `TOKEN_PATH` and `CREDS_PATH` for Google API authentication
- The `google_client` package (external dependency) handles OAuth and service initialization

**Git Status Notes**:
The recent git activity shows a major refactoring moving from `agents/` to `google-agent/` directory structure. When working with imports, use the new `google-agent/` paths.

## Important Implementation Details

1. **Always wait for tool outputs**: Agents must check outputs before making subsequent tool calls. This is enforced in system prompts.

2. **Include IDs in responses**: Agents should return message_ids, thread_ids, event_ids, task_ids, and file_ids to enable follow-up actions.

3. **Full file paths**: When downloading attachments or saving files, always provide complete file paths.

4. **Cross-domain intelligence**: The GoogleAgent system prompt emphasizes recognizing when requests span multiple services (e.g., creating calendar events from emails, creating tasks from meetings).

5. **Current datetime injection**: System prompts include `datetime.now()` to provide temporal context for relative date queries.

6. **Sequential tool execution**: The `agent_executor.execute()` streams agent responses and prints intermediate steps when `print_steps=True`.
