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
        
        # Generate report summary
        if relevant_publications:
            # Create a clean overview summary
            overview = f"Found {len(relevant_publications)} publications with relevance score >= {self.min_relevance} for {date_str}."
            
            # Create detailed publication summaries
            detailed_summaries = []
            for i, pub in enumerate(relevant_publications, 1):
                title = pub.get('title', 'Untitled')
                journal = pub.get('journal', '')
                relevance = pub.get('relevance_score', 0)
                pub_id = pub.get('id', '')
                
                # Format publication header
                pub_header = f"### {i}. {title}"
                pub_meta = f"**Journal:** {journal} | **Relevance:** {relevance}/10 | **ID:** {pub_id}"
                
                # Include the full LLM summary with proper formatting
                llm_summary = ""
                if pub.get('llm_summary'):
                    # Clean up the LLM summary for markdown display
                    raw_summary = pub.get('llm_summary', '')
                    
                    # Remove duplicate headers if our formatting already adds them
                    if raw_summary.startswith('##'):
                        llm_summary = raw_summary
                    else:
                        llm_summary = f"#### Analysis\n{raw_summary}"
                
                # Combine all elements of this publication's summary
                detailed_summaries.append(f"{pub_header}\n{pub_meta}\n\n{llm_summary}")
            
            # Combine overview and detailed summaries
            summary = f"{overview}\n\n" + "\n\n".join(detailed_summaries)
        else:
            summary = f"No publications with relevance score >= {self.min_relevance} found for {date_str}.\n\n" + \
                     f"Consider adjusting the minimum relevance threshold in config.yaml if needed."
            
            summary += "\n"
        
        # Add a note if there are many publications
        if len(relevant_publications) > 5:
            summary += f"\n\nPlus {len(relevant_publications) - 5} more relevant publications."
        
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
        
        # Display summary as formatted markdown text
        summary_text = report.get('summary', '')
        if summary_text:
            self.console.print("\n[bold]Report Summary:[/bold]")
            self.console.print(Markdown(summary_text))
        
        # Display detailed publications table
        table = Table(title=f"Relevant Publications ({report_date}, Relevance >= {self.min_relevance})")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Journal", style="cyan", width=15)
        table.add_column("Title", style="green")
        table.add_column("Relevance", justify="center", style="magenta", width=10)
        
        # Count relevant publications for display
        relevant_count = 0
        
        for pub in report.get('publications', []):
            relevance = pub.get('relevance_score', 0)
            if relevance >= self.min_relevance:  # Only show publications above threshold
                relevant_count += 1
                table.add_row(
                    str(pub.get('id', '')),
                    pub.get('journal', ''),
                    pub.get('title', ''),
                    f"{relevance}/10"
                )
        
        if relevant_count > 0:
            self.console.print(table)
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
        """Display detailed information for a single publication.
        
        Args:
            publication: Publication dictionary
        """
        self.console.print("\n")
        
        # Header with publication title and metadata
        relevance = publication.get('relevance_score', 0)
        relevance_color = "green" if relevance >= self.min_relevance else "yellow" if relevance >= 5 else "red"
        
        self.console.print(Panel(
            f"[bold]{publication.get('title', 'Untitled')}[/bold]",
            title=f"{publication.get('journal', '')} | Relevance: [{relevance_color}]{relevance}/10[/{relevance_color}] | Date: {publication.get('pub_date', '')[:10]}",
            expand=False
        ))
        
        # Publication abstract
        if publication.get('abstract'):
            self.console.print(Panel(
                publication.get('abstract', ''),
                title="Abstract",
                expand=False
            ))
        
        # LLM analysis with better formatting
        if publication.get('llm_summary'):
            # Format the LLM summary with better markdown rendering
            llm_analysis = publication.get('llm_summary', '')
            
            # Add section headers if they don't exist
            if "## Summary" not in llm_analysis and "## Relevance" not in llm_analysis:
                # Try to structure the analysis with headers
                summary_parts = llm_analysis.split("\n\n", 1)
                if len(summary_parts) > 1:
                    llm_analysis = f"## Summary\n\n{summary_parts[0]}\n\n## Relevance\n\n{summary_parts[1]}"
                else:
                    llm_analysis = f"## Analysis\n\n{llm_analysis}"
            
            self.console.print(Panel(
                Markdown(llm_analysis),
                title=f"LLM Analysis (Relevance Score: {relevance}/10)",
                expand=False
            ))
        
        # Links and additional information
        self.console.print("\n[bold]Additional Information:[/bold]")
        if publication.get('url'):
            self.console.print(f"[link={publication.get('url')}]View Publication Online[/link]")
        
        self.console.print(f"Publication ID: {publication.get('id')}")
        self.console.print(f"GUID: {publication.get('guid', 'Not available')}[:30]...")
        
        # Threshold information
        if relevance < self.min_relevance:
            self.console.print(f"\n[yellow]Note: This publication's relevance score ({relevance}) is below the current threshold ({self.min_relevance}).[/yellow]")
            self.console.print(f"[yellow]It will not appear in reports unless you adjust the threshold in the configuration.[/yellow]")
