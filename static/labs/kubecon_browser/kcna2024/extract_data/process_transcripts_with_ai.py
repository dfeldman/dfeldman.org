import json
import sys
import openai
from typing import Dict, List
from pathlib import Path

MAX_PRESENTATIONS = 500  # Limit number of presentations to process

def load_json(filename: str) -> List[Dict]:
    with open(filename, 'r') as f:
        return json.load(f)

def save_json(data: List[Dict], filename: str):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# This is a bit of a misnomer. It generates a coherent transcript from raw speech-to-text, 
# it's not an outline. Originally it split the transcript into smaller chunks, but that turned out to be unnecessary.
def extract_outline(transcript: str, title: str, abstract: str, speakers: str, chunk_size: int = 100000) -> List[str]:
    chunks = [transcript[i:i+chunk_size] for i in range(0, len(transcript), chunk_size)]
    outline_points = []
    
    for chunk in chunks:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                #{"role": "system", "content": "You are a note-taker. This is a section of a raw transcript of a technical presentation. Create a detailed outline of the topics discussed in this section. Each bullet point should be a topic discussed; roughly one per few sentences. It should be detailed but does not need to mention every single individual sentence. Output HTML format, using nested bullet points. The transcript was auto-generated and may have typos, especially with technical langauge; use the provided abstract for key terms. Do not include any markdown (eg ```html), just output HTML directly. Typically, a section like this one will have about 10-30 major topics, with more bullet points under each topic. Do not include the names of the speakers. Thank you."},
                #{"role": "user", "content": f"This is a presentation with the abstract {abstract}. Create an outline from this transcript section:\n\n{chunk}"}
                {"role": "system", "content": "This is an unedited transcript of a technical presentation generated using text-to-speech software. Turn it into a coherent, readable transcript. It should be readable, as if taken by a professional note-taker for consumption by the public. It should include most sentences from the original, except if they are unreadable or don't make sense (no need to note that though, just ignore them). Output HTML format, and do not include any markdown (eg ```html). The transcript may have typos, especially in proper names; correct them if you can. You can use bold, italic, headings, lists as necessary to make sense. No need to include the word 'presentation' in the title or things like 'applause'. Everything should be present-tense. The transcript cannot identify different voices, so don't attempt to distinguish between multiple speakers. The conference name is KubeCon. If names are mentioned, try to match them with the speakers listed, as speech-to-text is very bad with names. Thank you."},
                {"role": "user", "content": f"This is a presentation with the title '{title}' and abstract: {abstract}. \n The speakers are {speakers}. Create an edited version of this transcript section:\n\n{chunk}"}
            ]
        )
        outline_points.extend(response.choices[0].message.content.split('\n'))
    print("raw outline points", ''.join(outline_points)) 
    return outline_points

