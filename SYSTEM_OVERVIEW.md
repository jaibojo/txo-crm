# 📊 System Overview & Visual Guide

---

## 🎯 The Big Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                    10 YEARS OF RELATIONSHIPS                     │
│                         (1800+ Clients)                          │
└───────────────┬─────────────────────────────────────────────────┘
                │
                │ Currently scattered across:
                │ • MySQL database (clients, roles, SPOCs)
                │ • Email archives (conversations, signals)
                │ • LinkedIn (current companies, job changes)
                │
                ▼
┌───────────────────────────────────────────────────────────────────┐
│              SALES INTELLIGENCE PIPELINE                          │
│                                                                   │
│  [Extract] → [Enrich] → [Classify] → [Prioritize] → [Template]  │
└───────────────┬───────────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────────┐
│                    ACTIONABLE OUTPUTS                             │
│                                                                   │
│  • Segmented lead lists (by funnel stage)                        │
│  • Priority scores (0-100 for each contact)                      │
│  • Strategic plays (cross-SPOC, job changes, dormant)            │
│  • Personalized outreach templates                               │
│  • CRM-ready imports                                             │
└───────────────┬───────────────────────────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────────┐
│                    BUSINESS OUTCOMES                              │
│                                                                   │
│  💰 Reactivate dormant $300k+ accounts                           │
│  🤝 Leverage trust for cross-SPOC referrals                      │
│  🔄 Re-engage stalled middle funnel conversations                │
│  💎 Surface hidden opportunities buried in email                 │
└───────────────────────────────────────────────────────────────────┘
```

---

## 📁 Complete File Structure

```
recruitment-sales-intelligence/
│
├── 📘 QUICK_START.md              ← Start here! (15 min)
├── 📘 README.md                   ← Project overview
├── 📘 PROJECT_SUMMARY.md          ← What was built & why
├── 📘 SYSTEM_OVERVIEW.md          ← This file
│
├── 🔧 setup.sh                    ← Automated setup script
├── 📦 requirements.txt            ← Python dependencies
├── 🚫 .gitignore                  ← Protect sensitive data
│
├── ⚙️ config/
│   └── settings.yaml              ← Tune classification rules, scoring weights
│
├── 📂 data/
│   ├── raw/                       ← YOUR UPLOADS GO HERE ⬅️
│   │   ├── clients.csv            ← MySQL export (required)
│   │   ├── spocs.csv              ← MySQL export (required)
│   │   ├── roles.csv              ← MySQL export (optional)
│   │   ├── interactions.csv       ← MySQL export (optional)
│   │   ├── emails.mbox            ← Email archive (required)
│   │   │
│   │   └── SAMPLE_*.csv           ← Reference examples
│   │
│   ├── processed/                 ← Intermediate data (auto-generated)
│   │   ├── email_contacts.csv
│   │   ├── email_conversations.csv
│   │   ├── email_signals.csv
│   │   ├── processed_clients.csv
│   │   ├── processed_spocs.csv
│   │   └── client_spoc_mapping.csv
│   │
│   └── enriched/                  ← LinkedIn-enriched (optional)
│       ├── linkedin_enriched_spocs.csv
│       └── job_change_opportunities.csv
│
├── 🐍 scripts/
│   ├── orchestrator.py            ← MAIN ENTRY POINT ⬅️
│   ├── validate_data.py           ← Pre-flight check
│   │
│   ├── parsers/
│   │   ├── mbox_parser.py         ← Extract from email archive
│   │   └── csv_processor.py       ← Process MySQL exports
│   │
│   ├── enrichers/
│   │   └── linkedin_enricher.py   ← Find current companies (optional)
│   │
│   └── classifiers/
│       └── funnel_classifier.py   ← Segment & score contacts
│
├── 📊 outputs/
│   ├── leads/                     ← YOUR GOLD MINE 🎯
│   │   │
│   │   ├── master_classified_contacts.csv        ← Import to CRM
│   │   │
│   │   ├── bottom_funnel_contacts.csv           ← 🟢 Active/dormant clients
│   │   ├── middle_funnel_contacts.csv           ← 🟡 Warm but unconverted
│   │   ├── hidden_opportunities_contacts.csv    ← 🔵 Buried gems
│   │   ├── top_funnel_contacts.csv              ← ⚪ Cold leads
│   │   │
│   │   ├── cross_spoc_opportunities.csv         ← Same company, different SPOC
│   │   ├── dormant_reactivation_targets.csv     ← High-value dormant accounts
│   │   └── job_change_opportunities.csv         ← SPOCs who switched companies
│   │
│   ├── templates/                 ← Outreach email templates
│   │   ├── cross_spoc_template.txt
│   │   ├── spoc_new_company_template.txt
│   │   ├── reverse_referral_template.txt
│   │   └── middle_funnel_bump_template.txt
│   │
│   └── reports/
│       ├── pipeline_summary.txt   ← Execution summary
│       └── processing.log         ← Detailed logs
│
└── 📚 docs/
    ├── schema.md                  ← Data format guide
    └── workflow.md                ← Step-by-step walkthrough
