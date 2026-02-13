# Database Schema Documentation

This document describes the expected schema for MySQL CSV exports and other data sources.

---

## MySQL CSV Exports

### 1. clients.csv

Contains information about your 1800+ client companies.

**Required Columns:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `client_id` | int | Unique client identifier | 1001 |
| `company_name` | string | Company name | "Acme Corp" |
| `industry` | string | Industry sector | "Technology" |
| `company_size` | string | Company size category | "50-200" or "Series B" |
| `first_engagement_date` | date | When we first worked with them | "2018-03-15" |
| `last_engagement_date` | date | Most recent interaction | "2024-06-20" |
| `total_positions_filled` | int | Number of successful placements | 12 |
| `revenue_generated` | float | Total revenue from this client | 45000.00 |

**Optional Columns:**
- `website`
- `headquarters_location`
- `account_manager`
- `notes`

**Sample SQL Query:**
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

---

### 2. spocs.csv

Single Points of Contact - the people you work with at each client.

**Required Columns:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `spoc_id` | int | Unique SPOC identifier | 5001 |
| `client_id` | int | Links to clients.csv | 1001 |
| `full_name` | string | Contact's full name | "Jane Smith" |
| `email` | string | Email address | "jane.smith@acme.com" |
| `phone` | string | Phone number | "+1-555-0123" |
| `job_title` | string | Their role | "VP of Engineering" |
| `linkedin_url` | string | LinkedIn profile URL (if known) | "linkedin.com/in/janesmith" |
| `first_contact_date` | date | When we first connected | "2018-03-15" |
| `last_contact_date` | date | Most recent contact | "2024-06-20" |
| `is_active` | boolean | Still at this company? | 1 or 0 |

**Optional Columns:**
- `department`
- `seniority_level`
- `timezone`

**Sample SQL Query:**
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

---

### 3. roles.csv

Positions/jobs you've worked on (successful and unsuccessful).

**Required Columns:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `role_id` | int | Unique role identifier | 3001 |
| `client_id` | int | Which client | 1001 |
| `job_title` | string | Position title | "Senior Backend Engineer" |
| `job_description` | text | Full JD (can be long) | "We are looking for..." |
| `seniority_level` | string | Level | "Senior" or "Mid-Level" |
| `department` | string | Department/team | "Engineering" |
| `posted_date` | date | When role was posted | "2023-11-01" |
| `closed_date` | date | When filled/cancelled | "2023-12-15" |
| `status` | string | Current status | "Filled", "Open", "Cancelled" |
| `salary_range` | string | Compensation range | "$120k-$150k" |

**Optional Columns:**
- `location`
- `remote_policy`
- `required_skills`
- `placed_candidate_id`

**Sample SQL Query:**
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

---

### 4. interactions.csv (Optional but Recommended)

Timeline of all interactions with clients/SPOCs.

**Required Columns:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `interaction_id` | int | Unique interaction ID | 7001 |
| `client_id` | int | Which client | 1001 |
| `spoc_id` | int | Which SPOC (if applicable) | 5001 |
| `interaction_date` | datetime | When it happened | "2024-06-20 14:30:00" |
| `interaction_type` | string | Type of interaction | "Email", "Call", "Meeting" |
| `notes` | text | Details of interaction | "Discussed Q3 hiring needs..." |
| `outcome` | string | Result | "Positive", "Neutral", "Follow-up needed" |
| `next_steps` | text | What's next | "Send proposal by Friday" |

**Sample SQL Query:**
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
LIMIT 10000;
```

---

## Email Data (.mbox format)

**How to Export:**

### Gmail:
1. Go to Google Takeout: https://takeout.google.com
2. Deselect all, then select only "Mail"
3. Under "Multiple formats" choose "Include all messages in Mail"
4. Click "Next step" → "Create export"
5. Download the .mbox file

### Outlook:
1. File → Open & Export → Import/Export
2. Choose "Export to a file"
3. Select "Outlook Data File (.pst)"
4. Convert .pst to .mbox using a tool like "PST to MBOX Converter"

### Apple Mail:
1. Select mailbox in sidebar
2. Mailbox → Export Mailbox
3. Choose location and save as .mbox

**What the parser extracts:**
- Email addresses of all senders/recipients
- Conversation threads (grouped by subject/reply-to)
- Keywords indicating funnel stage (stalled, JD shared, proposal sent, etc.)
- References to companies, roles, referrals
- Timestamps of all communications

---

## LinkedIn/WhatsApp Data (Optional)

### LinkedIn Conversations Export:
If you have Sales Navigator, you can export your message history as CSV.

**Expected format:**
```csv
name,company,message_date,message_content,linkedin_url
John Doe,TechCorp,2024-01-15,"Hi, looking for engineers...",linkedin.com/in/johndoe
```

### WhatsApp Chats:
1. Open chat → Three dots → More → Export chat
2. Save as .txt file
3. Upload to `data/raw/whatsapp_chats.txt`

**The system will parse:**
- Contact names
- Companies mentioned
- Hiring needs mentioned
- Timestamps

---

## Inbound Leads (Website Forms)

If you have a contact form on your website, export submissions as CSV.

**Expected format:**
```csv
submission_date,name,email,company,message,source_page
2024-02-10,Sarah Johnson,sarah@startup.com,StartupXYZ,Looking to hire 3 engineers,/contact-us
```

---

## Data Quality Tips

### For Best Results:

1. **Consistency:** Use consistent date formats (YYYY-MM-DD preferred)
2. **Completeness:** Fill as many fields as possible
3. **Accuracy:** Ensure email addresses are correct (critical for deduplication)
4. **Recency:** Include all interactions from past 3-5 years minimum
5. **Notes:** Rich notes in `interactions.csv` help detect funnel signals

### Common Issues:

❌ **Multiple date formats:** "01/15/2024", "2024-01-15", "Jan 15 2024"
✅ **Use:** "2024-01-15" everywhere

❌ **Messy company names:** "Acme Corp", "ACME", "Acme Corporation"
✅ **Standardize:** Pick one canonical name

❌ **Missing emails:** Some SPOCs without email addresses
✅ **Critical:** Email is the primary deduplication key

❌ **Inactive SPOCs included:** People who left companies years ago
✅ **Mark explicitly:** Use `is_active` column to track this

---

## Next Steps

1. **Export your data** using the SQL queries above
2. **Save CSVs** to `data/raw/` in the project folder
3. **Export your email archive** as .mbox
4. **Run the pipeline:** `python scripts/orchestrator.py`

If your database schema is different, you can:
- Edit the `scripts/parsers/csv_processor.py` to match your schema
- Or rename your columns to match the expected format
