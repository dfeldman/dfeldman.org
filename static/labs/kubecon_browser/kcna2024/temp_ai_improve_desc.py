import json
import openai
import random
all_keywords = ["Learn", "Discover", "Explore", "Understand", "See", "Watch",
        "Dive into", "Investigate", "Review", "Unpack", "Examine",
        "Follow", "Track", "Walk through", "Step into", "Journey through",
        "Navigate", "Master", "Grasp", "Study", "Consider", "Observe",
        "Preview", "Survey", "Uncover", "Witness", "Experience", "Look at",
        "Venture into", "Dive into", "Focus on", "Analyze", "Inspect",
        "Experience", "Accelerate", "Decipher", "Reveal", "Navigate", "Solve",
        "Tackle"
        ]

# Function to improve descriptions using ChatGPT
def improve_description(description: str) -> str:
    keywords = random.sample(all_keywords, 3)
    prompt = f"""
    Original Description: {description}
    
    Improve the description to make it concise, engaging, and easy to skim, suitable for a search result page. Avoid buzzwords and focus on clarity. Use a unique imperative phrase to start, especially one of these as appropriate: {keywords}. This should capture the gist of the presentation for browsing quickly, and be a bit intriguing. It should start with an imperative, and not include buzzwords like delve, innovative, cutting-edge, or revolutionary but instead softer words like enables, automates, in action, focus, and similar. This should be text format. Do not include the names of the speakers or the title as they are already included. Example: Explore SPIRE's approach to workload identity with a focus on automated key recovery and recovery from compromises. Includes a live demo of this new feature in action. Second example: See how live traffic inspection with Pixie and OPA enables dynamic, automated authorization policies for Envoy. A hands-on demo shows the approach in evolving microservices setups.. 
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that rewrites descriptions for clarity and engagement. You do NOT USE MARKDOWN OR HTML, only plain text."},
            {"role": "user", "content": prompt}
        ]
    )
    print(response.choices[0].message.content) 
    return response.choices[0].message.content

# Main script to process the JSON file
def process_descriptions(input_file: str, output_file: str):
    # Load input JSON file
    with open(input_file, 'r') as infile:
        data = json.load(infile)
    
    # Process each description
    for item in data:
        if 'description' in item:
            original = item['description']
            item['improved_description'] = improve_description(original)
    
    # Save the updated data to output file
    with open(output_file, 'w') as outfile:
        json.dump(data, outfile, indent=4)

# Example usage
input_json_file = "ai.json"
output_json_file = "ai_improved_description.json"
process_descriptions(input_json_file, output_json_file)

