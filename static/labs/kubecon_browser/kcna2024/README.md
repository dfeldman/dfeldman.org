# Kubecon Content Browser

This is meant to just be a nice browser/searcher for KubeCon content. It will nicely display the videos and slides for each talk alongside the abstract.

1. Download all the Sched .html files (one for each day)
1. Download the YouTube playlist by going to YouTube and running the console command in extract_data/js_command.js. Save it in orig_data/playlist_data.csv
1. Get the URLs for content pages from Sched: python3 extract_data/sched_to_urls.py > orig_data/urls
1. Fetch all URLs and store in a giant JSON blob (takes a while): python3 extract_data/fetch_urls.py orig_data/urls > orig_data/sched_contents.json
1. Reformat as nice JSON: python3 extract_data/html_to_json.py orig_data/sched_contents.json
1. Add in YouTube video URLs: python3 extract_data/match_sched_to_video.py orig_data/sched_content_without_video.json orig_data/playlist_data.csv > combined_data/data.json
1. Fetch YouTube transcripts to a file transcripts.json. These are not used directly, just for the AI summaries. The file is a state file so if it gets interrupted, you can restart. The file is very large (6.7 MB in my copy). 
1. Run the AI part of the process, which creates transcripts, short descriptions, outlines, keywords, and tags for all talks. This creates a file ai.json containing the AI output. Again, this is a state file so you can start and stop the process as needed. This does cost a few bucks in OpenAI credits and take quite a while to run. python3 extract_data/process_transcripts_with_ai.py combined_data/data.json transcripts.json ai.json  . This also produces ai-preview.html which is just for a quick check to make sure the AI is not running off the rails.
1. Download all the slides and convert them to JSON and PNG. This is necessary because some are .pptx files, which no browser can read, and some are .pdf files, which mobile browsers are not very good at reading. 
1. python -m http.serve 
1. Visit port 8000 and browse
