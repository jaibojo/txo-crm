#!/bin/bash
set -e

echo "🚀 TalentXO CRM - Automated Deployment"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd /sessions/bold-tender-volta/mnt/Claude1/recruitment-sales-intelligence

# Step 1: Fix Git Lock
echo -e "${BLUE}Step 1: Preparing Git repository...${NC}"
rm -f .git/index.lock .git/*.lock 2>/dev/null || true

# Step 2: Configure Git
echo -e "${BLUE}Step 2: Configuring Git...${NC}"
git config user.email "jai.goyal@talentxo.com"
git config user.name "Jai Goyal"

# Step 3: Stage and Commit
echo -e "${BLUE}Step 3: Committing files...${NC}"
git add -A
git commit -m "Initial commit: TalentXO Sales Intelligence CRM

Features:
- Standalone HTML CRM with 1,000+ contacts
- Python backend with SQLite database
- Email analysis (8,333+ threads)
- Bottom/Middle/Hidden funnel classification
- Priority scoring algorithm
- Company profiles with revenue tracking
- Excel reports and templates
- Ready for Azure deployment" || echo "Already committed"

# Step 4: Set branch to main
echo -e "${BLUE}Step 4: Setting main branch...${NC}"
git branch -M main

# Step 5: Setup remote
echo -e "${BLUE}Step 5: Setting up GitHub remote...${NC}"
git remote remove origin 2>/dev/null || true

# Check if GitHub token is provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  GitHub Personal Access Token not found${NC}"
    echo ""
    echo "To push automatically, set your token:"
    echo "  export GITHUB_TOKEN='your_token_here'"
    echo ""
    echo "Or create one at: https://github.com/settings/tokens/new"
    echo "  - Permissions needed: repo (full control)"
    echo ""
    echo "Then run: bash automated_deploy.sh"
    echo ""
    echo "Alternatively, push manually:"
    git remote add origin https://github.com/jaibojo/txo-crm.git
    echo "  git push -u origin main"
    exit 0
fi

# Step 6: Push to GitHub with token
echo -e "${BLUE}Step 6: Pushing to GitHub...${NC}"
git remote add origin https://${GITHUB_TOKEN}@github.com/jaibojo/txo-crm.git
git push -u origin main --force

echo ""
echo -e "${GREEN}✅ Successfully pushed to GitHub!${NC}"
echo "🌐 Repository: https://github.com/jaibojo/txo-crm"
echo ""

# Step 7: Azure Deployment Options
echo -e "${BLUE}Step 7: Azure Deployment Options${NC}"
echo ""
echo "Choose deployment method:"
echo ""
echo "A) Azure CLI (Recommended - Fastest)"
echo "   - Requires Azure CLI and login"
echo "   - Fully automated"
echo ""
echo "B) Azure Portal + GitHub (Easy)"
echo "   - Go to: https://portal.azure.com"
echo "   - Create Resource → Static Web App"
echo "   - Connect to: jaibojo/txo-crm"
echo "   - Auto-deploys on push"
echo ""
echo "C) Azure DevOps"
echo "   - Set up pipeline in Azure DevOps"
echo "   - Connect to GitHub repo"
echo ""

read -p "Enter choice (A/B/C) or press Enter to skip: " choice

case $choice in
    A|a)
        if command -v az &> /dev/null; then
            echo ""
            echo -e "${BLUE}Checking Azure login...${NC}"

            if az account show &> /dev/null; then
                echo -e "${GREEN}✅ Already logged in to Azure${NC}"

                # Get subscription info
                SUBSCRIPTION=$(az account show --query name -o tsv)
                echo "📋 Using subscription: $SUBSCRIPTION"
                echo ""

                # Prompt for details
                read -p "Enter resource group name (default: talentxo-crm-rg): " RG_NAME
                RG_NAME=${RG_NAME:-talentxo-crm-rg}

                read -p "Enter app name (default: talentxo-crm): " APP_NAME
                APP_NAME=${APP_NAME:-talentxo-crm}

                read -p "Enter region (default: centralus): " REGION
                REGION=${REGION:-centralus}

                echo ""
                echo -e "${BLUE}Creating Azure Static Web App...${NC}"

                # Create resource group
                az group create --name $RG_NAME --location $REGION

                # Create static web app
                az staticwebapp create \
                    --name $APP_NAME \
                    --resource-group $RG_NAME \
                    --source https://github.com/jaibojo/txo-crm \
                    --location $REGION \
                    --branch main \
                    --app-location "/" \
                    --login-with-github

                # Get the URL
                APP_URL=$(az staticwebapp show --name $APP_NAME --resource-group $RG_NAME --query "defaultHostname" -o tsv)

                echo ""
                echo -e "${GREEN}🎉 Deployment Complete!${NC}"
                echo ""
                echo "🌐 Your CRM is live at:"
                echo "   https://$APP_URL/crm_standalone.html"
                echo ""

            else
                echo -e "${YELLOW}⚠️  Please login to Azure:${NC}"
                echo "   az login"
                echo ""
                echo "Then run this script again"
            fi
        else
            echo -e "${YELLOW}⚠️  Azure CLI not installed${NC}"
            echo ""
            echo "Install with: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
            echo "Or use Option B (Azure Portal)"
        fi
        ;;
    B|b)
        echo ""
        echo -e "${GREEN}📋 Manual Deployment Steps:${NC}"
        echo ""
        echo "1. Go to: https://portal.azure.com"
        echo "2. Click 'Create a resource'"
        echo "3. Search for 'Static Web App'"
        echo "4. Fill in details:"
        echo "   - Name: talentxo-crm"
        echo "   - Region: Choose closest"
        echo "   - Deployment: GitHub"
        echo "   - Repo: jaibojo/txo-crm"
        echo "   - Branch: main"
        echo "   - Build Presets: Custom"
        echo "   - App location: /"
        echo "5. Click 'Review + Create'"
        echo ""
        echo "Your CRM will be live at:"
        echo "https://talentxo-crm-*.azurestaticapps.net/crm_standalone.html"
        ;;
    C|c)
        echo ""
        echo "Azure DevOps deployment instructions:"
        echo "See AZURE_DEPLOYMENT_GUIDE.md"
        ;;
    *)
        echo ""
        echo "Skipping Azure deployment"
        echo "See AZURE_DEPLOYMENT_GUIDE.md for manual steps"
        ;;
esac

echo ""
echo -e "${GREEN}✨ Deployment script complete!${NC}"
echo ""
