#!/usr/bin/env python3

import os
import json
import shutil
import argparse
import requests
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import tiktoken
from pathlib import Path
import markdown
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Set up rich console for better output
console = Console()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bookbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BookBot')

# Constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TEMPERATURE = 0.7
PREVIEW_DIR = Path("preview")
FINAL_DIR = Path("final")
COMMON_DIR = Path("common")
CHAPTERS_DIR = Path("chapters")
PROMPTS_DIR = Path("prompts")
REVIEWS_DIR = Path("reviews")

# Default configuration
DEFAULT_CONFIG = {
    "default_llm": "gpt-4o",
    "max_tokens": 2000,
    "temperature": 0.7,
    "git_enabled": True,
    "auto_preview": True,
    "backup_enabled": True,
    "backup_dir": ".bookbot_backups",
    "logging_level": "INFO"
}


# Default prompts - simplified for clarity
# Default prompts
DEFAULT_PROMPTS = {
    "system_prompt.md": """You are a professional author and writing assistant. Your task is to help write a book based on the provided outline and guidelines. Your writing should be engaging, consistent, and follow proper narrative structure. When asked to write or edit, provide your output in Markdown format. Signal completion with "THE END" on a new line.""",
    
    "settings_prompt.md": """Based on the initial book description below, create a detailed description of the story's setting. Include:
- Time period and historical context
- Physical locations and environments
- Social and cultural context
- Important background information
- Unique elements of the world
- Atmosphere and mood

Initial Description:
{{ initial }}

Remember to be specific and vivid in your descriptions. End with "THE END".""",
    
    "characters_prompt.md": """Based on the initial description and setting below, create a detailed list of main and supporting characters. For each character, provide:
- Name and role in the story
- Physical description
- Personality traits and mannerisms
- Background and history
- Goals and motivations
- Relationships with other characters
- Key conflicts or challenges

Initial Description:
{{ initial }}

Setting:
{{ setting }}

Present each character in their own section with clear headers. End with "THE END".""",
    
    "outline_prompt.md": """Based on the materials below, create a detailed chapter-by-chapter outline of the book. For each chapter, include:
- Chapter number and title
- Main plot points and events
- Character arcs and developments
- Key scenes and their purposes
- Emotional beats and tone

Initial Description:
{{ initial }}

Setting:
{{ setting }}

Characters:
{{ characters }}

Format each chapter clearly and show how the story progresses. End with "THE END".""",
    
    "write_prompt.md": """Write Chapter {{ chapter_number }} according to the details below. Remember to:
- Follow the outline's key events
- Maintain consistent character voices
- Create vivid descriptions
- Use natural dialogue
- Balance action, dialogue, and description

Outline:
{{ outline }}

Setting:
{{ setting }}

Characters:
{{ characters }}

Write the chapter in engaging prose. End with "THE END".""",
    
    "edit_prompt.md": """Review and improve the provided content while maintaining consistency with the larger story. Focus on:
- Clarity and flow of prose
- Character voice consistency
- Description quality and vividness
- Dialogue naturality
- Pacing and engagement
- Grammar and style

Current Content:
{{ content }}

Make your improvements while keeping the core story elements intact. End with "THE END".""",
    
    "review_prompt.md": """Review the complete draft below, analyzing:
- Plot progression and consistency
- Character development and arcs
- Pacing and engagement
- Writing style and voice
- Setting utilization
- Themes and motifs

Provide specific examples and constructive suggestions for improvement.

Draft:
{{ content }}

End your review with "THE END"."""
}

@dataclass
class LLMConfig:
    """Configuration for an LLM model"""
    name: str
    provider: str
    cost_per_million_tokens: float
    temperature: float = DEFAULT_TEMPERATURE
    
    @property
    def full_name(self) -> str:
        return f"{self.provider}/{self.name}"

# Available LLMs and their configurations
AVAILABLE_LLMS = [
    LLMConfig("gpt-4o", "openai", 15.0),
    LLMConfig("claude-2.1", "anthropic", 8.0),
    LLMConfig("gpt-3.5-turbo", "openai", 0.5)
]