def synthesize_presentation(title: str, abstract: str, outline_points: str) -> Dict:
    prompt = f"""
    Title: {title}
    Abstract: {abstract}
    Auto-generated traasncript: {outline_points}
    
    Create:
    1. 1-4 technical tags. These should only be things that are directly related to the presentation - especially key technologies or pieces of software.
    2. 2-3 sentence description. This should capture the gist of the presentation for browsing quickly, and be a bit intriguing while being clear and easy to skim. It should start with an imperative, and not include buzzwords like innovative, cutting-edge, or revolutionary but instead softer words like enables, automates, in action, focus, and similar. This should be text format, but use html bolding for any product names. Do not include the names of the speakers or the title as they are already included. Example: Explore <b>SPIRE's</b> approach to workload identity with a focus on automated key recovery and recovery from compromises. Includes a live demo of this new feature in action. Second example: See how live traffic inspection with <b>Pixie</b> and <b>OPA</b> enables dynamic, automated authorization policies for Envoy. A hands-on demo shows the approach in evolving microservices setups. 
    3. Coherent HTML-formatted outline from the auto-generated transcript. Use HTML format. Do not use nested JSON output. Focus on making each point discussed clearly readable and easy to understand. Start with <ul> and end with </ul>. Use nested lists to structure the presentation outline. Do not include things that are only relevant in the actual conference hall, like asking for questions or scanning QR codes. Make the outline high-quality and professional, as if it were taken by a professional note-taker. If something doesn't make sense (looks like corrupted text), ignore it. The presentation is about 30 minutes, so a typical outline should have around 10 major topics with more bullet points under each topic. Do not include the names of the speakers.
    4. Search keywords. This should contain any technical terms that are mentioned, plus the general area of the presentation. These will be searched (not the entire outline or transcript), so be sure to include anything that seems relevant. 
    
    Format as JSON with keys: tags, description, outline, keywords
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Create structured presentation summary in JSON format"},
            {"role": "user", "content": prompt}
        ],
        response_format={ "type": "json_object" }
    )
    
    return json.loads(response.choices[0].message.content)

def generate_preview_html(presentations: List[Dict]) -> str:
    """Generate a preview HTML file from the AI-processed presentations"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI-Processed Presentations Preview</title>
        <style>
            body { 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            .presentation {
                margin-bottom: 40px;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            .title {
                font-size: 24px;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            .metadata {
                background: #f7f9fc;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }
            .tag {
                display: inline-block;
                background: #e1f5fe;
                padding: 3px 8px;
                border-radius: 12px;
                margin: 2px;
                font-size: 14px;
            }
            .keyword {
                display: inline-block;
                background: #e8f5e9;
                padding: 3px 8px;
                border-radius: 12px;
                margin: 2px;
                font-size: 14px;
            }
            .outline-section {
                margin-top: 20px;
                padding: 15px;
                background: #fff;
                border: 1px solid #eee;
                border-radius: 5px;
            }
            .outline-title {
                font-size: 18px;
                color: #34495e;
                margin-bottom: 10px;
            }
            .abstract {
                color: #666;
                line-height: 1.6;
            }
            .description {
                font-style: italic;
                color: #2c3e50;
                margin: 10px 0;
            }
            .evtid {
                color: #666;
                font-size: 14px;
                float: right;
            }
        </style>
    </head>
    <body>
    """
    
    for pres in presentations:
        html += f"""
        <div class="presentation">
            <div class="evtid">{pres['evtid']}</div>
            <h1 class="title">{pres['title']}</h1>
            
            <div class="metadata">
                <div class="tags">
                    <strong>Tags:</strong> {' '.join(f'<span class="tag">{tag}</span>' for tag in pres['tags'])}
                </div>
                <div class="keywords">
                    <strong>Keywords:</strong> {' '.join(f'<span class="keyword">{kw}</span>' for kw in pres['keywords'])}
                </div>
            </div>

            <div class="abstract">
                <strong>Abstract:</strong> {pres['abstract']}
            </div>

            <div class="description">
                <strong>AI Description:</strong> {pres['description']}
            </div>

            <div class="outline-section">
                <div class="outline-title">GPT-4o Quick Outline:</div>
                {pres['outline']}
            </div>

            <div class="outline-section">
                <div class="outline-title">GPT-4o-mini Transcript:</div>
                {pres['edited_transcript']}
            </div>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    return html

def save_preview(presentations: List[Dict], filename: str = "ai-preview.html"):
    """Save the preview HTML to a file"""
    html = generate_preview_html(presentations)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    if len(sys.argv) != 4:
        print("Usage: script.py data.json transcript.json ai.json")
        sys.exit(1)

    data_file, transcript_file, output_file = sys.argv[1:]
    
    # Load input data
    presentations = load_json(data_file)
    transcripts = {t['evtid']: t['transcript'] for t in load_json(transcript_file)}
    #presentations_dict = {p['evtid']: p for p in presentations} 
    # Load existing output or create empty list
    output = []
    if Path(output_file).exists():
        output = load_json(output_file)
    
    # Track processed evtids
    processed_ids = {item['evtid'] for item in output}
    
    # Process presentations
    count = 0
    for pres in presentations:
        if count >= MAX_PRESENTATIONS:
            break
            
        evtid = pres['evtid']
        if evtid in processed_ids:
            continue
            
        if evtid not in transcripts:
            print(f"Warning: No transcript for {evtid}")
            continue
            
        print(f"Processing {evtid}")
        speakers = ' '.join(pres['speakers'])
        outline_points = ''.join(extract_outline(transcripts[evtid], pres['title'], pres['abstract'], speakers))
        result = synthesize_presentation(pres['title'], pres['abstract'], outline_points)
        result["outline"] = "".join(result["outline"])        
        # There is already a field called "tags". Rename the ai-generated tags to aitags.
        result["aitags"] = result["tags"]
        del result["tags"]
        output.append({
            'evtid': evtid,
            'title': pres['title'],
            'abstract': pres['abstract'], # This is duplicated just to make preview HTML easier
            'edited_transcript': outline_points,
            **result
        })
        
        save_json(output, output_file)
        count += 1
        if output:
            save_preview(output)
    print(f"Processed {count} presentations")

if __name__ == "__main__":
    main()

