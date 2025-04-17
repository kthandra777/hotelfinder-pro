# Import tool from crewai.tools if available, otherwise define custom decorator
try:
    from crewai.tools import BaseTool, tool
except ImportError:
    # If tool is not available in crewai.tools, create a simple decorator
    class BaseTool:
        pass
        
    def tool(name):
        def decorator(func):
            func.name = name
            return func
        return decorator

from langchain_core.tools import Tool, StructuredTool
from hotel_search import search_hotels
from browserbase import browserbase
from kayak import kayak_hotels, kayak_hotel_search, tool
from typing import Dict, Optional, List, Any
import streamlit as st
from datetime import date
from crewai import Task, Agent

# Define a BaseTool class if it's not available from crewai
class BaseTool:
    """Simple base tool class for compatibility"""
    pass

# Define tools as LangChain tools
browserbase_tool = StructuredTool.from_function(
    search_hotels,
    name="BrowserBaseSearch",
    description="Search hotels using BrowserBase based on location.",
    input_schema={
        "location": str,
        "check_in_date": str,
        "check_out_date": str,
        "num_adults": int
    }
)

def continue_iteration(response: str) -> bool:
    """
    Determine if the search should continue based on user response.
    
    Args:
        response (str): User's response to continue prompt
        
    Returns:
        bool: True if search should continue, False otherwise
    """
    positive_responses = ['yes', 'y', 'continue', 'proceed', 'go on', 'iterate']
    return response.lower().strip() in positive_responses

# Combine tools into a custom executor
def run_hotel_search(location: str, check_in_date: str = None, check_out_date: str = None, num_adults: int = 2, api_keys: Optional[Dict[str, str]] = None):
    """
    Fast executor to run hotel search.
    
    Args:
        location: Location to search
        check_in_date: Check-in date (YYYY-MM-DD)
        check_out_date: Check-out date (YYYY-MM-DD)
        num_adults: Number of adults
        api_keys: Dictionary containing API keys (BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, GROQ_API_KEY)
    """
    # Run search
    try:
        # Convert API key names if needed for backward compatibility
        search_api_keys = {}
        
        if api_keys:
            # Map new key names to the ones expected by search_hotels
            key_mapping = {
                "BROWSERBASE_API_KEY": "BROWSERBASE_KEY",
                "BROWSERBASE_PROJECT_ID": "BROWSERBASE_PROJECT_ID",
                "GROQ_API_KEY": "GROQ_API_KEY"
            }
            
            for new_key, old_key in key_mapping.items():
                if new_key in api_keys and api_keys[new_key]:
                    search_api_keys[old_key] = api_keys[new_key]
        
        # Run the search with mapped keys
        results = search_hotels(
            location=location,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            num_adults=num_adults,
            api_keys=search_api_keys  # Pass API keys to the search function
        )
        
        # Ensure results is a list of dictionaries
        if not isinstance(results, list):
            return []
            
        # Filter out any non-dictionary items
        filtered_results = []
        for item in results:
            if isinstance(item, dict):
                filtered_results.append(item)
                
        return filtered_results
    except Exception as e:
        print(f"Error in hotel search: {e}")
        return []

# Create a separate function for additional iterations if needed
def iterate_hotel_search(initial_results, location: str, check_in_date: str = None, check_out_date: str = None, num_adults: int = 2, api_keys: Optional[Dict[str, str]] = None):
    """
    Perform additional hotel search iterations if requested.
    
    Args:
        initial_results: Results from the first search
        location: Location to search
        check_in_date: Check-in date (YYYY-MM-DD)
        check_out_date: Check-out date (YYYY-MM-DD)
        num_adults: Number of adults
        api_keys: Dictionary containing API keys (BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, GROQ_API_KEY)
        
    Returns:
        Updated results with any new hotels found
    """
    results = initial_results.copy() if initial_results else []
    
    # Ask if user wants to iterate (for more results)
    response = input("\nWould you like to search for more hotels? (yes/no): ")
    should_continue = continue_iteration(response)
    
    # Convert API key names if needed for backward compatibility
    search_api_keys = {}
    
    if api_keys:
        # Map new key names to the ones expected by search_hotels
        key_mapping = {
            "BROWSERBASE_API_KEY": "BROWSERBASE_KEY",
            "BROWSERBASE_PROJECT_ID": "BROWSERBASE_PROJECT_ID",
            "GROQ_API_KEY": "GROQ_API_KEY"
        }
        
        for new_key, old_key in key_mapping.items():
            if new_key in api_keys and api_keys[new_key]:
                search_api_keys[old_key] = api_keys[new_key]
    
    while should_continue:
        print("Searching for more hotels...")
        more_results = search_hotels(
            location=location,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            num_adults=num_adults,
            api_keys=search_api_keys  # Pass mapped API keys to the search function
        )
        
        if more_results:
            # Add new results that aren't duplicates
            existing_names = {h['name'] for h in results}
            new_hotels = [h for h in more_results if h['name'] not in existing_names]
            
            if new_hotels:
                results.extend(new_hotels)
                print(f"Found {len(new_hotels)} additional hotels!")
            else:
                print("No new hotels found in this iteration.")
                should_continue = False
        else:
            print("No additional hotels found.")
            should_continue = False
        
        if should_continue:
            response = input("\nContinue to iterate for more results? (yes/no): ")
            should_continue = continue_iteration(response)
    
    # Sort final results by rating
    if results:
        results.sort(key=lambda x: (-x.get('rating_normalized', 0), x.get('price_value', float('inf'))))
    
    return results

