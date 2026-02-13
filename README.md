# Recruitment Sales Intelligence & Referral Engine

**Objective:** Leverage 10 years of recruitment relationships (1800+ clients) to unlock referrals, re-engage warm leads, and convert dormant accounts using multi-source data analysis and automated outreach.

---

## 🎯 Business Objectives

### 1. Referral Strategies (Trust-Based Leverage)
- **Same Company, Different SPOC**: Reach out to new SPOCs mentioning existing relationships
- **SPOC Changed Companies**: Reconnect with past contacts at their new organizations
- **Reverse Referrals**: Ask successful contacts to refer us to their previous companies
- **Core Principle**: Activate existing trust across organizational boundaries

### 2. Middle Funnel Re-engagement
- Conversations that stalled
- JDs shared but no closure
- Proposals sent without response
- Negotiations stopped midway
- "Reconnect later" requests

### 3. Hidden Opportunities
- Inbound hiring requests not followed up
- Referral mentions buried in emails
- HR professionals who changed companies
- Past candidates now in hiring roles
- "Keep in touch" threads

---

## 📊 Data Sources

| Source | Type | Contains | Priority |
|--------|------|----------|----------|
| MySQL Database | CSV Export | 1800+ clients, roles, SPOCs, timelines | HIGH |
| Email Archive | .mbox | Conversations, funnel signals, hidden opps | HIGH |
| LinkedIn/WhatsApp | Docs/Exports | Outbound conversations, engagement | MEDIUM |
| Website Forms | CSV | Inbound leads | MEDIUM |

---

## 🏗️ System Architecture

```
┌─────────────────┐
│  DATA INGESTION │
└────────┬────────┘
         │
    ┌────▼─────┬──────────┬──────────────┐
    │          │          │              │
┌───▼───┐  ┌──▼───┐  ┌───▼────┐  ┌──────▼──────┐
│ .mbox │  │ MySQL│  │LinkedIn│  │   Inbound   │
│Parser │  │  CSV │  │Scraper │  │    Leads    │
└───┬───┘  └──┬───┘  └───┬────┘  └──────┬──────┘
    │         │          │              │
    └─────────┴──────────┴──────────────┘
                    │
            ┌───────▼────────┐
            │ DATA ENRICHMENT│
            │  & DEDUPLICATION│
            └───────┬────────┘
                    │
            ┌───────▼────────┐
            │ FUNNEL CLASSIFIER│
            └───────┬────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
    ┌───▼───┐   ┌──▼──┐   ┌────▼─────┐
    │BOTTOM │   │MIDDLE│  │  HIDDEN   │
    │FUNNEL │   │FUNNEL│  │   OPPS    │
    └───┬───┘   └──┬──┘   └────┬─────┘
        │          │           │
        └──────────┴───────────┘
                   │
         ┌─────────▼──────────┐
         │ REFERRAL ENGINE    │
         │ & OUTREACH GENERATOR│
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  CRM-READY OUTPUT  │
         └────────────────────┘
```

---

## 📁 Project Structure

```
recruitment-sales-intelligence/
│
├── data/
│   ├── raw/              # Original .mbox, CSV, docs
│   ├── processed/        # Cleaned, normalized data
│   └── enriched/         # LinkedIn-enriched, deduplicated
│
├── scripts/
│   ├── parsers/          # Email, CSV, chat parsers
│   ├── enrichers/        # LinkedIn scraper, data enrichment
│   ├── classifiers/      # Funnel classification logic
│   └── orchestrator.py   # Main workflow controller
│
├── outputs/
│   ├── leads/            # Segmented lead lists
│   ├── templates/        # Personalized outreach templates
│   └── reports/          # Analysis reports, dashboards
│
├── config/
│   └── settings.yaml     # Configuration parameters
│
└── docs/
    ├── schema.md         # Database schema documentation
    └── workflow.md       # Step-by-step execution guide
```

---

## 🚀 Workflow Phases

### Phase 1: Data Collection & Parsing
- [ ] Upload MySQL CSV exports to `data/raw/`
- [ ] Upload .mbox email archive
- [ ] Parse emails for SPOCs, companies, conversation signals
- [ ] Extract database relationships

### Phase 2: LinkedIn Enrichment
- [ ] Build LinkedIn profile scraper
- [ ] Match SPOCs to current companies
- [ ] Identify job changes and career moves
- [ ] Map referral opportunities

### Phase 3: Funnel Classification
- [ ] Apply classification rules to segment contacts
- [ ] Score opportunities by trust level and timing
- [ ] Identify cross-company relationship patterns
- [ ] Flag hidden opportunities

### Phase 4: Outreach Generation
- [ ] Generate personalized templates by segment
- [ ] Create referral request scripts
- [ ] Build re-engagement sequences
- [ ] Export CRM-ready lead lists

### Phase 5: Automation & CRM Integration
- [ ] Schedule recurring data updates
- [ ] Build scoring/prioritization engine
- [ ] Create CRM import formats
- [ ] Deploy monitoring dashboard

---

## 🎯 Success Metrics

- **Bottom Funnel Activation**: # of dormant clients re-engaged
- **Referral Conversion**: # of successful cross-company/cross-SPOC referrals
- **Middle Funnel Revival**: % of stalled conversations restarted
- **Hidden Opportunity Capture**: # of inbound/mentioned leads recovered
- **Pipeline Value**: Total potential revenue from reactivated relationships

---

## 🔧 Next Steps

1. **Immediate**: Upload data files to `data/raw/`
2. **Configure**: Review and update `config/settings.yaml`
3. **Execute**: Run orchestrator to process pipeline
4. **Review**: Analyze outputs and refine classification rules
5. **Deploy**: Integrate with CRM and schedule automation

---

**Created:** 2026-02-12
**Version:** 1.0
**Owner:** TalentXO Sales Team
