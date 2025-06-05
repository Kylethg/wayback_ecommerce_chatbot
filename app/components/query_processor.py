"""
Query processor for the Wayback Ecommerce Chatbot.
"""

import re
import datetime
import os
from dateutil.relativedelta import relativedelta
from typing import Tuple, Optional, Dict, Any
import google.generativeai as genai

class QueryProcessor:
    """Extract information from natural language queries"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = 'gemini-1.5-flash'):
        # Initialize Google Gemini client for date inference
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Common time period patterns
        self.time_patterns = {
            r'last year': relativedelta(years=1),
            r'last month': relativedelta(months=1),
            r'last week': relativedelta(weeks=1),
            r'(\d+) years? ago': lambda m: relativedelta(years=int(m.group(1))),
            r'(\d+) months? ago': lambda m: relativedelta(months=int(m.group(1))),
            r'(\d+) weeks? ago': lambda m: relativedelta(weeks=int(m.group(1))),
            r'(\d+) days? ago': lambda m: relativedelta(days=int(m.group(1))),
            r'last (january|february|march|april|may|june|july|august|september|october|november|december)': 
                lambda m: self._last_month_of_name(m.group(1)),
            r'last (spring|summer|fall|autumn|winter)': 
                lambda m: self._last_season(m.group(1)),
            r'last (black friday|cyber monday|christmas|easter|valentine|halloween)': 
                lambda m: self._last_holiday(m.group(1))
        }
    
    def process_query(self, query: str, custom_date: Optional[datetime.date] = None) -> Dict[str, Any]:
        """
        Extract domain and date information from user query
        
        Args:
            query: User query as string
            custom_date: Optional custom date override (deprecated, will be removed)
            
        Returns:
            Dictionary with extracted information
        """
        result = {
            "domain": None,
            "target_date": None,
            "focus": None,
            "original_query": query
        }
        
        # Extract domain using regex
        domain_match = re.search(r'([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z0-9]{2,}', query)
        if domain_match:
            result["domain"] = domain_match.group(0)
        
        # Determine focus area
        if any(term in query.lower() for term in ["promo", "promotion", "offer", "discount", "sale"]):
            result["focus"] = "promotions"
        elif any(term in query.lower() for term in ["product", "range", "item", "selling"]):
            result["focus"] = "products"
        elif any(term in query.lower() for term in ["delivery", "shipping", "fulfillment"]):
            result["focus"] = "delivery"
        
        # If custom_date is provided, use it (for backward compatibility)
        if custom_date:
            result["target_date"] = custom_date
            return result
            
        # First try to extract date using regex patterns
        date_extracted = False
        for pattern, delta_func in self.time_patterns.items():
            match = re.search(pattern, query.lower())
            if match:
                if callable(delta_func):
                    delta = delta_func(match)
                else:
                    delta = delta_func
                
                result["target_date"] = datetime.date.today() - delta
                date_extracted = True
                break
        
        # If regex patterns didn't work, use LLM to infer the date
        if not date_extracted:
            result["target_date"] = self._infer_date_with_llm(query)
        
        return result
    
    def _infer_date_with_llm(self, query: str) -> datetime.date:
        """
        Use Google Gemini to infer a date from the query
        
        Args:
            query: User query as string
            
        Returns:
            Inferred date as datetime.date object
        """
        # Create a prompt for the LLM
        prompt = f"""
        Extract a specific date or time period from this query: "{query}"
        
        If the query mentions a specific date or time period (like "last Christmas", "summer 2023", "3 months ago", etc.), 
        convert it to an exact date in YYYY-MM-DD format.
        
        If no specific date or time period is mentioned, return "1 year ago" as the default.
        
        Only return the date in YYYY-MM-DD format or the relative time period (like "1 year ago").
        Do not include any other text or explanation.
        """
        
        try:
            # Combine system and user prompts for Gemini
            full_prompt = "You are a date extraction assistant. Extract dates or time periods from queries.\n\n" + prompt
            
            # Call the Gemini API
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for more deterministic results
                    max_output_tokens=50
                )
            )
            
            # Try to get text using the .text property first (simpler approach)
            try:
                date_text = response.text.strip()
            except (ValueError, AttributeError) as e:
                # If that fails, try the more detailed approach
                if not response.candidates:
                    raise ValueError("No response candidates generated. Content may have been blocked.")
                
                candidate = response.candidates[0]
                # Check finish reason using the enum
                if hasattr(candidate, 'finish_reason'):
                    # Import the FinishReason enum from the candidate class
                    FinishReason = candidate.FinishReason
                    if candidate.finish_reason == FinishReason.SAFETY:
                        raise ValueError("Response was blocked due to safety filters.")
                    elif candidate.finish_reason != FinishReason.STOP:
                        raise ValueError(f"Response generation stopped with reason: {candidate.finish_reason}")
                
                if not candidate.content or not candidate.content.parts:
                    raise ValueError("No content in response.")
                
                # Get the response text
                date_text = candidate.content.parts[0].text.strip()
            
            # Check if the response is a relative time period
            if "ago" in date_text.lower():
                # Extract the number and unit
                match = re.search(r'(\d+)\s+(year|month|week|day)s?\s+ago', date_text.lower())
                if match:
                    num = int(match.group(1))
                    unit = match.group(2)
                    
                    # Create a relativedelta based on the unit
                    if unit == "year":
                        delta = relativedelta(years=num)
                    elif unit == "month":
                        delta = relativedelta(months=num)
                    elif unit == "week":
                        delta = relativedelta(weeks=num)
                    elif unit == "day":
                        delta = relativedelta(days=num)
                    
                    # Return the date
                    return datetime.date.today() - delta
            
            # Check if the response is a date in YYYY-MM-DD format
            match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
            if match:
                date_str = match.group(1)
                return datetime.date.fromisoformat(date_str)
            
            # Default to 1 year ago if we couldn't parse the response
            return datetime.date.today() - relativedelta(years=1)
            
        except Exception as e:
            print(f"Error inferring date with LLM: {e}")
            # Default to 1 year ago if there was an error
            return datetime.date.today() - relativedelta(years=1)
    
    def _last_month_of_name(self, month_name: str) -> relativedelta:
        """
        Calculate the date of the last occurrence of a specific month
        
        Args:
            month_name: Name of the month
            
        Returns:
            relativedelta to the last occurrence of that month
        """
        month_names = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]
        target_month = month_names.index(month_name.lower()) + 1
        current_month = datetime.date.today().month
        
        if current_month > target_month:
            # The month has already passed this year, so use this year's occurrence
            return relativedelta(
                year=datetime.date.today().year,
                month=target_month,
                day=15
            ) - datetime.date.today()
        else:
            # The month is either current or hasn't occurred yet this year, so use last year's occurrence
            return relativedelta(
                year=datetime.date.today().year - 1,
                month=target_month,
                day=15
            ) - datetime.date.today()
    
    def _last_season(self, season_name: str) -> relativedelta:
        """
        Calculate the date of the last occurrence of a specific season
        
        Args:
            season_name: Name of the season
            
        Returns:
            relativedelta to the last occurrence of that season
        """
        seasons = {
            'spring': (3, 5),  # March to May
            'summer': (6, 8),  # June to August
            'fall': (9, 11),   # September to November
            'autumn': (9, 11), # September to November
            'winter': (12, 2)  # December to February
        }
        
        start_month, end_month = seasons[season_name.lower()]
        current_month = datetime.date.today().month
        
        # For winter, which spans across years
        if season_name.lower() == 'winter':
            if current_month in [12, 1, 2]:
                # We're currently in winter, so return last winter
                return relativedelta(years=1)
            else:
                # We're not in winter, so return the most recent winter
                return relativedelta(
                    year=datetime.date.today().year,
                    month=1,
                    day=15
                ) - datetime.date.today()
        
        # For other seasons
        if current_month > end_month:
            # The season has already passed this year, so use this year's occurrence
            return relativedelta(
                year=datetime.date.today().year,
                month=start_month,
                day=15
            ) - datetime.date.today()
        else:
            # The season is either current or hasn't occurred yet this year, so use last year's occurrence
            return relativedelta(
                year=datetime.date.today().year - 1,
                month=start_month,
                day=15
            ) - datetime.date.today()
    
    def _last_holiday(self, holiday_name: str) -> relativedelta:
        """
        Calculate the date of the last occurrence of a specific holiday
        
        Args:
            holiday_name: Name of the holiday
            
        Returns:
            relativedelta to the last occurrence of that holiday
        """
        holidays = {
            'black friday': (11, 25),  # November 25th (approximate)
            'cyber monday': (11, 28),  # November 28th (approximate)
            'christmas': (12, 25),     # December 25th
            'easter': None,            # Variable date
            'valentine': (2, 14),      # February 14th
            'halloween': (10, 31)      # October 31st
        }
        
        if holiday_name.lower() == 'easter':
            # Easter requires special calculation as it's a movable feast
            # For simplicity, we'll just return last April
            return self._last_month_of_name('april')
        
        month, day = holidays[holiday_name.lower()]
        current_date = datetime.date.today()
        
        # Create a date for this year's holiday
        this_year_holiday = datetime.date(current_date.year, month, day)
        
        # If the holiday hasn't occurred yet this year, use last year's date
        if current_date < this_year_holiday:
            holiday_date = datetime.date(current_date.year - 1, month, day)
        else:
            # If the holiday has already occurred this year, use this year's date
            holiday_date = this_year_holiday
            
        # Calculate the difference between today and the holiday date
        delta = relativedelta(current_date, holiday_date)
        
        return delta