def summarize_hotels(hotels):
    """
    Summarize hotel results.
    """
    # Input validation - make sure hotels is a list
    if not isinstance(hotels, list):
        return "No hotels found to summarize."
        
    if not hotels:
        return "No hotels found to summarize."
    
    if len(hotels) == 1 and isinstance(hotels[0], dict) and 'error' in hotels[0]:
        return "No hotels found to summarize."
        
    # Include all hotels in the summary - ensure they're dictionaries and have normalized ratings
    valid_hotels = []
    for h in hotels:
        if not isinstance(h, dict):
            continue  # Skip non-dictionary items
            
        # Make sure hotel has a rating_normalized value (default to 3.0 if missing)
        if h.get('rating_normalized') is None:
            h['rating_normalized'] = 3.0
        valid_hotels.append(h)
            
    if not valid_hotels:
        return "No hotels found."

    # Sort by normalized rating (desc)
    sorted_hotels = sorted(valid_hotels, key=lambda x: -x.get('rating_normalized', 0))
    
    top_10 = sorted_hotels[:10]
    
    # Build summary
    summary = f"**Top 10 Hotels (sorted by rating):**\n"
    for idx, h in enumerate(top_10, 1):
        normalized_rating = h.get('rating_normalized', 0)
        price = h.get('price', 'N/A')
        source = h.get('source', '')
        
        # Add rating text
        rating_text = h.get('rating', 'No rating')
        if rating_text == 'No rating' and normalized_rating > 0:
            rating_text = f"{normalized_rating:.1f}/5"
            
        summary += f"{idx}. {h.get('name', 'Unknown Hotel')} | {price} | Rating: {rating_text} | Source: {source}\n"
    
    return summary

def present_hotel_results(hotels):
    """
    Format hotel results for presentation to the user.
    """
    # Input validation - make sure hotels is a list
    if not isinstance(hotels, list):
        return "No hotels found matching your criteria."
        
    if not hotels:
        return "No hotels found matching your criteria."
    
    # Filter to ensure we only have dictionaries
    hotels = [h for h in hotels if isinstance(h, dict)]
    if not hotels:
        return "No valid hotels found matching your criteria."
    
    # Make sure all hotels have rating_normalized
    for hotel in hotels:
        if hotel.get('rating_normalized') is None:
            hotel['rating_normalized'] = 3.0  # Default middle rating
    
    # Sort by rating for better presentation
    sorted_hotels = sorted(hotels, key=lambda x: (-x.get('rating_normalized', 0), x.get('price_value', float('inf'))))
    
    result = "Here are the best hotel options I found:\n\n"
    
    for hotel in sorted_hotels:
        source = hotel.get('source', 'Unknown')
        name = hotel.get('name', 'Unknown Hotel')
        price = hotel.get('price', 'Price not available')
        
        # Use the rating_display field if available, otherwise fall back to other rating fields
        rating_display = hotel.get('rating_display')
        if not rating_display:
            normalized_rating = hotel.get('rating_normalized')
            if normalized_rating:
                original_rating = hotel.get('rating')
                if original_rating:
                    try:
                        rating_display = str(original_rating)
                    except:
                        rating_display = f"{normalized_rating:.1f}/5"
                else:
                    # Only show the computed normalized rating if there's no original rating
                    rating_display = f"{normalized_rating:.1f}/5"
            else:
                rating_display = hotel.get('rating', 'No rating available')
        
        result += f"🏨 {name} ({source})\n"
        result += f"💰 Price: {price}\n"
        if rating_display != 'No rating available':
            result += f"⭐ Rating: {rating_display}\n"
        if hotel.get('location'):
            result += f"📍 Location: {hotel['location']}\n"
        result += "\n"
    
    return result

