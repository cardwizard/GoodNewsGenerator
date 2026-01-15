# Azure Deployment Guide - Good News Aggregator

This guide will walk you through deploying the Good News Aggregator Flask application to Azure App Service.

## Prerequisites

1. **Azure Account**: Sign up at https://azure.microsoft.com/free/
2. **Azure CLI** (optional but recommended): Install from https://docs.microsoft.com/cli/azure/install-azure-cli
3. **Git**: Already configured in this project

## Deployment Options

Choose one of the following methods:

---

## Option 1: Deploy via Azure Portal (Easiest)

### Step 1: Create Azure App Service

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"** → Search for **"Web App"**
3. Fill in the details:
   - **Subscription**: Choose your subscription
   - **Resource Group**: Create new (e.g., `goodnews-rg`)
   - **Name**: Choose a unique name (e.g., `goodnews-app-yourname`)
   - **Publish**: Code
   - **Runtime stack**: Python 3.11
   - **Region**: Choose closest to you
   - **Pricing plan**: F1 (Free) or B1 (Basic) recommended
4. Click **"Review + create"** → **"Create"**

### Step 2: Configure Application Settings

1. Go to your Web App in Azure Portal
2. Navigate to **Configuration** → **Application settings**
3. Add the following environment variables:

```
SECRET_KEY = 9e2e4a5f001f90f1a2c791d5de59f5bdc1c418154da3569f5d55c2238e0f7c3e
FLASK_ENV = production
NEWS_API_KEY = (your NewsAPI key if you want to use it - currently using RSS feeds)
```

4. Click **"Save"**

### Step 3: Configure Deployment

1. Go to **Deployment Center** in your Web App
2. Choose **GitHub** as source
3. Authorize Azure to access your GitHub account
4. Select your repository: `cardwizard/GoodNewsGenerator`
5. Select branch: `main`
6. Click **"Save"**

Azure will automatically:
- Deploy your code from GitHub
- Install dependencies from `requirements.txt`
- Use `startup.sh` to start the application

### Step 4: Configure Startup Command

1. Go to **Configuration** → **General settings**
2. Set **Startup Command**: `bash startup.sh`
3. Click **"Save"**

### Step 5: Add Database (Optional - Recommended for Production)

For production, you should use Azure Database for PostgreSQL instead of SQLite:

1. Create **Azure Database for PostgreSQL**:
   - Go to Azure Portal → Create resource → "Azure Database for PostgreSQL"
   - Choose **Flexible Server**
   - Configure server name, admin credentials, region

2. Get connection string:
   ```
   postgresql://username:password@servername.postgres.database.azure.com:5432/dbname?sslmode=require
   ```

3. Add to Application Settings:
   ```
   DATABASE_URL = postgresql://username:password@servername.postgres.database.azure.com:5432/goodnews?sslmode=require
   ```

4. Install PostgreSQL adapter (already in requirements.txt if needed):
   Add to `requirements.txt`:
   ```
   psycopg2-binary==2.9.9
   ```

### Step 6: Verify Deployment