class BookBotError(Exception):
    """Base exception for all BookBot errors"""
    pass

class LLMError(BookBotError):
    """Errors related to LLM API calls"""
    def __init__(self, message: str, response: Optional[requests.Response] = None):
        super().__init__(message)
        self.response = response
        self.response_json = None
        
        if response is not None:
            try:
                self.response_json = response.json()
            except json.JSONDecodeError:
                self.response_text = response.text if response.text else None

    def __str__(self) -> str:
        base_msg = super().__str__()
        if not self.response:
            return base_msg
            
        status = f"HTTP {self.response.status_code}"
        
        if self.response_json:
            if isinstance(self.response_json, dict):
                if 'error' in self.response_json:
                    error_msg = self.response_json['error'].get('message', 'Unknown error')
                    error_type = self.response_json['error'].get('type', 'Unknown type')
                    return f"{base_msg}: {status} - [{error_type}] {error_msg}"
                elif 'message' in self.response_json:
                    return f"{base_msg}: {status} - {self.response_json['message']}"
            return f"{base_msg}: {status} - {str(self.response_json)}"
        
        if hasattr(self, 'response_text') and self.response_text:
            return f"{base_msg}: {status} - {self.response_text[:200]}..."
            
        return f"{base_msg}: {status}"

class TextFile:
    """Represents a markdown file with content and metadata"""
    
    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self.content = ""
        self.metadata = {}
        self.conversation_history = []
        self._load()
    
    def _load(self):
        """Load the file if it exists"""
        try:
            if self.filepath.exists():
                text = self.filepath.read_text(encoding='utf-8')
                if text.startswith('---'):
                    # Parse metadata
                    _, metadata, content = text.split('---', 2)
                    self.metadata = {
                        k.strip(): v.strip()
                        for k, v in (line.split(':', 1) 
                        for line in metadata.strip().split('\n')
                        if ':' in line)
                    }
                    self.content = content.strip()
                else:
                    self.content = text.strip()
                    
                # Load conversation history if it exists
                history_path = self.filepath.with_suffix('.history.json')
                if history_path.exists():
                    with history_path.open('r', encoding='utf-8') as f:
                        self.conversation_history = json.load(f)
        except Exception as e:
            logger.error(f"Error loading file {self.filepath}: {e}")
            raise BookBotError(f"Failed to load file: {e}")
    
    def save(self):
        """Save the file and its metadata"""
        try:
            # Create parent directories if they don't exist
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare content with metadata if present
            content = []
            if self.metadata:
                content.append('---')
                content.extend(f"{k}: {v}" for k, v in self.metadata.items())
                content.append('---')
            content.append(self.content)
            
            # Write main content
            self.filepath.write_text('\n'.join(content), encoding='utf-8')
            
            # Save conversation history
            if self.conversation_history:
                history_path = self.filepath.with_suffix('.history.json')
                with history_path.open('w', encoding='utf-8') as f:
                    json.dump(self.conversation_history, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Error saving file {self.filepath}: {e}")
            raise BookBotError(f"Failed to save file: {e}")
    
    def update_conversation_history(self, entry: dict):
        """Add an entry to the conversation history"""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            **entry
        })

