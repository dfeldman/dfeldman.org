#!/usr/bin/env python3

import os
import json
import shutil
import argparse
import requests
import logging
import time
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime
import tiktoken
from pathlib import Path
import markdown
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import yaml
import re

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
logger.setLevel(logging.DEBUG) # For now
# Constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TEMPERATURE = 0.8
PREVIEW_DIR = Path("preview")
FINAL_DIR = Path("final")
COMMON_DIR = Path("common")
CHAPTERS_DIR = Path("chapters")
PROMPTS_DIR = Path("prompts")
REVIEWS_DIR = Path("reviews")
FRONTMATTER_DIR = Path("frontmatter")
BACKMATTER_DIR = Path("frontmatter")

# Default configuration
DEFAULT_CONFIG = {
    "default_llm": "gpt-4o",
    "max_tokens": 2000,
    "temperature": 0.8,
    "git_enabled": True,
    "auto_preview": True,
    "backup_enabled": True,
    "backup_dir": ".bookbot_backups",
    "logging_level": "DEBUG",
    "bot_dir": "bots" 
}

DEFAULT_TITLE_FILE="""
---
title: Your Book Title
author: Your Name
language: en-US
rights: All rights reserved
publisher: Optional Publisher Name
date: 2025
subtitle: Optional Subtitle
---

# Your Book Title

By Your Name
"""

########################### NEW BOT SYSTEM ###########################
# Once this is fully working, get rid of the old way to call LLMs

#### INIT

def initialize_bot_yaml(bot_dir: Path):
    """Initialize example bot YAML files in the specified directory.
    Never overwrites existing files.
    """
    bot_dir.mkdir(exist_ok=True)
    
    # Default configuration
    default_yaml = {
        "name": "default",
        "type": "default",
        "llm": "anthropic/claude-2.1",
        "input_price": 8.00,
        "output_price": 24.00,
        "provider": "anthropic",
        "temperature": 0.7,
        "expected_length": 3000,
        "context_window": 4096,
        "system_prompt": """You are a professional writing assistant.
Provide clear, detailed responses that directly address the task at hand.
Focus on quality and completeness in your writing."""
    }
    
    # Example bots for each type
    example_bots = {
        "write_setting": {
            "name": "write_setting",
            "type": "write_setting",
            "system_prompt": """You are an expert worldbuilding consultant.
Create rich, detailed settings that feel alive and internally consistent.
Focus on atmosphere, historical context, and the subtle details that make a world feel real.""",
            "main_prompt": """Based on the initial book description, create a detailed setting that includes:
- Time period and historical context
- Physical locations and environments
- Social and cultural backdrop
- Key locations and their significance
- Atmosphere and mood
- Unique elements that make this world special

Initial Description:
{initial}"""
        },
        
        "write_characters": {
            "name": "write_characters",
            "type": "write_characters",
            "system_prompt": """You are an expert character designer.
Create deep, complex characters with clear motivations, distinct voices, and compelling arcs.
Focus on making each character unique and memorable while fitting naturally into the story world.""",
            "main_prompt": """Create a detailed cast of characters for this story. For each character, include:
- Name and role
- Physical description and mannerisms
- Personality and psychological profile
- Background and history
- Goals and motivations
- Key relationships
- Potential for growth and change

Initial Description:
{initial}

Setting Context:
{setting}"""
        },
        
        "write_outline": {
            "name": "write_outline",
            "type": "write_outline",
            "system_prompt": """You are an expert story architect.
Create well-structured outlines that balance plot, character development, and thematic elements.
Focus on pacing, dramatic tension, and satisfying story arcs.""",
            "main_prompt": """Create a detailed chapter-by-chapter outline including:
- Chapter summaries
- Key plot points and revelations
- Character development moments
- Important scenes and their purpose
- Emotional beats and tone shifts

Initial Description:
{initial}

Setting:
{setting}

Characters:
{characters}"""
        },
        
        "write_chapter": {
            "name": "write_chapter",
            "type": "write_chapter",
            "system_prompt": """You are an expert prose writer.
Create engaging, well-crafted chapters that advance the story while maintaining style and voice.
Focus on balancing description, dialogue, and action while keeping the reader engaged.""",
            "main_prompt": """Write Chapter {chapter_number}. Include:
- Rich, evocative descriptions
- Natural, character-driven dialogue
- Clear action and scene progression
- Character thoughts and emotions
- Proper pacing and flow

Previous Chapter:
{previous_chapter}

Chapter Outline:
{outline}

Setting:
{setting}

Characters:
{characters}"""
        },
        
        "review_commons": {
            "name": "review_commons",
            "type": "review_commons",
            "system_prompt": """You are an expert story editor focusing on worldbuilding and character consistency.
Provide detailed feedback on how to improve and maintain consistency across story elements.
Focus on internal logic, character authenticity, and world coherence.""",
            "main_prompt": """Review this {file_type} focusing on:
- Internal consistency
- Completeness of detail
- Integration with other elements
- Areas needing expansion
- Potential plot implications

Content to Review:
{content}

Related Context:
{context}"""
        },
        
        "review_chapter": {
            "name": "review_chapter",
            "type": "review_chapter",
            "system_prompt": """You are an expert chapter reviewer.
Analyze chapters for story effectiveness, character consistency, and engaging writing.
Focus on both technical execution and narrative impact.""",
            "main_prompt": """Review Chapter {chapter_number} focusing on:
- Plot progression
- Character consistency
- Pacing and flow
- Description quality
- Dialogue effectiveness
- Scene structure

Chapter Content:
{content}

Story Context:
{outline}

Setting:
{setting}

Characters:
{characters}"""
        },
        
        "edit_chapter": {
            "name": "edit_chapter",
            "type": "edit_chapter",
            "system_prompt": """You are an expert line editor.
Provide specific, actionable suggestions for improving prose quality and readability.
Focus on clarity, style, and impact while maintaining the author's voice.""",
            "main_prompt": """Edit Chapter {chapter_number} focusing on:
- Sentence structure and variety
- Word choice and clarity
- Show vs tell balance
- Dialogue tags and action beats
- Paragraph flow and transitions

Original Content:
{content}

Previous Edit Notes:
{edit_notes}"""
        },
        
        "review_whole": {
            "name": "review_whole",
            "type": "review_whole",
            "llm": "anthropic/claude-3-opus-20240229",  # Different LLM for full book review
            "input_price": 15.00,
            "output_price": 75.00,
            "context_window": 1000000,
            "system_prompt": """You are an expert book editor conducting a comprehensive review.
Analyze the complete manuscript for overall effectiveness and cohesion.
Focus on large-scale story elements, character arcs, and thematic consistency.""",
            "main_prompt": """Review the complete manuscript focusing on:
- Overall plot arc and pacing 
- Character development and arcs
- Theme exploration and resolution
- World building consistency
- Narrative voice consistency
- Major strengths and weaknesses

Full Manuscript:
{content}"""
        }
    }
    
    # Write default config
    default_path = bot_dir / "default.yaml"
    if not default_path.exists():
        with default_path.open('w') as f:
            yaml.dump(default_yaml, f, sort_keys=False, indent=2)
    
    # Write example bots
    for bot_name, bot_config in example_bots.items():
        bot_path = bot_dir / f"{bot_name}.yaml"
        if not bot_path.exists():
            # Only include non-default values
            minimal_config = {
                "name": bot_config["name"],
                "type": bot_config["type"],
                "system_prompt": bot_config["system_prompt"],
                "main_prompt": bot_config["main_prompt"]
            }
            
            # For book reviewer, include special LLM config
            if bot_name == "book_reviewer":
                minimal_config.update({
                    "llm": bot_config["llm"],
                    "input_price": bot_config["input_price"],
                    "output_price": bot_config["output_price"],
                    "context_window": bot_config["context_window"]
                })
            
            with bot_path.open('w') as f:
                yaml.dump(minimal_config, f, sort_keys=False, indent=2)
    
    logger.info(f"Initialized example bot configurations in {bot_dir}")
    return list(bot_dir.glob("*.yaml"))