```

---

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STEP 1: DATA INGESTION                      │
└───────────┬─────────────────────────────────────────────────────────┘
            │
            ├─────► MySQL Database
            │         │
            │         ├─► clients.csv (1800+ companies)
            │         ├─► spocs.csv (3000+ contacts)
            │         ├─► roles.csv (positions worked)
            │         └─► interactions.csv (timeline)
            │
            ├─────► Email Archive
            │         │
            │         └─► emails.mbox (10 years of conversations)
            │
            └─────► LinkedIn (optional)
                      │
                      └─► Current companies, job changes

            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       STEP 2: PARSING & EXTRACTION                  │
└───────────┬─────────────────────────────────────────────────────────┘
            │
            ├─────► mbox_parser.py
            │         │ Extracts:
            │         ├─► Contact names & emails
            │         ├─► Conversation threads
            │         ├─► Funnel signals (stalled, JD shared, etc.)
            │         └─► Hidden opportunities
            │
            └─────► csv_processor.py
                      │ Extracts:
                      ├─► Client relationships
                      ├─► SPOC mappings
                      ├─► Cross-SPOC opportunities
                      └─► Dormant account identification

            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 3: ENRICHMENT (Optional)                    │
└───────────┬─────────────────────────────────────────────────────────┘
            │
            └─────► linkedin_enricher.py
                      │ Adds:
                      ├─► Current company
                      ├─► Current title
                      ├─► Job change detection
                      └─► Past companies

            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 4: MERGE & DEDUPLICATE                      │
└───────────┬─────────────────────────────────────────────────────────┘
            │
            └─────► funnel_classifier.py
                      │ Matches on:
                      ├─► Email (exact match)
                      ├─► LinkedIn URL (exact match)
                      └─► Name + Company (fuzzy match)

            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       STEP 5: CLASSIFICATION                        │
└───────────┬─────────────────────────────────────────────────────────┘
            │
            └─────► funnel_classifier.py
                      │ Segments into:
                      │
                      ├─► 🟢 BOTTOM FUNNEL
                      │     ├─ Active clients (last 6 months)
                      │     ├─ Dormant warm (6-24 months)
                      │     └─ Dormant cold (24+ months)
                      │
                      ├─► 🟡 MIDDLE FUNNEL
                      │     ├─ Conversation stalled
                      │     ├─ JD shared but not closed
                      │     ├─ Proposal sent, no response
                      │     ├─ Negotiation stopped
                      │     └─ "Reconnect later" requests
                      │
                      ├─► 🔵 HIDDEN OPPORTUNITIES
                      │     ├─ Inbound not followed up
                      │     ├─ Referral mentions
                      │     ├─ Job changes detected
                      │     └─ "Keep in touch" threads
                      │
                      └─► ⚪ TOP FUNNEL (Cold leads)

            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        STEP 6: PRIORITIZATION                       │
└───────────┬─────────────────────────────────────────────────────────┘
            │
            └─────► funnel_classifier.py
                      │ Calculates Priority Score (0-100):
                      │
                      ├─► Recency (30%)
                      │     └─ Days since last contact
                      │
                      ├─► Relationship Depth (25%)
                      │     └─ # of placements, revenue generated
                      │
                      ├─► Engagement Level (20%)
                      │     └─ Email response ratio
                      │
                      ├─► Seniority (15%)
                      │     └─ Decision-making authority
                      │
                      └─► Company Size (10%)
                            └─ Larger = more roles

            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     STEP 7: STRATEGIC OPPORTUNITIES                 │
└───────────┬─────────────────────────────────────────────────────────┘
            │
            ├─────► Cross-SPOC Opportunities
            │         │ "We worked with Jane (VP Eng),
            │         │  can we help Michael (Head TA)?"
            │
            ├─────► Job Change Opportunities
            │         │ "SPOC moved to new company
            │         │  → reach out there"
            │         │ "Ask for referral back to old company"
            │
            └─────► Dormant Reactivation
                      │ "High-value clients we haven't
                      │  talked to in 6-24 months"

            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      STEP 8: TEMPLATE GENERATION                    │
└───────────┬─────────────────────────────────────────────────────────┘
            │
            └─────► orchestrator.py
                      │ Generates:
                      │
                      ├─► cross_spoc_template.txt
                      ├─► spoc_new_company_template.txt
                      ├─► reverse_referral_template.txt
                      └─► middle_funnel_bump_template.txt

            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FINAL OUTPUTS                               │
└───────────┬─────────────────────────────────────────────────────────┘
            │
            ├─────► CRM Import File
            │         └─ master_classified_contacts.csv
            │
            ├─────► Segmented Lead Lists
            │         └─ 4 files (bottom, middle, hidden, top)
            │
            ├─────► Strategic Plays
            │         └─ 3 opportunity files
            │
            ├─────► Outreach Templates
            │         └─ 4 personalized templates
            │
            └─────► Reports & Logs
                      └─ Summary & processing logs
```

