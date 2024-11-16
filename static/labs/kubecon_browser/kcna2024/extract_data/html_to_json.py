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

def extract_slides_url(soup):
    """Extract slides URL from HTML content"""
    # Look for PDF files in sched-file divs
    file_div = soup.find('div', class_='sched-file')
    if file_div:
        pdf_link = file_div.find('a', class_='file-uploaded-pdf')
        if pdf_link:
            return pdf_link.get('href')
    
    # Fallback to look for generic presentation/slides links
    for link in soup.find_all('a', href=True):
        href = link['href'].lower()
        if any(x in href for x in ['.pdf', '.pptx', '.ppt', 'slides', 'presentation']):
            return link['href']
    
    return None

def extract_tags(soup):
    """Extract tags from HTML content"""
    tags = []
    
    # Get event type
    event_type = soup.find('div', class_='sched-event-type')
    if event_type:
        # Find all type links and extract their text
        type_links = event_type.find_all('a')
        for link in type_links:
            tag_text = link.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)
    
    # Get experience level
    custom_fields = soup.find('ul', class_='tip-custom-fields')
    if custom_fields:
        for field in custom_fields.find_all('li'):
            if 'Content Experience Level' in field.get_text():
                level = field.find('a')
                if level:
                    tags.append(level.get_text(strip=True))

    seen = set()
    tags = [tag for tag in tags if not (tag in seen or seen.add(tag))]
     
    return tags

def extract_session_info(html_content):
    """Extract session information from HTML content"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Title - from the name class anchor
        title_element = soup.find('a', class_='name')
        title = title_element.get_text(strip=True) if title_element else None
        title = "-".join(title.split("-")[:-1]) # Remove speakers as they are elsewhere     
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
        tags = extract_tags(soup)
 
        # Slides URL - look for links containing 'slides'
        slides_url = extract_slides_url(soup)
        
        return {
            "title": title,
            "speakers": speakers,
            "speaker_details": speaker_details,
            "abstract": abstract,
            "tags": tags,
            "slidesUrl": slides_url,
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