##### Core bot system

# Global helper functions
def format_text_stats(text: str) -> str:
    """Format text statistics as bytes/words/tokens
    
    Returns a string like '1234b/456w/789t'
    """
    bytes_count = len(text.encode('utf-8'))
    words_count = len(text.split())
    enc = tiktoken.encoding_for_model("gpt-4")
    tokens_count = len(enc.encode(text))
    return f"{bytes_count}b/{words_count}w/{tokens_count}t"

def format_price(input_tokens: int, output_tokens: int, 
                input_price: float, output_price: float) -> str:
    """Format price calculation
    
    Returns a string like '$1.234 (in:$0.123 out:$1.111)'
    """
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    total_cost = input_cost + output_cost
    return f"${total_cost:.4f} (in:${input_cost:.4f} out:${output_cost:.4f})"


##### BotType


class BotType(Enum):
    """Types of bots and their required template variables"""
    DEFAULT = auto()           # No specific variables required
    WRITE_OUTLINE = auto()     # initial, setting, characters
    WRITE_SETTING = auto()     # initial
    WRITE_CHARACTERS = auto()  # initial, setting
    WRITE_CHAPTER = auto()     # chapter_number, outline, setting, characters, previous_chapter
    REVIEW_COMMONS = auto()    # file_type, content, context
    REVIEW_CHAPTER = auto()    # chapter_number, content, outline, setting, characters
    EDIT_CHAPTER = auto()      # chapter_number, content, edit_notes
    REVIEW_WHOLE = auto()      # content
    
    @property
    def required_vars(self) -> Set[str]:
        """Get required template variables for this bot type"""
        return {
            BotType.DEFAULT: set(),
            BotType.WRITE_OUTLINE: {"initial", "setting", "characters"},
            BotType.WRITE_SETTING: {"initial"},
            BotType.WRITE_CHARACTERS: {"initial", "setting"},
            BotType.WRITE_CHAPTER: {"chapter_number", "outline", "setting", "characters", "previous_chapter"},
            BotType.REVIEW_COMMONS: {"initial", "setting", "characters", "outline"},
            BotType.REVIEW_CHAPTER: {"chapter_number", "content", "outline", "setting", "characters"},
            BotType.EDIT_CHAPTER: {"chapter_number", "content", "edit_notes"},
            BotType.REVIEW_WHOLE: {"content"}
        }[self]

@dataclass
class Bot:
    """Configuration for a chat bot"""
    # TODO everything here is hardcoded around reading bots from "bots/"
    # should make this configurable
    name: str
    type: BotType
    llm: str
    input_price: float  # Price per million tokens
    output_price: float  # Price per million tokens
    provider: Optional[str] = None
    temperature: float = 0.7
    expected_length: int = 2000  # Expected length in words
    system_prompt: str = ""
    context_window: int = 4096
    main_prompt: str = ""
    continuation_prompt_initial: str = "Type THE END when finished, or CONTINUE if you need to write more."
    continuation_prompt: str = "You have written {current_words} words out of {expected_words} expected words. Continue the text."
    
    @classmethod
    def from_file(cls, file_path: Path, defaults_path: Optional[Path] = None) -> 'Bot':
        """Load bot configuration from a YAML file with defaults"""
        if defaults_path is None:
            defaults_path = Path("bots/default.yaml")
        try:
            # Load defaults if provided
            defaults = {}
            if defaults_path.exists():
                with defaults_path.open('r') as f:
                    defaults = yaml.safe_load(f)
            else:
                logger.warning(f"Defaults file {defaults_path} not found, using empty defaults")
            # Load bot config
            with file_path.open('r') as f:
                config = yaml.safe_load(f)
            
            # Merge with defaults
            merged = {**defaults, **config}
            
            # Convert type string to enum
            merged['type'] = BotType[merged['type'].upper()]
            
            return cls(**merged)
            
        except Exception as e:
            raise ValueError(f"Failed to load bot config from {file_path}: {e}")
    
    @staticmethod
    def list_bots(bot_dir: Path, bot_type: Optional[BotType] = None) -> List[Path]:
        """List all bot configuration files, optionally filtered by type"""
        bot_dir.mkdir(exist_ok=True)
        
        if bot_type:
            # Load each file to check its type
            matching_bots = []
            for file in bot_dir.glob("*.yaml"):
                try:
                    bot = Bot.from_file(file)
                    if bot.type == bot_type:
                        matching_bots.append(file)
                except Exception as e:
                    logger.warning(f"Skipping invalid bot file {file}: {e}")
            return matching_bots
        else:
            return list(bot_dir.glob("*.yaml"))
    
    def validate_template_vars(self, variables: Dict[str, str]):
        """Validate that all required template variables are present"""
        required = self.type.required_vars
        missing = required - set(variables.keys())
        if missing:
            raise ValueError(f"Missing required template variables for {self.type}: {missing}")