---

## 🎯 Funnel Classification Logic

```
FOR EACH CONTACT:

┌─────────────────────────────────────────────────────────────┐
│ 1. Check Database Status                                    │
└─────┬───────────────────────────────────────────────────────┘
      │
      ├─ Last engagement < 180 days? → 🟢 BOTTOM (Active)
      ├─ Last engagement 180-730 days + placements > 0? → 🟢 BOTTOM (Dormant Warm)
      └─ Else, check email signals...

┌─────────────────────────────────────────────────────────────┐
│ 2. Check LinkedIn Data                                      │
└─────┬───────────────────────────────────────────────────────┘
      │
      └─ Job change detected? → 🔵 HIDDEN (Job Change)

┌─────────────────────────────────────────────────────────────┐
│ 3. Check Email Signals                                      │
└─────┬───────────────────────────────────────────────────────┘
      │
      ├─ "Let me circle back", "Will check" → 🟡 MIDDLE (Stalled)
      ├─ "JD attached", "Requirement shared" → 🟡 MIDDLE (JD Shared)
      ├─ "Proposal attached", "Pricing" → 🟡 MIDDLE (Proposal Sent)
      ├─ "Budget", "Negotiate terms" → 🟡 MIDDLE (Negotiation)
      ├─ "Next quarter", "Touch base later" → 🟡 MIDDLE (Reconnect Later)
      │
      ├─ "Form submission", "Website inquiry" → 🔵 HIDDEN (Inbound)
      ├─ "Recommend you to", "Should talk to" → 🔵 HIDDEN (Referral)
      └─ "Keep in touch", "Stay connected" → 🔵 HIDDEN (Keep in Touch)

┌─────────────────────────────────────────────────────────────┐
│ 4. Default Classification                                   │
└─────┬───────────────────────────────────────────────────────┘
      │
      └─ No strong signals → ⚪ TOP (Cold Lead)

┌─────────────────────────────────────────────────────────────┐
│ 5. Calculate Priority Score                                 │
└─────┬───────────────────────────────────────────────────────┘
      │
      └─ Weighted formula (0-100) based on recency,
         relationship depth, engagement, seniority, company size
```

---

## 🚀 Execution Flow

```
START
  │
  ├─► python scripts/validate_data.py
  │     │
  │     ├─ Check clients.csv ✓
  │     ├─ Check spocs.csv ✓
  │     ├─ Check emails.mbox ✓
  │     └─ Report: PASSED
  │
  ├─► python scripts/orchestrator.py
  │     │
  │     ├─ [Step 1] Parse emails.mbox → 1,856 contacts
  │     ├─ [Step 2] Process CSV files → 1,834 clients, 3,201 SPOCs
  │     ├─ [Step 3] Skip LinkedIn (optional)
  │     ├─ [Step 4] Classify → 2,450 unique contacts
  │     ├─ [Step 5] Generate strategies → 245 opportunities
  │     ├─ [Step 6] Create templates → 4 templates
  │     └─ [Step 7] Summary report
  │
  └─► Review outputs/leads/
        │
        ├─ master_classified_contacts.csv (2,450 contacts, scored)
        ├─ bottom_funnel_contacts.csv (850 active/dormant)
        ├─ middle_funnel_contacts.csv (420 warm but unconverted)
        ├─ hidden_opportunities_contacts.csv (180 buried gems)
        └─ cross_spoc_opportunities.csv (245 referral plays)

READY FOR OUTREACH! 🎯
```

