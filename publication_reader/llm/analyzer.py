"""Ollama LLM integration for publication analysis."""

import re
import ollama
from typing import Dict, Any, Tuple, Optional
import os


class OllamaAnalyzer:
    """Publication analyzer using Ollama LLM."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the analyzer.
        
        Args:
            config: Ollama configuration dictionary
        """
        self.model = config.get('model', 'llama3.2')
        self.host = config.get('host', 'http://localhost:11434')
        self.relevance_prompt = config.get('relevance_prompt', '')
        self.summary_prompt = config.get('summary_prompt', '')
        
        # Set environment variable for Ollama host
        os.environ['OLLAMA_HOST'] = self.host
    
    def analyze_publication(self, publication: Dict[str, Any]) -> Tuple[int, str]:
        """Analyze a publication to determine relevance and generate a summary.
        
        Args:
            publication: Publication dictionary with title and abstract
            
        Returns:
            Tuple of (relevance_score, summary)
        """
        title = publication.get('title', '')
        abstract = publication.get('abstract', '')
        journal = publication.get('journal', '')
        
        if not title or not abstract:
            return 0, "Insufficient data for analysis"
        
        # Get relevance score
        relevance_score, relevance_text = self._analyze_relevance(title, abstract)
        
        # Always generate a summary, but with different detail level based on relevance
        if relevance_score >= 7:  # Highly relevant
            summary = self._generate_summary(title, abstract, journal, relevance_score, relevance_text)
        elif relevance_score >= 5:  # Moderately relevant
            summary = self._generate_summary(title, abstract, journal, relevance_score, relevance_text, detailed=False)
        else:  # Low relevance
            summary = f"## Low Relevance Analysis\n\nThis publication has a relevance score of {relevance_score}/10.\n\n{relevance_text}"
        
        return relevance_score, summary
    
    def _analyze_relevance(self, title: str, abstract: str) -> Tuple[int, str]:
        """Determine the relevance of a publication.
        
        Args:
            title: Publication title
            abstract: Publication abstract
            
        Returns:
            Tuple of (relevance_score, explanation)
        """
        try:
            prompt = self._create_relevance_prompt(title, abstract)
            response = ollama.chat(
                model=self.model, 
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            # Extract the response text
            response_text = response['message']['content']
            
            # Extract relevance score (assuming format like "Relevance: 7/10")
            score = self._extract_relevance_score(response_text)
            
            return score, response_text
        except Exception as e:
            print(f"Error analyzing relevance: {str(e)}")
            return 0, f"Error analyzing relevance: {str(e)}"
    
    def _generate_summary(self, title: str, abstract: str, journal: str = '', relevance_score: int = 0, 
                       relevance_text: str = '', detailed: bool = True) -> str:
        """Generate a summary for a publication with relevance explanation.
        
        Args:
            title: Publication title
            abstract: Publication abstract
            journal: Publication journal name
            relevance_score: Relevance score (0-10)
            relevance_text: Relevance explanation from LLM
            detailed: Whether to generate a detailed summary (True) or brief summary (False)
            
        Returns:
            Formatted summary text with markdown formatting
        """
        try:
            # Create a more comprehensive prompt that incorporates the relevance information
            if detailed:
                prompt = f"{self.summary_prompt}\n\n"
                prompt += f"Journal: {journal}\n"
                prompt += f"Title: {title}\n"
                prompt += f"Abstract: {abstract}\n\n"
                prompt += f"This publication has been rated {relevance_score}/10 for relevance.\n"
                prompt += f"Structure your response in markdown format with the following sections:\n"
                prompt += f"1. ## Summary - A concise summary of key findings and methodology\n"
                prompt += f"2. ## Relevance - Why this publication is relevant to our interests\n"
                prompt += f"Keep each section brief but informative."
            else:
                # Simpler prompt for less relevant publications
                prompt = f"Briefly summarize the following publication and explain why it received a relevance score of {relevance_score}/10.\n\n"
                prompt += f"Title: {title}\n"
                prompt += f"Abstract: {abstract}\n"
            
            response = ollama.chat(
                model=self.model, 
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            summary_text = response['message']['content']
            
            # Format the response with markdown headers if they don't exist
            if detailed and "##" not in summary_text:
                parts = summary_text.split('\n\n', 1)
                if len(parts) > 1:
                    summary_text = f"## Summary\n\n{parts[0]}\n\n## Relevance\n\n{parts[1]}"
                else:
                    summary_text = f"## Analysis\n\n{summary_text}"
            
            return summary_text
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return f"## Error\n\nError generating summary: {str(e)}"
    
    def _create_relevance_prompt(self, title: str, abstract: str) -> str:
        """Create a prompt for relevance analysis.
        
        Args:
            title: Publication title
            abstract: Publication abstract
            
        Returns:
            Formatted prompt
        """
        base_prompt = self.relevance_prompt or (
            "Analyze this scientific publication and determine if it's relevant. "
            "Rate relevance from 0-10 and explain why."
        )
        
        return f"{base_prompt}\n\nTitle: {title}\n\nAbstract: {abstract}\n\n"
    
    def _create_summary_prompt(self, title: str, abstract: str) -> str:
        """Create a prompt for summary generation.
        
        Args:
            title: Publication title
            abstract: Publication abstract
            
        Returns:
            Formatted prompt
        """
        base_prompt = self.summary_prompt or (
            "Create a concise summary of this scientific publication highlighting key findings and methodology."
        )
        
        return f"{base_prompt}\n\nTitle: {title}\n\nAbstract: {abstract}\n\n"
    
    def _extract_relevance_score(self, text: str) -> int:
        """Extract relevance score from LLM response.
        
        Args:
            text: Response text from LLM
            
        Returns:
            Relevance score (0-10)
        """
        # Look for patterns like "Relevance: 7/10" or "Score: 7" or just "7/10"
        patterns = [
            r'relevance:?\s*(\d+)(?:/10)?',
            r'score:?\s*(\d+)(?:/10)?',
            r'rating:?\s*(\d+)(?:/10)?',
            r'(\d+)/10',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    score = int(match.group(1))
                    # Ensure score is between 0 and 10
                    return max(0, min(score, 10))
                except (ValueError, IndexError):
                    pass
        
        # If no score found, estimate based on positive/negative language
        positive_terms = ['relevant', 'interesting', 'important', 'significant', 'novel']
        negative_terms = ['irrelevant', 'not relevant', 'unrelated', 'not aligned']
        
        score = 5  # Default neutral score
        
        for term in positive_terms:
            if term in text.lower():
                score += 1
        
        for term in negative_terms:
            if term in text.lower():
                score -= 1
        
        return max(0, min(score, 10))  # Ensure score is between 0 and 10
