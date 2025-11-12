# Railway Deployment Guide

## Overview

This project uses Railway's `preDeployCommand` to automatically sync OpenRouter models to the PostgreSQL database before each deployment.

## Architecture

```
Railway Deployment Flow:
1. Git push triggers Railway build
2. Railpack builds Go API
3. preDeployCommand runs scripts/pre_deploy.sh
   ├── Installs uv (Python package manager)
   ├── Syncs Python dependencies
   └── Runs setup/sync OpenRouter models
4. Go API starts with fresh database
```

## Required Environment Variables

Set these in your Railway project:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `PORT` | API port (Railway sets automatically) | `8080` |

## Configuration Files

### `/railway.json`
Main Railway configuration with pre-deploy command.

### `/scripts/pre_deploy.sh`
Bash script that:
- Validates environment
- Installs Python dependencies (via uv)
- Runs model registry setup script
- Syncs OpenRouter models to PostgreSQL

### `/.railway-ignore`
Optimizes Railway builds by excluding unnecessary files.

## Manual Testing

Test the pre-deploy script locally:

```bash
# Set your database URL
export DATABASE_URL="postgresql://user:pass@localhost:5432/adaptive"

# Run the pre-deploy script
bash scripts/pre_deploy.sh
```

## Deployment Process

### First Deployment

1. **Set up Railway Project**
   ```bash
   railway login
   railway init
   railway link
   ```

2. **Add PostgreSQL Database**
   ```bash
   railway add --database postgresql
   ```

3. **Set Environment Variables**
   - Railway automatically sets `DATABASE_URL` when you add PostgreSQL
   - Verify: `railway variables`

4. **Deploy**
   ```bash
   git push
   # Or trigger manual deploy in Railway dashboard
   ```

### Subsequent Deployments

Every deployment will automatically:
1. Run pre-deploy script
2. Sync latest models from OpenRouter
3. Start Go API with updated database

## Monitoring Pre-Deploy Execution

View pre-deploy logs in Railway dashboard:

1. Go to your service
2. Click on deployment
3. Look for "Pre Deploy Command" section in logs
4. You'll see output like:

```
════════════════════════════════════════════════════════
🚀 Railway Pre-Deploy: Database Setup
════════════════════════════════════════════════════════
✓ Database URL configured
✓ uv already installed
📦 Syncing Python dependencies...
✓ Dependencies synced

🔄 Syncing OpenRouter models to database...
════════════════════════════════════════════════════════
🚀 Starting OpenRouter model sync pipeline
Fetching endpoints for 234 models in parallel...
✓ Fetched endpoints for 234 models
✓ Fetched 156 ZDR endpoints
...
✅ Pre-Deploy Setup Completed Successfully!
════════════════════════════════════════════════════════
```

## Troubleshooting

### Pre-Deploy Fails: "DATABASE_URL not set"
**Solution:** Ensure PostgreSQL service is linked and `DATABASE_URL` is in environment variables.

```bash
railway variables
railway add --database postgresql
```

### Pre-Deploy Fails: Python Dependency Issues
**Solution:** Lock dependencies and commit updated `uv.lock`:

```bash
cd scripts
uv lock
git add uv.lock
git commit -m "Lock Python dependencies"
git push
```

### Pre-Deploy Times Out
**Solution:** Increase timeout in `railway.json`:

```json
{
  "deploy": {
    "preDeployCommand": ["bash scripts/pre_deploy.sh"],
    "healthcheckTimeout": 300
  }
}
```

### Skip Pre-Deploy for Testing
To temporarily disable pre-deploy:

1. Go to Railway dashboard
2. Service Settings → Deploy
3. Remove pre-deploy command
4. Redeploy

## Scheduled Updates (Optional)

For regular model updates beyond deployments, create a cron service:

1. **Create new Railway service**
2. **Point to same repository**
3. **Set custom start command:**
   ```bash
   cd scripts && uv run python -m setup --db-url $DATABASE_URL --no-cache
   ```
4. **Enable cron schedule:** `0 */6 * * *` (every 6 hours)

## Local Development

Run setup locally without Railway:

```bash
# Install dependencies
cd scripts
uv sync

# Run setup
export DATABASE_URL="postgresql://localhost:5432/adaptive"
uv run python -m setup --db-url "$DATABASE_URL"
```

## Best Practices

1. **Always test pre-deploy script locally** before pushing
2. **Monitor first deployment logs** to ensure pre-deploy succeeds
3. **Use `--no-cache` flag** in pre-deploy to get fresh OpenRouter data
4. **Keep `uv.lock` committed** for reproducible builds
5. **Set appropriate timeouts** for large model syncs

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: [Your GitHub issues URL]