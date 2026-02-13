# Azure Deployment Guide for TalentXO CRM

## Option 1: Quick Deploy - Standalone HTML (Recommended)

The standalone HTML CRM (`crm_standalone.html` + `crm_data.json`) can be deployed immediately to Azure Static Web Apps.

### Steps:

1. **Manual Git Setup**:
   ```bash
   # Remove the stuck lock file
   rm .git/index.lock

   # Configure Git
   git config user.email "jai.goyal@talentxo.com"
   git config user.name "Jai Goyal"

   # Commit your changes
   git add -A
   git commit -m "Initial commit: TalentXO CRM"

   # Rename branch to main (if needed)
   git branch -M main
   ```

2. **Create GitHub Repository**:
   - Go to https://github.com/new
   - Create a new repository (e.g., "talentxo-crm")
   - Don't initialize with README, .gitignore, or license

3. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/talentxo-crm.git
   git push -u origin main
   ```

4. **Deploy to Azure Static Web Apps**:
   - Go to Azure Portal: https://portal.azure.com
   - Click "Create a resource" → "Static Web App"
   - Connect your GitHub account
   - Select the repository and branch
   - Build Presets: "Custom"
   - App location: "/"
   - No API or output location needed
   - Click "Review + Create"

5. **Access Your CRM**:
   - Azure will provide a URL like: `https://your-app.azurestaticapps.net`
   - Your CRM will be live at: `https://your-app.azurestaticapps.net/crm_standalone.html`

---

## Option 2: Python Backend Deployment (Azure App Service)

For the full Python backend with database capabilities.

### Steps:

1. **Prepare for Deployment**:
   ```bash
   # Ensure requirements.txt includes all dependencies
   echo "flask>=2.3.0" >> requirements.txt
   ```

2. **Create Azure Web App**:
   - Go to Azure Portal
   - Create a resource → Web App
   - Runtime stack: Python 3.10
   - Operating System: Linux
   - Region: Choose closest to your users

3. **Deploy via Azure CLI**:
   ```bash
   # Install Azure CLI if needed
   # https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

   az login
   az webapp up --name talentxo-crm --resource-group YourResourceGroup --runtime "PYTHON:3.10"
   ```

4. **Configure Startup Command**:
   - In Azure Portal → Your Web App → Configuration → General Settings
   - Startup Command: `python simple_crm.py`
   - Save

---

## Option 3: Azure DevOps Deployment

1. **Create Azure DevOps Project**:
   - Go to https://dev.azure.com
   - Create new project "TalentXO-CRM"

2. **Push to Azure Repos**:
   ```bash
   git remote add azure https://YOUR_ORG@dev.azure.com/YOUR_ORG/TalentXO-CRM/_git/TalentXO-CRM
   git push azure main
   ```

3. **Set up Pipeline**:
   - Go to Pipelines → Create Pipeline
   - Select Azure Repos Git
   - Choose "Python to Linux Web App on Azure"
   - Configure and run

---

## Files Included for Deployment

### Frontend (Static):
- `crm_standalone.html` - Standalone web interface (no server needed)
- `crm_data.json` - Contact and company data

### Backend (Python):
- `simple_crm.py` - Python web server
- `crm_app.py` - Alternative Flask app
- `requirements.txt` - Python dependencies

### Data Processing:
- `scripts/orchestrator.py` - Full pipeline
- `scripts/preprocess_enhanced.py` - Data preprocessing
- All classification and enrichment scripts

### Configuration:
- `.gitignore` - Git ignore rules
- `config/settings.yaml` - Classification rules

---

## Quick Test Locally

Before deploying, test the standalone HTML:

```bash
# Simple HTTP server
python3 -m http.server 8000

# Or the Python CRM
python3 simple_crm.py
```

Then open:
- Standalone: `http://localhost:8000/crm_standalone.html`
- Python CRM: `http://localhost:5000`

---

## Security Notes

1. **Data Privacy**:
   - Raw CSV and email files are gitignored
   - Only processed data is included
   - Consider encrypting sensitive data before deployment

2. **Authentication** (For Production):
   - Add Azure AD authentication
   - Configure App Service Authentication
   - Restrict access to your organization

3. **Environment Variables**:
   - Store sensitive configs in Azure Key Vault
   - Use App Service application settings

---

## Updating the CRM

To update data:

1. Re-run the data export:
   ```bash
   python3 -c "
   import sqlite3, json
   conn = sqlite3.connect('/tmp/crm.db')
   c = conn.cursor()
   # ... export script ...
   "
   ```

2. Commit and push:
   ```bash
   git add crm_data.json
   git commit -m "Update CRM data"
   git push
   ```

3. Azure will auto-deploy the update

---

## Cost Estimate (Azure)

- **Static Web App**: FREE tier available (perfect for standalone HTML)
- **App Service** (Python): ~$13/month (Basic tier)
- **Storage**: Minimal cost for static files

**Recommendation**: Start with Azure Static Web Apps (FREE) for the standalone HTML version.

---

## Support & Troubleshooting

**Issue**: Lock file error in Git
```bash
rm .git/index.lock
```

**Issue**: Data not loading in browser
- Ensure `crm_data.json` is in the same directory as HTML
- Check browser console for errors (F12)

**Issue**: Python app won't start on Azure
- Check Application Insights logs
- Verify Python version matches requirements
- Check startup command configuration

---

## Next Steps

1. ✅ Remove Git lock file: `rm .git/index.lock`
2. ✅ Commit your code
3. ✅ Push to GitHub
4. ✅ Deploy to Azure Static Web Apps
5. ✅ Access your live CRM!

Your CRM is ready to go live! 🚀
