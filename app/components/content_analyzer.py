"""
Content analyzer using Google Gemini for the Wayback Ecommerce Chatbot.
"""

import os
import datetime
from typing import Optional, Dict, Any
import google.generativeai as genai

# Change relative imports to absolute imports
from app.utils.cache import cache_result
from app.utils.error_handling import retry_with_exponential_backoff

class ContentAnalyzer:
    """Analyze extracted content using Google Gemini"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = 'gemini-2.5-flash-preview-04-17'):
        """
        Initialize the content analyzer
        
        Args:
            api_key: Google Gemini API key (optional, defaults to environment variable)
            model_name: Gemini model name to use (default: gemini-2.5-flash-preview-04-17)
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Seasonal retail context by month
        self.seasonal_context = {
            'January': 'post-holiday sales and winter promotions',
            'February': 'Valentine\'s Day and early spring transitions',
            'March': 'spring launches and seasonal transitions',
            'April': 'Easter promotions and spring campaigns',
            'May': 'Mother\'s Day and early summer preparations',
            'June': 'summer launches and vacation season',
            'July': 'mid-summer sales and early back-to-school',
            'August': 'back-to-school and end-of-summer sales',
            'September': 'fall launches and fashion week influences',
            'October': 'Halloween and early holiday preparations',
            'November': 'Black Friday, Cyber Monday, and holiday shopping',
            'December': 'holiday gifting and end-of-year sales'
        }
    
    @cache_result(expire_after_days=7)
    @retry_with_exponential_backoff(max_retries=3)
    def analyze_content(self, domain: str, snapshot_date: datetime.date,
                       extracted_content: str, query_context: Optional[str] = None) -> str:
        """
        Analyze extracted content using Google Gemini
        
        Args:
            domain: Domain name of the website
            snapshot_date: Date of the snapshot
            extracted_content: Extracted content as formatted string
            query_context: Original user query for context
            
        Returns:
            Analysis as string
        """
        # Determine the focus of analysis based on query context
        focus_area = "general trading activity"
        if query_context:
            if any(term in query_context.lower() for term in ["promo", "promotion", "offer", "discount", "sale"]):
                focus_area = "promotions and discounts"
            elif any(term in query_context.lower() for term in ["product", "range", "item", "selling"]):
                focus_area = "product range and merchandising"
            elif any(term in query_context.lower() for term in ["delivery", "shipping", "fulfillment"]):
                focus_area = "delivery and shipping offers"
        
        # Create a structured, detailed prompt with clear instructions
        system_prompt = """You are an expert ecommerce trading analyst with deep knowledge of retail strategies, promotions, and merchandising.
        
        Your task is to analyze historical ecommerce website content and provide valuable insights about their trading strategy.
        
        Guidelines for your analysis:
        1. Focus on concrete observations before making interpretations
        2. Identify specific promotional mechanics (e.g., "20% off with code SAVE20" rather than just "discount")
        3. Note price points and thresholds (e.g., "Free shipping on orders over £50")
        4. Identify featured brands, categories, or products and their prominence
        5. Consider seasonal context based on the snapshot date
        6. Format your response with clear sections and bullet points
        7. Be specific and precise - avoid vague statements
        8. Include 3-5 key trading insights that would be valuable to a competitor
        
        Your analysis should be professional, data-driven, and actionable."""
        
        # Create a detailed user prompt with the extracted content
        user_prompt = f"""Analyze this content extracted from {domain}'s homepage from {snapshot_date.strftime('%B %d, %Y')}.
        
        Focus specifically on {focus_area}.
        
        EXTRACTED CONTENT:
        {extracted_content}
        
        Please structure your response as follows:
        
        1. SUMMARY: A 2-3 sentence overview of the main trading strategy
        2. KEY PROMOTIONS: Bullet points of specific offers, discounts, and promotional mechanics
        3. FEATURED PRODUCTS/CATEGORIES: What was being highlighted on the homepage
        4. TRADING INSIGHTS: 3-5 specific observations about their strategy that would be valuable to a competitor
        5. COMPARISON TO INDUSTRY NORMS: How this approach compares to typical ecommerce strategies
        
        Remember to be specific and precise in your analysis."""
        
        # Add seasonal context if available
        month = snapshot_date.strftime('%B')
        if month in self.seasonal_context:
            user_prompt += f"\n\nNote that this snapshot is from {month}, which typically features {self.seasonal_context[month]} in retail."
        
        # Combine system and user prompts for Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Make the API call with Gemini
        response = self.model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,  # Lower temperature for more focused, consistent results
                max_output_tokens=1000,
                top_p=0.95,
            )
        )
        
        # Try to get text using the .text property first (simpler approach)
        try:
            return response.text
        except (ValueError, AttributeError) as e:
            # If that fails, try the more detailed approach
            if not response.candidates:
                raise ValueError("No response candidates generated. Content may have been blocked.")
            
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason == genai.types.FinishReason.SAFETY:
                raise ValueError("Response was blocked due to safety filters.")
            
            if not candidate.content or not candidate.content.parts:
                raise ValueError("No content in response.")
            
            # Extract text from the response
            return candidate.content.parts[0].text