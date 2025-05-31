"""Report generator for publication summaries."""

import os
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown


class ReportGenerator:
    """Generator for daily publication reports."""
    
    def __init__(self, reports_path: str, min_relevance: int = 7):
        """Initialize the report generator.
        
        Args:
            reports_path: Path to store report files
            min_relevance: Minimum relevance score threshold (0-10)
        """
        self.reports_path = os.path.expanduser(reports_path)
        os.makedirs(self.reports_path, exist_ok=True)
        self.console = Console()
        self.min_relevance = min_relevance
    
    def generate_daily_report(self, publications: List[Dict[str, Any]], date_str: str) -> Dict[str, Any]:
        """Generate a daily report for a list of publications.
        
        Args:
            publications: List of publication dictionaries
            date_str: Date string in ISO format (YYYY-MM-DD)
            
        Returns:
            Report dictionary
        """
        # Filter out publications with low relevance scores
        relevant_publications = [p for p in publications if p.get('relevance_score', 0) >= self.min_relevance]
        
        # Sort publications by relevance score (highest first)
        relevant_publications.sort(key=lambda p: p.get('relevance_score', 0), reverse=True)
        
        # Generate report summary - just a simple overview without detailed publication info
        if relevant_publications:
            summary = f"Found {len(relevant_publications)} publications with relevance score >= {self.min_relevance} for {date_str}."
            
            # Add publication count by relevance band
            high_relevance = len([p for p in relevant_publications if p.get('relevance_score', 0) >= 8])
            medium_relevance = len([p for p in relevant_publications if 7 <= p.get('relevance_score', 0) < 8])
            
            if high_relevance > 0:
                summary += f"\n\n{high_relevance} publications have high relevance (8-10)."
            if medium_relevance > 0:
                summary += f"\n{medium_relevance} publications have medium relevance (7)."
            
            # Add top fields/journals if available
            journals = {}
            for pub in relevant_publications:
                journal = pub.get('journal', 'Unknown')
                journals[journal] = journals.get(journal, 0) + 1
            
            if journals:
                top_journals = sorted(journals.items(), key=lambda x: x[1], reverse=True)[:3]
                if top_journals:
                    summary += "\n\nTop journals: " + ", ".join([f"{j} ({c})" for j, c in top_journals])
        else:
            summary = f"No publications with relevance score >= {self.min_relevance} found for {date_str}.\n\n" + \
                     f"Consider adjusting the minimum relevance threshold in config.yaml if needed."
        
        # Create the report dictionary
        report = {
            'date': date_str,
            'summary': summary,
            'publications': relevant_publications
        }
        
        # Save the report to a file
        self._save_report(date_str, relevant_publications, summary)
        
        return report
    
    def _save_report(self, report_date: str, publications: List[Dict[str, Any]], summary: str) -> None:
        """Save a report to disk.
        
        Args:
            report_date: Date string in ISO format (YYYY-MM-DD)
            publications: List of publication dictionaries
            summary: Report summary text
        """
        report_file = os.path.join(self.reports_path, f"report_{report_date}.json")
        
        report_data = {
            "date": report_date,
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "publications": publications
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
    
    def get_report(self, report_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a previously generated report.
        
        Args:
            report_date: Date string in ISO format (YYYY-MM-DD)
            
        Returns:
            Report data dictionary or None if not found
        """
        if not report_date:
            report_date = datetime.now().strftime('%Y-%m-%d')
        
        report_file = os.path.join(self.reports_path, f"report_{report_date}.json")
        
        if not os.path.exists(report_file):
            return None
        
        with open(report_file, 'r') as f:
            return json.load(f)
    
    def display_report(self, report_date: Optional[str] = None) -> None:
        """Display a report in the terminal.
        
        Args:
            report_date: Date string in ISO format (YYYY-MM-DD)
        """
        if not report_date:
            report_date = datetime.now().strftime('%Y-%m-%d')
        
        report = self.get_report(report_date)
        
        if not report:
            self.console.print(f"[bold red]No report found for {report_date}[/bold red]")
            return
        
        # Display header with basic information
        self.console.print(Panel(
            f"[bold]Publication Report for {report_date}[/bold]",
            title="Report Date",
            expand=False
        ))
        
        # Display detailed publications table first
        table = Table(title=f"Relevant Publications ({report_date}, Relevance >= {self.min_relevance})")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Journal", style="cyan", width=15)
        table.add_column("Title", style="green")
        table.add_column("Relevance", justify="center", style="magenta", width=10)
        
        # Count relevant publications for display
        relevant_count = 0
        relevant_pubs = []
        
        for pub in report.get('publications', []):
            relevance = pub.get('relevance_score', 0)
            if relevance >= self.min_relevance:  # Only show publications above threshold
                relevant_count += 1
                relevant_pubs.append(pub)
                table.add_row(
                    str(pub.get('id', '')),
                    pub.get('journal', ''),
                    pub.get('title', ''),
                    f"{relevance}/10"
                )
        
        if relevant_count > 0:
            self.console.print(table)
            
            # Create a consolidated summary of all relevant publications
            self.console.print("\n[bold]Publication Summaries:[/bold]")
            
            # Create a consolidated markdown content with better formatting
            consolidated_summary = "## Relevant Publications Summary\n\n"
            
            # Sort publications by relevance score (highest first)
            sorted_pubs = sorted(relevant_pubs, key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            for pub in sorted_pubs:
                pub_id = pub.get('id', '')
                title = pub.get('title', 'Untitled')
                relevance = pub.get('relevance_score', 0)
                url = pub.get('url', '')
                summary = pub.get('llm_summary', 'No summary available.')
                journal = pub.get('journal', '')
                
                # Add each publication's info to the consolidated summary with better formatting
                consolidated_summary += f"### {title}\n\n"
                consolidated_summary += f"**ID:** {pub_id} | **Journal:** {journal} | **Relevance:** {relevance}/10\n"
                if url:
                    consolidated_summary += f"**URL:** [{url}]({url})\n\n"
                else:
                    consolidated_summary += "\n\n"
                consolidated_summary += f"{summary}\n\n"
                consolidated_summary += "---\n\n"  # Add a separator between publications
                
            # Display the consolidated summary in a single panel
            self.console.print(Panel(
                Markdown(consolidated_summary),
                expand=False,
                padding=(1, 2)  # Add padding for better readability
            ))
            
            self.console.print(f"\n[bold]To view detailed information about a publication, use:[/bold]")
            self.console.print(f"python -m publication_reader show <ID>")
        else:
            self.console.print(f"[yellow]No publications with relevance score >= {self.min_relevance} found in this report.[/yellow]")
            self.console.print(f"[yellow]Adjust the minimum relevance threshold in config.yaml if needed.[/yellow]")
    
    def list_reports(self) -> List[str]:
        """List all available reports.
        
        Returns:
            List of report dates
        """
        reports = []
        for file in os.listdir(self.reports_path):
            if file.startswith("report_") and file.endswith(".json"):
                date_str = file[7:-5]  # Extract date from filename
                reports.append(date_str)
        
        return sorted(reports, reverse=True)
    
    def display_publication_details(self, publication: Dict[str, Any]) -> None:
        """Display detailed information about a publication.
        
        Args:
            publication: Publication dictionary
        """
        title = publication.get('title', 'Untitled')
        journal = publication.get('journal', '')
        pub_date = publication.get('pub_date', '')
        authors = publication.get('authors', [])
        abstract = publication.get('abstract', '')
        relevance_score = publication.get('relevance_score', 0)
        llm_summary = publication.get('llm_summary', '')
        url = publication.get('url', '')
        
        # Set color based on relevance score
        if relevance_score >= 8:
            score_color = "green"
        elif relevance_score >= self.min_relevance:
            score_color = "yellow"
        else:
            score_color = "red"
        
        # Display warning if below threshold
        if relevance_score < self.min_relevance:
            self.console.print(f"[bold yellow]Warning: This publication has a relevance score of {relevance_score}/10, "
                               f"which is below the minimum threshold of {self.min_relevance}.[/bold yellow]")
        
        # Header panel with basic information including URL
        header_content = f"[bold]{title}[/bold]\n\n"
        header_content += f"Journal: {journal}\n"
        header_content += f"Date: {pub_date}\n"
        header_content += f"Authors: {', '.join(authors)}\n"
        header_content += f"Relevance: [{score_color}]{relevance_score}/10[/{score_color}]\n"
        
        if url:
            header_content += f"URL: [link={url}]{url}[/link]"
        
        self.console.print(Panel(
            header_content,
            title="Publication Details",
            expand=False
        ))
        
        # Abstract panel
        if abstract:
            self.console.print(Panel(
                abstract,
                title="Abstract",
                expand=False
            ))
        
        # LLM summary panel
        if llm_summary:
            self.console.print(Panel(
                llm_summary,
                title="Concise Summary",
                expand=False
            ))
            

        
        # Links and additional information
        self.console.print("\n[bold]Additional Information:[/bold]")
        if publication.get('url'):
            self.console.print(f"[link={publication.get('url')}]View Publication Online[/link]")
        
        self.console.print(f"Publication ID: {publication.get('id')}")
        self.console.print(f"GUID: {publication.get('guid', 'Not available')}[:30]...")
        
        # Threshold information
        if relevance_score < self.min_relevance:
            self.console.print(f"\n[yellow]Note: This publication's relevance score ({relevance_score}) is below the current threshold ({self.min_relevance}).[/yellow]")
            self.console.print(f"[yellow]It will not appear in reports unless you adjust the threshold in the configuration.[/yellow]")
