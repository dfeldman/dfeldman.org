import os
import sys
from bs4 import BeautifulSoup

def extract_talk_ids(html_content):
    """
    Extract IDs from <a> elements with class="name"
    
    Args:
        html_content (str): HTML content as string
        
    Returns:
        list: List of talk IDs
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        talk_links = soup.find_all('a', class_='name')
        talk_ids = [link.get('href') for link in talk_links if link.get('id')]
        return talk_ids
    except Exception as e:
        print(f"Error processing HTML content: {e}", file=sys.stderr)
        return []

def process_directory(directory_path):
    """
    Process all files in the given directory and extract talk IDs
    
    Args:
        directory_path (str): Path to directory containing HTML files
        
    Returns:
        list: Combined list of all talk IDs
    """
    all_ids = []
    
    try:
        # Iterate through all files in directory
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            
            # Skip if not a file
            if not os.path.isfile(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                    ids = extract_talk_ids(html_content)
                    all_ids.extend(ids)
            except Exception as e:
                print(f"Error processing file {filename}: {e}", file=sys.stderr)
                continue
                
        return all_ids
        
    except Exception as e:
        print(f"Error accessing directory {directory_path}: {e}", file=sys.stderr)
        return []

def main():
    # Check if directory path was provided
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory_path>", file=sys.stderr)
        sys.exit(1)
        
    directory_path = sys.argv[1]
    
    # Check if directory exists
    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    # Process all files and get IDs
    all_ids = process_directory(directory_path)
    
    # Print all IDs, one per line
    for id in all_ids:
        print(id)

if __name__ == "__main__":
    main()

