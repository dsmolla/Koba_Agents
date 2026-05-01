CREATE TABLE IF NOT EXISTS public.recursive_tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    cron_schedule VARCHAR(50) NOT NULL,
    human_schedule VARCHAR(255) NOT NULL,
    prompt TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'active' NOT NULL,
    timezone VARCHAR(100) DEFAULT 'UTC' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.recursive_task_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES public.recursive_tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    executed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    status VARCHAR(50) NOT NULL,
    output TEXT,
    thread_id VARCHAR(255)
);

-- RLS
ALTER TABLE public.recursive_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recursive_task_logs ENABLE ROW LEVEL SECURITY;

-- Indexes
CREATE INDEX idx_recursive_tasks_user_id ON public.recursive_tasks(user_id);
CREATE INDEX idx_recursive_tasks_execution ON public.recursive_tasks(status, next_run_at) WHERE status = 'active';
CREATE INDEX idx_recursive_task_logs_task_id ON public.recursive_task_logs(task_id);