def load_llm():
    """Load and return a simple LLM implementation without using crewai"""
    try:
        # Return a dictionary with dummy functions
        return {
            "generate_review_summary": lambda *args, **kwargs: "Review summary not available.",
            "generate_personalized_recommendation": lambda *args, **kwargs: "Personalized recommendation not available.",
            "instance": None
        }
    except Exception as e:
        print(f"Error loading LLM: {e}")
        # Return None, but the UI should handle this case
        return {
            "generate_review_summary": lambda *args, **kwargs: "Review summary not available.",
            "generate_personalized_recommendation": lambda *args, **kwargs: "Personalized recommendation not available.",
            "instance": None
        }

# Create CrewAI tools using the @tool decorator
@tool("KayakHotelSearch")
def kayak_search_tool(location: str, check_in_date: str, check_out_date: str, num_adults: int = 2):
    """Search for hotels on Kayak based on location and dates"""
    url = kayak_hotel_search(location, check_in_date, check_out_date, num_adults)
    print(f"Generated URL for Kayak: {url}")
    return kayak_hotels(location, check_in_date, check_out_date, num_adults)

@tool("BrowserbaseSearch")
def browserbase_search_tool(url: str, options: Optional[Dict[str, Any]] = None):
    """Use Browserbase to navigate to a URL and extract data"""
    return browserbase(url, options)

# Initialize agents with proper tools
def create_hotels_agent():
    """Create and return the hotels agent with proper error handling"""
    llm_result = load_llm()
    if llm_result.get("instance") is None:
        # Return a minimal agent configuration that won't cause errors
        return Agent(
            role="Hotels",
            goal="Search hotels",
            backstory="I am an agent that can search for hotels and find the best accommodations.",
            tools=[kayak_search_tool, browserbase_search_tool],
            allow_delegation=False,
            verbose=True
        )
    return Agent(
        role="Hotels",
        goal="Search hotels",
        backstory="I am an agent that can search for hotels and find the best accommodations.",
        tools=[kayak_search_tool, browserbase_search_tool],
        allow_delegation=False,
        llm=llm_result["instance"],
    )

def create_summarize_agent():
    """Create and return the summarize agent with proper error handling"""
    llm_result = load_llm()
    if llm_result.get("instance") is None:
        # Return a minimal agent configuration that won't cause errors
        return Agent(
            role="Summarize",
            goal="Summarize hotel information",
            backstory="I am an agent that can summarize hotel details and amenities.",
            allow_delegation=False,
            verbose=True
        )
    return Agent(
        role="Summarize",
        goal="Summarize hotel information",
        backstory="I am an agent that can summarize hotel details and amenities.",
        allow_delegation=False,
        llm=llm_result["instance"],
    )

# Create the agents
hotels_agent = create_hotels_agent()
summarize_agent = create_summarize_agent()

output_search_example = """
Here are our top 5 hotels in New York for September 21-22, 2024:
1. Hilton Times Square:
   - Rating: 4.5/5
   - Price: $299/night
   - Location: Times Square
   - Amenities: Pool, Spa, Restaurant
   - Booking: https://www.kayak.com/hotels/hilton-times-square
"""

search_task = Task(
    description=(
        "Search hotels according to criteria {request}. Current year: {current_year}"
    ),
    expected_output=output_search_example,
    agent=hotels_agent,
)

