


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";





SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."auto_reply_log" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "message_id" character varying(255) NOT NULL,
    "thread_id" character varying(255),
    "replied_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "reply_message_id" character varying(255),
    "status" character varying(50) DEFAULT 'sent'::character varying NOT NULL,
    "error_message" "text",
    "llm_model" character varying(100),
    "subject" character varying(500)
);


ALTER TABLE "public"."auto_reply_log" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."auto_reply_rules" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "is_enabled" boolean DEFAULT true NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "sort_order" integer DEFAULT 1 NOT NULL,
    "when_condition" "text",
    "do_action" "text",
    "tone" character varying(50) DEFAULT 'Professional'::character varying
);


ALTER TABLE "public"."auto_reply_rules" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."checkpoint_blobs" (
    "thread_id" "text" NOT NULL,
    "checkpoint_ns" "text" DEFAULT ''::"text" NOT NULL,
    "channel" "text" NOT NULL,
    "version" "text" NOT NULL,
    "type" "text" NOT NULL,
    "blob" "bytea"
);


ALTER TABLE "public"."checkpoint_blobs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."checkpoint_migrations" (
    "v" integer NOT NULL
);


ALTER TABLE "public"."checkpoint_migrations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."checkpoint_writes" (
    "thread_id" "text" NOT NULL,
    "checkpoint_ns" "text" DEFAULT ''::"text" NOT NULL,
    "checkpoint_id" "text" NOT NULL,
    "task_id" "text" NOT NULL,
    "idx" integer NOT NULL,
    "channel" "text" NOT NULL,
    "type" "text",
    "blob" "bytea" NOT NULL,
    "task_path" "text" DEFAULT ''::"text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL
);


ALTER TABLE "public"."checkpoint_writes" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."checkpoints" (
    "thread_id" "text" NOT NULL,
    "checkpoint_ns" "text" DEFAULT ''::"text" NOT NULL,
    "checkpoint_id" "text" NOT NULL,
    "parent_checkpoint_id" "text",
    "type" "text",
    "checkpoint" "jsonb" NOT NULL,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb" NOT NULL
);


ALTER TABLE "public"."checkpoints" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."gmail_watch_state" (
    "user_id" "uuid" NOT NULL,
    "email" character varying(255) NOT NULL,
    "history_id" bigint NOT NULL,
    "watch_expiration" timestamp with time zone NOT NULL,
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."gmail_watch_state" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."pubsub_notifications" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "message_id" character varying(255) NOT NULL,
    "email" character varying(255) NOT NULL,
    "history_id" bigint NOT NULL,
    "processed_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."pubsub_notifications" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."store" (
    "prefix" "text" NOT NULL,
    "key" "text" NOT NULL,
    "value" "jsonb" NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    "expires_at" timestamp with time zone,
    "ttl_minutes" integer
);


ALTER TABLE "public"."store" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."store_migrations" (
    "v" integer NOT NULL
);


ALTER TABLE "public"."store_migrations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_integrations" (
    "user_id" "uuid" NOT NULL,
    "provider" "text" NOT NULL,
    "credentials" "text" NOT NULL,
    "updated_at" timestamp with time zone NOT NULL
);