class PreviewGenerator:
    """Generates HTML previews of the book content"""
    
    def __init__(self, preview_dir: Path = PREVIEW_DIR):
        self.preview_dir = Path(preview_dir)
        self.stats = {
            'total_words': 0,
            'total_tokens_in': 0,
            'total_tokens_out': 0
        }
    
    def setup(self):
        """Set up preview directory"""
        if self.preview_dir.exists():
            shutil.rmtree(self.preview_dir)
        self.preview_dir.mkdir(parents=True)
    
    def generate_file_preview(self, file: TextFile, title: str) -> Tuple[int, int, int]:
        """Generate preview for a single file"""
        html_content = markdown.markdown(file.content)
        
        # Calculate stats
        words = len(file.content.split())
        tokens_in = sum(entry.get('tokens_in', 0) for entry in file.conversation_history)
        tokens_out = sum(entry.get('tokens_out', 0) for entry in file.conversation_history)
        
        # Create HTML file
        html_path = self.preview_dir / f"{file.filepath.stem}.html"
        html_path.write_text(self._wrap_html(title, html_content))
        
        return words, tokens_in, tokens_out
    
    def generate(self, files: Dict[str, List[TextFile]]):
        """Generate complete preview"""
        self.setup()
        
        # Process all files and collect stats
        for category, file_list in files.items():
            for file in file_list:
                words, tokens_in, tokens_out = self.generate_file_preview(
                    file, f"{category} - {file.filepath.name}")
                self.stats['total_words'] += words
                self.stats['total_tokens_in'] += tokens_in
                self.stats['total_tokens_out'] += tokens_out
        
        # Generate index page
        self._generate_index(files)
        
        console.print(f"\n[green]✓[/green] Preview generated in {self.preview_dir}")
        console.print(f"[blue]ℹ[/blue] Open {self.preview_dir}/index.html in your browser")
    
    def _wrap_html(self, title: str, content: str) -> str:
        """Wrap content in HTML template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: system-ui; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}
                pre {{ background: #f5f5f5; padding: 1rem; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="content">
                {content}
            </div>
        </body>
        </html>
        """
    
    def _generate_index(self, files: Dict[str, List[TextFile]]):
        """Generate index page"""
        content = [
            "<h1>Book Preview</h1>",
            "<h2>Statistics</h2>",
            f"<p>Total Words: {self.stats['total_words']:,}</p>",
            f"<p>Total Tokens In: {self.stats['total_tokens_in']:,}</p>",
            f"<p>Total Tokens Out: {self.stats['total_tokens_out']:,}</p>"
        ]
        
        for category, file_list in files.items():
            content.extend([
                f"<h2>{category}</h2>",
                "<ul>"
            ])
            for file in file_list:
                content.append(
                    f'<li><a href="{file.filepath.stem}.html">{file.filepath.name}</a></li>'
                )
            content.append("</ul>")
        
        index_path = self.preview_dir / "index.html"
        index_path.write_text(self._wrap_html("Book Preview", "\n".join(content)))

