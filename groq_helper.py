import requests
import json
from typing import List, Dict, Any, Optional

def generate_review_summary(hotel_data: Dict[str, Any], api_key: str) -> str:
    """
    Generate a summary of hotel reviews using GROQ API.
    
    Args:
        hotel_data: Dictionary containing hotel information
        api_key: GROQ API key
        
    Returns:
        A summary of hotel reviews
    """
    # If no review data, generate a simulated review
    hotel_name = hotel_data.get('name', 'this hotel')
    hotel_rating = hotel_data.get('rating_normalized', 4.0)
    
    # Construct a prompt for GROQ
    prompt = f"""
    You are an expert hotel analyst. Based on the following hotel information, create a summary of 
    what guests might say in reviews. Be realistic and consider both positives and negatives.
    
    Hotel Name: {hotel_name}
    Rating: {hotel_rating}/5
    Price: {hotel_data.get('price', 'Unknown')}
    Location: {hotel_data.get('location', 'Unknown')}
    Source: {hotel_data.get('source', 'Unknown')}
    
    Generate a concise summary of likely guest reviews in 3-4 sentences. Include common themes about 
    location, service, cleanliness, and value for money. Be realistic based on the rating - higher rated 
    hotels should have more positive reviews, lower rated hotels more negative.
    """
    
    # Make the API call to GROQ
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 200
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result['choices'][0]['message']['content'].strip()
            return summary
        else:
            # Fallback if API call fails
            return f"Review data not available for {hotel_name}. Please check back later."
            
    except Exception as e:
        print(f"Error generating review summary with GROQ: {str(e)}")
        return f"Review data not available for {hotel_name}. Please check back later."

def generate_personalized_recommendation(hotels: List[Dict[str, Any]], preferences: Dict[str, Any], api_key: str) -> str:
    """
    Generate personalized hotel recommendations using GROQ API.
    
    Args:
        hotels: List of hotel dictionaries
        preferences: User preferences dictionary
        api_key: GROQ API key
        
    Returns:
        Personalized recommendation text
    """
    if not hotels or len(hotels) == 0:
        return "No hotels available to make recommendations."
    
    # Extract top 5 hotels to include in prompt
    top_hotels = hotels[:5]
    
    # Create a structured representation of hotels for the prompt
    hotel_descriptions = []
    for i, hotel in enumerate(top_hotels):
        description = f"Hotel {i+1}: {hotel.get('name', 'Unknown')}\n"
        description += f"Rating: {hotel.get('rating_normalized', 0)}/5\n"
        description += f"Price: {hotel.get('price', 'Unknown')}\n"
        description += f"Source: {hotel.get('source', 'Unknown')}\n"
        
        if hotel.get('location'):
            description += f"Location: {hotel.get('location')}\n"
            
        hotel_descriptions.append(description)
    
    hotels_text = "\n".join(hotel_descriptions)
    
    # Extract preferences
    budget = preferences.get('budget', 'moderate')
    priorities = preferences.get('priorities', ['Value for money', 'Location', 'Amenities'])
    priorities_text = ", ".join(priorities)
    
    # Construct prompt for GROQ
    prompt = f"""
    You are an expert hotel concierge. Based on the following hotels and user preferences,
    provide personalized hotel recommendations.
    
    AVAILABLE HOTELS:
    {hotels_text}
    
    USER PREFERENCES:
    - Budget: {budget}
    - Priorities: {priorities_text}
    
    Please recommend the best hotel for this user with a brief explanation (2-3 sentences) 
    about why it's a good match for their preferences. Then suggest a second option as an alternative.
    Keep your response under 150 words total.
    """
    
    # Make the API call to GROQ
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 300
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            recommendation = result['choices'][0]['message']['content'].strip()
            return recommendation
        else:
            return "Unable to generate personalized recommendations at this time."
            
    except Exception as e:
        print(f"Error generating personalized recommendation with GROQ: {str(e)}")
        return "Unable to generate personalized recommendations at this time." 