#!/usr/bin/env python3
"""
Simple CRM Web Server using only Python standard library
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import json
import urllib.parse

class CRMHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/' or path == '/index.html':
            self.serve_dashboard()
        elif path == '/contacts':
            self.serve_contacts()
        elif path.startswith('/contact/'):
            email = path.split('/')[-1]
            self.serve_contact_detail(urllib.parse.unquote(email))
        elif path == '/companies':
            self.serve_companies()
        elif path == '/api/contacts':
            self.serve_contacts_json()
        else:
            self.send_error(404)

    def serve_dashboard(self):
        conn = sqlite3.connect('/tmp/crm.db')
        c = conn.cursor()

        total = c.execute('SELECT COUNT(*) FROM contacts').fetchone()[0]
        bottom = c.execute("SELECT COUNT(*) FROM contacts WHERE funnel_stage LIKE 'bottom%'").fetchone()[0]
        middle = c.execute("SELECT COUNT(*) FROM contacts WHERE funnel_stage LIKE 'middle%'").fetchone()[0]

        top_contacts = c.execute('''
            SELECT name, email, company, funnel_stage, priority_score
            FROM contacts
            ORDER BY priority_score DESC
            LIMIT 10
        ''').fetchall()

        conn.close()

        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>TalentXO CRM</title>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, system-ui, sans-serif; background: #f5f7fa; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; }}
        .header h1 {{ font-size: 24px; }}
        .nav {{ background: white; padding: 15px 20px; border-bottom: 1px solid #ddd; }}
        .nav a {{ text-decoration: none; color: #2c3e50; margin-right: 30px; padding: 10px 0; border-bottom: 3px solid transparent; }}
        .nav a:hover, .nav a.active {{ color: #3498db; border-bottom-color: #3498db; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-card h3 {{ font-size: 14px; color: #7f8c8d; margin-bottom: 10px; text-transform: uppercase; }}
        .stat-card .number {{ font-size: 36px; font-weight: 600; color: #2c3e50; }}
        table {{ width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-collapse: collapse; }}
        th {{ text-align: left; padding: 15px; background: #f8f9fa; font-weight: 600; border-bottom: 2px solid #e1e8ed; }}
        td {{ padding: 15px; border-bottom: 1px solid #f1f3f5; }}
        tr:hover {{ background: #f8f9fa; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
        .badge-green {{ background: #d4edda; color: #155724; }}
        .badge-yellow {{ background: #fff3cd; color: #856404; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 TalentXO CRM</h1>
        <p style="opacity: 0.8; margin-top: 5px;">Sales Intelligence & Relationship Management</p>
    </div>

    <div class="nav">
        <a href="/" class="active">Dashboard</a>
        <a href="/contacts">Contacts</a>
        <a href="/companies">Companies</a>
    </div>

    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <h3>Total Contacts</h3>
                <div class="number">{total:,}</div>
            </div>
            <div class="stat-card">
                <h3>Bottom Funnel</h3>
                <div class="number" style="color: #27ae60;">{bottom}</div>
            </div>
            <div class="stat-card">
                <h3>Middle Funnel</h3>
                <div class="number" style="color: #f39c12;">{middle}</div>
            </div>
        </div>

        <h2 style="margin-bottom: 20px; font-size: 20px;">🔥 Top Priority Contacts</h2>
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Company</th>
                    <th>Funnel Stage</th>
                    <th>Priority</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>'''

        for row in top_contacts:
            name, email, company, funnel, score = row
            name = name or "N/A"
            email = email or "no-email@unknown.com"
            company = company or "Unknown"
            funnel = funnel or "unclassified"
            score = score if score is not None else 0
            badge_class = 'badge-green' if 'bottom' in funnel else ('badge-yellow' if 'middle' in funnel else '')
            html += f'''
                <tr>
                    <td><strong>{name}</strong><br><small style="color: #7f8c8d;">{email}</small></td>
                    <td>{company}</td>
                    <td><span class="badge {badge_class}">{funnel}</span></td>
                    <td><strong>{score:.1f}</strong></td>
                    <td><a href="/contact/{urllib.parse.quote(email)}" style="color: #3498db; text-decoration: none;">View →</a></td>
                </tr>'''

        html += '''
            </tbody>
        </table>
    </div>
</body>
</html>'''

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def serve_contacts(self):
        conn = sqlite3.connect('/tmp/crm.db')
        c = conn.cursor()

        contacts = c.execute('''
            SELECT name, email, company, title, funnel_stage, priority_score
            FROM contacts
            ORDER BY priority_score DESC
            LIMIT 100
        ''').fetchall()

        conn.close()

        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Contacts - TalentXO CRM</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, system-ui, sans-serif; background: #f5f7fa; }
        .header { background: #2c3e50; color: white; padding: 20px; }
        .header h1 { font-size: 24px; }
        .nav { background: white; padding: 15px 20px; border-bottom: 1px solid #ddd; }
        .nav a { text-decoration: none; color: #2c3e50; margin-right: 30px; padding: 10px 0; border-bottom: 3px solid transparent; }
        .nav a:hover, .nav a.active { color: #3498db; border-bottom-color: #3498db; }
        .container { max-width: 1400px; margin: 0 auto; padding: 30px 20px; }
        .search { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .search input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        table { width: 100%; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-collapse: collapse; }
        th { text-align: left; padding: 15px; background: #f8f9fa; font-weight: 600; border-bottom: 2px solid #e1e8ed; }
        td { padding: 15px; border-bottom: 1px solid #f1f3f5; }
        tr:hover { background: #f8f9fa; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
        .badge-green { background: #d4edda; color: #155724; }
        .badge-yellow { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 TalentXO CRM</h1>
    </div>

    <div class="nav">
        <a href="/">Dashboard</a>
        <a href="/contacts" class="active">Contacts</a>
        <a href="/companies">Companies</a>
    </div>

    <div class="container">
        <div class="search">
            <input type="text" id="searchBox" placeholder="Search contacts by name, company, or email..." onkeyup="filterTable()">
        </div>

        <table id="contactsTable">
            <thead>
                <tr>
                    <th>Contact</th>
                    <th>Company</th>
                    <th>Title</th>
                    <th>Funnel Stage</th>
                    <th>Priority</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>'''

        for row in contacts:
            name, email, company, title, funnel, score = row
            name = name or "N/A"
            email = email or "no-email@unknown.com"
            company = company or "Unknown"
            title = title or "N/A"
            funnel = funnel or "unclassified"
            score = score if score is not None else 0
            badge_class = 'badge-green' if 'bottom' in funnel else ('badge-yellow' if 'middle' in funnel else '')
            html += f'''
                <tr>
                    <td><strong>{name}</strong><br><small style="color: #7f8c8d;">{email}</small></td>
                    <td>{company}</td>
                    <td>{title}</td>
                    <td><span class="badge {badge_class}">{funnel}</span></td>
                    <td><strong>{score:.1f}</strong></td>
                    <td><a href="/contact/{urllib.parse.quote(email)}" style="color: #3498db; text-decoration: none; font-weight: 600;">View →</a></td>
                </tr>'''

        html += '''
            </tbody>
        </table>
    </div>

    <script>
    function filterTable() {
        const search = document.getElementById('searchBox').value.toLowerCase();
        const table = document.getElementById('contactsTable');
        const rows = table.getElementsByTagName('tr');

        for (let i = 1; i < rows.length; i++) {
            const text = rows[i].textContent.toLowerCase();
            rows[i].style.display = text.includes(search) ? '' : 'none';
        }
    }
    </script>
</body>
</html>'''

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def serve_contact_detail(self, email):
        conn = sqlite3.connect('/tmp/crm.db')
        c = conn.cursor()

        contact = c.execute('SELECT * FROM contacts WHERE email = ?', (email,)).fetchone()

        if not contact:
            self.send_error(404)
            return

        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>{contact[1] or "Contact"} - TalentXO CRM</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, system-ui, sans-serif; background: #f5f7fa; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; }}
        .nav {{ background: white; padding: 15px 20px; border-bottom: 1px solid #ddd; }}
        .nav a {{ text-decoration: none; color: #2c3e50; margin-right: 30px; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 30px 20px; }}
        .profile {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .profile h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .profile .email {{ color: #7f8c8d; margin-bottom: 20px; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 20px; }}
        .info-item {{ padding: 15px; background: #f8f9fa; border-radius: 6px; }}
        .info-item label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; display: block; margin-bottom: 5px; }}
        .info-item value {{ font-size: 16px; color: #2c3e50; font-weight: 600; }}
        .back-btn {{ display: inline-block; padding: 10px 20px; background: #95a5a6; color: white; text-decoration: none; border-radius: 4px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 TalentXO CRM</h1>
    </div>

    <div class="nav">
        <a href="/">Dashboard</a>
        <a href="/contacts">Contacts</a>
        <a href="/companies">Companies</a>
    </div>

    <div class="container">
        <a href="/contacts" class="back-btn">← Back to Contacts</a>

        <div class="profile">
            <h1>{contact[1] or "N/A"}</h1>
            <div class="email">{contact[0]}</div>

            <div class="info-grid">
                <div class="info-item">
                    <label>Company</label>
                    <value>{contact[2] or "Unknown"}</value>
                </div>
                <div class="info-item">
                    <label>Title</label>
                    <value>{contact[3] or "N/A"}</value>
                </div>
                <div class="info-item">
                    <label>Funnel Stage</label>
                    <value>{contact[4]}</value>
                </div>
                <div class="info-item">
                    <label>Priority Score</label>
                    <value>{contact[5]:.1f if contact[5] else 0}</value>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

        conn.close()

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def serve_companies(self):
        conn = sqlite3.connect('/tmp/crm.db')
        c = conn.cursor()

        companies = c.execute('''
            SELECT company_name, total_positions_filled, revenue_generated, client_status
            FROM companies
            ORDER BY total_positions_filled DESC
            LIMIT 100
        ''').fetchall()

        conn.close()

        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Companies - TalentXO CRM</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, system-ui, sans-serif; background: #f5f7fa; }
        .header { background: #2c3e50; color: white; padding: 20px; }
        .nav { background: white; padding: 15px 20px; border-bottom: 1px solid #ddd; }
        .nav a { text-decoration: none; color: #2c3e50; margin-right: 30px; padding: 10px 0; border-bottom: 3px solid transparent; }
        .nav a:hover, .nav a.active { color: #3498db; border-bottom-color: #3498db; }
        .container { max-width: 1400px; margin: 0 auto; padding: 30px 20px; }
        table { width: 100%; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-collapse: collapse; }
        th { text-align: left; padding: 15px; background: #f8f9fa; font-weight: 600; border-bottom: 2px solid #e1e8ed; }
        td { padding: 15px; border-bottom: 1px solid #f1f3f5; }
        tr:hover { background: #f8f9fa; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
        .badge-green { background: #d4edda; color: #155724; }
        .badge-yellow { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 TalentXO CRM</h1>
    </div>

    <div class="nav">
        <a href="/">Dashboard</a>
        <a href="/contacts">Contacts</a>
        <a href="/companies" class="active">Companies</a>
    </div>

    <div class="container">
        <h2 style="margin-bottom: 20px;">Companies</h2>
        <table>
            <thead>
                <tr>
                    <th>Company Name</th>
                    <th>Positions Filled</th>
                    <th>Revenue Generated</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>'''

        for row in companies:
            name, positions, revenue, status = row
            name = name or "Unknown Company"
            positions = positions if positions is not None else 0
            revenue = revenue if revenue is not None else 0
            status = status or "Unknown"
            badge_class = 'badge-green' if status == 'active' else 'badge-yellow'
            html += f'''
                <tr>
                    <td><strong>{name}</strong></td>
                    <td>{positions}</td>
                    <td>${revenue:,.0f}</td>
                    <td><span class="badge {badge_class}">{status}</span></td>
                </tr>'''

        html += '''
            </tbody>
        </table>
    </div>
</body>
</html>'''

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def serve_contacts_json(self):
        conn = sqlite3.connect('/tmp/crm.db')
        c = conn.cursor()

        contacts = c.execute('SELECT email, name, company FROM contacts LIMIT 100').fetchall()

        data = [{'email': r[0], 'name': r[1], 'company': r[2]} for r in contacts]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

        conn.close()

def run_server(port=5000):
    server = HTTPServer(('0.0.0.0', port), CRMHandler)
    print("=" * 80)
    print("🎯 TalentXO CRM - Web Server Started")
    print("=" * 80)
    print(f"\n✅ Access your CRM at: http://localhost:{port}")
    print("\n📊 Features:")
    print("  - Dashboard with key metrics")
    print("  - Searchable contacts database")
    print("  - Company profiles")
    print("  - Contact detail pages")
    print("\nPress CTRL+C to stop the server")
    print("=" * 80)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        server.server_close()

if __name__ == '__main__':
    run_server()
