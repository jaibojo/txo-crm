# ⚡ Quick Start Guide

Get up and running in 15 minutes.

---

## 1️⃣ Install Dependencies (2 min)

```bash
cd recruitment-sales-intelligence
pip install -r requirements.txt --break-system-packages
```

---

## 2️⃣ Prepare Your Data (10 min)

### Export from MySQL:

Run these queries and save as CSV:

```sql
-- clients.csv
SELECT client_id, company_name, industry, company_size,
       first_engagement_date, last_engagement_date,
       total_positions_filled, revenue_generated
FROM clients;

-- spocs.csv
SELECT spoc_id, client_id, full_name, email, phone,
       job_title, linkedin_url, first_contact_date,
       last_contact_date, is_active
FROM contacts WHERE contact_type = 'SPOC';
```

### Export Email Archive:

**Gmail:** [Google Takeout](https://takeout.google.com) → Mail → Download .mbox

**Outlook:** File → Export → .pst file → Convert to .mbox

### Place Files Here:

```
data/raw/
├── clients.csv        ← Your MySQL export
├── spocs.csv          ← Your MySQL export
└── emails.mbox        ← Your email archive
```

---

## 3️⃣ Run the Pipeline (3 min)

```bash
python scripts/orchestrator.py
```

**Processing time:** ~3-5 minutes for 1000+ contacts

---

## 4️⃣ Review Results

All outputs are in `outputs/leads/`:

```
📊 master_classified_contacts.csv  ← Import this to your CRM
🟢 bottom_funnel_contacts.csv     ← Active/dormant clients
🟡 middle_funnel_contacts.csv     ← Warm but not converted
🔵 hidden_opportunities_contacts.csv ← Buried gold
🎯 cross_spoc_opportunities.csv   ← Referral plays
```

**Sort by `priority_score` to find your hottest leads!**

---

## 5️⃣ Start Outreach

Use templates in `outputs/templates/`:

1. **Open** `cross_spoc_template.txt`
2. **Customize** with your top contact's data
3. **Send** your first referral outreach!

---

## 🎯 Your First Win

**Goal:** Send 5 outreach emails in the next hour using your top-scoring contacts.

1. Open `master_classified_contacts.csv`
2. Sort by `priority_score` (highest first)
3. Pick top 5 contacts
4. Use appropriate template for each
5. Customize and send!

---

## 📚 Need More Help?

- **Full Guide:** Read `docs/workflow.md`
- **Data Format:** Check `docs/schema.md`
- **Configuration:** Edit `config/settings.yaml`
- **Logs:** Check `outputs/reports/processing.log`

---

## ⚠️ Important Notes

- **LinkedIn scraping is optional** (and requires manual setup)
- **Start without LinkedIn** - you can add it later
- **Sample data** is in `data/raw/SAMPLE_*.csv` for reference
- **Customize keywords** in `config/settings.yaml` for your industry

---

**Ready? Let's turn 10 years of relationships into revenue! 🚀**
