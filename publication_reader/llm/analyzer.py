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
        relevance_score, relevance_text = self._determine_relevance(title, abstract)
        
        # Always generate a summary, but with different detail level based on relevance
        if relevance_score >= 7:  # Highly relevant
            summary = self._generate_summary(title, abstract, journal, relevance_score, relevance_text)
        elif relevance_score >= 5:  # Moderately relevant
            summary = self._generate_summary(title, abstract, journal, relevance_score, relevance_text, detailed=False)
        else:  # Low relevance
            summary = f"## Low Relevance Analysis\n\nThis publication has a relevance score of {relevance_score}/10.\n\n{relevance_text}"
        
        return relevance_score, summary
    
    def _determine_relevance(self, title: str, abstract: str) -> Tuple[int, str]:
        """Determine the relevance of a publication to the user's interests.
        
        Args:
            title: Publication title
            abstract: Publication abstract
            
        Returns:
            Tuple of (relevance_score, explanation)
        """
        try:
            # Define the analysis prompt - this already includes interests from config file
            prompt = self._create_relevance_prompt(title, abstract)
            
            # Print prompt for debugging with nice formatting
            print("\n" + "="*80)
            print(f"[DEBUG] PROMPT SENT TO LLM:")
            print("-"*80)
            print(f"{prompt}")
            print("="*80)
            
            # Call the LLM
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
            
            # Print response for debugging with nice formatting
            print("\n" + "="*80)
            print(f"[DEBUG] LLM RESPONSE:")
            print("-"*80)
            print(f"{response_text}")
            print("="*80)
            
            # Try multiple patterns to extract relevance score (models format scores differently)
            # First try the standard N/10 format
            relevance_match = re.search(r'\b([0-9]|10)\s*\/\s*10\b', response_text)
            
            # If that fails, try other common formats
            if not relevance_match:
                # Try formats like "Relevance: 7" or "Score: 7" or "Rating: 7"
                relevance_match = re.search(r'(?:relevance|score|rating)\s*(?:is|:)\s*([0-9]|10)\b', 
                                          response_text, re.IGNORECASE)
            
            # Try a simple number after the word "score" or similar
            if not relevance_match:
                relevance_match = re.search(r'(?:score|rating|relevance).*?([0-9]|10)\b', 
                                          response_text, re.IGNORECASE)
                
            # Last resort - just find any number between 0-10 
            if not relevance_match:
                relevance_match = re.search(r'\b([0-9]|10)\b', response_text)
            
            # Print relevance match details with nice formatting
            if relevance_match:
                print(f"\n[DEBUG] RELEVANCE MATCH: Score {relevance_match.group(1)}/10")
                print(f"        Pattern matched: '{relevance_match.group(0)}'")
                print(f"        Match position: characters {relevance_match.span()[0]}-{relevance_match.span()[1]}")
            else:
                print("\n[DEBUG] NO RELEVANCE MATCH FOUND - defaulting to 0/10")
            
            # Use the first captured group as the relevance score
            relevance_score = int(relevance_match.group(1)) if relevance_match else 0
            
            # Extract the explanation
            explanation_match = re.search(r'(?:explanation|because|as)[:.]?\s*(.+)', 
                                        response_text, re.IGNORECASE | re.DOTALL)
            explanation = explanation_match.group(1).strip() if explanation_match else ""
            
            print(f"\n[DEBUG] FINAL RELEVANCE SCORE: {relevance_score}/10")

            
            return relevance_score, explanation
        
        except Exception as e:
            print(f"Error determining relevance: {str(e)}")
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
            # Create a prompt that enforces very concise output (1-2 sentences)
            prompt = f"{self.summary_prompt}\n\n"
            prompt += f"Journal: {journal}\n"
            prompt += f"Title: {title}\n"
            prompt += f"Abstract: {abstract}\n\n"
            prompt += f"This publication has been rated {relevance_score}/10 for relevance.\n\n"
            prompt += f"IMPORTANT: Be EXTREMELY concise. Limit your entire response to 1-2 sentences total.\n"
            prompt += f"Just provide a single concise statement about what the paper does.\n"
            
            response = ollama.chat(
                model=self.model, 
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            # Get the raw summary without truncation
            summary_text = response['message']['content'].strip()

            print(f"[DEBUG] LLM SUMMARY:")
            print("-"*80)
            print(f"{summary_text}")
            print("="*80)

            return summary_text
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
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
