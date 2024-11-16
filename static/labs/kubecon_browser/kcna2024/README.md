# Kubecon Content Browser

This is meant to just be a nice browser/searcher for KubeCon content. It will nicely display the videos and slides for each talk alongside the abstract.

1. Download all the Sched .html files (one for each day)
1. Download the YouTube playlist by going to YouTube and running the console command in extract_data/js_command.js. Save it in orig_data/playlist_data.csv
1. Get the URLs for content pages from Sched: python3 extract_data/sched_to_urls.py > orig_data/urls
1. Fetch all URLs and store in a giant JSON blob (takes a while): python3 extract_data/fetch_urls.py orig_data/urls > orig_data/sched_contents.json
1. Reformat as nice JSON: python3 extract_data/html_to_json.py orig_data/sched_contents.json
1. Add in YouTube video URLs: python3 extract_data/match_sched_to_video.py orig_data/sched_content_without_video.json orig_data/playlist_data.csv > combined_data/data.json
1. python -m http.serve 
1. Visit port 8000 and browse
