CREATE TABLE IF NOT EXISTS public.invitation_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    is_used BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Secure the table so only service roles (backend) and Postgres triggers can read/write directly
ALTER TABLE public.invitation_codes ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.validate_invitation_code()
RETURNS trigger AS $$
DECLARE
    provided_code TEXT;
    valid_code_id UUID;
BEGIN
    provided_code := NEW.raw_user_meta_data->>'invitation_code';
    
    -- If provided_code is NULL (e.g. Google SSO signup without filling a form),
    -- we check if a valid, unused code simply exists for their confirmed email.
    IF provided_code IS NULL THEN
        SELECT id INTO valid_code_id FROM public.invitation_codes 
        WHERE email = NEW.email AND is_used = false;
        
        IF valid_code_id IS NULL THEN
            RAISE EXCEPTION 'You must have an approved invitation code to sign up.';
        END IF;
    ELSE
        -- Standard password signup via form: must provide the correct code matching this email.
        SELECT id INTO valid_code_id FROM public.invitation_codes 
        WHERE email = NEW.email AND code = provided_code AND is_used = false;
        
        IF valid_code_id IS NULL THEN
            RAISE EXCEPTION 'Invalid, mismatched, or already used invitation code for this email address.';
        END IF;
    END IF;

    -- Mark the code as used so it cannot be reused
    UPDATE public.invitation_codes SET is_used = true WHERE id = valid_code_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Hook the function into the Supabase Auth system
DROP TRIGGER IF EXISTS tr_validate_invitation_code ON auth.users;

CREATE TRIGGER tr_validate_invitation_code
BEFORE INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION public.validate_invitation_code();
