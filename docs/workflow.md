# Workflow Guide: Step-by-Step Execution

This guide walks you through running the complete sales intelligence pipeline.

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.8 or higher installed
- MySQL database access (for CSV exports)
- Email archive access (Gmail, Outlook, etc.)

### Installation

```bash
# 1. Navigate to project directory
cd recruitment-sales-intelligence

# 2. Install Python dependencies
pip install -r requirements.txt --break-system-packages

# 3. Verify installation
python --version
python -c "import pandas; print('✓ Dependencies installed')"
```

---

## 📁 Step 1: Prepare Your Data (15-30 minutes)

### 1A. Export MySQL Data

Run these SQL queries in your MySQL database and save as CSV files:

**clients.csv:**
```sql
SELECT
    client_id,
    company_name,
    industry,
    company_size,
    first_engagement_date,
    last_engagement_date,
    COUNT(DISTINCT position_id) as total_positions_filled,
    SUM(revenue) as revenue_generated
FROM clients
LEFT JOIN positions ON clients.client_id = positions.client_id
GROUP BY client_id;
```

**spocs.csv:**
```sql
SELECT
    spoc_id,
    client_id,
    full_name,
    email,
    phone,
    job_title,
    linkedin_url,
    first_contact_date,
    last_contact_date,
    is_active
FROM contacts
WHERE contact_type = 'SPOC';
```

**roles.csv (optional):**
```sql
SELECT
    role_id,
    client_id,
    job_title,
    job_description,
    seniority_level,
    department,
    posted_date,
    closed_date,
    status,
    salary_range
FROM positions
ORDER BY posted_date DESC;
```

**interactions.csv (optional):**
```sql
SELECT
    interaction_id,
    client_id,
    spoc_id,
    interaction_date,
    interaction_type,
    notes,
    outcome,
    next_steps
FROM interactions
ORDER BY interaction_date DESC
LIMIT 50000;  -- Last 50k interactions
```

### 1B. Export Email Archive

