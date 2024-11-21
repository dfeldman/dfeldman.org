# Kubecon Content Browser

This is meant to just be a nice browser/searcher for KubeCon content. It will nicely display the videos and slides for each talk alongside the abstract.

## Prerequisites
1. Python dependencies: just openai and requests
1. OpenAI key in environment
1. Some place to host several gigabytes of slides and other data; I use CloudFront (not included)

## Phase 1: Basic browser
1. Download all the Sched .html files (one for each day)
1. Get the URLs for content pages from Sched: python3 extract_data/sched_to_urls.py > orig_data/urls
1. Fetch all URLs and store in a giant JSON blob (takes a while): python3 extract_data/fetch_urls.py orig_data/urls > orig_data/sched_contents.json
1. Download the YouTube playlist by going to YouTube and running the console command in extract_data/js_command.js. Save it in orig_data/playlist_data.csv
1. Add in YouTube video URLs: python3 extract_data/match_sched_to_video.py orig_data/sched_content_without_video.json orig_data/playlist_data.csv > combined_data/data.json
1. Reformat as nice JSON: python3 extract_data/html_to_json.py orig_data/sched_contents.json
1. python -m http.serve 
1. Visit port 8000 and browse

At this point, everything should work. The slides will not be visible, and the descriptions and tags will not be 

## Phase 2: Slides and AI
1. Fetch YouTube transcripts to a file transcripts.json. These are not used directly, just for the AI summaries. The file is a state file so if it gets interrupted, you can restart. The file is very large (6.7 MB in my copy). 
1. Run the AI part of the process, which creates transcripts, short descriptions, outlines, keywords, and tags for all talks. This creates a file ai.json containing the AI output. Again, this is a state file so you can start and stop the process as needed. This does cost a few bucks in OpenAI credits and take quite a while to run. python3 extract_data/process_transcripts_with_ai.py combined_data/data.json transcripts.json ai.json  . This also produces ai-preview.html which is just for a quick check to make sure the AI is not running off the rails. AI uses gpt-4o-mini to process transcripts, and gpt-4o to then generate descriptions and keywords; cost is around $5 per run. 
1. Download all the slides and convert them to JSON and PNG. This is necessary because some are .pptx files, which no browser can read, and some are .pdf files, which mobile browsers are not very good at reading. This is done with fetch_slides.py and slides_to_images2.py. You will end up with a slides/ dir with several gigabytes of PNG images, and slides.json which has the index of the slides and text format versions.

## Deployment
Right now, data.json is deployed through GitHub Pages, while slides.json, ai.json, and the massive slides/ dir are on S3 hosted through CloudFront.

Be sure to invalidate CloudFront every time you push new content. 

## Issues
1. It would make sense to merge all the JSON files and host everything in one big file on CloudFront.
1. Some presentations are missing. For videos, this is likely because the hacky method of matching videos to schedule entries is broken. For slides, this is likely because the slide URL changed after initial download. It also looks like the transcript download failed completely for some presentations. Each step should be checked more carefully.
1. It would make sense to generate pre-cached index for Fuse.js search and push that to CloudFront as well.
1. I've been tweaking the AI descriptions a lot. This code is in temp_ai_improve_desc.py. I'm still not really happy with the result. This should be improved and put in process_transcripts_with_ai.json . 
1. I'd like to bold every product name. I started on this with a list of CNCF project names. This could also be used as higher weight in search. 
1. The Related Presentations view uses Jaccard scores of the AI-generated tags to calculate similarity between presentations on the client side. This ... does not really work well at all. 
1. It would be really nice to have a statically rendered view alongside the JavaScript view to aid searching. 
1. As we do more conferences, will need something better than Fuse.js search on the client side. Maybe Algolia? Not sure. 
