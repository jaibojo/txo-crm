"""
TalentXO CRM - Web-based Customer Relationship Management System
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import pandas as pd
from pathlib import Path

app = Flask(__name__)
app.config['DATABASE'] = '/tmp/crm.db'

def get_db():
    """Connect to database"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    """Main dashboard"""
    conn = get_db()

    # Get stats
    stats = {
        'total_contacts': conn.execute('SELECT COUNT(*) FROM contacts').fetchone()[0],
        'total_companies': conn.execute('SELECT COUNT(*) FROM companies').fetchone()[0],
        'bottom_funnel': conn.execute("SELECT COUNT(*) FROM contacts WHERE funnel_stage LIKE 'bottom%'").fetchone()[0],
        'middle_funnel': conn.execute("SELECT COUNT(*) FROM contacts WHERE funnel_stage LIKE 'middle%'").fetchone()[0],
        'high_priority': conn.execute("SELECT COUNT(*) FROM contacts WHERE priority_score > 60").fetchone()[0],
    }

    # Get recent contacts
    recent = conn.execute('''
        SELECT email, name, company, funnel_stage, priority_score
        FROM contacts
        ORDER BY priority_score DESC
        LIMIT 10
    ''').fetchall()

    # Get funnel breakdown
    funnel_breakdown = conn.execute('''
        SELECT funnel_stage, COUNT(*) as count
        FROM contacts
        GROUP BY funnel_stage
        ORDER BY count DESC
    ''').fetchall()

    conn.close()

    return render_template('dashboard.html',
                         stats=stats,
                         recent=recent,
                         funnel_breakdown=funnel_breakdown)

@app.route('/contacts')
def contacts():
    """Contacts list"""
    conn = get_db()

    # Get filters
    funnel = request.args.get('funnel', '')
    search = request.args.get('search', '')

    query = 'SELECT * FROM contacts WHERE 1=1'
    params = []

    if funnel:
        query += ' AND funnel_stage = ?'
        params.append(funnel)

    if search:
        query += ' AND (name LIKE ? OR company LIKE ? OR email LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term])

    query += ' ORDER BY priority_score DESC LIMIT 100'

    contacts_list = conn.execute(query, params).fetchall()

    # Get funnel options
    funnels = conn.execute('SELECT DISTINCT funnel_stage FROM contacts').fetchall()

    conn.close()

    return render_template('contacts.html',
                         contacts=contacts_list,
                         funnels=funnels,
                         current_funnel=funnel,
                         current_search=search)

@app.route('/contact/<email>')
def contact_detail(email):
    """Contact detail page"""
    conn = get_db()

    contact = conn.execute('SELECT * FROM contacts WHERE email = ?', (email,)).fetchone()

    if not contact:
        return "Contact not found", 404

    # Get company info
    company = conn.execute('SELECT * FROM companies WHERE name = ?', (contact['company'],)).fetchone()

    conn.close()

    return render_template('contact_detail.html',
                         contact=contact,
                         company=company)

@app.route('/companies')
def companies():
    """Companies list"""
    conn = get_db()

    companies_list = conn.execute('''
        SELECT * FROM companies
        ORDER BY positions DESC
        LIMIT 100
    ''').fetchall()

    conn.close()

    return render_template('companies.html', companies=companies_list)

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard stats"""
    conn = get_db()

    funnel_data = conn.execute('''
        SELECT funnel_stage, COUNT(*) as count
        FROM contacts
        GROUP BY funnel_stage
    ''').fetchall()

    conn.close()

    return jsonify({
        'labels': [row['funnel_stage'] for row in funnel_data],
        'data': [row['count'] for row in funnel_data]
    })

if __name__ == '__main__':
    print("=" * 80)
    print("TalentXO CRM - Starting Web Server")
    print("=" * 80)
    print()
    print("Access your CRM at: http://localhost:5000")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 80)

    app.run(debug=True, host='0.0.0.0', port=5000)
