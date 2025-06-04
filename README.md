# Wayback Machine Ecommerce Insights Chatbot

A Python-based web application that allows ecommerce trading managers to query historical website data from the Wayback Machine. Users can ask natural language questions like "What was competitor.com promoting this time last year?" and receive detailed insights about promotions, trading activity, and marketing strategies.

## Features

- Natural language query interface
- Historical website snapshot retrieval
- Intelligent content extraction from archived HTML
- AI-powered analysis of ecommerce trading strategies
- Formatted insights with actionable recommendations

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your Google Gemini API key: `GEMINI_API_KEY=your_api_key_here`

## Usage

Run the Streamlit application:

```
streamlit run app/main.py
```

Then open your browser to http://localhost:8501

## Project Structure

```
/wayback_ecommerce_chatbot
  /app
    __init__.py
    main.py                # Main Streamlit application
    /components
      __init__.py
      query_processor.py   # Extract info from queries
      wayback_client.py    # Wayback Machine API client
      content_extractor.py # HTML parsing and extraction
      content_analyzer.py  # Google Gemini integration
      response_generator.py # Format responses
    /utils
      __init__.py
      cache.py             # Caching utilities
      error_handling.py    # Error handling utilities
  /static
    styles.css             # Custom CSS
  /tests
    __init__.py
    test_wayback_client.py
    test_content_extractor.py
  .env                     # Environment variables
  requirements.txt         # Dependencies
  README.md                # Documentation
```

## License

MIT