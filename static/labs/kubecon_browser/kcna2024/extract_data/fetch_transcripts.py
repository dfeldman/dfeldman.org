import os
import sys
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def clean_video_url(video_url):
    """
    Removes playlist-related query parameters from a YouTube URL, leaving only the video ID.
    """
    parsed_url = urlparse(video_url)
    query_params = parse_qs(parsed_url.query)

    # Retain only the 'v' parameter (video ID)
    clean_query_params = {'v': query_params['v']} if 'v' in query_params else {}

    # Reconstruct the URL without playlist-related parameters
    cleaned_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        '',
        urlencode(clean_query_params, doseq=True),
        ''
    ))
    return cleaned_url


def clean_subtitles(file_path):
    """
    Cleans and extracts the text from a WebVTT subtitle file, removing metadata and duplicates.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        transcript = []
        seen_lines = set()  # To track and remove duplicate lines

        for line in lines:
            line = line.strip()

            # Skip empty lines or lines with timestamps
            if not line or "-->" in line:
                continue

            # Remove metadata tags like <00:00:03.320><c>
            line = re.sub(r"<.*?>", "", line)

            # Skip lines already added (to remove duplicates)
            if line not in seen_lines:
                transcript.append(line)
                seen_lines.add(line)

        # Combine all lines into a single transcript
        return " ".join(transcript)
    except Exception as e:
        print(f"Error cleaning subtitles from {file_path}: {e}")
        return ""


def download_subtitles(video_url, output_file):
    """
    Downloads the subtitles for a YouTube video using yt-dlp.
    """
    try:
        # Command to fetch auto-generated subtitles and save to the output file
        print("cleaned URL", clean_video_url(video_url))
        result = subprocess.run(
            [
                "yt-dlp",
                "--write-auto-subs",
                "--skip-download",
                "--sub-langs", "en",  # Change 'en' to your preferred language if needed
                "--output", output_file,
                clean_video_url(video_url)
            ],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error downloading subtitles for {video_url}: {e}")
        return False

        return ""

def save_transcripts(transcripts, transcripts_file):
    """
    Save the transcripts to the JSON file.
    """
    with open(transcripts_file, 'w', encoding='utf-8') as f:
        json.dump(transcripts, f, indent=4)
    print(f"Progress saved to {transcripts_file}")

def main(input_file):
    # Load input data JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load existing transcripts if available
    transcripts_file = "transcripts.json"
    if os.path.exists(transcripts_file):
        with open(transcripts_file, 'r', encoding='utf-8') as f:
            transcripts = json.load(f)
    else:
        transcripts = []

    existing_evtids = {entry["evtid"] for entry in transcripts}

    # Process each video in the input JSON
    for entry in data:
        evtid = entry.get("evtid")
        video_url = entry.get("videoUrl")

        if not evtid or not video_url:
            print(f"Skipping entry with missing evtid or videoUrl: {entry}")
            continue

        if evtid in existing_evtids:
            print(f"Skipping already processed evtid: {evtid}")
            continue

        print(f"Processing evtid: {evtid}, video: {video_url}")

        # Temporary file to save subtitles
        temp_file = f"temp_{evtid}"
        #temp_file = "output.en.vtt"
        # Download subtitles
        if download_subtitles(video_url, temp_file):
            # Clean subtitles and add to transcripts
            transcript_text = clean_subtitles(temp_file+".en.vtt")
            if transcript_text:
                transcripts.append({"evtid": evtid, "transcript": transcript_text})
                existing_evtids.add(evtid)
                print(f"Successfully processed evtid: {evtid}")
                # Save after processing each video
                save_transcripts(transcripts, transcripts_file)
            else:
                print(f"Failed to extract transcript for evtid: {evtid}")
        else:
            print(f"Failed to download subtitles for evtid: {evtid}")

        # Clean up temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)

    print(f"All transcripts processed. Final data saved to {transcripts_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fetch_transcripts.py <input_data.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        sys.exit(1)

    main(input_file)