---

## 📊 Expected Outcomes

### Week 1: Setup & First Batch
```
✅ Pipeline executed
✅ Data validated
✅ Top 20 contacts identified (score > 80)
📧 5 outreach emails sent (cross-SPOC, high priority)
📈 Response rate: 40-60% (leveraging trust)
📞 Meetings booked: 2-3
```

### Month 1: Scale Outreach
```
📧 100 total outreach emails sent
   ├─ 30 bottom funnel (dormant reactivation)
   ├─ 40 cross-SPOC plays
   ├─ 20 job change follow-ups
   └─ 10 middle funnel bumps

📈 Estimated outcomes:
   ├─ Response rate: 35%
   ├─ Meetings: 15-20
   └─ Opportunities created: 8-12
```

### Quarter 1: Revenue Impact
```
💰 Estimated revenue from reactivated relationships:
   ├─ Dormant accounts: $300k
   ├─ Cross-SPOC referrals: $200k
   ├─ Middle funnel conversions: $150k
   └─ Total: $650k+

🔄 Ongoing:
   └─ Monthly pipeline refresh with new data
```

---

## 🎓 Key Concepts

### Funnel Stages Explained

**🟢 BOTTOM FUNNEL** = Existing relationship, proven track record
- **Action:** Reactivate, expand, referrals
- **Conversion:** 30-50%

**🟡 MIDDLE FUNNEL** = Conversation started but stalled
- **Action:** Re-engage with value-add
- **Conversion:** 10-20%

**🔵 HIDDEN OPPORTUNITIES** = Gold buried in data
- **Action:** Surface and prioritize
- **Conversion:** 15-30% (often overlooked)

**⚪ TOP FUNNEL** = Cold leads
- **Action:** Nurture campaigns
- **Conversion:** 1-5%

### Priority Score Breakdown

```
Score 80-100: 🔥 HOT
  → Immediate outreach (today/this week)
  → High conversion probability
  → Personal, custom emails

Score 60-79: 🌡️ WARM
  → Priority outreach (this month)
  → Good conversion probability
  → Semi-personalized templates

Score 40-59: 🌤️ LUKEWARM
  → Secondary outreach (this quarter)
  → Moderate conversion probability
  → Template-based with minimal customization

Score 0-39: ❄️ COLD
  → Nurture campaigns
  → Low conversion probability
  → Automated sequences
```

---

## ✅ Success Metrics

Track these KPIs to measure ROI:

```
INPUT METRICS:
  ├─ Contacts processed: 2,450
  ├─ Bottom funnel: 850
  ├─ Middle funnel: 420
  └─ Hidden opportunities: 180

ACTIVITY METRICS:
  ├─ Emails sent: 100/month
  ├─ Templates used: 4 types
  └─ Outreach channels: Email, LinkedIn, WhatsApp

OUTCOME METRICS:
  ├─ Response rate: Target 35%+
  ├─ Meetings booked: Target 15/month
  ├─ Opportunities created: Target 8/month
  └─ Deals closed: Target 2-3/month

REVENUE METRICS:
  ├─ Reactivated account value: $300k+
  ├─ New opportunities from referrals: $200k+
  └─ Total pipeline impact: $650k+ (Year 1)
```

---

## 🎯 Your Action Plan

```
TODAY:
  □ Run setup.sh
  □ Add your data files
  □ Run validation
  □ Execute pipeline
  □ Identify top 10 contacts

THIS WEEK:
  □ Send 20 outreach emails
  □ Book 3-5 meetings
  □ Import contacts to CRM

THIS MONTH:
  □ Scale to 100 outreach emails
  □ Close first deal from reactivation
  □ Refine templates based on response rates

THIS QUARTER:
  □ Process $500k+ in new pipeline
  □ Automate monthly data refresh
  □ Integrate with sales tools (Zapier, etc.)
```

---

**Ready to turn 10 years of trust into revenue? Let's execute! 🚀**
