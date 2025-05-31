"""Static site generator for publication reader reports."""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

class StaticSiteGenerator:
    """Generate static HTML pages for publication reader reports."""
    
    def __init__(self, reports_path: str, output_path: str):
        """Initialize the static site generator.
        
        Args:
            reports_path: Path to the JSON reports
            output_path: Path where the static site will be generated
        """
        self.reports_path = os.path.expanduser(reports_path)
        self.output_path = os.path.expanduser(output_path)
        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        
    def generate_site(self) -> None:
        """Generate the complete static website."""
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)
        
        # Copy static assets
        self._copy_assets()
        
        # Get all reports
        reports = self._get_reports()
        
        # Generate index page
        self._generate_index_page(reports)
        
        # Generate individual report pages
        for report_date in reports:
            self._generate_report_page(report_date)
            
        print(f"Static site generated at: {self.output_path}")
            
    def _copy_assets(self) -> None:
        """Copy static assets to the output directory."""
        # Create assets directory if it doesn't exist
        assets_output = os.path.join(self.output_path, "assets")
        os.makedirs(assets_output, exist_ok=True)
        
        # Copy CSS file
        css_src = os.path.join(self.assets_dir, "styles.css")
        css_dest = os.path.join(assets_output, "styles.css")
        
        if os.path.exists(css_src):
            shutil.copy2(css_src, css_dest)
        
        # Copy JS file
        js_src = os.path.join(self.assets_dir, "scripts.js")
        js_dest = os.path.join(assets_output, "scripts.js")
        
        if os.path.exists(js_src):
            shutil.copy2(js_src, js_dest)
            
    def _get_reports(self) -> List[str]:
        """Get all available reports.
        
        Returns:
            List of report dates sorted by date (newest first)
        """
        reports = []
        for file in os.listdir(self.reports_path):
            if file.startswith("report_") and file.endswith(".json"):
                date_str = file[7:-5]  # Extract date from filename
                reports.append(date_str)
        
        return sorted(reports, reverse=True)
    
    def _load_report(self, report_date: str) -> Dict[str, Any]:
        """Load a report from disk.
        
        Args:
            report_date: Date string in ISO format (YYYY-MM-DD)
            
        Returns:
            Report data dictionary or empty dict if not found
        """
        report_file = os.path.join(self.reports_path, f"report_{report_date}.json")
        
        if not os.path.exists(report_file):
            return {}
        
        with open(report_file, 'r') as f:
            return json.load(f)
    
    def _generate_index_page(self, report_dates: List[str]) -> None:
        """Generate the index page listing all reports.
        
        Args:
            report_dates: List of report dates
        """
        html = self._get_html_template("index")
        
        # Generate report list HTML
        reports_html = ""
        for date_str in report_dates:
            report = self._load_report(date_str)
            if not report:
                continue
                
            # Format date for display
            try:
                display_date = datetime.fromisoformat(date_str).strftime("%B %d, %Y")
            except ValueError:
                display_date = date_str
                
            pub_count = len(report.get('publications', []))
            
            reports_html += f"""
            <div class="report-card">
                <div class="report-date">{display_date}</div>
                <div class="report-count">{pub_count} publications</div>
                <a href="report_{date_str}.html" class="view-button">View Report</a>
            </div>
            """
        
        # If no reports, show message
        if not reports_html:
            reports_html = """
            <div class="no-reports">
                <p>No reports available yet. Run the publication reader to generate reports.</p>
            </div>
            """
            
        # Replace placeholder with report list
        html = html.replace("{{REPORTS_LIST}}", reports_html)
        
        # Write to file
        with open(os.path.join(self.output_path, "index.html"), "w") as f:
            f.write(html)
    
    def _generate_report_page(self, report_date: str) -> None:
        """Generate a page for a single report.
        
        Args:
            report_date: Date string in ISO format (YYYY-MM-DD)
        """
        report = self._load_report(report_date)
        if not report:
            return
            
        html = self._get_html_template("report")
        
        # Format date for display
        try:
            display_date = datetime.fromisoformat(report_date).strftime("%B %d, %Y")
        except ValueError:
            display_date = report_date
            
        # Replace report date
        html = html.replace("{{REPORT_DATE}}", display_date)
        
        # Replace report summary
        summary = report.get('summary', 'No summary available')
        html = html.replace("{{REPORT_SUMMARY}}", summary)
        
        # Generate publications table
        publications = report.get('publications', [])
        
        if publications:
            pubs_html = """
            <table class="publications-table">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Journal</th>
                        <th>Score</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for i, pub in enumerate(publications):
                title = pub.get('title', 'Untitled')
                journal = pub.get('journal', 'Unknown')
                score = pub.get('relevance_score', 0)
                pub_id = f"pub_{i}"
                
                # Determine score color
                if score >= 8:
                    score_class = "score-high"
                elif score >= 7:
                    score_class = "score-medium"
                else:
                    score_class = "score-low"
                    
                # Create URL link if available
                doi_link = ""
                url = pub.get('url', '')
                if url:
                    doi_link = f'<a href="{url}" target="_blank" class="doi-link">View Paper</a>'
                
                # Prepare summary for details section
                summary = pub.get('llm_summary', 'No summary available')
                abstract = pub.get('abstract', 'No abstract available')
                
                # Create table row
                pubs_html += f"""
                <tr>
                    <td>{title}</td>
                    <td>{journal}</td>
                    <td><span class="{score_class}">{score}/10</span></td>
                    <td>
                        {doi_link}
                        <button class="details-button" onclick="toggleDetails('{pub_id}')">Details</button>
                    </td>
                </tr>
                <tr class="details-row" id="{pub_id}" style="display: none;">
                    <td colspan="4" class="details-cell">
                        <div class="details-content">
                            <h4>AI Assessment</h4>
                            <p>{summary}</p>
                            <h4>Abstract</h4>
                            <p>{abstract}</p>
                        </div>
                    </td>
                </tr>
                """
                
            pubs_html += """
                </tbody>
            </table>
            """
        else:
            pubs_html = """
            <div class="no-publications">
                <p>No publications available in this report.</p>
            </div>
            """
            
        # Replace publications table
        html = html.replace("{{PUBLICATIONS_TABLE}}", pubs_html)
        
        # Write to file
        with open(os.path.join(self.output_path, f"report_{report_date}.html"), "w") as f:
            f.write(html)
    
    def _get_html_template(self, template_name: str) -> str:
        """Get an HTML template.
        
        Args:
            template_name: Name of the template ('index' or 'report')
            
        Returns:
            HTML template as string
        """
        if template_name == "index":
            return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Publication Reader - Reports</title>
    <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
    <header>
        <div class="container">
            <h1>Publication Reader</h1>
            <p>Scientific Publication Reports</p>
        </div>
    </header>
    
    <main class="container">
        <h2>Available Reports</h2>
        
        <div class="reports-grid">
            {{REPORTS_LIST}}
        </div>
    </main>
    
    <footer>
        <div class="container">
            <p>&copy; 2025 Publication Reader</p>
        </div>
    </footer>
    
    <script src="assets/scripts.js"></script>
</body>
</html>"""
        elif template_name == "report":
            return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report - {{REPORT_DATE}} - Publication Reader</title>
    <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
    <header>
        <div class="container">
            <h1>Publication Reader</h1>
            <p>Scientific Publication Reports</p>
        </div>
    </header>
    
    <main class="container">
        <div class="report-header">
            <h2>Report: {{REPORT_DATE}}</h2>
            <a href="index.html" class="back-button">← Back to Reports</a>
        </div>
        
        <div class="report-summary">
            <h3>Summary</h3>
            <p>{{REPORT_SUMMARY}}</p>
        </div>
        
        <div class="publications-section">
            <h3>Publications</h3>
            {{PUBLICATIONS_TABLE}}
        </div>
    </main>
    
    <footer>
        <div class="container">
            <p>&copy; 2025 Publication Reader</p>
        </div>
    </footer>
    
    <script src="assets/scripts.js"></script>
</body>
</html>"""
        else:
            return ""