class BookBot:
    """Main class for managing the book writing process"""
    
    def __init__(self, api_key: str, llm: Optional[str] = None, config: Optional[Dict] = None):
        self.api_key = api_key
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        self.llm = self._get_llm_config(llm) if llm else AVAILABLE_LLMS[0]
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        
        # Ensure required directories exist
        for directory in [COMMON_DIR, CHAPTERS_DIR, PROMPTS_DIR, REVIEWS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Initialize prompt templates
        self._init_prompts()
    
    def _init_prompts(self):
        """Initialize default prompts if they don't exist"""
        for name, content in DEFAULT_PROMPTS.items():
            prompt_file = PROMPTS_DIR / name
            if not prompt_file.exists():
                prompt_file.write_text(content)
    
    def _get_llm_config(self, llm_name: str) -> LLMConfig:
        """Get LLM configuration by name"""
        for llm in AVAILABLE_LLMS:
            if llm.name == llm_name:
                return llm
        raise ValueError(f"Unknown LLM: {llm_name}")
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
    
    def _load_template(self, template_name: str, variables: Dict[str, str] = None) -> str:
        """Load and fill a template"""
        template_path = PROMPTS_DIR / f"{template_name}.md"
        if not template_path.exists():
            raise BookBotError(f"Template not found: {template_name}")
            
        content = template_path.read_text()
        if variables:
            for key, value in variables.items():
                content = content.replace(f"{{{{ {key} }}}}", str(value))
        return content
    
    def _call_llm(self, prompt: str, max_retries: int = 3) -> Tuple[str, int, int]:
        """Call the LLM API with retry logic"""
        system_prompt = self._load_template("system_prompt")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.llm.full_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.llm.temperature,
            "max_tokens": self.config['max_tokens']
        }
        
        for attempt in range(max_retries):
            try:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                    task = progress.add_task("Generating content...", total=None)
                    
                    response = requests.post(
                        OPENROUTER_API_URL,
                        headers=headers,
                        json=data,
                        timeout=60
                    )
                    
                    if response.status_code == 429:  # Rate limit
                        retry_after = int(response.headers.get('Retry-After', 5))
                        time.sleep(retry_after)
                        continue
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    if 'error' in result:
                        raise LLMError("API returned error", response)
                    
                    if not result.get('choices'):
                        raise LLMError("No choices in API response", response)
                    
                    content = result["choices"][0]["message"]["content"]
                    tokens_in = result["usage"]["prompt_tokens"]
                    tokens_out = result["usage"]["completion_tokens"]
                    
                    # Remove completion marker if present
                    if "THE END" in content:
                        content = content.split("THE END")[0].strip()
                    
                    return content, tokens_in, tokens_out
                    
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise LLMError(f"Failed to call LLM API after {max_retries} attempts: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise LLMError("Max retries exceeded")
        
    def _git_commit(self, message: str):
        """
        Commit changes to git repository.
        Assumes git is already initialized and config is properly set up.
        
        Args:
            message (str): The commit message
        """
        if not self.config['git_enabled']: 
            return
        
        import subprocess
        
        try:
            # Add files
            result = subprocess.run(
                ["git", "add", "."],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(f"Git add failed: {result.stderr}")
                return
                
            # Commit with message
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                if "nothing to commit" in result.stderr:
                    logger.info("No changes to commit")
                else:
                    logger.error(f"Git commit failed: {result.stderr}")
                return
                
            logger.info(f"Successfully committed changes: {message}")
            
        except subprocess.SubprocessError as e:
            logger.error(f"Git operation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during git commit: {str(e)}")

    def write_setting(self):
        """Generate the story setting"""
        try:
            # Load initial description
            initial = TextFile(Path("initial.md"))
            if not initial.filepath.exists():
                raise BookBotError("initial.md not found. Please create it with your story description.")
            
            # Generate setting
            prompt = self._load_template("settings_prompt", {"initial": initial.content})
            content, tokens_in, tokens_out = self._call_llm(prompt)
            
            # Save setting
            setting = TextFile(COMMON_DIR / "setting.md")
            setting.content = content
            setting.metadata = {
                "created_at": datetime.now().isoformat()
            }
            setting.update_conversation_history({
                "command": "write_setting",
                "llm": self.llm.name,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "prompt": prompt,
                "content": content

            })
            setting.save()
            
            # Generate preview
            self._generate_preview()
            
            console.print("\n[green]✓[/green] Setting generated successfully")
            
        except Exception as e:
            logger.error(f"Error writing setting: {e}")
            raise BookBotError(f"Failed to write setting: {e}")
    
    def write_characters(self):
        """Generate the story characters"""
        try:
            # Load required files
            initial = TextFile(Path("initial.md"))
            setting = TextFile(COMMON_DIR / "setting.md")
            if not initial.filepath.exists() or not setting.filepath.exists():
                raise BookBotError("Required files (initial.md and setting.md) not found")
            
            # Generate characters
            prompt = self._load_template("characters_prompt", {
                "initial": initial.content,
                "setting": setting.content
            })
            content, tokens_in, tokens_out = self._call_llm(prompt)
            
            # Save characters
            characters = TextFile(COMMON_DIR / "characters.md")
            characters.content = content
            characters.metadata = {
                "created_at": datetime.now().isoformat()
            }
            characters.update_conversation_history({
                "command": "write_characters",
                "llm": self.llm.name,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "prompt": prompt,
                "content": content

            })
            characters.save()

            # Commit git if enabled
            self._git_commit("Generated characters")

            # Generate preview
            self._generate_preview()
            
            console.print("\n[green]✓[/green] Characters generated successfully")
            
        except Exception as e:
            logger.error(f"Error writing characters: {e}")
            raise BookBotError(f"Failed to write characters: {e}")
    
    def write_outline(self):
        """Generate the story outline"""
        try:
            # Load required files
            initial = TextFile(Path("initial.md"))
            setting = TextFile(COMMON_DIR / "setting.md")
            characters = TextFile(COMMON_DIR / "characters.md")
            if not all(f.filepath.exists() for f in [initial, setting, characters]):
                raise BookBotError("Required files (initial.md, setting.md, characters.md) not found")
            
            # Generate outline
            prompt = self._load_template("outline_prompt", {
                "initial": initial.content,
                "setting": setting.content,
                "characters": characters.content
            })
            content, tokens_in, tokens_out = self._call_llm(prompt)
            
            # Save outline
            outline = TextFile(COMMON_DIR / "outline.md")
            outline.content = content
            outline.metadata = {
                "created_at": datetime.now().isoformat()
            }
            outline.update_conversation_history({
                "command": "write_outline",
                "llm": self.llm.name,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "prompt": prompt,
                "content": content
            })
            outline.save()
            
            self._git_commit("Generated outline")

            # Generate preview
            self._generate_preview()
            
            console.print("\n[green]✓[/green] Outline generated successfully")
            
        except Exception as e:
            logger.error(f"Error writing outline: {e}")
            raise BookBotError(f"Failed to write outline: {e}")

    def write_chapter(self, chapter_num: int):
        """Write a new chapter"""
        try:
            # Load necessary context
            outline = TextFile(COMMON_DIR / "outline.md")
            setting = TextFile(COMMON_DIR / "setting.md")
            characters = TextFile(COMMON_DIR / "characters.md")
            
            # Prepare variables for template
            variables = {
                "chapter_number": chapter_num,
                "outline": outline.content,
                "setting": setting.content,
                "characters": characters.content
            }
            
            # Generate chapter content
            prompt = self._load_template("write_prompt", variables)
            content, tokens_in, tokens_out = self._call_llm(prompt)
            
            # Save chapter
            chapter_file = TextFile(CHAPTERS_DIR / f"chapter_{chapter_num:02d}.md")
            chapter_file.content = content
            chapter_file.metadata = {
                "chapter_number": str(chapter_num),
                "created_at": datetime.now().isoformat()
            }
            chapter_file.update_conversation_history({
                "command": "write_chapter",
                "llm": self.llm.name,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "prompt": prompt,
                "content": content
            })
            chapter_file.save()
            
            self._git_commit(f"Generated chapter {chapter_num}")

            # Generate preview
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Chapter {chapter_num} generated successfully")
            
        except Exception as e:
            logger.error(f"Error writing chapter {chapter_num}: {e}")
            raise BookBotError(f"Failed to write chapter: {e}")
    
    def edit_chapter(self, chapter_num: int):
        """Edit an existing chapter"""
        try:
            chapter_path = CHAPTERS_DIR / f"chapter_{chapter_num:02d}.md"
            if not chapter_path.exists():
                raise BookBotError(f"Chapter {chapter_num} not found")
            
            chapter = TextFile(chapter_path)
            
            # Prepare editing prompt
            variables = {
                "chapter_number": chapter_num,
                "content": chapter.content
            }
            
            prompt = self._load_template("edit_prompt", variables)
            content, tokens_in, tokens_out = self._call_llm(prompt)
            
            # Update chapter
            chapter.content = content
            chapter.metadata["edited_at"] = datetime.now().isoformat()
            chapter.update_conversation_history({
                "command": "edit_chapter",
                "llm": self.llm.name,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "prompt": prompt
            })
            chapter.save()
            
            self._git_commit(f"Edited chapter {chapter_num}")

            # Generate preview
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Chapter {chapter_num} edited successfully")
            
        except Exception as e:
            logger.error(f"Error editing chapter {chapter_num}: {e}")
            raise BookBotError(f"Failed to edit chapter: {e}")
    
    def review_book(self):
        """Generate a review of the entire book"""
        try:
            # Collect all chapters
            chapters = []
            chapter_num = 1
            while True:
                chapter_path = CHAPTERS_DIR / f"chapter_{chapter_num:02d}.md"
                if not chapter_path.exists():
                    break
                chapter = TextFile(chapter_path)
                chapters.append(chapter.content)
                chapter_num += 1
            
            if not chapters:
                raise BookBotError("No chapters found to review")
            
            # Generate review
            full_text = "\n\n".join(chapters)
            prompt = self._load_template("review_prompt", {"content": full_text})
            content, tokens_in, tokens_out = self._call_llm(prompt)
            
            # Save review
            review_num = len(list(REVIEWS_DIR.glob("*.md"))) + 1
            review = TextFile(REVIEWS_DIR / f"review_{review_num:02d}.md")
            review.content = content
            review.metadata = {
                "review_number": str(review_num),
                "created_at": datetime.now().isoformat()
            }
            review.update_conversation_history({
                "command": "review_book",
                "llm": self.llm.name,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "prompt": prompt
            })
            review.save()
            
            self._git_commit(f"Generated review #{review_num}")

            # Generate preview
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Book review generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating review: {e}")
            raise BookBotError(f"Failed to generate review: {e}")
    
    def _generate_preview(self):
        """Generate HTML preview of all content"""
        try:
            # Collect all files by category
            files = {
                "Chapters": sorted(
                    [TextFile(p) for p in CHAPTERS_DIR.glob("*.md")],
                    key=lambda f: int(f.filepath.stem.split('_')[1])
                ),
                "Common": [TextFile(p) for p in COMMON_DIR.glob("*.md")],
                "Reviews": [TextFile(p) for p in REVIEWS_DIR.glob("*.md")]
            }
            
            # Generate preview
            preview = PreviewGenerator()
            preview.generate(files)
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            console.print(f"[red]![/red] Failed to generate preview: {e}")
    
    def finalize(self):
        """Create final versions of all content"""
        try:
            if FINAL_DIR.exists():
                shutil.rmtree(FINAL_DIR)
            FINAL_DIR.mkdir(parents=True)
            
            # Copy all chapters
            for chapter_path in sorted(CHAPTERS_DIR.glob("*.md")):
                chapter = TextFile(chapter_path)
                final_path = FINAL_DIR / chapter_path.name
                final_path.write_text(chapter.content)
            
            # Copy common files
            for common_path in COMMON_DIR.glob("*.md"):
                final_path = FINAL_DIR / common_path.name
                final_path.write_text(common_path.read_text())
            
            console.print(f"\n[green]✓[/green] Final version created in {FINAL_DIR}")
            
        except Exception as e:
            logger.error(f"Error creating final version: {e}")
            raise BookBotError(f"Failed to create final version: {e}")
        


def main():
    """Main entry point for BookBot"""
    parser = argparse.ArgumentParser(description="BookBot - Automated Book Writing Tool")
    
    # Common arguments
    parser.add_argument('--llm', help="LLM model to use", 
                       choices=[llm.name for llm in AVAILABLE_LLMS])
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Initial setup commands
    subparsers.add_parser('write-setting', help='Generate the story setting')
    subparsers.add_parser('write-characters', help='Generate the story characters')
    subparsers.add_parser('write-outline', help='Generate the story outline')
    
    # Write chapter command
    write_parser = subparsers.add_parser('write-chapter', help='Write a new chapter')
    write_parser.add_argument('number', type=int, help='Chapter number')
    
    # Edit chapter command
    edit_parser = subparsers.add_parser('edit-chapter', help='Edit an existing chapter')
    edit_parser.add_argument('number', type=int, help='Chapter number')
    
    # Review command
    subparsers.add_parser('review', help='Generate a review of the book')
    
    # Finalize command
    subparsers.add_parser('finalize', help='Create final versions of all content')
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        console.print("[red]Error:[/red] OPENROUTER_API_KEY environment variable not set")
        return 1
    
    try:
        bot = BookBot(api_key, args.llm)
        
        if args.command == 'write-setting':
            bot.write_setting()
        elif args.command == 'write-characters':
            bot.write_characters()
        elif args.command == 'write-outline':
            bot.write_outline()
        elif args.command == 'write-chapter':
            bot.write_chapter(args.number)
        elif args.command == 'edit-chapter':
            bot.edit_chapter(args.number)
        elif args.command == 'review':
            bot.review_book()
        elif args.command == 'finalize':
            bot.finalize()
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return 1


if __name__ == '__main__':
    exit(main())