# Streamlit UI setup
def setup_streamlit_ui():
    # Set the title of the application
    st.title("Best Hotel Finder")

    # Sidebar for API Key Inputs
    st.sidebar.header("API Key Settings")
    browserbase_key = st.sidebar.text_input("BrowserBase API Key", type="password")
    browserbase_project_id = st.sidebar.text_input("BrowserBase Project ID", type="password")
    groq_key = st.sidebar.text_input("GROQ API Key", type="password")

    # User inputs
    location = st.text_input("Enter location:", key="location_input")
    num_adults = st.number_input("Number of adults:", min_value=1, value=2, key="num_adults_input")

    # Add date fields for check-in and check-out
    check_in_date = st.date_input("Check-in date:", min_value=date.today(), key="check_in_input")
    check_out_date = st.date_input("Check-out date:", min_value=check_in_date, key="check_out_input")

    # Button to find hotels
    if st.button("Find Hotels", key="find_hotels_button"):
        if location and check_in_date and check_out_date:
            # Check if API keys are provided
            if not (browserbase_key and browserbase_project_id and groq_key):
                st.warning("Some API keys are missing. Will use mock data where possible.")
                # Continue anyway since we've updated code to use mock data

            # Format dates as strings
            check_in_str = check_in_date.strftime("%Y-%m-%d")
            check_out_str = check_out_date.strftime("%Y-%m-%d")
            
            with st.spinner("Searching for hotels..."):
                # Use the custom function to find hotels
                results = run_hotel_search(
                    location=location,
                    check_in_date=check_in_str,
                    check_out_date=check_out_str,
                    num_adults=num_adults,
                    api_keys={
                        "BROWSERBASE_KEY": browserbase_key,
                        "BROWSERBASE_PROJECT_ID": browserbase_project_id,
                        "GROQ_API_KEY": groq_key
                    }
                )
            
            # Display summary of results
            kayak_count = len([h for h in results if h.get('source') == 'Kayak'])
            booking_count = len([h for h in results if h.get('source') == 'Booking.com'])
            st.write(f"Found {len(results)} hotels: {kayak_count} from Kayak and {booking_count} from Booking.com")
            
            st.write("### Top Hotel Results:")
            
            # Filter and sort by rating only - ensure we have both Kayak and Booking.com results
            valid_hotels = []
            for h in results:
                if h.get('rating') or h.get('rating_normalized'):
                    # Ensure every hotel has a 'rating_num' for sorting
                    if h.get('rating_normalized'):
                        h['rating_num'] = h['rating_normalized']
                    else:
                        # Extract numeric rating from string (e.g. "8.5 Excellent" -> 8.5)
                        import re
                        rating_text = str(h.get('rating', '0'))
                        match = re.search(r"(\d+\.?\d*)", rating_text)
                        h['rating_num'] = float(match.group(1)) if match else 0
                        
                        # Normalize to 5-star scale if it's from Booking.com (which uses 10-point scale)
                        if h.get('source') == 'Booking.com' and h['rating_num'] > 5:
                            h['rating_num'] = h['rating_num'] / 2
                    
                    valid_hotels.append(h)
            
            sorted_hotels = sorted(valid_hotels, key=lambda x: (-x.get('rating_num', 0), x.get('price_value', float('inf'))))
            top_hotels = sorted_hotels[:10]
            
            # Create tabs for Kayak and Booking.com results
            all_tab, kayak_tab, booking_tab = st.tabs(["All Hotels", "Kayak", "Booking.com"])
            
            with all_tab:
                display_hotels(top_hotels)
                
            with kayak_tab:
                kayak_hotels = [h for h in sorted_hotels if h.get('source') == 'Kayak']
                if kayak_hotels:
                    display_hotels(kayak_hotels[:10])
                else:
                    st.info("No Kayak hotel results found.")
                    
            with booking_tab:
                booking_hotels = [h for h in sorted_hotels if h.get('source') == 'Booking.com']
                if booking_hotels:
                    display_hotels(booking_hotels[:10])
                else:
                    st.info("No Booking.com hotel results found.")
        else:
            st.error("Please enter all required fields.")

def display_hotels(hotels):
    """Display hotels in Streamlit UI"""
    for hotel in hotels:
        st.write(f"- **{hotel['name']}**")
        if hotel.get('price'):
            st.write(f"  Price: {hotel['price']}")
        if hotel.get('rating'):
            rating_display = hotel['rating']
            if hotel.get('source') == 'Booking.com' and hotel.get('rating_num'):
                st.write(f"  Rating: {rating_display} ({hotel['rating_num']:.1f}/5 normalized)")
            else:
                st.write(f"  Rating: {rating_display}")
        elif hotel.get('rating_normalized'):
            st.write(f"  Rating: {hotel['rating_normalized']:.1f}/5")
        if hotel.get('stars'):
            st.write(f"  Stars: {hotel['stars']}⭐")
        if hotel.get('location'):
            st.write(f"  Area: {hotel['location']}")
        if hotel.get('booking_link'):
            st.write(f"  [Book Now]({hotel['booking_link']})")
        if hotel.get('source'):
            st.write(f"  Source: {hotel['source']}")
        st.write("")  # Add a blank line between hotels