class BotChat:
    """Manages a conversation with a bot"""
    
    def __init__(self, bot: Bot, command: str, api_key: str,
                 history_file: Optional[Path] = None,
                 stats_file: Optional[Path] = None,
                 content_file: Optional[Path] = None):
        self.bot = bot
        self.command = command
        self.api_key = api_key
        self.history_file = history_file
        self.stats_file = stats_file
        self.messages: List[Dict] = []
        self.stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_time": 0,
            "calls": []
        }
        self.error: Optional[Exception] = None
        self.final_text: Optional[str] = None
        self.content_file = content_file
        logger.info(f"Initializing chat with bot '{bot.name}' for command: {command}")
        
    def _update_history(self):
        """Update history file with current messages"""
        if self.history_file:
            try:
                history = {
                    "timestamp": datetime.now().isoformat(),
                    "bot": self.bot.name,
                    "command": self.command,
                    "messages": self.messages
                }
                self.history_file.write_text(json.dumps(history, indent=2))
            except Exception as e:
                logger.error(f"Failed to update history file: {e}")
                
    def _update_stats(self):
        """Update stats file with current statistics"""
        if self.stats_file:
            try:
                self.stats_file.write_text(json.dumps(self.stats, indent=2))
            except Exception as e:
                logger.error(f"Failed to update stats file: {e}")
    
    def _get_provider_config(self) -> Dict:
        """Get provider configuration for OpenRouter API"""
        if not self.bot.provider:
            return {"sort": "price"}
        elif self.bot.provider == "together" and "deepseek" in self.bot.llm.lower():
            return {"order": ["together"]}
        elif self.bot.provider == "google" and "gemini" in self.bot.llm.lower():
            return {"order": ["google"]}
        else:
            return {"order": [self.bot.provider]}
    
    def _clean_content(self, content: str) -> str:
        """Clean continuation markers and think tags from content"""
        # Remove CONTINUE markers at end
        if content.endswith("CONTINUE\n"):
            content = content[:-len("CONTINUE\n")].strip()
        if content.endswith("**CONTINUE**\n"):
            content = content[:-len("**CONTINUE**\n")].strip()
            
        # Remove think tags if present
        import re
        content = re.sub(r'<think>.*?</think>\n?', '', content, flags=re.DOTALL)
        
        return content.strip()

    def _create_progress_display(self, continuation_count: int) -> Progress:
        """Create a progress display for API calls"""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[white]•[/white]"),
            TextColumn("[yellow]{task.fields[status]}"),
            TextColumn("[bold white]Cmd: {task.fields[command]}•"),
            TextColumn("[bold white]Out: {task.fields[content_file]}•"),
            TextColumn("[bold blue]Bot: {task.fields[bot]}"),
            TextColumn("[white]•[/white]"),
            TextColumn("[green]In: {task.fields[tokens_in]}[/green]"),
            TextColumn("[white]•[/white]"),
            TextColumn("[cyan]Out: {task.fields[tokens_out]}[/cyan]"),
            TextColumn("[white]•[/white]"),
            TextColumn("[magenta]{task.fields[cost]}[/magenta]"),
            console=console
        )
        
        # Add initial task
        task = progress.add_task(
            "",
            command=self.command,
            bot=f"{self.bot.name} ({self.bot.llm})",
            content_file=self.content_file,
            status=f"Continuation {continuation_count}",
            tokens_in=self.stats['input_tokens'],
            tokens_out=self.stats['output_tokens'],
            cost=format_price(
                self.stats['input_tokens'],
                self.stats['output_tokens'],
                self.bot.input_price,
                self.bot.output_price
            ).split()[0]
        )
        
        return progress

    def _update_progress(self, progress: Progress, input_tokens: int = 0, 
                        output_tokens: int = 0, status: Optional[str] = None):
        """Update the progress display with new information"""
        fields = {}
        
        # Update tokens if provided
        if input_tokens or output_tokens:
            total_in = self.stats['input_tokens'] + input_tokens
            total_out = self.stats['output_tokens'] + output_tokens
            fields.update({
                'tokens_in': total_in,
                'tokens_out': total_out,
                'cost': format_price(total_in, total_out, 
                                self.bot.input_price, 
                                self.bot.output_price).split()[0]
            })
        
        # Update status if provided or add retry information
        if status:
            fields['status'] = status
        
        # Update the task
        progress.update(progress.tasks[0].id, **fields)

    def _make_api_call(self, messages: List[Dict], retry: int = 0, continuation_count: int = 0) -> Tuple[str, int, int]:
        """Make a single API call with retry logic"""
        max_retries = 3
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "BookBot",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.bot.llm,
            "messages": messages,
            "temperature": self.bot.temperature,
            "provider": self._get_provider_config()
        }
        
        try:
            start_time = time.time()
            with self._create_progress_display(continuation_count) as progress:

                # Log request details
                logger.info(f"Making OpenRouter API call ({self.command})")
                logger.debug(f"Request data: {json.dumps(data, indent=2)}")
                self._update_progress(progress, status="Generating...")

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                elapsed = time.time() - start_time
                
                # Log raw response for debugging
                logger.debug(f"Raw API response: {response.text}")
                
                if response.status_code != 200:
                    if response.status_code == 429:  # Rate limit
                        if retry < max_retries:
                            wait_time = int(response.headers.get('Retry-After', 5))
                            logger.warning(f"Rate limited. Waiting {wait_time}s (retry {retry + 1}/{max_retries})")
                            time.sleep(wait_time)
                            return self._make_api_call(messages, retry + 1)
                        else:
                            raise Exception("Max retries exceeded for rate limit")
                            
                    logger.error(f"Error response ({response.status_code}): {response.text}")
                    response.raise_for_status()
                    
                result = response.json()
                
                # Extract data from response
                if not result.get('choices'):
                    raise Exception("No choices in API response")
                    
                content = result["choices"][0]["message"]["content"]
                if not content or content.isspace():
                    if retry < max_retries:
                        logger.warning(f"Received empty content, retrying ({retry + 1}/{max_retries})")
                        time.sleep(2 ** retry)
                        return self._make_api_call(messages, retry + 1)
                    raise Exception("Empty response after retries")
                    
                # Get token counts
                input_tokens = result["usage"]["prompt_tokens"]
                output_tokens = result["usage"]["completion_tokens"]
                
                # Log success details
                words = len(content.split())
                logger.info(f"Response stats: {len(content)}b/{words}w/{output_tokens}t in {elapsed:.1f}s ({output_tokens/elapsed:.1f} t/s)")
                logger.info(f"Tokens: {input_tokens} in, {output_tokens} out")
                logger.debug(f"Content preview: {content[:200]}...")
                
                # In the final output, all these stats are stored in the file props.
                # The purpose of the stats file is to have a real time update. 
                # Ideally, this would also be persistent if the file is rewritten multiple times. 
                # But that is not implemented. 
                call_stats = {
                    "timestamp": datetime.now().isoformat(),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "elapsed": elapsed,
                    "retry": retry,
                    "provider": result.get("provider", "unknown"),
                    "model": result.get("model", self.bot.llm)
                }
                self.stats["calls"].append(call_stats)
                self.stats["input_tokens"] += input_tokens
                self.stats["output_tokens"] += output_tokens
                self.stats["total_time"] += elapsed
                
                self._update_stats()
            
            return content, input_tokens, output_tokens
            
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            if retry < max_retries:
                wait_time = 2 ** retry
                logger.warning(f"Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                time.sleep(wait_time)
                return self._make_api_call(messages, retry + 1)
            raise
    
    def generate(self, template_vars: Dict[str, str]):
        """Generate content using the bot"""
        try:
            # Validate template variables
            self.bot.validate_template_vars(template_vars)
            
            # Initialize messages with system prompt
            self.messages = [
                {"role": "system", "content": self.bot.system_prompt},
                {"role": "user", "content": (
                    self.bot.main_prompt.format(**template_vars) +
                    "\n Write one chunk of content. Write as much as you wish, and end your output with CONTINUE to have the chance to " +
                    "continue writing in a new chunk of content. CONTINUE must be at the end of your message if you want to write more than one chunk of content. " +
                    "Write THE END if this chunk concludes the section. You can write as much or as little as you wish, but typically aim for around 3000 words. " +
                    "If you CONTINUE, you'll get a current word count of how much you've written so far. You should ALWAYS write at least two chunks."
                )}
            ]
            
            # Track accumulated content
            accumulated_content = []
            continuation_count = 0
            max_continuations = 10  # Safety limit
            
            while continuation_count < max_continuations:
                continuation_count += 1
                logger.info(f"Making API call {continuation_count} for {self.command}")
                
                # Check context window
                total_tokens = sum(len(m['content'].split()) for m in self.messages) * 1.5  # Rough estimate
                if total_tokens > self.bot.context_window / 2:
                    logger.warning(f"Context window is more than half full ({total_tokens} tokens)")
                
                # Make API call
                content, input_tokens, output_tokens = self._make_api_call(self.messages, continuation_count)
                
                # Clean the content before accumulating
                cleaned_content = self._clean_content(content)
                accumulated_content.append(cleaned_content)
                
                # Calculate total words written
                total_words = sum(len(chunk.split()) for chunk in accumulated_content)
                logger.info(f"Total words written: {total_words}")
                
                # Update conversation history with raw content
                self.messages.append({"role": "assistant", "content": content})
                self._update_history()
                
                # Check if we're done
                if "THE END" in content:
                    logger.info("Found THE END marker")
                    break
                    
                # Not done - add continuation prompt
                continuation_prompt = (
                    f"You have written {total_words} words so far out of a minimum 3000 words. Continue writing the next chunk. " +
                    "When you're done with this chunk of text, write CONTINUE, and then end your message. Then you'll get a new prompt to " +
                    "continue writing the chapter. Don't write CONTINUE in the middle of your output, that *WILL NOT* help you write more. " +
                    "Only write it at the end of your output in order to get a new prompt where you can continue writing the chapter. " +
                    "Write THE END when you're done writing. CONTINUE or THE END *MUST* be at the end of your output. Be sure to write enough words."
                )
                self.messages.append({"role": "user", "content": continuation_prompt})
                logger.info("Added continuation prompt")
            
            # Clean and store final text
            if accumulated_content:
                final_text = "\n".join(accumulated_content)
                if "THE END" in final_text:
                    final_text = final_text.split("THE END")[0].strip()
                self.final_text = final_text
                if self.content_file:
                    f = TextFile(self.content_file)
                    f.content = final_text
                    f.metadata["command"] = self.command
                    f.metadata["bot"] = self.bot.name
                    f.metadata["timestamp"] = datetime.now().isoformat()
                    f.metadata["input_tokens"] = self.stats["input_tokens"]
                    f.metadata["output_tokens"] = self.stats["output_tokens"]
                    f.metadata["total_time"] = self.stats["total_time"]
                    f.metadata["continuation_count"] = continuation_count
                    f.metadata["provider"] = self.bot.provider
                    f.metadata["model"] = self.bot.llm
                    f.save()
                # Log final statistics
                # The stats file should probably be removed since it serves no purpose
                logger.info(f"Generation complete for {self.command}:")
                logger.info(f"Final length: {format_text_stats(self.final_text)}")
                logger.info(f"Total tokens: {self.stats['input_tokens']} in, {self.stats['output_tokens']} out")
                logger.info(f"Total cost: {format_price(self.stats['input_tokens'], self.stats['output_tokens'], self.bot.input_price, self.bot.output_price)}")
            else:
                raise Exception("No content generated")
            
        except Exception as e:
            logger.error(f"Error in generation: {str(e)}")
            self.error = e
            raise
            
    @property
    def has_error(self) -> bool:
        """Check if an error occurred during generation"""
        return self.error is not None
        
    @property
    def content(self) -> Optional[str]:
        """Get the generated content if available"""
        return self.final_text
        
    def get_stats(self) -> Dict:
        """Get the current statistics"""
        return self.stats.copy()
        
    def get_messages(self) -> List[Dict]:
        """Get the conversation messages"""
        return self.messages.copy()
    



#### YAML validation

def extract_template_vars(prompt: str) -> Set[str]:
    """Extract all template variables from a prompt string.
    Variables are in the format {variable_name}"""
    import re
    matches = re.findall(r'\{([^}]+)\}', prompt)
    return set(matches)

def validate_bot_template_vars(bot_config: dict, bot_type: BotType) -> Tuple[List[str], List[str]]:
    """Validate template variables in a bot configuration
    
    Returns:
        Tuple of (missing_vars, extra_vars)
    """
    required_vars = bot_type.required_vars
    
    # Extract variables from main prompt and continuation prompts
    found_vars = set()
    if 'main_prompt' in bot_config:
        found_vars.update(extract_template_vars(bot_config['main_prompt']))
    if 'continuation_prompt' in bot_config:
        found_vars.update(extract_template_vars(bot_config['continuation_prompt']))
    if 'continuation_prompt_initial' in bot_config:
        found_vars.update(extract_template_vars(bot_config['continuation_prompt_initial']))
        
    # Compare against required vars
    missing_vars = list(required_vars - found_vars)
    extra_vars = list(found_vars - required_vars)
    
    return missing_vars, extra_vars

def validate_bot_yaml(file_path: Path) -> bool:
    """Validate a bot YAML file's template variables
    
    Returns:
        bool: True if validation passes
    """
    try:
        with file_path.open('r') as f:
            config = yaml.safe_load(f)
            
        # Skip validation for default config
        if config.get('type', '').upper() == 'DEFAULT':
            return True
            
        bot_type = BotType[config['type'].upper()]
        missing_vars, extra_vars = validate_bot_template_vars(config, bot_type)
        
        if missing_vars or extra_vars:
            logger.warning(f"Template variable issues in {file_path.name}:")
            if missing_vars:
                logger.warning(f"  Missing required variables: {', '.join(missing_vars)}")
            if extra_vars:
                logger.warning(f"  Extra variables not in spec: {', '.join(extra_vars)}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error validating {file_path}: {e}")
        return False

####################### END NEW BOT SYSTEM ########################








@dataclass
class LLMConfig:
    """Configuration for an LLM model"""
    group: str
    name: str
    provider: str
    cost_per_million_tokens: float
    temperature: float = DEFAULT_TEMPERATURE
    
    @property
    def full_name(self) -> str:
        return f"{self.group}/{self.name}"

# Available LLMs and their configurations
AVAILABLE_LLMS = [
    LLMConfig("deepseek", "deepseek-r1", "Together", 15.0),
    LLMConfig("openai", "gpt-4o", "", 15.0),
    LLMConfig("anthropic", "claude-2.1", "", 8.0),
    LLMConfig("openai", "gpt-3.5-turbo", "", 0.5),
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
    
    def __init__(self, filepath: Path, config: Optional[Dict] = None):
        self.filepath = Path(filepath)
        self.content = ""
        self.metadata = {}
        self.conversation_history = []
        self.config = config if config else DEFAULT_CONFIG
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
            
            # If backups are enabled, create a backup
            if self.filepath.exists() and self.filepath.stat().st_size > 0:
                backup_dir = Path(self.filepath.parent, self.config['backup_dir'])
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_dir / f"{self.filepath.name}.bak"
                shutil.copy(self.filepath, backup_path)
                logger.info(f"Backup created at {backup_path}")
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
        logger.setLevel(logging.getLevelName(self.config['logging_level'].upper()))
        # Ensure required directories exist
        for directory in [COMMON_DIR, CHAPTERS_DIR, PROMPTS_DIR, REVIEWS_DIR, FRONTMATTER_DIR, BACKMATTER_DIR, FINAL_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
            
        self._init_bots()
        self._init_title()
    
    def _init_bots(self):
        initialize_bot_yaml(Path(self.config['bot_dir']))

    def _init_title(self):
        """Initialize default title file if it doesn't exist"""
        title_file = FRONTMATTER_DIR / "title.md"
        if not title_file.exists():
            title_file.write_text(DEFAULT_TITLE_FILE)

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
        """Load and fill a template. Designed to be somewhat flexible to how the variables are used in the template."""
        template_path = PROMPTS_DIR / f"{template_name}.md"
        if not template_path.exists():
            raise BookBotError(f"Template not found: {template_name}")
            
        content = template_path.read_text()
        if variables:
            for key, value in variables.items():
                # Handle both {{ key }} and {{key}} formats
                content = content.replace(f"{{{{ {key} }}}}", str(value))
                content = content.replace(f"{{{{{key}}}}}", str(value))
                
                # Also handle potential YAML-style variables
                content = content.replace(f"{ key }", str(value))
                content = content.replace(f"{key}", str(value))
        
        # Clean up any remaining template markers
        content = re.sub(r'{{\s*\w+\s*}}', '', content)
        
        return content.strip()

    def _call_llm(self, output_file: str, bot_name: str, template_vars: Optional[Dict[str, str]] = None, max_retries: int = 3, command:str="") -> Tuple[str, int, int]:
        """
        Call the LLM API using a specific bot configuration.
        
        Args:
            output_file: File prefix to save the 3 outputs (stats, history, content)
            bot_name: Name of the bot YAML file (without .yaml extension)
            template_vars: Variables to fill in the bot's prompt template
            max_retries: Maximum number of retries per API call
            command (Optional): Command name for logging and progress bar display only
        Returns:
            Tuple of (final_text, total_input_tokens, total_output_tokens)
            (In general just use the output files though)
        """
        try:
            # Load bot configuration
            # TODO FIX THIS
            bot_dir = Path(self.config['bot_dir'])
            bot_path = bot_dir / f"{bot_name}.yaml"
            if not bot_path.exists():
                raise BookBotError(f"Bot configuration not found: {bot_name}")
                
            # Load the bot
            bot = Bot.from_file(bot_path)
            
            # Override LLM settings if specified in BookBot
            if self.llm:
                bot.llm = self.llm.full_name
                bot.provider = self.llm.provider
                bot.temperature = self.llm.temperature
                bot.input_price = self.llm.cost_per_million_tokens
                bot.output_price = self.llm.cost_per_million_tokens
                
            history_file = Path(output_file + "_history.json")
            stats_file = Path(output_file + "_stats.json")
            content_file = Path(output_file + ".md")
                
            # Initialize BotChat
            chat = BotChat(
                bot=bot,
                command=command,
                api_key=self.api_key,
                history_file=history_file,
                stats_file=stats_file,
                content_file=content_file
            )
            
            # Use template variables if provided, otherwise use prompt directly
            vars_to_use = template_vars 
            
            # Generate content
            chat.generate(vars_to_use)
            
            if chat.has_error:
                raise Exception(f"BotChat error: {chat.error}")
                
            # Get results
            content = chat.final_text
            stats = chat.get_stats()
            
            return (
                content,
                stats["input_tokens"],
                stats["output_tokens"]
            )
                
        except Exception as e:
            logger.error(f"Error in _call_llm using bot {bot_name}: {str(e)}")
            raise BookBotError(f"LLM call failed: {str(e)}")

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
            initial = TextFile(Path("initial.md"), config=self.config)
            if not initial.filepath.exists():
                raise BookBotError("initial.md not found. Please create it with your story description.")
            
            # Generate setting
            self._call_llm("common/setting", "write_setting", {"initial": initial.content}, command="write_setting")
            
            self._git_commit("Generated setting")
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
            initial = TextFile(Path("initial.md"), config=self.config)
            setting = TextFile(COMMON_DIR / "setting.md", config=self.config)
            if not initial.filepath.exists() or not setting.filepath.exists():
                raise BookBotError("Required files (initial.md and setting.md) not found")

            # Generate characters using the write_characters bot
            self._call_llm(
                "common/characters",
                "write_characters",
                {
                    "initial": initial.content,
                    "setting": setting.content
                },
                command="write_characters"
            )

            self._git_commit("Generated characters")
            self._generate_preview()
            
            console.print("\n[green]✓[/green] Characters generated successfully")
            
        except Exception as e:
            logger.error(f"Error writing characters: {e}")
            raise BookBotError(f"Failed to write characters: {e}")

    def write_outline(self):
        """Generate the story outline"""
        try:
            # Load required files
            initial = TextFile(Path("initial.md"), config=self.config)
            setting = TextFile(COMMON_DIR / "setting.md", config=self.config)
            characters = TextFile(COMMON_DIR / "characters.md", config=self.config)
            if not all(f.filepath.exists() for f in [initial, setting, characters]):
                raise BookBotError("Required files (initial.md, setting.md, characters.md) not found")

            # Generate outline using the write_outline bot
            self._call_llm(
                "common/outline",
                "write_outline",
                {
                    "initial": initial.content,
                    "setting": setting.content,
                    "characters": characters.content
                },
                command="write_outline"
            )

            self._git_commit("Generated outline")
            self._generate_preview()
            
            console.print("\n[green]✓[/green] Outline generated successfully")
            
        except Exception as e:
            logger.error(f"Error writing outline: {e}")
            raise BookBotError(f"Failed to write outline: {e}")

    def write_commons_review(self):
        """Generate the commons review"""
        try:
            # Load required files
            initial = TextFile(Path("initial.md"), config=self.config)
            setting = TextFile(COMMON_DIR / "setting.md", config=self.config)
            characters = TextFile(COMMON_DIR / "characters.md", config=self.config)
            outline = TextFile(COMMON_DIR / "outline.md", config=self.config)
            if not all(f.filepath.exists() for f in [initial, setting, characters, outline]):
                raise BookBotError("Required files not found")

            # Generate review using the review_commons bot
            self._call_llm(
                "common/commons_review",
                "review_commons",
                {
                    "initial": initial.content,
                    "setting": setting.content,
                    "characters": characters.content,
                    "outline": outline.content
                },
                command="write_commons_review"
            )

            self._git_commit("Generated commons review")
            self._generate_preview()
            
            console.print("\n[green]✓[/green] Commons review generated successfully")
            
        except Exception as e:
            logger.error(f"Error writing commons review: {e}")
            raise BookBotError(f"Failed to write commons review: {e}")

    def write_chapter(self, chapter_num: int):
        """Write a new chapter"""
        try:
            # Load necessary context
            outline = TextFile(COMMON_DIR / "outline.md", config=self.config)
            setting = TextFile(COMMON_DIR / "setting.md", config=self.config)
            characters = TextFile(COMMON_DIR / "characters.md", config=self.config)
            commons_review = TextFile(COMMON_DIR / "commons_review.md", config=self.config)
            
            prev_chapter_content = self._get_previous_chapter_content(chapter_num)
            if prev_chapter_content:
                prev_chapter_content = self._truncate_to_last_n_words(prev_chapter_content)

            # Generate chapter using write_chapter bot
            self._call_llm(
                f"chapters/chapter_{chapter_num:02d}",
                "write_chapter",
                {
                    "chapter_number": chapter_num,
                    "outline": outline.content,
                    "setting": setting.content,
                    "characters": characters.content,
                    "previous_chapter": prev_chapter_content or "No previous chapter available."
                },
                command=f"write_chapter_{chapter_num}"
            )

            self._git_commit(f"Generated chapter {chapter_num}")
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
            
            chapter = TextFile(chapter_path, config=self.config)

            # Edit chapter using edit_chapter bot
            self._call_llm(
                f"chapters/chapter_{chapter_num:02d}",
                "edit_chapter",
                {
                    "chapter_number": chapter_num,
                    "content": chapter.content,
                    "edit_notes": "No previous edit notes available."  # Could store previous edits in future
                },
                command=f"edit_chapter_{chapter_num}"
            )

            self._git_commit(f"Edited chapter {chapter_num}")
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
                chapter = TextFile(chapter_path, config=self.config)
                chapters.append(chapter.content)
                chapter_num += 1
            
            if not chapters:
                raise BookBotError("No chapters found to review")

            # Generate review using review_whole bot
            review_num = len(list(REVIEWS_DIR.glob("*.md"))) + 1
            self._call_llm(
                f"reviews/review_{review_num:02d}",
                "review_whole",
                {
                    "content": "\n\n".join(chapters)
                },
                command=f"review_book_{review_num}"
            )

            self._git_commit(f"Generated review #{review_num}")
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Book review generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating review: {e}")
            raise BookBotError(f"Failed to generate review: {e}")

    def review_and_edit_with_2_bots(self, reviewer_bot: str, editor_bot: str, file: str):
        """Review and edit a file using two different bots.
        First, loads the file, which can be a chapter file or commons file specified by its path in either case.
        Then call the LLM with the reviewer bot and the file to generate a new review file.
        Then call the LLM with the editor bot and the review file to edit the original file (overwriting it)."""
        try:
            # Load the file to be reviewed
            file_path = Path(file)
            if not file_path.exists():
                raise BookBotError(f"File not found: {file}")
                
            text_file = TextFile(file_path, config=self.config)

            # Generate review using the reviewer bot
            review_file = file_path.with_suffix('.review.md')
            self._call_llm(
                review_file,
                reviewer_bot,
                {
                    "content": text_file.content
                },
                command=f"review_and_edit_with_2_bots_{reviewer_bot}_{editor_bot}"
            )

            # Edit the original file using the editor bot
            self._call_llm(
                file_path,
                editor_bot,
                {
                    "content": text_file.content,
                    "review": TextFile(review_file).content
                },
                command=f"edit_with_2_bots_{reviewer_bot}_{editor_bot}"
            )

            self._git_commit(f"Reviewed and edited {file}")
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Reviewed and edited successfully")
            
        except Exception as e:
            logger.error(f"Error reviewing and editing with 2 bots: {e}")
            raise BookBotError(f"Failed to review and edit: {e}")



    def _get_previous_chapter_content(self, chapter_num: int) -> Optional[str]:
        """Get content from the previous chapter if it exists"""
        if chapter_num <= 1:
            return None
            
        prev_chapter = CHAPTERS_DIR / f"chapter_{chapter_num-1:02d}.md"
        if not prev_chapter.exists():
            return None
            
        try:
            return TextFile(prev_chapter).content
        except Exception as e:
            logger.warning(f"Could not read previous chapter: {e}")
            return None

    def _truncate_to_last_n_words(self, text: str, n: int = 5000) -> str:
        """
        Truncate text to last N words, preserving complete sentences.
        
        Args:
            text: The text to truncate
            n: Maximum number of words to keep (default 5000)
            
        Returns:
            Truncated text ending with complete sentences
        """
        # Split into sentences (handling common abbreviations)
        import re
        
        # Pattern matches sentence endings while preserving common abbreviations
        sent_pattern = r'(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+'
        sentences = re.split(sent_pattern, text)
        
        # Count words in each sentence
        sentence_word_counts = [len(s.split()) for s in sentences]
        
        # Find how many sentences we need from the end to get close to N words
        total_words = 0
        sentences_needed = 0
        for count in reversed(sentence_word_counts):
            if total_words + count > n:
                break
            total_words += count
            sentences_needed += 1
        
        # Get the required sentences from the end
        final_sentences = sentences[-sentences_needed:] if sentences_needed > 0 else [sentences[-1]]
        
        # Join sentences back together
        result = ' '.join(final_sentences).strip()
        
        logger.info(f"Truncated previous chapter from {sum(sentence_word_counts)} to {len(result.split())} words")
        
        return result
    
    def _generate_preview(self):
        """Generate HTML preview of all content"""
        try:
            # Collect all files by category
            files = {
                "Chapters": sorted(
                    [TextFile(p, config=self.config) for p in CHAPTERS_DIR.glob("*.md")],
                    key=lambda f: int(f.filepath.stem.split('_')[1])
                ),
                "Common": [TextFile(p, config=self.config) for p in COMMON_DIR.glob("*.md")],
                "Reviews": [TextFile(p, config=self.config) for p in REVIEWS_DIR.glob("*.md")]
            }
            
            # Generate preview
            preview = PreviewGenerator()
            preview.generate(files)
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            console.print(f"[red]![/red] Failed to generate preview: {e}")

    def _get_book_metadata(self) -> dict:
        """Get book metadata from title.md if it exists"""
        metadata = {
            "title": "Untitled",
            "author": "Anonymous",
            "language": "en-US",
            "rights": "All rights reserved",
            "date": datetime.now().strftime("%Y")
        }
        
        title_file = FINAL_DIR / "front_matter" / "title.md"
        if title_file.exists():
            content = title_file.read_text(encoding='utf-8')
            
            # Parse YAML metadata if present
            if content.startswith('---'):
                try:
                    import yaml
                    _, yaml_text, _ = content.split('---', 2)
                    file_metadata = yaml.safe_load(yaml_text)
                    if isinstance(file_metadata, dict):
                        metadata.update(file_metadata)
                except Exception as e:
                    logger.warning(f"Error parsing title.md metadata: {e}")

        return metadata
            
        
    def _create_pandoc_defaults(self, output_format: str, cover_image: Optional[Path] = None) -> Path:
        if output_format not in ['epub', 'pdf']:
            raise ValueError(f"Unsupported output format: {output_format}")
            
        defaults_dir = Path(".pandoc")
        defaults_dir.mkdir(exist_ok=True)
        
        defaults_file = defaults_dir / f"{output_format}-defaults.yaml"
        
        common_settings = {
            "metadata": {
                "title": self.config.get("book_title", "Untitled"),
                "author": self.config.get("author", "Anonymous"),
                "language": self.config.get("language", "en-US"),
                "rights": self.config.get("rights", "All rights reserved")
            },
            "top-level-division": "chapter",
            #"number-sections": True, NOt needed
        }

        
        if output_format == 'epub':
            settings = {
                **common_settings,
                "toc": True,
                "toc-depth": 2,
            }
            if cover_image:
                settings["epub-cover-image"] = str(cover_image)
        else:  # PDF
            settings = {
                **common_settings,
                "pdf-engine": "xelatex",
                # Note: PDF cover is handled via LaTeX in header-includes
                "variables": {
                    "papersize": "6in:9in",
                    #"mainfont": "Garamond",
                    "mainfont": "Times New Roman",
                    "fontsize": "11pt",
                    "geometry": [
                        "paperwidth=6in",
                        "paperheight=9in",
                        "margin=1in",
                        "headheight=14pt"
                    ],
                    "linkcolor": "black",
                    "header-includes": [
                        "\\usepackage{fancyhdr}",
                        "\\usepackage{graphicx}",
                        "\\pagestyle{fancy}",
                        "\\fancyhead{}",
                        "\\fancyhead[CO]{\\leftmark}",
                        "\\fancyhead[CE]{\\rightmark}",
                        "\\fancyfoot{}",
                        "\\fancyfoot[C]{\\thepage}"
                    ]
                }
            }
        
        try:
            import yaml
            with defaults_file.open('w', encoding='utf-8') as f:
                yaml.dump(settings, f, sort_keys=False, allow_unicode=True)
            return defaults_file
        except Exception as e:
            logger.error(f"Error creating pandoc defaults file: {e}")
            raise BookBotError(f"Failed to create pandoc defaults: {e}")

    def _merge_markdown_files(self) -> Path:
        """Merge all markdown files into a single file in the correct order"""
        try:
            merged_content = []
            
            # Front matter (if exists)
            front_matter_dir = FINAL_DIR / "front_matter"
            if front_matter_dir.exists():
                for file in sorted(front_matter_dir.glob("*.md")):
                    merged_content.append(file.read_text(encoding='utf-8'))
            
            # Add main content
            chapters = sorted(
                [p for p in FINAL_DIR.glob("chapter_*.md")],
                key=lambda p: int(p.stem.split('_')[1])
            )
            
            for chapter in chapters:
                # Add chapter marker for proper pandoc processing
                chapter_content = "" # for numbering chapters f"\n# {chapter.stem.replace('_', ' ').title()}\n\n"
                chapter_content += chapter.read_text(encoding='utf-8')
                merged_content.append(chapter_content)
            
            # Back matter (if exists)
            back_matter_dir = FINAL_DIR / "back_matter"
            if back_matter_dir.exists():
                for file in sorted(back_matter_dir.glob("*.md")):
                    merged_content.append(file.read_text(encoding='utf-8'))
            
            # Write merged content
            merged_file = FINAL_DIR / "book.md"
            merged_file.write_text("\n\n".join(merged_content), encoding='utf-8')
            return merged_file
            
        except Exception as e:
            logger.error(f"Error merging markdown files: {e}")
            raise BookBotError(f"Failed to merge markdown files: {e}")

    def _run_pandoc(self, input_file: Path, output_format: str, cover_image: Optional[Path] = None) -> Path:
        """Run pandoc to convert merged markdown to specified format"""
        try:
            import subprocess
            from shutil import which
            
            # Check if pandoc is installed
            if not which('pandoc'):
                raise BookBotError("Pandoc is not installed")
                
            # Create defaults file
            defaults_file = self._create_pandoc_defaults(output_format, cover_image)
            
            # For PDF, we need to create a temporary LaTeX template if there's a cover
            if output_format == 'pdf' and cover_image:
                cover_tex = self._create_pdf_cover_template(cover_image)
                input_file = self._prepend_cover_to_content(cover_tex, input_file)
            
            # Set up output file
            output_file = FINAL_DIR / f"book.{output_format}"
            
            # Build pandoc command
            cmd = [
                "pandoc",
                "--defaults", str(defaults_file),
                "-o", str(output_file),
                str(input_file)
            ]
            
            # Run pandoc
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"Generating {output_format.upper()}...",
                    total=None
                )
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    raise BookBotError(
                        f"Pandoc conversion failed: {result.stderr}"
                    )
                
            return output_file
            
        except subprocess.SubprocessError as e:
            logger.error(f"Pandoc conversion failed: {e}")
            raise BookBotError(f"Failed to run pandoc: {e}")
        except Exception as e:
            logger.error(f"Error during pandoc conversion: {e}")
            raise BookBotError(f"Failed to convert file: {e}")

    def _create_pdf_cover_template(self, cover_image: Path) -> Path:
        """Create a LaTeX template for the PDF cover page"""
        try:
            cover_template = FINAL_DIR / "cover.tex"
            template_content = f"""\\begin{{titlepage}}
    \\thispagestyle{{empty}}
    \\includegraphics[width=\\textwidth,height=\\textheight,keepaspectratio]{{"{cover_image}"}}
    \\end{{titlepage}}
    """
            cover_template.write_text(template_content)
            return cover_template
        except Exception as e:
            logger.error(f"Error creating PDF cover template: {e}")
            raise BookBotError(f"Failed to create PDF cover template: {e}")

    def _prepend_cover_to_content(self, cover_tex: Path, content_file: Path) -> Path:
        """Combine cover LaTeX with main content"""
        try:
            combined_file = FINAL_DIR / "book_with_cover.md"
            cover_content = cover_tex.read_text()
            main_content = content_file.read_text()
            combined_file.write_text(f"{cover_content}\n\n{main_content}")
            return combined_file
        except Exception as e:
            logger.error(f"Error combining cover with content: {e}")
            raise BookBotError(f"Failed to combine cover with content: {e}")

    def generate_epub(self, cover_image: Optional[Path] = None):
        """Generate EPUB version of the book"""
        try:
            if cover_image and not cover_image.exists():
                raise BookBotError(f"Cover image not found: {cover_image}")
                
            merged_file = self._merge_markdown_files()
            epub_file = self._run_pandoc(merged_file, 'epub', cover_image)
            console.print(f"\n[green]✓[/green] EPUB generated: {epub_file}")
        except Exception as e:
            logger.error(f"Error generating EPUB: {e}")
            console.print(f"[red]![/red] Failed to generate EPUB: {e}")
            raise

    def generate_pdf(self, cover_image: Optional[Path] = None):
        """Generate PDF version of the book"""
        try:
            if cover_image and not cover_image.exists():
                raise BookBotError(f"Cover image not found: {cover_image}")
                
            merged_file = self._merge_markdown_files()
            pdf_file = self._run_pandoc(merged_file, 'pdf', cover_image)
            console.print(f"\n[green]✓[/green] PDF generated: {pdf_file}")
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            console.print(f"[red]![/red] Failed to generate PDF: {e}")
            raise

    # Modified finalize method
    def finalize(self):
        """Create final versions of all content"""
        try:
            if FINAL_DIR.exists():
                shutil.rmtree(FINAL_DIR)
            FINAL_DIR.mkdir(parents=True)
            
            # Copy all chapters
            for chapter_path in sorted(CHAPTERS_DIR.glob("*.md")):
                chapter = TextFile(chapter_path, config=self.config)
                final_path = FINAL_DIR / chapter_path.name
                final_path.write_text(chapter.content)
            
            # Copy common files
            for common_path in COMMON_DIR.glob("*.md"):
                final_path = FINAL_DIR / common_path.name
                final_path.write_text(common_path.read_text())
            
            # Check for cover image
            cover_image = None
            if (FINAL_DIR / "cover.jpg").exists():
                cover_image = FINAL_DIR / "cover.jpg"
            elif (FINAL_DIR / "cover.png").exists():
                cover_image = FINAL_DIR / "cover.png"
                
            # Generate EPUB and PDF versions
            self.generate_epub(cover_image)
            self.generate_pdf(cover_image)
            
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
    subparsers.add_parser('write-commons-review', help='Generate commons review (plot hole fix)')

    # Write chapter command
    write_parser = subparsers.add_parser('write-chapter', help='Write a new chapter')
    write_parser.add_argument('number', type=int, help='Chapter number')
    
    # Edit chapter command
    edit_parser = subparsers.add_parser('edit-chapter', help='Edit an existing chapter')
    edit_parser.add_argument('number', type=int, help='Chapter number')
    

    # Extend chapter command
    extend_parser = subparsers.add_parser('extend-chapter', help='Edit an existing chapter to make it longer')
    extend_parser.add_argument('number', type=int, help='Chapter number')

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
        elif args.command == 'write-commons-review':
            bot.write_commons_review()
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