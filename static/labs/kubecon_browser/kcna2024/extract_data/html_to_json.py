import json
import sys
from bs4 import BeautifulSoup
import re

def extract_speaker_info(speaker_div):
    """Extract speaker information from a speaker div"""
    name = speaker_div.find('h2').get_text(strip=True) if speaker_div.find('h2') else None
    
    # Get avatar URL if it exists
    avatar_img = speaker_div.find('img')
    avatar_url = avatar_img.get('src') if avatar_img else None
    
    # Get role/company
    role_div = speaker_div.find('div', class_='sched-event-details-role-company')
    role = role_div.get_text(strip=True) if role_div else None
    
    # Get bio
    bio_div = speaker_div.find('div', class_='sched-person-session-role')
    bio = bio_div.get_text(strip=True) if bio_div else None
    
    return {
        "name": name,
        "avatar_url": avatar_url,
        "role": role,
        "bio": bio
    }

def extract_session_info(html_content):
    """Extract session information from HTML content"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Title - from the name class anchor
        title_element = soup.find('a', class_='name')
        title = title_element.get_text(strip=True) if title_element else None
        
        # Abstract - from tip-description div
        abstract_div = soup.find('div', class_='tip-description')
        abstract = abstract_div.get_text(strip=True) if abstract_div else None
        
        # Speaker information
        speakers = []
        speaker_details = []
        speaker_divs = soup.find_all('div', class_='sched-person-session')
        
        for speaker_div in speaker_divs:
            speaker_info = extract_speaker_info(speaker_div)
            if speaker_info["name"]:
                speakers.append(speaker_info["name"])
                speaker_details.append(speaker_info)
        
        # Tags - event type and any other relevant tags
        tags = []
        event_type = soup.find('div', class_='sched-event-type')
        if event_type:
            type_text = event_type.get_text(strip=True)
            if type_text:
                tags.append(type_text)
        
        # Slides URL - look for links containing 'slides'
        slides_url = None
        for link in soup.find_all('a', href=True):
            if 'slides' in link['href'].lower():
                slides_url = link['href']
                break
        
        return {
            "title": title,
            "speakers": speakers,
            "speaker_details": speaker_details,
            "abstract": abstract,
            "tags": tags,
            "slidesUrl": slides_url
        }
        
    except Exception as e:
        print(f"Error processing HTML content: {e}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_json>", file=sys.stderr)
        sys.exit(1)
        
    input_file = sys.argv[1]
    
    try:
        # Read the JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process each entry
        results = []
        for entry in data:
            if entry.get('content'):
                info = extract_session_info(entry['content'])
                if info:
                    info['url'] = entry['url']  # Keep original URL for reference
                    results.append(info)
            
        # Output results as JSON
        json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
        
    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