ALTER TABLE "public"."user_integrations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_settings" (
    "user_id" "uuid" NOT NULL,
    "timezone" character varying(100) DEFAULT 'UTC'::character varying NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."user_settings" OWNER TO "postgres";


ALTER TABLE ONLY "public"."auto_reply_log"
    ADD CONSTRAINT "auto_reply_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."auto_reply_rules"
    ADD CONSTRAINT "auto_reply_rules_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."checkpoint_blobs"
    ADD CONSTRAINT "checkpoint_blobs_pkey" PRIMARY KEY ("thread_id", "checkpoint_ns", "channel", "version");



ALTER TABLE ONLY "public"."checkpoint_migrations"
    ADD CONSTRAINT "checkpoint_migrations_pkey" PRIMARY KEY ("v");



ALTER TABLE ONLY "public"."checkpoint_writes"
    ADD CONSTRAINT "checkpoint_writes_pkey" PRIMARY KEY ("thread_id", "checkpoint_ns", "checkpoint_id", "task_id", "idx");



ALTER TABLE ONLY "public"."checkpoints"
    ADD CONSTRAINT "checkpoints_pkey" PRIMARY KEY ("thread_id", "checkpoint_ns", "checkpoint_id");



ALTER TABLE ONLY "public"."gmail_watch_state"
    ADD CONSTRAINT "gmail_watch_state_pkey" PRIMARY KEY ("user_id");



ALTER TABLE ONLY "public"."pubsub_notifications"
    ADD CONSTRAINT "pubsub_notifications_message_id_key" UNIQUE ("message_id");



ALTER TABLE ONLY "public"."pubsub_notifications"
    ADD CONSTRAINT "pubsub_notifications_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."store_migrations"
    ADD CONSTRAINT "store_migrations_pkey" PRIMARY KEY ("v");



ALTER TABLE ONLY "public"."store"
    ADD CONSTRAINT "store_pkey" PRIMARY KEY ("prefix", "key");



ALTER TABLE ONLY "public"."user_integrations"
    ADD CONSTRAINT "user_integrations_pkey" PRIMARY KEY ("user_id", "provider");



ALTER TABLE ONLY "public"."user_settings"
    ADD CONSTRAINT "user_settings_pkey" PRIMARY KEY ("user_id");



CREATE INDEX "checkpoint_blobs_thread_id_idx" ON "public"."checkpoint_blobs" USING "btree" ("thread_id");



CREATE INDEX "checkpoint_writes_thread_id_idx" ON "public"."checkpoint_writes" USING "btree" ("thread_id");



CREATE INDEX "checkpoints_thread_id_idx" ON "public"."checkpoints" USING "btree" ("thread_id");



CREATE UNIQUE INDEX "idx_auto_reply_log_message" ON "public"."auto_reply_log" USING "btree" ("user_id", "message_id");



CREATE INDEX "idx_auto_reply_log_user_message" ON "public"."auto_reply_log" USING "btree" ("user_id", "message_id");



CREATE INDEX "idx_auto_reply_log_user_replied_at" ON "public"."auto_reply_log" USING "btree" ("user_id", "replied_at" DESC);



CREATE INDEX "idx_auto_reply_log_user_time" ON "public"."auto_reply_log" USING "btree" ("user_id", "replied_at" DESC);



CREATE INDEX "idx_auto_reply_rules_user_enabled" ON "public"."auto_reply_rules" USING "btree" ("user_id", "is_enabled");



CREATE INDEX "idx_auto_reply_rules_user_enabled_order" ON "public"."auto_reply_rules" USING "btree" ("user_id", "sort_order") WHERE ("is_enabled" = true);



CREATE INDEX "idx_auto_reply_rules_user_sort" ON "public"."auto_reply_rules" USING "btree" ("user_id", "sort_order");



CREATE INDEX "idx_gmail_watch_email" ON "public"."gmail_watch_state" USING "btree" ("email");



CREATE INDEX "idx_gmail_watch_email_active" ON "public"."gmail_watch_state" USING "btree" ("email", "is_active") WHERE ("is_active" = true);



CREATE INDEX "idx_pubsub_message_id" ON "public"."pubsub_notifications" USING "btree" ("message_id");



CREATE INDEX "idx_store_expires_at" ON "public"."store" USING "btree" ("expires_at") WHERE ("expires_at" IS NOT NULL);



CREATE INDEX "store_prefix_idx" ON "public"."store" USING "btree" ("prefix" "text_pattern_ops");



ALTER TABLE ONLY "public"."auto_reply_log"
    ADD CONSTRAINT "fk_auto_reply_log_user" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."auto_reply_rules"
    ADD CONSTRAINT "fk_auto_reply_rules_user" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."gmail_watch_state"
    ADD CONSTRAINT "fk_gmail_watch_user" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_settings"
    ADD CONSTRAINT "fk_user_settings_user" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_integrations"
    ADD CONSTRAINT "user_integrations_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE "public"."auto_reply_log" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."auto_reply_rules" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."checkpoint_blobs" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."checkpoint_migrations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."checkpoint_writes" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."checkpoints" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."gmail_watch_state" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."pubsub_notifications" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."store" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."store_migrations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_integrations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_settings" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";








































































































































































GRANT ALL ON TABLE "public"."auto_reply_log" TO "anon";
GRANT ALL ON TABLE "public"."auto_reply_log" TO "authenticated";
GRANT ALL ON TABLE "public"."auto_reply_log" TO "service_role";



GRANT ALL ON TABLE "public"."auto_reply_rules" TO "anon";
GRANT ALL ON TABLE "public"."auto_reply_rules" TO "authenticated";
GRANT ALL ON TABLE "public"."auto_reply_rules" TO "service_role";



GRANT ALL ON TABLE "public"."checkpoint_blobs" TO "anon";
GRANT ALL ON TABLE "public"."checkpoint_blobs" TO "authenticated";
GRANT ALL ON TABLE "public"."checkpoint_blobs" TO "service_role";



GRANT ALL ON TABLE "public"."checkpoint_migrations" TO "anon";
GRANT ALL ON TABLE "public"."checkpoint_migrations" TO "authenticated";
GRANT ALL ON TABLE "public"."checkpoint_migrations" TO "service_role";



GRANT ALL ON TABLE "public"."checkpoint_writes" TO "anon";
GRANT ALL ON TABLE "public"."checkpoint_writes" TO "authenticated";
GRANT ALL ON TABLE "public"."checkpoint_writes" TO "service_role";



GRANT ALL ON TABLE "public"."checkpoints" TO "anon";
GRANT ALL ON TABLE "public"."checkpoints" TO "authenticated";
GRANT ALL ON TABLE "public"."checkpoints" TO "service_role";



GRANT ALL ON TABLE "public"."gmail_watch_state" TO "anon";
GRANT ALL ON TABLE "public"."gmail_watch_state" TO "authenticated";
GRANT ALL ON TABLE "public"."gmail_watch_state" TO "service_role";



GRANT ALL ON TABLE "public"."pubsub_notifications" TO "anon";
GRANT ALL ON TABLE "public"."pubsub_notifications" TO "authenticated";
GRANT ALL ON TABLE "public"."pubsub_notifications" TO "service_role";



GRANT ALL ON TABLE "public"."store" TO "anon";
GRANT ALL ON TABLE "public"."store" TO "authenticated";
GRANT ALL ON TABLE "public"."store" TO "service_role";



GRANT ALL ON TABLE "public"."store_migrations" TO "anon";
GRANT ALL ON TABLE "public"."store_migrations" TO "authenticated";
GRANT ALL ON TABLE "public"."store_migrations" TO "service_role";



GRANT ALL ON TABLE "public"."user_integrations" TO "anon";
GRANT ALL ON TABLE "public"."user_integrations" TO "authenticated";
GRANT ALL ON TABLE "public"."user_integrations" TO "service_role";



GRANT ALL ON TABLE "public"."user_settings" TO "anon";
GRANT ALL ON TABLE "public"."user_settings" TO "authenticated";
GRANT ALL ON TABLE "public"."user_settings" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";































drop extension if exists "pg_net";


  create policy "Give users access to own folder rur790_0"
  on "storage"."objects"
  as permissive
  for insert
  to public
with check (((bucket_id = 'KobaFiles'::text) AND (( SELECT (auth.uid())::text AS uid) = (storage.foldername(name))[1])));



  create policy "Give users access to own folder rur790_1"
  on "storage"."objects"
  as permissive
  for select
  to public
using (((bucket_id = 'KobaFiles'::text) AND (( SELECT (auth.uid())::text AS uid) = (storage.foldername(name))[1])));



  create policy "Give users access to own folder rur790_2"
  on "storage"."objects"
  as permissive
  for delete
  to public
using (((bucket_id = 'KobaFiles'::text) AND (( SELECT (auth.uid())::text AS uid) = (storage.foldername(name))[1])));



