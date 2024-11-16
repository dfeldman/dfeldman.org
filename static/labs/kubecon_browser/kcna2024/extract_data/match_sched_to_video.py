import json
import sys
from typing import Dict, Tuple, List
import re

def clean_title(title: str) -> str:
    """Clean title for comparison by removing punctuation and extra spaces"""
    # Remove punctuation except hyphens between words
    title = re.sub(r'[^\w\s-]', '', title)
    # Normalize spaces
    title = ' '.join(title.split())
    return title.lower()

def get_first_n_words(text: str, n: int = 5) -> str:
    """Get first N words from text"""
    words = clean_title(text).split()
    return ' '.join(words[:n])

def parse_video_line(line: str) -> Tuple[str, str]:
    """Parse a line from the video file, handling commas in titles"""
    # Find the last comma
    last_comma = line.rstrip().rfind(',')
    if last_comma == -1:
        return None, None
        
    title = line[:last_comma].strip()
    url = line[last_comma + 1:].strip()
    
    return title, url

def load_video_data(video_file: str, n_words: int = 5) -> Dict[str, str]:
    """Load video data and create lookup dictionary based on first N words"""
    video_lookup = {}
    
    with open(video_file, 'r', encoding='utf-8') as f:
        for line in f:
            title, url = parse_video_line(line)
            if title and url:
                # Create lookup key from first N words
                key = get_first_n_words(title, n_words)
                video_lookup[key] = url
    
    return video_lookup

def match_sessions_with_videos(sessions_file: str, video_file: str, n_words: int = 5):
    """Match session data with video URLs"""
    # Load video lookup data
    video_lookup = load_video_data(video_file, n_words)
    
    # Load session data
    with open(sessions_file, 'r', encoding='utf-8') as f:
        sessions = json.load(f)
    
    # Match each session
    matched_count = 0
    for session in sessions:
        if 'title' in session:
            lookup_key = get_first_n_words(session['title'], n_words)
            session['videoUrl'] = video_lookup.get(lookup_key)
            if session['videoUrl']:
                matched_count += 1
    
    # Print matching statistics
    print(f"Matched {matched_count} of {len(sessions)} sessions", file=sys.stderr)
    
    return sessions

def main():
    if len(sys.argv) not in [3, 4]:
        print("Usage: python script.py <sessions_json> <videos_file> [n_words]", file=sys.stderr)
        sys.exit(1)
    
    sessions_file = sys.argv[1]
    video_file = sys.argv[2]
    n_words = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    try:
        # Match sessions with videos
        matched_sessions = match_sessions_with_videos(sessions_file, video_file, n_words)
        
        # Output results as JSON
        json.dump(matched_sessions, sys.stdout, indent=2, ensure_ascii=False)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

