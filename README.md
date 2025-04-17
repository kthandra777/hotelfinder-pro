# HotelFinder Pro

A Streamlit application that uses AI agents to find the best hotel deals across multiple booking platforms.

![HotelFinder Pro](static/hotel_finder_banner.png)

## Features

- 🏨 Search hotels by location, dates, and number of guests
- 🔄 Combines results from multiple sources (Kayak, Booking.com)
- ⭐ Normalizes ratings and prices for easy comparison
- 🤖 AI-powered summaries and recommendations
- 📋 View hotels in organized tabs by source

## Demo

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hotelfinderpro.streamlit.app/)

## Architecture

The application is built with a modular architecture designed for maintainability and extensibility:

- `ui.py`: Streamlit user interface
- `agents.py`: AI agent definitions and Streamlit UI setup
- `hotel_search.py`: Core search functionality across multiple providers
- `kayak.py`: Kayak-specific functionality
- `browserbase.py`: Interface with BrowserBase API for web scraping
- `groq_helper.py`: Groq LLM integration for AI summaries

## Getting Started

### Prerequisites

- Python 3.8+
- API keys for:
  - BrowserBase (for web scraping)
  - Groq (for LLM functionality)

### Installation

1. Clone this repository
   ```bash
   git clone https://github.com/yourusername/hotelfinder-pro.git
   cd hotelfinder-pro
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Mac/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables by creating a `.env` file:
   ```
   BROWSERBASE_API_KEY=your_browserbase_api_key
   BROWSERBASE_PROJECT_ID=your_browserbase_project_id
   GROQ_API_KEY=your_groq_api_key
   ```

### Running the Application

You can run the application in two ways:

1. Using Streamlit directly:
   ```bash
   streamlit run ui.py
   ```

2. Using the Python wrapper:
   ```bash
   python app.py
   ```

## Usage

1. Enter your API keys in the sidebar (or set them in the .env file)
2. Enter your search criteria:
   - Location (city, region, or country)
   - Check-in and check-out dates
   - Number of adults
3. Click "Search Hotels" to see results
4. View results in the "All Hotels", "Kayak", or "Booking.com" tabs

## Development

### Adding New Hotel Providers

To add a new hotel provider:

1. Create a new file similar to `kayak.py` with provider-specific functionality
2. Add the necessary search function to `hotel_search.py`
3. Update the UI in `agents.py` to display the new provider's results

### Running Tests

```bash
pytest tests/
```

## Deployment

### Deploying to Streamlit Cloud

1. Push your code to GitHub
2. Connect your repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Set the required secrets in the Streamlit Cloud dashboard
4. Deploy the application

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Streamlit](https://streamlit.io/)
- [CrewAI](https://github.com/joaomdmoura/crewAI)
- [BrowserBase](https://browserbase.io/)
- [Groq](https://groq.com/)