1. Go to your Web App **Overview** page
2. Click the **URL** (e.g., https://goodnews-app-yourname.azurewebsites.net)
3. Your application should load!

---

## Option 2: Deploy via Azure CLI (Advanced)

### Prerequisites
```bash
# Install Azure CLI
# Windows: Download from https://aka.ms/installazurecliwindows

# Login to Azure
az login
```

### Step 1: Create Resource Group
```bash
az group create --name goodnews-rg --location eastus
```

### Step 2: Create App Service Plan
```bash
az appservice plan create \
  --name goodnews-plan \
  --resource-group goodnews-rg \
  --sku B1 \
  --is-linux
```

### Step 3: Create Web App
```bash
az webapp create \
  --resource-group goodnews-rg \
  --plan goodnews-plan \
  --name goodnews-app-yourname \
  --runtime "PYTHON:3.11" \
  --deployment-local-git
```

### Step 4: Configure Environment Variables
```bash
az webapp config appsettings set \
  --resource-group goodnews-rg \
  --name goodnews-app-yourname \
  --settings \
    SECRET_KEY="9e2e4a5f001f90f1a2c791d5de59f5bdc1c418154da3569f5d55c2238e0f7c3e" \
    FLASK_ENV="production" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

### Step 5: Set Startup Command
```bash
az webapp config set \
  --resource-group goodnews-rg \
  --name goodnews-app-yourname \
  --startup-file "bash startup.sh"
```

### Step 6: Deploy Code
```bash
# Add Azure remote
git remote add azure <deployment-url-from-step-3>

# Push to Azure
git push azure main
```

---

## Option 3: Deploy via GitHub Actions (CI/CD)

Create `.github/workflows/azure-deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'goodnews-app-yourname'
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

To set up:
1. Download publish profile from Azure Portal → Web App → **Get publish profile**
2. Add it as GitHub Secret: `AZURE_WEBAPP_PUBLISH_PROFILE`
3. Push code to trigger deployment

---

## Post-Deployment Steps

### 1. Create Admin User

SSH into your Azure Web App:
```bash
az webapp ssh --resource-group goodnews-rg --name goodnews-app-yourname
```

Then create an admin user:
```python
python
>>> from app import create_app
>>> from app.models import db, User
>>> app = create_app()
>>> with app.app_context():
...     admin = User(username='admin', is_admin=True)
...     admin.set_password('YourSecurePassword123')
...     db.session.add(admin)
...     db.session.commit()
...     print('Admin created!')
```

### 2. Configure Custom Domain (Optional)

1. Go to **Custom domains** in Azure Portal
2. Add your domain
3. Configure DNS records as instructed

### 3. Enable HTTPS/SSL

Azure App Service provides free SSL certificates:
1. Go to **TLS/SSL settings**
2. Click **Private Key Certificates (.pfx)** → **Create App Service Managed Certificate**
3. Select your domain

### 4. Monitor Application

- **Logs**: Go to **Log stream** to see real-time logs
- **Metrics**: View performance metrics in **Monitoring** section
- **Alerts**: Set up alerts for errors or downtime

---

## Troubleshooting

### Issue: Application won't start
**Solution**: Check logs in Azure Portal → **Log stream** or run:
```bash
az webapp log tail --resource-group goodnews-rg --name goodnews-app-yourname
```

### Issue: Database not initialized
**Solution**: The `startup.sh` should handle this, but you can manually run:
```bash
az webapp ssh --resource-group goodnews-rg --name goodnews-app-yourname
python -c "from app import create_app; from app.models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Issue: Static files not loading
**Solution**: Azure App Service serves static files automatically. Ensure your static files are in `app/static/`

### Issue: RSS feeds not updating
**Solution**: Azure App Service may restart your app, stopping the background scheduler. Consider using:
- Azure Functions for scheduled tasks
- Azure Logic Apps for periodic RSS fetching

---

## Cost Optimization

- **Free Tier (F1)**: Good for testing, limited resources
- **Basic Tier (B1)**: ~$13/month, recommended for production
- **Standard Tier (S1)**: ~$70/month, better performance and features

---

## Security Checklist

- ✅ Strong SECRET_KEY configured
- ✅ HTTPS enabled (Azure provides free SSL)
- ✅ Environment variables used for sensitive data
- ✅ SQLite replaced with PostgreSQL for production
- ✅ CSRF protection enabled
- ✅ Rate limiting configured
- ✅ Secure session cookies enabled

---

## Backup Strategy

1. **Database Backups**:
   - Azure Database for PostgreSQL has automatic backups
   - Configure retention period in Azure Portal

2. **Code Backups**:
   - Already backed up in GitHub repository

---

## Next Steps

1. Set up monitoring and alerts
2. Configure custom domain
3. Set up staging environment for testing
4. Implement CI/CD with GitHub Actions
5. Configure Azure CDN for static assets (optional)

---

## Support

- Azure Documentation: https://docs.microsoft.com/azure/app-service/
- Flask on Azure: https://docs.microsoft.com/azure/app-service/quickstart-python
- Issues: https://github.com/cardwizard/GoodNewsGenerator/issues