#### For Gmail:
1. Go to [Google Takeout](https://takeout.google.com)
2. Deselect all, select only "Mail"
3. Click "All Mail data included" → Deselect all except "Sent" and "Inbox"
4. Choose "Export once" → "Next step"
5. Format: .zip, Size: 50GB (or appropriate)
6. Click "Create export"
7. Wait for email notification (can take hours)
8. Download and extract to find `.mbox` file

#### For Outlook:
1. File → Open & Export → Import/Export
2. "Export to a file" → "Outlook Data File (.pst)"
3. Use [pst-to-mbox converter](https://www.coolutils.com/PST-Converter) if needed

#### For Apple Mail:
1. Select mailbox in sidebar
2. Mailbox → Export Mailbox
3. Save as .mbox format

### 1C. Organize Files

Place all exported files in the correct location:

```bash
# Copy your exports here:
data/raw/clients.csv           # ← Your MySQL export
data/raw/spocs.csv             # ← Your MySQL export
data/raw/roles.csv             # ← Optional
data/raw/interactions.csv      # ← Optional
data/raw/emails.mbox           # ← Your email archive
```

**Verify files are in place:**
```bash
ls -lh data/raw/
# Should show: clients.csv, spocs.csv, emails.mbox, etc.
```

---

## ⚙️ Step 2: Configure Settings (5 minutes)

### 2A. Review Configuration

Open `config/settings.yaml` and verify/update:

```yaml
# Check that paths match your files
data_sources:
  mysql_csv:
    clients: "data/raw/clients.csv"
    spocs: "data/raw/spocs.csv"
  email:
    mbox_file: "data/raw/emails.mbox"
```

### 2B. Customize Classification Rules

**Adjust timeframes** if needed:

```yaml
classification:
  bottom_funnel:
    active_threshold_days: 180    # Last 6 months = active
    dormant_min_days: 180         # 6-24 months = dormant warm
    dormant_max_days: 730         # 24+ months = dormant cold
```

**Customize keywords** for your industry:

```yaml
classification:
  middle_funnel:
    keywords:
      stalled: ["let me get back", "will check", "circle back"]
      # Add your own phrases here
```

---

## 🎯 Step 3: Run the Pipeline (10-30 minutes)

### 3A. Basic Run (Without LinkedIn)

```bash
python scripts/orchestrator.py
```

**What happens:**
1. ✅ Parses .mbox email archive
2. ✅ Processes MySQL CSV exports
3. ⏭️ Skips LinkedIn enrichment
4. ✅ Classifies contacts into funnels
5. ✅ Generates strategic outputs
6. ✅ Creates outreach templates

**Expected output:**
```
================================================================================
Sales Intelligence Pipeline Started
Timestamp: 2024-02-12 10:30:15
================================================================================

================================================================================
STEP 1: Parsing Email Archive (.mbox)
================================================================================
Processing emails: 100%|████████████| 5234/5234
✓ Parsed 1,856 unique email contacts
✓ Identified 892 conversation threads
✓ Detected 324 funnel signals

================================================================================
STEP 2: Processing MySQL CSV Exports
================================================================================
✓ Loaded 1,834 clients
✓ Loaded 3,201 SPOCs
✓ Database CSVs processed successfully

... (continues)
```

### 3B. Advanced Run (With LinkedIn)

**⚠️ Warning:** LinkedIn scraping requires:
- Valid LinkedIn account with Sales Navigator (recommended)
- Manual CAPTCHA solving
- Compliance with LinkedIn Terms of Service
- Time (5+ hours for 1000+ profiles)

**Setup:**
```bash
# Set credentials as environment variables (do NOT commit these!)
export LINKEDIN_USERNAME="your-email@company.com"
export LINKEDIN_PASSWORD="your-password"

# Run with LinkedIn enrichment
python scripts/orchestrator.py --with-linkedin
```

**Alternative:** Use third-party enrichment services instead:
- [Apollo.io](https://www.apollo.io/)
- [ZoomInfo](https://www.zoominfo.com/)
- [Clearbit](https://clearbit.com/)

---

## 📊 Step 4: Review Outputs (15-30 minutes)

### 4A. Funnel Segments

Navigate to `outputs/leads/` to find:

```
outputs/leads/
├── master_classified_contacts.csv         # All contacts with scores
├── bottom_funnel_contacts.csv            # Active/dormant clients
├── middle_funnel_contacts.csv            # Warm but unconverted
├── hidden_opportunities_contacts.csv     # Buried gems
├── top_funnel_contacts.csv               # Cold leads
├── cross_spoc_opportunities.csv          # Same company, different SPOC
├── dormant_reactivation_targets.csv      # Dormant but high-value
└── job_change_opportunities.csv          # SPOCs who switched companies
```

### 4B. Priority Contacts

Open `master_classified_contacts.csv` and sort by `priority_score` (descending).

**What the score means:**
- **80-100:** Immediate outreach (hot leads)
- **60-79:** High priority (reach out this week)
- **40-59:** Medium priority (reach out this month)
- **0-39:** Lower priority (nurture campaign)

### 4C. Strategic Opportunities

**Cross-SPOC Opportunities** (`cross_spoc_opportunities.csv`):
```csv
strategy,company_name,target_spoc_name,reference_spoc_name,priority
cross_spoc_same_company,TechCorp,Michael Chen,Jane Smith,HIGH
```

**Action:** "Hi Michael, we've worked with Jane Smith (VP Eng) on 12 placements. Can we support your team too?"

**Dormant Reactivation** (`dormant_reactivation_targets.csv`):
```csv
company_name,client_status,client_value_score,days_since_last_contact
DataDynamics LLC,dormant_warm,85.2,245
```

**Action:** "It's been ~8 months since we last connected. Here's what's new with us..."

---

## 📧 Step 5: Generate Outreach (30-60 minutes)

### 5A. Use Templates

Templates are in `outputs/templates/`:

- `cross_spoc_template.txt` - Same company, different SPOC
- `spoc_new_company_template.txt` - SPOC changed companies
- `reverse_referral_template.txt` - Ask for intro to old company
- `middle_funnel_bump_template.txt` - Re-engage stalled conversations

### 5B. Personalization Strategy

**For each high-priority contact:**

1. **Gather context:**
   - Which segment are they in?
   - What signals were detected?
   - What's their company/role?

2. **Choose template:**
   - Cross-SPOC → Use cross_spoc_template.txt
   - Job change → Use spoc_new_company_template.txt
   - Dormant → Use middle_funnel_bump_template.txt

3. **Customize variables:**
   ```
   {spoc_name} → "Jane Smith"
   {company_name} → "TechCorp Inc"
   {reference_spoc_name} → "Michael Chen"
   {roles_worked} → "Backend Engineers, Data Scientists"
   {timeframe} → "2019-2024"
   ```

4. **Add personal touch:**
   - Reference specific roles you filled
   - Mention recent company news (funding, expansion)
   - Include mutual connections if any

### 5C. Batch Outreach

**Create outreach batches:**

**Week 1:** Top 20 priority contacts (score 80+)
**Week 2:** Next 30 contacts (score 60-79)
**Week 3:** Next 50 contacts (score 40-59)

**Track in CRM:**
- Date contacted
- Response rate
- Meetings booked
- Opportunities created

---

## 🔄 Step 6: Import to CRM (15 minutes)

### 6A. Prepare Import File

The `master_classified_contacts.csv` is CRM-ready with these columns:

```csv
email,name,company,title,linkedin_url,funnel_stage,priority_score,last_contact,funnel_signals
```

### 6B. Import to Common CRMs

#### HubSpot:
1. Contacts → Import
2. Upload `master_classified_contacts.csv`
3. Map fields: email → Email, name → Full Name, etc.
4. Create custom property: "Lead Score" → Map to `priority_score`
5. Create custom property: "Funnel Stage" → Map to `funnel_stage`

#### Salesforce:
1. Setup → Data Import Wizard
2. Choose "Contacts"
3. Upload CSV
4. Map standard + custom fields
5. Review and import

#### Pipedrive:
1. Contacts → More → Import data
2. Upload CSV
3. Match columns
4. Import

### 6C. Create Segments

In your CRM, create these segments:

**Hot Leads:**
- Priority Score > 80
- Last Contact < 180 days ago

**Dormant Warm:**
- Funnel Stage = "bottom_dormant_warm"
- Priority Score > 60

**Job Change Follow-ups:**
- Funnel Stage = "hidden_job_change"

---

## 🔁 Step 7: Ongoing Maintenance

### Weekly Updates

```bash
# Re-export latest data from MySQL
# Re-run pipeline
python scripts/orchestrator.py

# Review new signals and opportunities
```

### Monthly Reviews

1. **Update configuration** based on what's working:
   - Which keywords are detecting signals accurately?
   - Are timeframes (active/dormant) correct?

2. **Refine scoring weights** in `config/settings.yaml`:
   ```yaml
   scoring:
     weights:
       recency: 0.35        # Increase if recent = more important
       relationship_depth: 0.25
       engagement_level: 0.20
       seniority: 0.15
       company_size: 0.05
   ```

3. **Track conversion metrics:**
   - Response rate by funnel stage
   - Meetings booked by priority score
   - Deals closed from reactivated dormant accounts

---

## 🎓 Advanced Features

### Custom Classification Rules

Edit `scripts/classifiers/funnel_classifier.py` to add custom logic:

```python
def _determine_funnel_stage(self, row, signals):
    # Add your own business logic
    if row.get('total_positions_filled', 0) > 10:
        return 'vip_client', ['high_volume']

    # ... rest of existing logic
```

### Integration with Other Tools

**Zapier Automation:**
1. When new lead is classified as "hot" (score > 80)
2. Create task in Asana/ClickUp
3. Send Slack notification
4. Add to email sequence

**API Integration:**
Build a REST API wrapper to run classification on-demand:
```python
# api.py
from flask import Flask, jsonify
from orchestrator import SalesIntelligenceOrchestrator

app = Flask(__name__)

@app.route('/classify', methods=['POST'])
def classify_contacts():
    orchestrator = SalesIntelligenceOrchestrator()
    orchestrator.run_pipeline()
    return jsonify({"status": "success"})
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'pandas'"
**Solution:**
```bash
pip install -r requirements.txt --break-system-packages
```

### Issue: ".mbox file not found"
**Solution:**
Ensure your email export is named exactly `emails.mbox` and located in `data/raw/`

### Issue: "Empty contacts DataFrame"
**Solution:**
- Check CSV column names match expected schema
- Verify CSV files are not empty
- Look at logs in `outputs/reports/processing.log`

### Issue: "Low priority scores across the board"
**Solution:**
- Adjust scoring weights in `config/settings.yaml`
- Check if `last_contact_date` data is present
- Verify `client_value_score` calculation

### Issue: LinkedIn scraper not working
**Solution:**
- LinkedIn frequently changes their HTML structure
- Use manual LinkedIn export from Sales Navigator instead
- Or use third-party enrichment services (Apollo, ZoomInfo)

---

## 📞 Support & Iteration

This system is meant to be **iterative**. After your first run:

1. **Review outputs** - Are segments accurate?
2. **Test outreach** - Do templates resonate?
3. **Measure results** - Track response rates
4. **Refine** - Adjust keywords, weights, templates
5. **Repeat** - Run pipeline monthly with updated data

**Questions?** Review the full documentation in `/docs/` or check the inline comments in each Python script.

---

## ✅ Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] MySQL data exported to CSVs
- [ ] Email archive exported to .mbox
- [ ] Files placed in `data/raw/`
- [ ] Configuration reviewed in `config/settings.yaml`
- [ ] Pipeline executed (`python scripts/orchestrator.py`)
- [ ] Outputs reviewed in `outputs/leads/`
- [ ] Top 20 contacts identified for outreach
- [ ] Templates customized with real data
- [ ] CRM import completed
- [ ] First outreach batch sent!

**Ready to unlock 10 years of relationship capital? Let's go! 🚀**
