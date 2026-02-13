#!/bin/bash
# Commands to push TalentXO CRM to GitHub

echo "🚀 Pushing TalentXO CRM to GitHub..."

cd /sessions/bold-tender-volta/mnt/Claude1/recruitment-sales-intelligence

# Remove any lock files
rm -f .git/index.lock
rm -f .git/*.lock

# Configure Git (if not already done)
git config user.email "jai.goyal@talentxo.com"
git config user.name "Jai Goyal"

# Stage all files
git add -A

# Commit
git commit -m "Initial commit: TalentXO Sales Intelligence CRM

- Standalone HTML CRM with 1,000+ contacts
- Python backend with SQLite database
- Email analysis (8,333+ threads)
- Bottom/Middle/Hidden funnel classification
- Priority scoring algorithm
- Company profiles with revenue tracking
- Excel reports and templates
- Ready for Azure deployment"

# Set main branch
git branch -M main

# Add remote (already done, but safe to rerun)
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/jaibojo/txo-crm.git

# Push to GitHub
echo ""
echo "📤 Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Done! Your code is now on GitHub"
echo "🌐 View it at: https://github.com/jaibojo/txo-crm"
echo ""
echo "Next step: Deploy to Azure Static Web Apps"
echo "See AZURE_DEPLOYMENT_GUIDE.md for instructions"
