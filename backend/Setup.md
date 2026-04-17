# GCP
1. Create Google pub/sub Topic
    * Give gmail-api-push@system.gserviceaccount.com publish permission to the topic

2. Create a Google pub/sub Subscription
    * Set pub/sub Topic to the one created above
    * Set delivery type to push
    * Endpoint URL = [cloud run endpoint]/webhooks/gmail?token=[SECRET_TOKEN]
    * Enable authentication

3. Create a Cloud Tasks Queue

4. Create a Redis Instance

    ```cli
    gcloud redis instances create --project=[PROJECT ID] \
    [INSTANCE ID] --tier=basic --size=1 --region=us-east1 \
    --redis-version=redis_7_2 --network=projects/[PROJECT ID]/global/networks/default \
    --connect-mode=DIRECT_PEERING --transit-encryption-mode=SERVER_AUTHENTICATION \
    --display-name="[INSTANCE NAME]" --persistence-mode=RDB --rdb-snapshot-period=1h --enable-auth
    ```

    * Download and save SSL Certificate

5. Add SSL Certificate to Secrets
    * Upload SSL Certificate for the secret value

6. Create Cloud Run Service
    * Continuously deploy from a repository
    * Set up with Cloud Build
        * Authenticate Github
        * Connect Repo
        * Set Dockerfile to /backend/Dockerfile
    * Mount SSL Certificate as a File
        * Add Volume
            * Volume type: Secrets
            * Select the Secrets name
            * Mount Path: /etc/secrets
            * Path 1: ca.pem
    * Networking
        * Connect to a VPC for oubound traffic
            * Send traffic directly to a VPC
                * Choose the network and subnet specified when setting up redis
            * Route only requests to private IPs to the VPC
    * Add Environment Variables
    * Change port to 8000

7. Update triggers for build
    * Go to cloud build/triggers
        * Change **included files** to backend/**

# SUPABASE
1. Install Supabase CLI
Install the CLI via your preferred package manager:
```bash
npm install supabase --save-dev
```

2. Initialize & Login
Authenticate the CLI and initialize the project:
```bash
npx supabase login
npx supabase init
```

3. Local Development
Start the local stack (Docker is required). This automatically applies all local migrations:
```bash
npx supabase start
```

4. Link Remote Project
Link your local setup to your existing remote Supabase project:
```bash
npx supabase link --project-ref <your-project-ref-id>
```

5. Deploy Schema
Push your local migration files to the remote database to sync the schema:
```bash
npx supabase db push
```
