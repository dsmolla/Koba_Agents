# Performance Improvement Recommendations for Koba_Agents

This document outlines several areas where the performance of the Koba_Agents application can be significantly improved, focusing on reducing latency, optimizing database/API calls, and increasing concurrency.

## 1. Concurrency & Parallelism

### 1.1. Parallel Auto-Reply Processing
In `backend/services/auto_reply.py`, the `process_notification` function currently iterates through `new_message_ids` and processes each email sequentially.
- **Problem**: Processing 10 emails one by one takes 10x the time of one email.
- **Solution**: Use `asyncio.gather` with an `asyncio.Semaphore(5)` to process multiple emails in parallel.

### 1.2. Parallel Watch Renewal
In `backend/services/gmail_watch.py`, `renew_all_watches` processes all users sequentially.
- **Problem**: As the user base grows, this job will take longer and longer, potentially missing renewal deadlines.
- **Solution**: Use `asyncio.gather` to renew multiple user watches concurrently.

## 2. Database Optimization

### 2.1. Bulk Duplicate Detection
In `process_notification`, there is a check for `already_processed` inside the loop for each `message_id`.
- **Problem**: N queries for N messages.
- **Solution**: Before the loop, fetch all `message_id`s from `auto_reply_log` for that `user_id` that match the `new_message_ids` list in a single query:
  ```sql
  SELECT message_id FROM public.auto_reply_log WHERE user_id = %s AND message_id = ANY(%s)
  ```

### 2.2. Connection Pool Size
In `backend/core/db.py`, the `AsyncConnectionPool` is configured with `max_size=10`.
- **Problem**: 10 connections can quickly be exhausted by concurrent WebSocket connections and background tasks.
- **Solution**: Increase `max_size` to 20 or 50, and ensure `min_size` is tuned to the baseline load.

### 2.3. Database Indexes
Ensure the following indexes exist for optimal query performance:
- `user_integrations (user_id, provider)` (Exists via primary key/unique constraint)
- `auto_reply_log (user_id, message_id)`
- `gmail_watch_state (is_active)`
- `auto_reply_rules (user_id, is_enabled)`

## 3. API & External Service Optimization

### 3.1. Async Google API Calls
The application uses `run_in_executor` to call the synchronous `google-api-python-client`.
- **Problem**: Threading overhead and potential pool exhaustion.
- **Solution**: Consider using an asynchronous-first Google API client library, or at least optimize the use of `run_in_executor` by using a dedicated thread pool for I/O tasks.

### 3.2. Caching Tokens & Timezones
`get_google_service` and `get_user_timezone` are called frequently.
- **Problem**: Redundant Redis/DB lookups within the same request context.
- **Solution**: Use a simple in-memory cache (like `functools.lru_cache` or a request-scoped cache) to store these values for the duration of a single message processing or notification task.

### 3.3. Token Refresh Sync
Ensure that if a token is refreshed during an API call, it is immediately updated in both Redis and the Database to prevent subsequent calls from triggering the same refresh process.

## 4. Agent & LLM Optimization

### 4.1. In-Memory System Prompts
Agents like `GmailAutoReplyAgent` read their system prompts from disk on every initialization.
- **Problem**: Repeated disk I/O.
- **Solution**: Load the `.txt` files once and store them in a module-level variable or a singleton cache.

### 4.2. Chat History Management
`send_chat_history` fetches and sends the entire history.
- **Problem**: Long conversations will result in large payloads and slow initial load times.
- **Solution**: Implement pagination or only send the last N messages by default, fetching older ones on demand.

## 5. Code-Level Optimizations

### 5.1. `should_skip_email` Optimization
This function performs metadata checks sequentially.
- **Problem**: Multiple round-trips to Google APIs for every email.
- **Solution**: Combine metadata fetches if possible, or parallelize the independent checks within the function.

### 5.2. Rule Priority Processing
In `process_notification`, all rules are fetched and then formatted into a prompt.
- **Problem**: If a user has 50 rules, the prompt becomes very large.
- **Solution**: Consider if some basic filtering can be done before passing rules to the LLM, or optimize the rule representation to save tokens.
