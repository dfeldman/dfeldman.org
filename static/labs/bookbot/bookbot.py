#!/usr/bin/env python3

import os
import json
import shutil
import argparse
import requests
import logging
import time
from typing import Dict, List, Optional, Tuple, Set, Union, Any
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


# Disable all LLM calls and file modifications
# When enabled, everything runs normally except:
# 1. No API calls are made to LLMs
# 2. No files are created or modified
# 3. Simulated content is returned for testing/debugging
# You can see if it works through logs
DRY_RUN = False

# Use Gemini Flash and override chosen LLMs
# This greatly reduces costs for testing/debugging
# Then disable to use the actual LLMs
# Gemini Flash is about 1/15th the cost of Claude 
CHEAP_MODE = False

# Set up rich console for better output
console = Console()

# Set up logging with improved formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bookbot.log'),
        logging.StreamHandler()
    ]
)

# Create BookBot logger
logger = logging.getLogger('BookBot')
logger.setLevel(logging.DEBUG)

# Add a helper method to logger for JSON formatting
def format_json(obj):
    """Format JSON objects for logging with proper indentation and handling of nested JSON."""
    if isinstance(obj, str):
        # Try to parse string as JSON first to handle JSON-in-JSON
        try:
            parsed = json.loads(obj)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # If it's not valid JSON, return it as is or look for JSON-like patterns
            # Try to find and format JSON within the string
            try:
                # Look for common JSON patterns like {"key": "value"}
                import re
                json_pattern = r'(\{[^{}]*\{.*\}[^{}]*\})'
                matches = re.findall(json_pattern, obj)
                
                # For each potential JSON string found, try to parse and format
                for match in matches:
                    try:
                        parsed_match = json.loads(match)
                        formatted_match = json.dumps(parsed_match, indent=2, ensure_ascii=False)
                        obj = obj.replace(match, f"\n{formatted_match}\n")
                    except:
                        pass
            except:
                pass
            return obj
    else:
        # If it's already a Python object, format it as JSON
        try:
            return json.dumps(obj, indent=2, ensure_ascii=False)
        except:
            return str(obj)

# Attach the formatter to the logger module
logger.format_json = format_json
# API Constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TEMPERATURE = 0.8

# Directory structure - these are relative paths within the book directory
PREVIEW_SUBDIR = "preview"
FINAL_SUBDIR = "final"
COMMON_SUBDIR = "common"
CHAPTERS_SUBDIR = "chapters"
PROMPTS_SUBDIR = "prompts"
REVIEWS_SUBDIR = "reviews"
FRONTMATTER_SUBDIR = "frontmatter"
BACKMATTER_SUBDIR = "backmatter"
BOTS_SUBDIR = "bots"

# Global variables
# BOOK_DIR will be set by the CLI and used throughout the code
BOOK_DIR = Path(".")

# These global variables will be accessible throughout the application
# For directories derived from BOOK_DIR
PREVIEW_DIR = None
FINAL_DIR = None
COMMON_DIR = None
CHAPTERS_DIR = None
PROMPTS_DIR = None
REVIEWS_DIR = None
FRONTMATTER_DIR = None
BACKMATTER_DIR = None
BOTS_DIR = None

# Default configuration
DEFAULT_CONFIG = {
    "max_tokens": 2000,
    "temperature": 0.8,
    "git_enabled": False,
    "auto_preview": True,
    "backup_enabled": True,
    "backup_dir": ".bookbot_backups",
    "logging_level": "DEBUG",
    "bot_dir": "bots",
    "review_dir": "reviews",
    "expansion": {
        "enabled": True,
        "romance_bot": "anthropic/claude-3-opus-20240229",
        "action_bot": "anthropic/claude-3-opus-20240229",
        "dialogue_bot": "anthropic/claude-3-opus-20240229",
        "description_bot": "anthropic/claude-3-opus-20240229",
        "worldbuilding_bot": "anthropic/claude-3-opus-20240229",
        "character_bot": "anthropic/claude-3-opus-20240229",
        "suspense_bot": "anthropic/claude-3-opus-20240229",
        "emotion_bot": "anthropic/claude-3-opus-20240229",
        "foreshadowing_bot": "anthropic/claude-3-opus-20240229",
        "metaphor_bot": "anthropic/claude-3-opus-20240229",
        "default_bot": "anthropic/claude-3-sonnet-20240229",
        "context_window": 500,
        "max_retries": 3
    }
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
        
        "expand_chapter": {
            "name": "expand_chapter",
            "type": "expand_chapter",
            "llm": "anthropic/claude-3-opus-20240229",
            "system_prompt": """You are an expert book editor and writing coach specializing in helping authors expand and enrich their content.
You understand how to identify sections of text that would benefit from expansion and specialized treatment.""",
            "main_prompt": """Expand this chapter to make it longer and more detailed. Add appropriate section tags to allow for specialized processing. 
The following tags are available:

[BEGIN ROMANCE]...[END ROMANCE] - For intimate or romantic scenes between characters
[BEGIN ACTION]...[END ACTION] - For action sequences, fights, chases, or other high-energy moments
[BEGIN DIALOGUE]...[END DIALOGUE] - For important conversations between characters
[BEGIN DESCRIPTION]...[END DESCRIPTION] - For detailed scene-setting or descriptive passages
[BEGIN WORLDBUILDING]...[END WORLDBUILDING] - For sections that establish the world, culture, history, etc.
[BEGIN CHARACTER]...[END CHARACTER] - For character development, introspection, or backstory
[BEGIN SUSPENSE]...[END SUSPENSE] - For tense moments of anticipation or dread
[BEGIN EMOTION]...[END EMOTION] - For emotionally charged moments or character feelings
[BEGIN FORESHADOWING]...[END FORESHADOWING] - For hints about future events
[BEGIN METAPHOR]...[END METAPHOR] - For extended metaphors or symbolic passages

Instructions:
1. Identify 3-5 key sections that would benefit from expansion and specialized processing
2. Add the appropriate tags around these sections
3. Expand the content between the tags to make it more detailed (each tagged section should be at least 150 words)
4. Add entirely new sections if needed to enhance the story
5. Ensure all tagged sections integrate naturally with the surrounding text

Note that each section should only have ONE tag type. Do not nest tags.

Chapter to expand:
{content}"""
        },
        
        "expand_default": {
            "name": "expand_default",
            "type": "expand_default",
            "llm": "anthropic/claude-3-opus-20240229",
            "system_prompt": """You are an expert writer specializing in improving text quality.
Create vivid, engaging, and impactful prose that enhances the original content while maintaining its meaning and context.""",
            "main_prompt": """Rewrite the following section to make it more engaging, vivid, and impressive.
Focus on creating high-quality prose that fits the surrounding context.

Context before the section:
---
{context_before}
---

Section to improve ({section_type} section):
---
{section}
---

Context after the section:
---
{context_after}
---

Your task is to rewrite ONLY the section, making it more vivid and engaging.
Maintain consistency with the surrounding context and characters.
Do not modify the overall meaning or plot points, just improve the quality of the writing.

Rewritten section:"""
        },
        
        "expand_romance": {
            "name": "expand_romance",
            "type": "expand_romance",
            "llm": "anthropic/claude-3-opus-20240229",
            "system_prompt": """You are an expert writer specializing in romance, emotional connection, and intimate character dynamics. 
Create vivid, emotionally resonant romantic scenes that feel authentic and moving.""",
            "main_prompt": """Rewrite the following ROMANCE section to make it more engaging, vivid, and emotionally resonant.

Context before the section:
---
{context_before}
---

Section to improve:
---
{section}
---

Context after the section:
---
{context_after}
---

Focus on:
- Emotional depth and authentic character feelings
- Subtle body language, attraction cues, and tension between characters
- Chemistry, yearning, vulnerability, and emotional connection
- Sensory details and nuanced expressions to convey intimacy and desire

Your task is to rewrite ONLY the section between the markers, making it more emotionally compelling.
Maintain consistency with the surrounding context and characters.
Do not modify the overall meaning or plot points, just improve the quality of the writing.

Rewritten ROMANCE section:"""
        },
        
        "expand_action": {
            "name": "expand_action",
            "type": "expand_action",
            "llm": "anthropic/claude-3-opus-20240229",
            "system_prompt": """You are an expert action sequence writer with a background in choreography and cinematography. 
Create dynamic, clear, and impactful action scenes with excellent pacing.""",
            "main_prompt": """Rewrite the following ACTION section to make it more engaging, vivid, and impactful.

Context before the section:
---
{context_before}
---

Section to improve:
---
{section}
---

Context after the section:
---
{context_after}
---

Focus on:
- Pacing, kinetic energy, clear spatial awareness, and visceral impact
- Short sentences for intensity, precise verbs for impact, and tension through rhythm
- Combat choreography, environmental interaction, and physical sensations
- Clear cause-and-effect sequencing of action

Your task is to rewrite ONLY the section, making it more dynamic and engaging.
Maintain consistency with the surrounding context and characters.
Do not modify the overall meaning or plot points, just improve the quality of the writing.

Rewritten ACTION section:"""
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
        
        "split_outline": {
            "name": "split_outline",
            "type": "split_outline",
            "llm": "anthropic/claude-3-haiku-20240307",  # Use cheaper model for splitting
            "input_price": 1.00,
            "output_price": 3.00,
            "system_prompt": """You are an expert at organizing and structuring book outlines.
Split book outlines into well-defined chapter sections for focused writing.""",
            "main_prompt": """Split this book outline into individual chapter outlines. 

For each chapter, create a separate markdown section starting with this exact format:
```
---
# Chapter {number}: {title}
```

Make sure each chapter section contains:
1. The full chapter title and number
2. All details about that chapter from the outline
3. A well-organized breakout of scenes or sections within the chapter
4. Character development notes specific to this chapter
5. Any plot points, revelations, or emotional beats in this chapter

Original Outline:
{outline}"""
        },
        
        "split_chapter": {
            "name": "split_chapter",
            "type": "split_chapter",
            "llm": "anthropic/claude-3-haiku-20240307",  # Use cheaper model for splitting
            "input_price": 1.00,
            "output_price": 3.00,
            "system_prompt": """You are an expert at organizing and structuring book chapters.
Split chapter outlines into well-defined sections for focused writing.""",
            "main_prompt": """Split this chapter outline into individual sections that can be written separately.

Create 3-6 distinct sections, each starting with this exact format:
```
---
## Section {number}: {descriptive_title}
```

Each section should:
1. Cover a complete scene or logical segment of the chapter
2. Have a clear beginning and ending point
3. Include specific details from the outline relevant to that section
4. Be approximately equal in expected length to other sections
5. Flow naturally from one section to the next

Original Chapter Outline:
{chapter_outline}"""
        },
        
        "write_section": {
            "name": "write_section",
            "type": "write_section",
            "system_prompt": """You are an expert prose writer specializing in focused, detailed scenes.
Write engaging, well-crafted sections of book chapters that maintain consistent style and voice.
Focus on rich descriptions, natural dialogue, and clear action.""",
            "main_prompt": """Write Section {section_number} of Chapter {chapter_number}. Include:
- Rich, evocative descriptions that engage the senses
- Natural, character-driven dialogue that reveals personality
- Clear action and scene progression
- Character thoughts and emotions appropriate to the moment
- Consistent pacing and tone with the chapter's purpose

Section Outline:
{section_outline}

Previous Section (if applicable):
{previous_section}

Setting (for reference):
{setting}

Characters (for reference):
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
    WRITE_SECTION = auto()     # section_number, chapter_number, section_outline, setting, characters, previous_section
    SPLIT_OUTLINE = auto()     # outline
    SPLIT_CHAPTER = auto()     # chapter_outline
    REVIEW_COMMONS = auto()    # file_type, content, context
    REVIEW_CHAPTER = auto()    # chapter_number, content, outline, setting, characters
    EDIT_CHAPTER = auto()      # chapter_number, outline, setting, characters, review, content
    REVIEW_WHOLE = auto()      # content
    SELF_EDIT = auto()          # initial, characters, settings, content
    
    @property
    def required_vars(self) -> Set[str]:
        """Get required template variables for this bot type"""
        return {
            BotType.DEFAULT: set(),
            BotType.WRITE_OUTLINE: {"initial", "setting", "characters"},
            BotType.WRITE_SETTING: {"initial"},
            BotType.WRITE_CHARACTERS: {"initial", "setting"},
            BotType.WRITE_CHAPTER: {"chapter_number", "outline", "setting", "characters", "previous_chapter"},
            BotType.WRITE_SECTION: {"section_number", "chapter_number", "section_outline", "setting", "characters", "previous_section"},
            BotType.SPLIT_OUTLINE: {"outline"},
            BotType.SPLIT_CHAPTER: {"chapter_outline"},
            BotType.REVIEW_COMMONS: {"initial", "setting", "characters", "content"}, # Content is the outline since it is being edited
            BotType.REVIEW_CHAPTER: {"content", "outline", "setting", "characters"},
            BotType.EDIT_CHAPTER: {"outline", "setting", "characters", "review", "content"},
            BotType.REVIEW_WHOLE: {"content"},
            BotType.SELF_EDIT: {"initial", "characters", "setting", "content"}
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
    max_continuations: int = 10
    continuation_prompt_initial: str = "Type THE END when finished, or CONTINUE if you need to write more."
    continuation_prompt: str = "You have written {current_words} words out of {expected_words} expected words. Continue the text."
    
    @classmethod
    def get_bot_type(cls, bot: str) -> str:
        """Get the BotType string for a given bot"""
        # Load the bot yaml
        bot_path = Path("bots") / f"{bot}.yaml"
        if not bot_path.exists():
            raise ValueError(f"Bot {bot} not found in {bot_path}")
        with bot_path.open('r') as f:
            config = yaml.safe_load(f)
        # Get the type from the config
        bot_type = config.get('type')
        if not bot_type:
            raise ValueError(f"Bot {bot} does not have a type defined")
        return bot_type

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
        """Validate that all required template variables are present and not empty
        
        Args:
            variables: Dictionary of template variables to validate
            
        Raises:
            ValueError: If any required variables are missing or empty
        """
        # Check for missing variables
        required = self.type.required_vars
        missing = required - set(variables.keys())
        if missing:
            raise ValueError(f"Missing required template variables for {self.type}: {missing}")
            
        # Check for empty variables
        empty_vars = [key for key in required if key in variables and not variables[key]]
        if empty_vars:
            raise ValueError(f"Empty required template variables for {self.type}: {empty_vars}")
            
        # Log warning for unknown variables
        unknown_vars = set(variables.keys()) - required
        if unknown_vars:
            logger.warning(f"Unknown template variables for {self.type}: {unknown_vars}")

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
            "time": 0,
            "calls": []
        }
        self.error: Optional[Exception] = None
        self.final_text: Optional[str] = None
        self.content_file = content_file
        self._load_initial_stats()
        logger.info(f"Initializing chat with bot '{bot.name}' for command: {command}")
        if CHEAP_MODE:
            logger.info(f"Running in CHEAP_MODE, changing model from {self.bot.llm} to Gemini Flash")
            # Use a cheaper model for testing
            self.bot.llm = "google/gemini-2.0-flash-001"
    
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
    
    def _load_initial_stats(self): 
        """Load initial statistics from an existing file if it exists"""
        if self.content_file:
            content_path = Path(self.content_file)
            if content_path.exists():
                f = TextFile(content_path)
                self.stats["previous_input_tokens"] = f.metadata.get("input_tokens", 0)
                self.stats["previous_output_tokens"] = f.metadata.get("output_tokens", 0)
                self.stats["previous_time"] = f.metadata.get("total_time", 0)
                self.stats["previous_continuation_count"] = f.metadata.get("total_continuation_count", 0)
                
                # Note that we're creating a new version of this file
                logger.info(f"Loading stats from existing file {content_path} (version {f.metadata.get('version', 1)})")
            else:
                # Create a new file with version 1
                logger.info(f"Creating new file {content_path} (version 1)")

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
        else:
            return {"order": [self.bot.provider]}
    
    def _clean_content(self, content: str) -> str:
        """Clean continuation markers and think tags from content"""
        if not content:
            return ""
            
        # Remove CONTINUE markers at end
        continuation_markers = ["CONTINUE\n", "**CONTINUE**\n", "CONTINUE", "**CONTINUE**"]
        for marker in continuation_markers:
            if content.endswith(marker):
                content = content[:-len(marker)].strip()
                break
            
        # Remove think tags if present (import re is at the top of the file)
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
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        
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

                # Log request details with enhanced formatting
                logger.info(f"Making OpenRouter API call ({self.command})")
                logger.debug(f"Request data:\n{logger.format_json(data)}")
                logger.debug(f"Model: {data.get('model', 'unknown')}, Temperature: {data.get('temperature', 0.7)}")
                logger.debug(f"Message count: {len(data.get('messages', []))}, Provider config: {logger.format_json(data.get('provider', {}))}")
                self._update_progress(progress, status="Generating...")

                if not DRY_RUN:
                    try:
                        response = requests.post(
                            api_url,
                            headers=headers,
                            json=data,
                            timeout=60
                        )
                    except requests.exceptions.Timeout:
                        logger.error("API request timed out")
                        if retry < max_retries:
                            wait_time = 5 * (retry + 1)
                            logger.warning(f"Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                            time.sleep(wait_time)
                            return self._make_api_call(messages, retry + 1, continuation_count)
                        raise Exception("API request timed out after multiple retries")
                    except requests.exceptions.ConnectionError:
                        logger.error("Connection error during API request")
                        if retry < max_retries:
                            wait_time = 5 * (retry + 1)
                            logger.warning(f"Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                            time.sleep(wait_time)
                            return self._make_api_call(messages, retry + 1, continuation_count)
                        raise Exception("Connection error persisted after multiple retries")
                else:
                    # TODO Move this out to a separate function
                    # Generate meaningful simulated content based on the request type and bot
                    bot_type = getattr(self.bot, 'type', BotType.DEFAULT).name
                    # Extract command details for better simulated responses
                    command_type = self.command.split('_')[0] if '_' in self.command else self.command
                    
                    # Create appropriate simulated content based on command/bot type
                    simulated_content = f"[DRY RUN MODE] Simulated content for {bot_type} bot, command: {self.command}\n\n"
                    
                    # Add more specific content based on the type of operation
                    if bot_type == "WRITE_CHAPTER":
                        chapter_num = next((m.get('content') for m in messages if 'chapter_number' in m.get('content', '')), 'UNKNOWN')
                        simulated_content += f"# Chapter {chapter_num}\n\nThis is simulated chapter content. It includes description, dialogue, and character development.\n\n"
                        simulated_content += "\"This is simulated dialogue,\" said Character A.\n\n"
                        simulated_content += "Character B nodded thoughtfully. \"I understand the purpose of dry run mode now.\"\n\n"
                        simulated_content += "THE END"
                    elif bot_type == "REVIEW_CHAPTER":
                        simulated_content += "# Review\n\n- Writing is clear and engaging\n- Characters are well developed\n- Pacing is appropriate\n- Dialogue is natural\n\n"
                        simulated_content += "Consider expanding the middle section where Character A confronts Character B.\n\nTHE END"
                    elif "OUTLINE" in bot_type:
                        simulated_content += "# Outline\n\n## Chapter 1\n- Introduction to main character\n- Setting established\n\n## Chapter 2\n- Conflict introduced\n- Supporting characters appear\n\nTHE END"
                    elif bot_type == "EXPAND_DEFAULT" or "EXPAND_" in bot_type:
                        simulated_content += "This is expanded content that would normally be generated by the LLM.\n"
                        simulated_content += "It would be more detailed and engaging than the original.\n\nTHE END"
                    else:
                        simulated_content += "Generic simulated content for testing purposes. This represents what would be returned by the LLM in a real run.\n\nTHE END"
                    
                    # Create a simulated response
                    response = requests.Response()
                    response.status_code = 200
                    # Create realistic simulated token counts based on content length
                    prompt_tokens = sum(len(m.get('content', '').split()) for m in messages)
                    completion_tokens = len(simulated_content.split())
                    response._content = (
                        f'{{"choices":[{{"message":{{"content":"{simulated_content.replace(chr(34), chr(92) + chr(34)).replace(chr(10), chr(92) + "n")}"}}}}], '
                        f'"usage":{{"prompt_tokens":{prompt_tokens},"completion_tokens":{completion_tokens}}}, '
                        f'"provider":"dry-run-provider","model":"dry-run-model"}}'
                    ).encode('utf-8')
                
                elapsed = time.time() - start_time
                
                # Log raw response for debugging with improved JSON formatting
                logger.debug(f"API Response Status: {response.status_code}")
                try:
                    # Try to parse and format the JSON response
                    logger.debug(f"API Response Content:\n{logger.format_json(response.text)}")
                except Exception as e:
                    # Fall back to raw text if JSON parsing fails
                    logger.debug(f"Raw API Response: {response.text}")
                    logger.debug(f"Failed to format response JSON: {e}")
                
                # Log response timing
                api_time = time.time() - start_time
                logger.debug(f"API call completed in {api_time:.2f} seconds")
                
                # Handle non-200 responses
                if response.status_code != 200:
                    if response.status_code == 429:  # Rate limit
                        if retry < max_retries:
                            wait_time = int(response.headers.get('Retry-After', 5))
                            logger.warning(f"Rate limited. Waiting {wait_time}s (retry {retry + 1}/{max_retries})")
                            time.sleep(wait_time)
                            return self._make_api_call(messages, retry + 1, continuation_count)
                        else:
                            raise Exception("Max retries exceeded for rate limit")
                    
                    # Handle other error codes        
                    logger.error(f"Error response ({response.status_code}): {response.text}")
                    response.raise_for_status()
                    
                # Parse JSON response
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response: {response.text}")
                    if retry < max_retries:
                        wait_time = 2 ** retry
                        logger.warning(f"Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                        time.sleep(wait_time)
                        return self._make_api_call(messages, retry + 1, continuation_count)
                    raise Exception("Invalid JSON response after retries")
                
                # Check for API errors in response
                if result.get("error"):
                    error_message = result["error"].get("message", "Unknown API error")
                    
                    # Handle out of credits error specifically
                    if "more credits are required" in error_message.lower():
                        logger.error("Out of credits. Waiting for user to add credits...")
                        console.print("[red]Out of credits. Waiting for user to add credits...[/red]")
                        console.input("Press any key to continue...")
                        return self._make_api_call(messages, retry + 1, continuation_count=continuation_count)
                    
                    # Handle other API errors
                    logger.error(f"API error: {error_message}")
                    if retry < max_retries:
                        wait_time = 2 ** retry
                        logger.warning(f"Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                        time.sleep(wait_time)
                        return self._make_api_call(messages, retry + 1, continuation_count)
                    raise Exception(f"API error after retries: {error_message}")

                # Extract data from response
                if not result.get('choices'):
                    logger.error("No choices in API response")
                    if retry < max_retries:
                        wait_time = 2 ** retry
                        logger.warning(f"Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                        time.sleep(wait_time)
                        return self._make_api_call(messages, retry + 1, continuation_count)
                    raise Exception("No choices in API response after retries")
                    
                content = result["choices"][0]["message"].get("content", "")
                if not content or content.isspace():
                    logger.warning("Received empty content")
                    if retry < max_retries:
                        wait_time = 2 ** retry
                        logger.warning(f"Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                        time.sleep(wait_time)
                        return self._make_api_call(messages, retry + 1, continuation_count)
                    raise Exception("Empty response after retries")
                
                # Check for finish reason
                finish_reason =  result["choices"][0].get("finish_reason", "unknown")


                # Get token counts
                usage = result.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                
                # Log success details
                words = len(content.split())
                tokens_per_sec = output_tokens/elapsed if elapsed > 0 else 0
                logger.info(f"Response stats: {len(content)}b/{words}w/{output_tokens}t in {elapsed:.1f}s ({tokens_per_sec:.1f} t/s)")
                logger.info(f"Tokens: {input_tokens} in, {output_tokens} out")
                logger.debug(f"Content preview: {content[:200]}...")
                
                # Record call stats
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
                self.stats["time"] += elapsed
                
                self._update_stats()
            
            return content, input_tokens, output_tokens, finish_reason
            
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            if retry < max_retries:
                wait_time = 2 ** retry
                logger.warning(f"Retrying in {wait_time}s (retry {retry + 1}/{max_retries})")
                time.sleep(wait_time)
                return self._make_api_call(messages, retry + 1, continuation_count)
            raise Exception(f"API call failed after {max_retries} retries: {str(e)}")
    
    def generate(self, template_vars: Dict[str, str]):
        """Generate content using the bot"""
        try:
            # Validate template variables
            self.bot.validate_template_vars(template_vars)
            expected_length = self.bot.expected_length
            # Initialize messages with system prompt
            self.messages = [
                {"role": "system", "content": self.bot.system_prompt},
                {"role": "user", "content": (
                    self.bot.main_prompt.format(**template_vars) +
                    f"\n Write one chunk of content. Write as much as you wish, and end your output with CONTINUE to have the chance to " +
                    "continue writing in a new chunk of content. CONTINUE must be at the end of your message if you want to write more than one chunk of content. " +
                    "Write THE END if this chunk concludes the section. You can write as much or as little as you wish, but typically aim for around {expected_length} words. " +
                    "If you CONTINUE, you'll get a current word count of how much you've written so far. You should ALWAYS write at least two chunks."
                )}
            ]
            
            # Track accumulated content
            accumulated_content = []
            continuation_count = 0
            max_continuations = 10  # Safety limit
            
            while continuation_count < self.bot.max_continuations:
                continuation_count += 1
                logger.info(f"Making API call {continuation_count} for {self.command}")
                
                # Check context window
                total_tokens = sum(len(m['content'].split()) for m in self.messages) * 1.5  # Rough estimate
                if total_tokens > self.bot.context_window / 2:
                    logger.warning(f"Context window is more than half full ({total_tokens} tokens)")
                
                # Make API call
                content, input_tokens, output_tokens, finish_reason = self._make_api_call(self.messages, continuation_count)
                
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
                if finish_reason == "stop" or finish_reason =="error" or "THE END" in content:
                    logger.info("Found THE END marker")
                    break
                    
                # Not done - add continuation prompt
                continuation_prompt = (
                    f"You have written {total_words} words so far out of a minimum {expected_length} words. Continue writing the next chunk. " +
                    "When you're done with this chunk of text, write CONTINUE, and then end your message. Then you'll get a new prompt to " +
                    "continue writing the chapter. Don't write CONTINUE in the middle of your output, that *WILL NOT* help you write more. " +
                    "Only write it at the end of your output in order to get a new prompt where you can continue writing the chapter. " +
                    "Write THE END when you're done writing. CONTINUE or THE END *MUST* be at the end of your output. Be sure to write enough words."
                )
                self.messages.append({"role": "user", "content": continuation_prompt})
                logger.info("Added continuation prompt")
                
                if self.content_file:
                    # Save on every continuation so we can see what's going on
                    f = TextFile(self.content_file)
                    
                    # Use append model for interim saves during continuations
                    # Only reset at the beginning of a new generation
                    if continuation_count == 1:
                        # First continuation of a new generation - reset the file
                        f.reset()
                        f.append('\n'.join(accumulated_content))
                    else:
                        # Replace content with latest accumulated content
                        # We don't want to append here because accumulated_content already contains all 
                        # previous continuations, and we want to replace the entire content
                        f.replace_content('\n'.join(accumulated_content))
                    
                    # Update metadata
                    f.metadata["command"] = self.command
                    f.metadata["bot"] = self.bot.name
                    f.metadata["timestamp"] = datetime.now().isoformat()
                    f.metadata["input_tokens"] = self.stats["input_tokens"]
                    f.metadata["output_tokens"] = self.stats["output_tokens"]
                    f.metadata["continuation_count"] = continuation_count
                    f.metadata["provider"] = self.bot.provider
                    f.metadata["model"] = self.bot.llm
                    f.metadata["time"] = self.stats["time"]
                    
                    # Track statistics across multiple generations
                    # Be a bit careful here. The stats are NOT reset to zero at the beginning of each continuation, 
                    # so we have to add these numbers to the ones from before we started the generation
                    # to get a running multi-generation total. The previous_* are only moved to the current values 
                    # once per generation.
                    f.metadata["total_input_tokens"] = f.metadata.get("previous_input_tokens", 0) + self.stats["input_tokens"]
                    f.metadata["total_output_tokens"] = f.metadata.get("previous_output_tokens", 0) + self.stats["output_tokens"]
                    f.metadata["total_time"] = f.metadata.get("previous_total_time", 0) + self.stats["time"]
                    f.metadata["total_continuation_count"] = f.metadata.get("previous_continuation_count", 0) + continuation_count
                    f.save()

            # Clean and store final text
            if accumulated_content:
                final_text = "\n".join(accumulated_content)
                # Make any final tweaks to the text
                if "THE END" in final_text:
                    final_text = final_text.split("THE END")[0].strip()
                self.final_text = final_text

                # Final save after tweaking
                if self.content_file:
                    f = TextFile(self.content_file)
                    # No need to reset here - we've already been updating the file during generation
                    # Just make sure the final content is correct
                    f.replace_content(self.final_text)
                    
                    # Add references if applicable
                    # Check if any template variables contain file paths that should be referenced
                    for key, value in template_vars.items():
                        if key in ['previous_chapter', 'outline', 'setting', 'characters', 'review'] and value:
                            # These are likely file references - try to find the corresponding file
                            for dir_path in [COMMON_DIR, CHAPTERS_DIR, REVIEWS_DIR]:
                                potential_files = list(dir_path.glob(f"*{key}*.md"))
                                if potential_files:
                                    f.add_reference(str(potential_files[0]))
                    
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









class BookBotError(Exception):
    """Base exception for all BookBot errors"""
    pass


# LLMError is currently unused
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
    """Represents a markdown file with content and metadata using version control
    
    TextFile supports:
    - Versioning with auto-incrementing version numbers
    - References to other files and specific versions
    - Append-only content model (content can only be appended, not changed)
    - History storage (previous versions saved in history/ folder)
    - Derived files (creating new files based on existing ones)
    """
    
    def __init__(self, filepath: Union[str, Path], config: Optional[Dict] = None, ensure_exists: bool = False):
        """Initialize a TextFile object
        
        Args:
            filepath: Path to the file (string or Path object)
            config: Optional configuration dictionary
            ensure_exists: If True, raises an error if the file doesn't exist
        """
        self.filepath = Path(filepath)
        if ensure_exists and not self.filepath.exists():
            raise FileNotFoundError(f"File {self.filepath} does not exist")
        
        self.content = ""
        self.metadata = {}
        self.conversation_history = []
        self.config = config if config else DEFAULT_CONFIG
        self.history_dir = self.filepath.parent / "history"
        self._load()
    
    def _load(self):
        """Load the file if it exists"""
        try:
            if self.filepath.exists():
                text = self.filepath.read_text(encoding='utf-8')
                
                # Check for empty file
                if not text.strip():
                    logger.warning(f"Empty file detected: {self.filepath}")
                    return
                
                if text.startswith('---'):
                    # Parse metadata
                    parts = text.split('---', 2)
                    if len(parts) < 3:
                        logger.warning(f"Malformed metadata in {self.filepath}")
                        self.content = text.strip()
                        return
                        
                    _, metadata, content = parts
                    try:
                        self.metadata = {
                            k.strip(): v.strip()
                            for k, v in (line.split(':', 1) 
                            for line in metadata.strip().split('\n')
                            if ':' in line)
                        }
                        self.content = content.strip()
                    except Exception as e:
                        logger.warning(f"Error parsing metadata in {self.filepath}: {e}")
                        self.content = text.strip()
                else:
                    self.content = text.strip()
                    
                # Ensure version number exists in metadata
                if 'version' not in self.metadata:
                    self.metadata['version'] = '1'
                
                # Ensure timestamp exists
                if 'timestamp' not in self.metadata:
                    self.metadata['timestamp'] = datetime.now().isoformat()
                
                # Load conversation history if it exists
                history_path = self.filepath.with_suffix('.history.json')
                if history_path.exists():
                    try:
                        with history_path.open('r', encoding='utf-8') as f:
                            self.conversation_history = json.load(f)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error loading conversation history for {self.filepath}: {e}")
                        self.conversation_history = []
        except Exception as e:
            logger.error(f"Error loading file {self.filepath}: {e}")
            raise BookBotError(f"Failed to load file: {e}")
    
    def append(self, content: str):
        """Append content (preserves existing content)"""
        if not self.content:
            self.content = content
        else:
            self.content = f"{self.content}\n\n{content}"
        
        # Update timestamp whenever content changes
        self.metadata['timestamp'] = datetime.now().isoformat()
        self.metadata['last_operation'] = 'append'
    
    def replace_content(self, new_content: str):
        """Replace content entirely - should only be used in specific cases
        
        This bypasses the append-only model and should be used with caution.
        Primarily for LLM-generated content replacement.
        """
        self.content = new_content
        self.metadata['timestamp'] = datetime.now().isoformat()
        self.metadata['last_operation'] = 'replace'
    
    def reset(self):
        """Reset content and increment version number"""
        # Store previous version in history
        self._save_to_history()
        
        # Increment version number
        try:
            current_version = int(self.metadata.get('version', '1'))
            self.metadata['version'] = str(current_version + 1)
        except ValueError:
            # If version isn't a valid number for some reason, reset to 1
            self.metadata['version'] = '1'
        
        # Clear content
        self.content = ""
        
        # Update timestamp
        self.metadata['timestamp'] = datetime.now().isoformat()
        self.metadata['last_operation'] = 'reset'
    
    def _save_to_history(self):
        """Save current version to history folder with associated files
        
        This saves:
        1. The main content file with version number
        2. The conversation history JSON file if it exists
        3. The stats JSON file if it exists
        
        Files include parent directory name to avoid conflicts between files 
        with the same name in different directories.
        """
        if not self.content:
            return  # Don't save empty files to history
            
        # If in DRY_RUN mode, log but don't actually save
        if DRY_RUN:
            logger.info(f"DRY RUN: Would save version to history for {self.filepath}")
            return
        
        # Ensure history directory exists
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Get current version number
        version = self.metadata.get('version', '1')
        basename = self.filepath.stem
        parent_dir = self.filepath.parent.name
        extension = self.filepath.suffix
        
        # Create a unique history basename including parent directory to avoid conflicts
        # Example: "chapters_file.v1.md" instead of just "file.v1.md"
        unique_basename = f"{parent_dir}_{basename}" if parent_dir else basename
        
        # Create history filename with version number and parent directory name
        history_path = self.history_dir / f"{unique_basename}.v{version}{extension}"
        
        # Add timestamp to metadata if not present
        if 'timestamp' not in self.metadata:
            self.metadata['timestamp'] = datetime.now().isoformat()
            
        # Add original path to metadata for reference
        self.metadata['original_path'] = str(self.filepath)
        
        # Prepare content with metadata
        content = []
        if self.metadata:
            content.append('---')
            content.extend(f"{k}: {v}" for k, v in self.metadata.items())
            content.append('---')
        content.append(self.content)
        
        try:
            # Write main content to history file
            history_path.write_text('\n'.join(content), encoding='utf-8')
            logger.info(f"Saved version {version} to history: {history_path}")
            
            # Copy associated files if they exist
            # 1. Conversation history file
            history_json_path = self.filepath.with_suffix('.history.json')
            if history_json_path.exists():
                history_json_dest = self.history_dir / f"{unique_basename}.v{version}.history.json"
                try:
                    shutil.copy2(history_json_path, history_json_dest)
                    logger.info(f"Copied conversation history to: {history_json_dest}")
                except Exception as e:
                    logger.warning(f"Failed to copy conversation history to history folder: {e}")
            
            # 2. Stats file
            stats_json_path = self.filepath.with_suffix('.stats.json')
            if stats_json_path.exists():
                stats_json_dest = self.history_dir / f"{unique_basename}.v{version}.stats.json"
                try:
                    shutil.copy2(stats_json_path, stats_json_dest)
                    logger.info(f"Copied stats to: {stats_json_dest}")
                except Exception as e:
                    logger.warning(f"Failed to copy stats to history folder: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to save version {version} to history: {e}")
    
    def save(self):
        """Save the file and its metadata"""
        try:
            # If in DRY_RUN mode, log but don't actually save
            if DRY_RUN:
                logger.info(f"DRY RUN: Would save file to {self.filepath}")
                self._log_dry_run_content()
                return
                
            # Create parent directories if they don't exist
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Update timestamp if not present
            if 'timestamp' not in self.metadata:
                self.metadata['timestamp'] = datetime.now().isoformat()
            
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
            
    def _log_dry_run_content(self):
        """Log file content for dry run mode"""
        logger.info(f"DRY RUN: File content for {self.filepath} ({len(self.content.split())} words):")
        # Log a preview of content (first 100 chars)
        content_preview = self.content[:100] + "..." if len(self.content) > 100 else self.content
        logger.info(f"  Content: {content_preview}")
        
        # Log important metadata
        important_keys = ['version', 'bot', 'model', 'expansion_count']
        metadata_preview = {k: v for k, v in self.metadata.items() if k in important_keys}
        if metadata_preview:
            logger.info(f"  Metadata: {metadata_preview}")
    
    def add_reference(self, file_path: Union[str, Path], version: int = None):
        """Add reference to another file with optional version"""
        # Normalize path to string
        file_path_str = str(file_path)
        
        # Construct reference with version if provided
        if version:
            ref = f"{file_path_str}#{version}"
        else:
            # Load the file to get its current version
            try:
                # Check if file exists first to avoid unnecessary errors
                path_obj = Path(file_path)
                if not path_obj.exists():
                    logger.warning(f"Referenced file does not exist: {file_path}")
                    ref = file_path_str
                    
                    # Record reference error in metadata
                    error_msg = f"File not found: {file_path_str}"
                    self._add_reference_error(file_path_str, error_msg)
                else:
                    # Load file and get version
                    ref_file = TextFile(path_obj)
                    ref_version = ref_file.metadata.get('version', '1')
                    ref = f"{file_path_str}#{ref_version}"
            except Exception as e:
                # If file can't be loaded, just use the file path
                logger.warning(f"Could not resolve reference version for {file_path}: {e}")
                ref = file_path_str
                
                # Record reference error in metadata
                self._add_reference_error(file_path_str, str(e))
        
        # Add to references in metadata
        if 'references' not in self.metadata:
            self.metadata['references'] = ref
        else:
            refs = self.metadata['references'].split(', ')
            if ref not in refs:  # Avoid duplicates
                refs.append(ref)
                self.metadata['references'] = ', '.join(refs)
    
    def _add_reference_error(self, file_path: str, error_msg: str):
        """Helper method to consistently add reference errors to metadata"""
        if 'reference_errors' not in self.metadata:
            self.metadata['reference_errors'] = f"{file_path}: {error_msg}"
        else:
            self.metadata['reference_errors'] += f", {file_path}: {error_msg}"
    
    def validate_history_file(self, history_path: Path) -> bool:
        """Validate a history file exists and has proper structure
        
        Args:
            history_path: Path to the history file to validate
            
        Returns:
            bool: True if the file exists and has a valid format
        """
        # Check if file exists
        if not history_path.exists():
            logger.error(f"Version file not found: {history_path}")
            return False
            
        try:
            # Basic validation of file format - should have metadata section
            history_text = history_path.read_text(encoding='utf-8')
            if not history_text.startswith('---'):
                logger.error(f"Invalid history file format (no metadata): {history_path}")
                return False
                
            # Validate that it has expected sections (metadata and content)
            parts = history_text.split('---', 2)
            if len(parts) < 3:
                logger.error(f"Invalid history file structure (incomplete metadata): {history_path}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Failed to validate history file {history_path}: {e}")
            return False
    
    def revert_to_version(self, version: int) -> bool:
        """Revert to a specific version from history
        
        Args:
            version: Version number to revert to
            
        Returns:
            bool: True if revert was successful, False otherwise
        """
        # Check that version is positive
        if version <= 0:
            logger.error(f"Invalid version number: {version}. Version must be positive.")
            return False
        
        # Find version in history using the same naming pattern as _save_to_history
        basename = self.filepath.stem
        parent_dir = self.filepath.parent.name
        extension = self.filepath.suffix
        
        # Create the same unique basename pattern used in _save_to_history
        unique_basename = f"{parent_dir}_{basename}" if parent_dir else basename
        
        # Construct the history path with the parent directory included
        history_path = self.history_dir / f"{unique_basename}.v{version}{extension}"
        
        # If the file doesn't exist, try the old naming pattern for backward compatibility
        if not history_path.exists():
            old_style_path = self.history_dir / f"{basename}.v{version}{extension}"
            if old_style_path.exists():
                history_path = old_style_path
                logger.info(f"Using old-style history path: {history_path}")
            else:
                logger.error(f"Version file not found: {history_path} or {old_style_path}")
                return False
        
        # Validate history file
        if not self.validate_history_file(history_path):
            return False
        
        # Save current version to history before reverting
        self._save_to_history()
        
        # Load content from history
        try:
            history_file = TextFile(history_path)
            
            # Set content and increment version
            self.content = history_file.content
            
            # Determine new version number
            try:
                current_version = int(self.metadata.get('version', '1'))
                self.metadata['version'] = str(current_version + 1)
            except ValueError:
                # Handle case where version is not a valid integer
                logger.warning(f"Invalid version format: {self.metadata.get('version')}. Resetting to 1.")
                self.metadata['version'] = '1'
                
            # Copy important metadata from reverted version
            for key in ['bot', 'model', 'provider']:
                if key in history_file.metadata:
                    self.metadata[f'original_{key}'] = history_file.metadata[key]
            
            # Look for associated files with the same version pattern
            history_json_path = None
            stats_json_path = None
            
            # Check for new naming pattern first
            new_history_json = self.history_dir / f"{unique_basename}.v{version}.history.json"
            new_stats_json = self.history_dir / f"{unique_basename}.v{version}.stats.json"
            
            # Then check old naming pattern for backward compatibility
            old_history_json = self.history_dir / f"{basename}.v{version}.history.json" 
            old_stats_json = self.history_dir / f"{basename}.v{version}.stats.json"
            
            # Determine which paths exist
            if new_history_json.exists():
                history_json_path = new_history_json
            elif old_history_json.exists():
                history_json_path = old_history_json
                
            if new_stats_json.exists():
                stats_json_path = new_stats_json
            elif old_stats_json.exists():
                stats_json_path = old_stats_json
            
            # Copy back associated files if they exist
            if history_json_path:
                dest_history_json = self.filepath.with_suffix('.history.json')
                try:
                    shutil.copy2(history_json_path, dest_history_json)
                    logger.info(f"Restored conversation history from: {history_json_path}")
                except Exception as e:
                    logger.warning(f"Failed to restore conversation history: {e}")
                    
            if stats_json_path:
                dest_stats_json = self.filepath.with_suffix('.stats.json')
                try:
                    shutil.copy2(stats_json_path, dest_stats_json)
                    logger.info(f"Restored stats from: {stats_json_path}")
                except Exception as e:
                    logger.warning(f"Failed to restore stats: {e}")
                
            # Add reference to the reverted version
            self.metadata['reverted_from'] = f"v{version}"
            self.metadata['timestamp'] = datetime.now().isoformat()
            self.metadata['last_operation'] = 'revert'
            
            # Save the file with updated content and metadata
            self.save()
            logger.info(f"Successfully reverted {self.filepath} to version {version}")
            return True
        except Exception as e:
            logger.error(f"Failed to revert to version {version}: {e}")
            return False
    
    @classmethod
    def create_derived_file(cls, source_path: Union[str, Path], suffix: str) -> 'TextFile':
        """Create a new file derived from an existing one with a suffix"""
        try:
            source_path = Path(source_path)
            
            # Check if source exists before proceeding
            if not source_path.exists():
                logger.warning(f"Source file {source_path} doesn't exist for derived file")
                
            # Create new file path with suffix
            stem = source_path.stem
            extension = source_path.suffix
            new_path = source_path.parent / f"{stem}_{suffix}{extension}"
            
            # Check for collision
            if new_path.exists():
                logger.warning(f"Derived file already exists: {new_path}")
                
            # Create new TextFile
            new_file = cls(new_path)
            
            # If source exists, copy metadata
            if source_path.exists():
                source_file = cls(source_path)
                # Copy metadata except version
                for key, value in source_file.metadata.items():
                    if key != 'version':
                        new_file.metadata[key] = value
                
                # Set version to 1
                new_file.metadata['version'] = '1'
                new_file.metadata['derived_from'] = str(source_path)
                new_file.metadata['derived_on'] = datetime.now().isoformat()
                new_file.metadata['last_operation'] = 'create_derived'
                
                # Add reference to source
                new_file.add_reference(str(source_path))
                
                # No content is copied - derived files start empty
            
            return new_file
        except Exception as e:
            logger.error(f"Failed to create derived file: {e}")
            raise BookBotError(f"Could not create derived file: {e}")
    
    def update_metadata(self, metadata_updates: Dict[str, Any]):
        """Update metadata with standardized handling"""
        # Ensure core fields exist
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = datetime.now().isoformat()
        if "version" not in self.metadata:
            self.metadata["version"] = "1"
            
        # Update with new values
        self.metadata.update(metadata_updates)
    
    def update_conversation_history(self, entry: dict):
        """Add an entry to the conversation history"""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            **entry
        })

class PreviewGenerator:
    """Generates HTML previews of the book content with enhanced features:
    
    1. Display statistics for each file (words, tokens, cost)
    2. Show references between files
    3. Show file version history
    4. Format conversation JSON for readability 
    """
    
    def __init__(self, preview_dir: Path = PREVIEW_DIR):
        self.preview_dir = Path(preview_dir)
        self.stats = {
            'total_words': 0,
            'total_tokens_in': 0,
            'total_tokens_out': 0,
            'total_cost': 0.0,
            'file_stats': {}
        }
    
    def setup(self):
        """Set up preview directory"""
        # Create subdirectories if they don't exist
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        (self.preview_dir / "history").mkdir(exist_ok=True)
        (self.preview_dir / "json").mkdir(exist_ok=True)
    
    def generate_file_preview(self, file: TextFile, title: str) -> Tuple[int, int, int]:
        """Generate preview for a single file with enhanced features"""
        # Convert markdown to HTML
        html_content = markdown.markdown(file.content)
        
        # Calculate stats
        words = len(file.content.split())
        
        # Get token information from metadata or history
        tokens_in = int(file.metadata.get("total_input_tokens", 0))
        if tokens_in == 0:
            tokens_in = file.metadata.get("input_tokens", 0)
        
        tokens_out = int(file.metadata.get("total_output_tokens", 0))
        if tokens_out == 0:
            tokens_out = file.metadata.get("output_tokens", 0)
        
        # Calculate cost (if token pricing info is available)
        # TODO use OpenRouter to get exact cost rather than try to calcualte
        input_price = float(file.metadata.get("input_price", 8.0)) / 1000000  # Per token price
        output_price = float(file.metadata.get("output_price", 24.0)) / 1000000

        cost = (tokens_in * input_price) + (tokens_out * output_price)

        # Extract references
        references = []
        if 'references' in file.metadata:
            references = file.metadata['references'].split(', ')
        
        # Add references section to content
        if references:
            references_html = "<div class='references'><h3>References:</h3><ul>"
            for ref in references:
                # Check if reference has version info (format: path#version)
                parts = ref.split('#')
                path = parts[0]
                version = parts[1] if len(parts) > 1 else None
                
                file_name = Path(path).name
                file_stem = Path(path).stem
                
                if version:
                    # Link to specific version in history
                    references_html += f"<li><a href='history/{file_stem}.v{version}.html'>{file_name} (v{version})</a></li>"
                else:
                    # Link to current version
                    references_html += f"<li><a href='{file_stem}.html'>{file_name}</a></li>"
            
            references_html += "</ul></div>"
            html_content = references_html + html_content
        # TODO removed numeric formatting because vals are strings?
        # Add file stats to content
        stats_html = f"""
        <div class="file-stats">
            <table>
                <tr><th>Words</th><th>Input Tokens</th><th>Output Tokens</th><th>Cost</th></tr>
                <tr>
                    <td>{words}</td>
                    <td>{tokens_in}</td>
                    <td>{tokens_out}</td>
                    <td>${cost}</td>
                </tr>
            </table>
            <p>Bot: {file.metadata.get('bot', 'Unknown')} | 
               Model: {file.metadata.get('model', 'Unknown')} | 
               Version: {file.metadata.get('version', '1')}</p>
        </div>
        """
        
        # Add history link if available
        history_link = ""
        history_dir = file.filepath.parent / "history"
        if history_dir.exists():
            history_files = list(history_dir.glob(f"{file.filepath.stem}.v*{file.filepath.suffix}"))
            if history_files:
                history_html_path = f"{file.filepath.stem}_history.html"
                history_link = f"<p><a href='{history_html_path}'>View Version History ({len(history_files)} versions)</a></p>"
                # Generate history view
                self._generate_history_view(file, history_files, history_html_path)
        
        # Add JSON conversation link if available
        json_link = ""
        json_path = file.filepath.with_suffix('.history.json')
        if json_path.exists():
            json_html_path = f"json/{file.filepath.stem}_conv.html"
            json_link = f"<p><a href='{json_html_path}'>View Conversation History</a></p>"
            # Generate JSON view
            self._generate_json_view(json_path, json_html_path)
        
        # Combine everything
        final_content = f"{stats_html}{history_link}{json_link}{html_content}"
        
        # Create HTML file
        html_path = self.preview_dir / f"{file.filepath.stem}.html"
        html_path.write_text(self._wrap_html(title, final_content))
        
        # Store file stats
        self.stats['file_stats'][str(file.filepath)] = {
            'words': words,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'cost': cost,
            'title': title
        }
        
        return words, tokens_in, tokens_out
    
    def _generate_history_view(self, file: TextFile, history_files: List[Path], output_path: str):
        """Generate history view showing all versions of a file, including links to associated files
        
        Args:
            file: The current TextFile object
            history_files: List of history file paths
            output_path: Path to save the history HTML
        """
        # Make sure we have the correct history files with the new naming convention
        if not history_files:
            return
            
        basename = file.filepath.stem
        parent_dir = file.filepath.parent.name
        extension = file.filepath.suffix
        
        # If we have old-style filenames and parent_dir exists, try looking for new style too
        if parent_dir and history_files and not str(history_files[0]).startswith(f"{parent_dir}_{basename}"):
            unique_basename = f"{parent_dir}_{basename}"
            history_dir = file.filepath.parent / "history"
            new_style_files = list(history_dir.glob(f"{unique_basename}.v*{extension}"))
            if new_style_files:
                # If we found new-style files, use those instead
                history_files = new_style_files
        
        # Sort files by version number
        sorted_files = sorted(history_files, key=lambda p: int(p.stem.split('.v')[1]))
        
        content = f"<h1>Version History for {file.filepath.name}</h1>"
        content += "<table class='history-table'>"
        content += "<tr><th>Version</th><th>Date</th><th>Words</th><th>Bot</th><th>Action</th><th>Files</th></tr>"
        
        # Process each version
        for v_file in sorted_files:
            try:
                # Extract version number
                v_num = v_file.stem.split('.v')[1]
                
                # Load the file to get metadata
                v_text = TextFile(v_file)
                v_date = v_text.metadata.get('timestamp', 'Unknown')
                v_words = len(v_text.content.split())
                v_bot = v_text.metadata.get('bot', 'Unknown')
                v_action = v_text.metadata.get('last_operation', 'Unknown')
                
                # Create HTML for this version
                v_html_path = f"history/{v_file.name}.html"
                self._generate_version_view(v_text, v_html_path)
                
                # Check for associated files
                history_dir = file.filepath.parent / "history"
                basename = file.filepath.stem
                
                # Look for history.json and stats.json with this version
                history_json_path = history_dir / f"{basename}.v{v_num}.history.json"
                stats_json_path = history_dir / f"{basename}.v{v_num}.stats.json"
                
                # Generate links to associated files if they exist
                associated_files = []
                if history_json_path.exists():
                    # Generate JSON view and add link
                    json_html_path = f"json/{basename}.v{v_num}_conv.html"
                    self._generate_json_view(history_json_path, json_html_path)
                    associated_files.append(f"<a href='{json_html_path}'>Conversation</a>")
                
                if stats_json_path.exists():
                    # Generate stats view and add link
                    stats_html_path = f"json/{basename}.v{v_num}_stats.html"
                    self._generate_json_view(stats_json_path, stats_html_path)
                    associated_files.append(f"<a href='{stats_html_path}'>Stats</a>")
                
                # Format the links
                files_cell = ", ".join(associated_files) if associated_files else "None"
                
                # Add to version table
                content += f"""
                <tr>
                    <td><a href='{v_html_path}'>v{v_num}</a></td>
                    <td>{v_date}</td>
                    <td>{v_words:,}</td>
                    <td>{v_bot}</td>
                    <td>{v_action}</td>
                    <td>{files_cell}</td>
                </tr>
                """
            except Exception as e:
                content += f"<tr><td colspan='6'>Error loading {v_file.name}: {str(e)}</td></tr>"
        
        content += "</table>"
        
        # Add a revert form (for future use)
        content += f"""
        <div class="revert-section">
            <h3>Revert to Version</h3>
            <p>To revert to a specific version, use the command line:</p>
            <pre>python bookbot.py revert {file.filepath} [VERSION]</pre>
        </div>
        """
        
        # Create history page
        history_path = self.preview_dir / output_path
        history_path.write_text(self._wrap_html(f"History of {file.filepath.name}", content))
    
    def _generate_version_view(self, file: TextFile, output_path: str):
        """Generate view for a specific version"""
        # Convert markdown to HTML
        html_content = markdown.markdown(file.content)
        
        # Add metadata
        metadata_html = "<div class='metadata'><h3>Version Metadata:</h3><table>"
        for key, value in file.metadata.items():
            if key != 'references':  # Skip references as they can be long
                metadata_html += f"<tr><td>{key}</td><td>{value}</td></tr>"
        metadata_html += "</table></div>"
        
        # Combine and save
        content = metadata_html + html_content
        version_path = self.preview_dir / output_path
        version_path.parent.mkdir(exist_ok=True)
        version_path.write_text(self._wrap_html(f"Version {output_path}", content))
    
    def _generate_json_view(self, json_path: Path, output_path: str):
        """Generate HTML view for JSON conversation history
        
        Args:
            json_path: Path to the JSON file to process
            output_path: Path where to save the HTML output file
        """
        try:
            # Load JSON
            with json_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determine if this is a versioned history file
            is_versioned = ".v" in json_path.stem
            version_label = ""
            if is_versioned:
                try:
                    version_num = json_path.stem.split(".v")[1].split(".")[0]
                    version_label = f" (Version {version_num})"
                except:
                    pass
            
            content = f"<h1>Conversation History{version_label}</h1>"
            
            # Add file info
            content += f"<p><strong>File:</strong> {json_path.name}</p>"
            
            # Format basic info
            if isinstance(data, dict):
                if 'bot' in data:
                    content += f"<p><strong>Bot:</strong> {data['bot']}</p>"
                if 'command' in data:
                    content += f"<p><strong>Command:</strong> {data['command']}</p>"
                if 'timestamp' in data:
                    content += f"<p><strong>Timestamp:</strong> {data['timestamp']}</p>"
            
            # Format messages
            messages = data.get('messages', []) if isinstance(data, dict) else data
            if messages:
                content += "<h2>Messages</h2>"
                
                for i, msg in enumerate(messages):
                    role = msg.get('role', 'unknown')
                    msg_content = msg.get('content', '')
                    
                    # Escape HTML in content
                    msg_content = msg_content.replace('<', '&lt;').replace('>', '&gt;')
                    
                    # Add message to view
                    content += f"""
                    <div class='message {role}'>
                        <div class='message-header'>
                            <span class='role'>{role.upper()}</span>
                            <span class='index'>Message {i+1}</span>
                        </div>
                        <pre class='message-content'>{msg_content}</pre>
                    </div>
                    """
            
            # Process any call stats if available
            if isinstance(data, dict) and 'calls' in data and isinstance(data['calls'], list):
                calls = data['calls']
                if calls:
                    content += "<h2>API Calls</h2>"
                    content += "<table class='calls-table'>"
                    content += "<tr><th>Timestamp</th><th>Provider</th><th>Model</th><th>Tokens (In/Out)</th><th>Time</th></tr>"
                    
                    for call in calls:
                        timestamp = call.get('timestamp', 'N/A')
                        provider = call.get('provider', 'N/A')
                        model = call.get('model', 'N/A')
                        input_tokens = call.get('input_tokens', 0)
                        output_tokens = call.get('output_tokens', 0)
                        elapsed = call.get('elapsed', 0)
                        
                        content += f"""
                        <tr>
                            <td>{timestamp}</td>
                            <td>{provider}</td>
                            <td>{model}</td>
                            <td>{input_tokens:,} / {output_tokens:,}</td>
                            <td>{elapsed:.2f}s</td>
                        </tr>
                        """
                    
                    content += "</table>"
            
            # Improved nested JSON handling 
            def format_nested_json(json_str):
                try:
                    # Try to parse it as JSON
                    json_data = json.loads(json_str)
                    # Format with syntax highlighting classes
                    formatted_json = json.dumps(json_data, indent=2)
                    # Add span classes for syntax highlighting
                    formatted_json = formatted_json.replace('"', '&quot;')
                    return f"<pre class='nested-json'>{formatted_json}</pre>"
                except:
                    return json_str
            
            # Search for JSON strings within content and format them
            for i, msg in enumerate(messages):
                if 'content' in msg and isinstance(msg['content'], str):
                    content_str = msg['content']
                    # Look for common JSON patterns
                    json_patterns = [
                        (r'{\s*"', r'"\s*}'),  # Object: {"key": "value"}
                        (r'\[\s*{', r'}\s*\]')  # Array of objects: [{"key": "value"}]
                    ]
                    
                    for start_pattern, end_pattern in json_patterns:
                        # Use regex to find potential JSON
                        import re
                        start_matches = list(re.finditer(start_pattern, content_str))
                        end_matches = list(re.finditer(end_pattern, content_str))
                        
                        if start_matches and end_matches:
                            for start_match in start_matches:
                                start_pos = start_match.start()
                                
                                # Find the matching end
                                for end_match in end_matches:
                                    end_pos = end_match.end()
                                    if end_pos > start_pos:
                                        # Extract potential JSON
                                        json_str = content_str[start_pos:end_pos]
                                        try:
                                            # Validate and format
                                            json.loads(json_str)  # Just to validate
                                            formatted = format_nested_json(json_str)
                                            # Replace in content only if valid
                                            content = content.replace(json_str, formatted)
                                            break
                                        except:
                                            # Not valid JSON, continue
                                            pass
            
            # Add link to original JSON
            filename = os.path.basename(json_path)
            content += f"<p><a href='#' onclick='toggleRawJson(); return false;'>Toggle Raw JSON</a></p>"
            content += f"<div id='rawJson' style='display:none;'><pre>{json.dumps(data, indent=2)}</pre></div>"
            
            # Add JavaScript for toggle
            js = """
            <script>
            function toggleRawJson() {
                var rawJson = document.getElementById('rawJson');
                if (rawJson.style.display === 'none') {
                    rawJson.style.display = 'block';
                } else {
                    rawJson.style.display = 'none';
                }
            }
            </script>
            """
            
            # Create JSON view page
            json_view_path = self.preview_dir / output_path
            json_view_path.parent.mkdir(exist_ok=True)
            json_view_path.write_text(self._wrap_html(f"Conversation History - {json_path.name}", content, extra_head=js))
            
        except Exception as e:
            # Create error page if JSON processing fails
            error_content = f"<h1>Error Processing JSON</h1><p>{str(e)}</p><p>File: {json_path}</p>"
            json_view_path = self.preview_dir / output_path
            json_view_path.parent.mkdir(exist_ok=True)
            json_view_path.write_text(self._wrap_html("JSON Error", error_content))
    
    def generate(self, files: Dict[str, List[TextFile]]):
        """Generate complete preview with enhanced features"""
        self.setup()
        
        # Process all files and collect stats
        for category, file_list in files.items():
            for file in file_list:
                words, tokens_in, tokens_out = self.generate_file_preview(
                    file, f"{category} - {file.filepath.name}")
                self.stats['total_words'] += words
                self.stats['total_tokens_in'] += int(tokens_in)
                self.stats['total_tokens_out'] += int(tokens_out)
                
                # Calculate and add to total cost
                file_stats = self.stats['file_stats'][str(file.filepath)]
                self.stats['total_cost'] += file_stats['cost']
        
        # Generate enhanced index page
        self._generate_enhanced_index(files)
        
        console.print(f"\n[green]✓[/green] Enhanced preview generated in {self.preview_dir}")
        console.print(f"[blue]ℹ[/blue] Open {self.preview_dir}/index.html in your browser")
    
    def _wrap_html(self, title: str, content: str) -> str:
        """Wrap content in HTML template with enhanced styling"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                :root {{
                    --primary: #1a73e8;
                    --secondary: #4285f4;
                    --background: #f8f9fa;
                    --text: #202124;
                    --link: #1967d2;
                    --border: #dadce0;
                }}
                
                body {{ 
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    max-width: 1000px; 
                    margin: 2rem auto; 
                    padding: 0 1rem; 
                    line-height: 1.6;
                    color: var(--text);
                    background-color: var(--background);
                }}
                
                h1, h2, h3 {{ color: var(--primary); }}
                
                a {{ color: var(--link); text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                
                .content {{
                    background-color: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                }}
                
                pre {{ 
                    background: #f5f5f5; 
                    padding: 1rem; 
                    overflow-x: auto;
                    border-radius: 4px; 
                }}
                
                .file-stats {{
                    background-color: #e8f0fe;
                    border: 1px solid #d2e3fc;
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 1.5rem;
                }}
                
                .file-stats table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                
                .file-stats th, .file-stats td {{
                    padding: 0.5rem;
                    text-align: center;
                    border-bottom: 1px solid #d2e3fc;
                }}
                
                .references {{
                    background-color: #f0fff1;
                    border: 1px solid #c6f6d5;
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 1.5rem;
                }}
                
                .history-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1rem 0;
                }}
                
                .history-table th, .history-table td {{
                    padding: 0.75rem;
                    text-align: left;
                    border-bottom: 1px solid var(--border);
                }}
                
                .history-table th {{
                    background-color: var(--background);
                }}
                
                .metadata {{
                    background-color: #fff8e1;
                    border: 1px solid #ffecb3;
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 1.5rem;
                    max-height: 300px;
                    overflow-y: auto;
                }}
                
                .metadata table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                
                .metadata th, .metadata td {{
                    padding: 0.5rem;
                    text-align: left;
                    border-bottom: 1px solid #ffecb3;
                    word-break: break-word;
                }}
                
                .message {{
                    margin-bottom: 1rem;
                    border: 1px solid var(--border);
                    border-radius: 8px;
                    overflow: hidden;
                }}
                
                .message-header {{
                    padding: 0.5rem 1rem;
                    background-color: var(--background);
                    display: flex;
                    justify-content: space-between;
                    border-bottom: 1px solid var(--border);
                }}
                
                .role {{
                    font-weight: bold;
                    color: var(--primary);
                }}
                
                .message-content {{
                    margin: 0;
                    padding: 1rem;
                    white-space: pre-wrap;
                    max-height: 300px;
                    overflow-y: auto;
                }}
                
                .system .message-header {{
                    background-color: #e8f0fe;
                }}
                
                .user .message-header {{
                    background-color: #e6f4ea;
                }}
                
                .assistant .message-header {{
                    background-color: #fce8e6;
                }}
                
                .nested-json {{
                    background-color: #f8f9fa;
                    border: 1px solid #dadce0;
                    padding: 0.5rem;
                    border-radius: 4px;
                    white-space: pre-wrap;
                }}
                
                .stats-card {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 1rem;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    margin-bottom: 1rem;
                }}
                
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 1rem;
                }}
                
                .file-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 1rem;
                }}
                
                .file-card {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 1rem;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                }}
                
                @media (max-width: 768px) {{
                    .stats-grid, .file-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <p><a href="index.html">← Back to Index</a></p>
            <div class="content">
                {content}
            </div>
        </body>
        </html>
        """
    
    def _generate_enhanced_index(self, files: Dict[str, List[TextFile]]):
        """Generate enhanced index page with detailed statistics"""
        # Format total cost
        total_cost = self.stats['total_cost']
        
        # Create stats cards
        stats_html = f"""
        <div class="stats-grid">
            <div class="stats-card">
                <h3>Content</h3>
                <div class="stat-value">{self.stats['total_words']:,}</div>
                <p>Total Words</p>
            </div>
            
            <div class="stats-card">
                <h3>Input Tokens</h3>
                <div class="stat-value">{self.stats['total_tokens_in']:,}</div>
                <p>Prompt Tokens</p>
            </div>
            
            <div class="stats-card">
                <h3>Output Tokens</h3>
                <div class="stat-value">{self.stats['total_tokens_out']:,}</div>
                <p>Generated Tokens</p>
            </div>
            
            <div class="stats-card">
                <h3>Cost</h3>
                <div class="stat-value">${total_cost:.4f}</div>
                <p>Estimated Total Cost</p>
            </div>
        </div>
        """
        
        # Start content with stats
        content = [
            "<h1>Book Preview</h1>",
            "<h2>Project Statistics</h2>",
            stats_html
        ]
        
        # Add file listings by category with enhanced display
        for category, file_list in files.items():
            content.append(f"<h2>{category}</h2>")
            content.append("<div class='file-grid'>")
            
            for file in file_list:
                file_stats = self.stats['file_stats'].get(str(file.filepath), {})
                words = file_stats.get('words', 0)
                tokens_in = file_stats.get('tokens_in', 0)
                tokens_out = file_stats.get('tokens_out', 0)
                cost = file_stats.get('cost', 0)
                
                # Create a card for each file
                content.append(f"""
                <div class="file-card">
                    <h3><a href="{file.filepath.stem}.html">{file.filepath.name}</a></h3>
                    <p>{words:,} words</p>
                    <p>{tokens_in:,} in / {tokens_out:,} out</p>
                    <p>${cost:.4f}</p>
                </div>
                """)
            
            content.append("</div>")
        
        # Write the enhanced index
        index_path = self.preview_dir / "index.html"
        index_path.write_text(self._wrap_html("Book Preview", "\n".join(content)))

class BookBot:
    """Main class for managing the book writing process"""
    
    def __init__(self, api_key: str, book_dir: Optional[Path] = None, config: Optional[Dict] = None):
        """Initialize BookBot with API key, book directory, and configuration
        
        Args:
            api_key: API key for OpenRouter
            book_dir: Directory containing the book project (default: current directory)
            config: Additional configuration options
        """
        global BOOK_DIR, PREVIEW_DIR, FINAL_DIR, COMMON_DIR, CHAPTERS_DIR
        global PROMPTS_DIR, REVIEWS_DIR, FRONTMATTER_DIR, BACKMATTER_DIR, BOTS_DIR
        
        self.api_key = api_key
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
            
        # Set book directory and create directory paths
        if book_dir:
            BOOK_DIR = Path(book_dir).resolve()
        else:
            BOOK_DIR = Path('.').resolve()
            
        logger.info(f"Using book directory: {BOOK_DIR}")
        
        # Create directory paths
        self.dirs = {
            'preview': BOOK_DIR / PREVIEW_SUBDIR,
            'final': BOOK_DIR / FINAL_SUBDIR,
            'common': BOOK_DIR / COMMON_SUBDIR,
            'chapters': BOOK_DIR / CHAPTERS_SUBDIR,
            'prompts': BOOK_DIR / PROMPTS_SUBDIR,
            'reviews': BOOK_DIR / REVIEWS_SUBDIR,
            'frontmatter': BOOK_DIR / FRONTMATTER_SUBDIR,
            'backmatter': BOOK_DIR / BACKMATTER_SUBDIR,
            'bots': BOOK_DIR / BOTS_SUBDIR
        }
        
        # Set global directory variables
        # TODO these shouldn't be constants 
        PREVIEW_DIR = self.dirs['preview']
        FINAL_DIR = self.dirs['final']
        COMMON_DIR = self.dirs['common']
        CHAPTERS_DIR = self.dirs['chapters']
        PROMPTS_DIR = self.dirs['prompts']
        REVIEWS_DIR = self.dirs['reviews']
        FRONTMATTER_DIR = self.dirs['frontmatter']
        BACKMATTER_DIR = self.dirs['backmatter']
        BOTS_DIR = self.dirs['bots']
        
        # Initialize tokenizer and logging
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        logger.setLevel(logging.getLevelName(self.config['logging_level'].upper()))
        
        # Ensure required directories exist
        for directory in self.dirs.values():
            directory.mkdir(parents=True, exist_ok=True)
            
        # Store paths in config for other components to access
        self.config.update({
            'book_dir': str(BOOK_DIR),
            'preview_dir': str(self.dirs['preview']),
            'final_dir': str(self.dirs['final']),
            'common_dir': str(self.dirs['common']),
            'chapters_dir': str(self.dirs['chapters']),
            'prompts_dir': str(self.dirs['prompts']),
            'reviews_dir': str(self.dirs['reviews']),
            'frontmatter_dir': str(self.dirs['frontmatter']),
            'backmatter_dir': str(self.dirs['backmatter']),
            'bot_dir': str(self.dirs['bots'])
        })
            
        self._init_bots()
        self._init_title()
    
    def _init_bots(self):
        initialize_bot_yaml(Path(self.config['bot_dir']))

    def _init_title(self):
        """Initialize default title file if it doesn't exist"""
        title_file = self.dirs['frontmatter'] / "title.md"
        if not title_file.exists():
            title_file.write_text(DEFAULT_TITLE_FILE)
    
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
            bot_dir = Path(self.config['bot_dir'])
            # loading a bot by name should be a common functin TODO 
            bot_path = bot_dir / f"{bot_name}.yaml"
            if not bot_path.exists():
                raise BookBotError(f"Bot configuration not found: {bot_name}")
                
            # Load the bot
            bot = Bot.from_file(bot_path)
                
            history_file = Path(output_file + "_history.json")
            stats_file = Path(output_file + "_stats.json")
            content_file = Path(output_file + ".md")
            
            # Handle versioning for existing files
            if content_file.exists():
                # This is just for the _call_llm context, as a safeguard
                # Most functions should be handling their own versioning
                logger.info(f"Content file {content_file} already exists - preparing for update")
                
                # Don't actually reset here, as that should be done by the calling function
                # This is just a note for transparency in the logs
            
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
            # We both return the text, and write to the content file. Confusing! TODO
            content = chat.final_text
            stats = chat.get_stats()
            
            # Process content for tagged sections if expansion is enabled
            # TODO Expansion doesn't work at all, and breaks some other stuff. Disabled for now. 
            if False: #self.config.get('expansion', {}).get('enabled', False):
                content, expansion_stats = self._process_expansion_tags(content)
                
                # Add expansion stats to overall stats
                if expansion_stats:
                    stats["input_tokens"] += expansion_stats.get("input_tokens", 0)
                    stats["output_tokens"] += expansion_stats.get("output_tokens", 0)
                    stats["time"] += expansion_stats.get("time", 0)
                    stats["expansion_count"] = expansion_stats.get("count", 0)
                    
                    # Add expansion details to stats
                    if "expansion_details" not in stats:
                        stats["expansion_details"] = []
                    stats["expansion_details"].extend(expansion_stats.get("details", []))
                    
                    # Log detailed expansion statistics
                    logger.info(f"Expansion statistics:")
                    logger.info(f"  Total sections expanded: {expansion_stats.get('count', 0)}")
                    logger.info(f"  Total tokens used: {expansion_stats.get('input_tokens', 0)} in, {expansion_stats.get('output_tokens', 0)} out")
                    logger.info(f"  Total time: {expansion_stats.get('time', 0):.2f}s")
                    
                    # Log details by expansion type
                    type_counts = {}
                    for detail in expansion_stats.get("details", []):
                        exp_type = detail.get("type", "UNKNOWN")
                        if exp_type not in type_counts:
                            type_counts[exp_type] = 0
                        type_counts[exp_type] += 1
                    
                    for exp_type, count in type_counts.items():
                        logger.info(f"  {exp_type}: {count} sections")
                
                # Update the file with expanded content
                if content_file.exists():
                    text_file = TextFile(content_file, config=self.config)
                    
                    # First make a backup if we're going to modify it
                    if expansion_stats.get("count", 0) > 0 and not DRY_RUN:
                        # Save current version to history
                        text_file._save_to_history()
                    
                    # Replace content with expanded version
                    text_file.replace_content(content)
                    
                    # Add expansion metadata
                    text_file.metadata["expansion_count"] = expansion_stats.get("count", 0)
                    text_file.metadata["expanded_at"] = datetime.now().isoformat()
                    
                    # Add detailed expansion metadata
                    if expansion_stats.get("count", 0) > 0:
                        # Get type counts from expansion stats
                        type_counts = {}
                        for detail in expansion_stats.get("details", []):
                            exp_type = detail.get("type", "UNKNOWN")
                            if exp_type not in type_counts:
                                type_counts[exp_type] = 0
                            type_counts[exp_type] += 1
                            
                        text_file.metadata["expansion_types"] = ", ".join(type_counts.keys())
                        for exp_type, count in type_counts.items():
                            text_file.metadata[f"expansion_{exp_type.lower()}_count"] = str(count)
                        
                        # Add a record of the expansion to the version history
                        text_file.metadata["last_operation"] = "expansion"
                    
                    # Save the updated file
                    text_file.save()
            
            return (
                content,
                stats["input_tokens"],
                stats["output_tokens"]
            )
                
        except Exception as e:
            logger.error(f"Error in _call_llm using bot {bot_name}: {str(e)}")
            raise BookBotError(f"LLM call failed: {str(e)}")
    
    # TODO There is no way this function works right now. 
    def _process_expansion_tags(self, content: str) -> Tuple[str, Dict]:
        """Process content for expansion tags and replace with specialized LLM content
        
        Args:
            content: Original content with expansion tags
            
        Returns:
            Tuple of (expanded_content, stats_dict)
        """
        import re
        
        # Define supported expansion types and their regex patterns
        expansion_types = {
            'ROMANCE': r'\[BEGIN ROMANCE\](.*?)\[END ROMANCE\]',
            'ACTION': r'\[BEGIN ACTION\](.*?)\[END ACTION\]',
            'DIALOGUE': r'\[BEGIN DIALOGUE\](.*?)\[END DIALOGUE\]',
            'DESCRIPTION': r'\[BEGIN DESCRIPTION\](.*?)\[END DESCRIPTION\]',
            'WORLDBUILDING': r'\[BEGIN WORLDBUILDING\](.*?)\[END WORLDBUILDING\]',
            'CHARACTER': r'\[BEGIN CHARACTER\](.*?)\[END CHARACTER\]',
            'SUSPENSE': r'\[BEGIN SUSPENSE\](.*?)\[END SUSPENSE\]',
            'EMOTION': r'\[BEGIN EMOTION\](.*?)\[END EMOTION\]',
            'FORESHADOWING': r'\[BEGIN FORESHADOWING\](.*?)\[END FORESHADOWING\]',
            'METAPHOR': r'\[BEGIN METAPHOR\](.*?)\[END METAPHOR\]'
        }
        
        # Collect statistics
        stats = {
            "count": 0,
            "input_tokens": 0,
            "output_tokens": 0, 
            "time": 0,
            "details": []
        }
        
        # Process each expansion type
        for exp_type, pattern in expansion_types.items():
            # Look for tags using regex with DOTALL flag to match across newlines
            matches = re.finditer(pattern, content, re.DOTALL)
            
            # Track replacements to avoid modifying the string during iteration
            replacements = []
            
            for match in matches:
                # Get the section to expand
                section = match.group(1).strip()
                start_pos = match.start()
                end_pos = match.end()
                
                # Only process if there's content between the tags
                if section:
                    # Determine which specialized LLM to use
                    exp_bot_key = f"{exp_type.lower()}_bot"
                    llm_model = self.config.get('expansion', {}).get(exp_bot_key, self.config['expansion']['default_bot'])
                    
                    # Get context window size from config or use default
                    context_size = self.config.get('expansion', {}).get('context_window', 500)
                    
                    # Scale context window based on section length (minimum 500, maximum 2000 characters)
                    section_length = len(section)
                    adjusted_context = min(max(context_size, int(section_length * 0.5)), 2000)
                    
                    # Get context (text before and after the section)
                    # This helps maintain coherence with surrounding text
                    context_before = content[max(0, start_pos-adjusted_context):start_pos].strip()
                    context_after = content[end_pos:min(len(content), end_pos+adjusted_context)].strip()
                    
                    # Log what we're doing
                    logger.info(f"Expanding {exp_type} section ({len(section)} chars) using {llm_model}")
                    
                    try:
                        # Use the appropriate bot for this expansion type by loading from YAML
                        bot_name = f"expand_{exp_type.lower()}"
                        exp_bot_path = self.dirs['bots'] / f"{bot_name}.yaml"
                        
                        # Fallback to default expansion bot if specific one doesn't exist
                        if not exp_bot_path.exists():
                            bot_name = "expand_default"
                            logger.info(f"No specific bot found for {exp_type}, using default expansion bot")
                        
                        # Load the bot configuration
                        exp_bot_path = self.dirs['bots'] / f"{bot_name}.yaml"
                        
                        # Track timing for all approaches
                        start_time = time.time()
                        
                        # Prepare variables for the bot
                        template_vars = {
                            "section_type": exp_type.lower(),
                            "section": section,
                            "context_before": context_before,
                            "context_after": context_after
                        }
                        
                        # Unified approach using BotChat system for all LLM calls
                        try:
                            # If bot file exists, load it directly
                            if exp_bot_path.exists():
                                exp_bot = Bot.from_file(exp_bot_path)
                            # Otherwise, load the default expansion bot but customize it for this expansion type
                            else:
                                logger.info(f"No specific bot found for {exp_type}, customizing default expansion bot")
                                
                                # Get the LLM model from config or use default
                                llm_model = self.config.get('expansion', {}).get(f"{exp_type.lower()}_bot", 
                                                                              self.config['expansion']['default_bot'])
                                
                                # Load default bot as base
                                default_path = self.dirs['bots'] / "expand_default.yaml"
                                if not default_path.exists():
                                    raise FileNotFoundError(f"Default expansion bot not found at {default_path}")
                                    
                                exp_bot = Bot.from_file(default_path)
                                
                                # Customize for this expansion type
                                exp_bot.llm = llm_model
                                exp_bot.name = f"expand_{exp_type.lower()}_temp"
                                exp_bot.type = BotType.DEFAULT  # Use default type for temp bot
                                
                                # Override system prompt for this expansion type
                                system_prompts = {
                                    'ROMANCE': f"You are an expert writer specializing in romance, emotional connection, and intimate character dynamics. Create vivid, emotionally resonant {exp_type.lower()} scenes that feel authentic and moving.",
                                    'ACTION': f"You are an expert action sequence writer with a background in choreography and cinematography. Create dynamic, clear, and impactful {exp_type.lower()} scenes with excellent pacing.",
                                    'DIALOGUE': f"You are an expert dialogue writer with perfect understanding of character voice, subtext, and conversational rhythm. Create authentic, character-revealing {exp_type.lower()} that advances the narrative.",
                                    'DESCRIPTION': f"You are an expert in descriptive prose with a painter's eye for detail and poet's gift for language. Create immersive, sensory-rich {exp_type.lower()} that builds atmosphere and draws readers in.",
                                    'WORLDBUILDING': f"You are an expert worldbuilding consultant who creates rich, coherent fictional settings. Create immersive, believable {exp_type.lower()} elements that feel organic to the story.",
                                    'CHARACTER': f"You are an expert character writer specializing in psychology, motivation, and behavior. Create nuanced, authentic {exp_type.lower()} moments that reveal depth and complexity.",
                                    'SUSPENSE': f"You are an expert in suspense and tension, with perfect understanding of pacing and anticipation. Create gripping, anxiety-inducing {exp_type.lower()} scenes that keep readers on edge.",
                                    'EMOTION': f"You are an expert in emotional writing with deep understanding of human psychology. Create authentic, resonant {exp_type.lower()} passages that connect readers to character experiences.",
                                    'FORESHADOWING': f"You are an expert in literary techniques with special focus on subtle narrative hints and setup. Create artful {exp_type.lower()} that plants seeds for future developments without being obvious.",
                                    'METAPHOR': f"You are an expert in figurative language and symbolic representation. Create powerful, original {exp_type.lower()} that adds depth and meaning through comparison and imagery."
                                }
                                
                                # Set customized system prompt if available
                                if exp_type in system_prompts:
                                    exp_bot.system_prompt = system_prompts[exp_type]
                                else:
                                    exp_bot.system_prompt = f"You are an expert at writing {exp_type.lower()} scenes."
                            
                            # Create BotChat instance with configured bot
                            exp_chat = BotChat(
                                bot=exp_bot,
                                command=f"expand_{exp_type.lower()}",
                                api_key=self.api_key,
                                # No need for history or stats files for expansion
                            )
                            
                            # Generate content using the bot
                            if not DRY_RUN:
                                exp_chat.generate(template_vars)
                                
                                if exp_chat.has_error:
                                    raise Exception(f"Expansion BotChat error: {exp_chat.error}")
                                    
                                # Get result
                                expanded_section = exp_chat.final_text
                                
                                # Get token usage
                                stats_data = exp_chat.get_stats()
                                input_tokens = stats_data.get("input_tokens", 0)
                                output_tokens = stats_data.get("output_tokens", 0)
                                
                                # Get elapsed time
                                elapsed = time.time() - start_time
                            else:
                                # In DRY_RUN mode, simulate a reasonable response
                                logger.info(f"DRY RUN: Simulated expansion of {exp_type} section")
                                
                                # Simulate processing time
                                time.sleep(0.5)
                                elapsed = time.time() - start_time
                                
                                # Create simulated expanded content
                                expanded_section = f"[DRY RUN] Expanded {exp_type} content:\n\n{section}\n\nThis would be enhanced by the {exp_type.lower()} specialized LLM."
                                
                                # Simulate token usage
                                input_tokens = len("".join(str(v) for v in template_vars.values()).split())
                                output_tokens = len(expanded_section.split())
                        
                        except Exception as e:
                            # If any error occurs in the process, log it and use the original content
                            logger.error(f"Error in expansion process for {exp_type}: {str(e)}")
                            expanded_section = section
                            input_tokens = 0
                            output_tokens = 0
                            elapsed = time.time() - start_time
                            
                            # Update stats
                            stats["input_tokens"] += input_tokens
                            stats["output_tokens"] += output_tokens
                            stats["time"] += elapsed
                            stats["count"] += 1
                            
                            # Calculate quality metrics
                            word_count_original = len(section.split())
                            word_count_expanded = len(expanded_section.split())
                            growth_ratio = word_count_expanded / max(1, word_count_original)
                            
                            # Add details for this expansion
                            stats["details"].append({
                                "type": exp_type,
                                "model": llm_model,
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "time": elapsed,
                                "original_length": len(section),
                                "expanded_length": len(expanded_section),
                                "word_count_original": word_count_original,
                                "word_count_expanded": word_count_expanded,
                                "growth_ratio": growth_ratio
                            })
                            
                            logger.info(f"Expanded {exp_type} section: {word_count_original} → {word_count_expanded} words ({growth_ratio:.2f}x) in {elapsed:.2f}s")
                        
                        # Add to replacements list
                        replacements.append((start_pos, end_pos, expanded_section))
                        
                    except Exception as e:
                        logger.error(f"Error expanding {exp_type} section: {str(e)}")
                        # If expansion fails, keep original content and don't update stats
            
            # Apply replacements in reverse order to maintain correct positions
            replacements.sort(reverse=True, key=lambda x: x[0])
            
            # Convert content to list for easier manipulation
            content_list = list(content)
            
            for start_pos, end_pos, expanded_text in replacements:
                # Replace the entire tag section (including the tags) with just the expanded content
                content_list[start_pos:end_pos] = expanded_text
            
            # Convert back to string
            content = ''.join(content_list)
        
        return content, stats

    # TODO Get rid of all git funciotnality it's useless
    def _git_commit(self, message: str):
        """
        Commit changes to git repository.
        Assumes git is already initialized and config is properly set up.
        
        Args:
            message (str): The commit message
        """
        if not self.config['git_enabled']: 
            return
            
        # If in DRY_RUN mode, log the commit message but don't actually commit
        if DRY_RUN:
            logger.info(f"DRY RUN: Would commit changes with message: {message}")
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
            initial_path = BOOK_DIR / "initial.md"
            initial = TextFile(initial_path, config=self.config)
            if not initial.filepath.exists():
                raise BookBotError(f"initial.md not found in {BOOK_DIR}. Please create it with your story description.")
            
            # Generate setting
            output_path = self.dirs['common'] / "setting.md"
            self._call_llm(str(output_path.with_suffix('')), "write_setting", {"initial": initial.content}, command="write_setting")
            
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
            initial_path = BOOK_DIR / "initial.md"
            setting_path = self.dirs['common'] / "setting.md"
            initial = TextFile(initial_path, config=self.config)
            setting = TextFile(setting_path, config=self.config)
            
            if not initial.filepath.exists() or not setting.filepath.exists():
                raise BookBotError(f"Required files (initial.md and setting.md) not found in {BOOK_DIR}")

            # Generate characters using the write_characters bot
            output_path = self.dirs['common'] / "characters.md"
            self._call_llm(
                str(output_path.with_suffix('')),
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
            
    def split_outline(self):
        """Split the main outline into individual chapter outlines"""
        try:
            # Load the outline
            outline = TextFile(COMMON_DIR / "outline.md", config=self.config)
            if not outline.filepath.exists():
                raise BookBotError("Outline not found. Please generate an outline first.")
            
            # Create a directory for chapter outlines if it doesn't exist
            chapter_outlines_dir = COMMON_DIR / "chapter_outlines"
            chapter_outlines_dir.mkdir(exist_ok=True)
            
            # Split the outline using split_outline bot
            content, _, _ = self._call_llm(
                f"common/outline_split",
                "split_outline",
                {
                    "outline": outline.content
                },
                command="split_outline"
            )
            
            # Process the split outline to extract chapter sections
            chapters = self._extract_chapters(content)
            
            # Save each chapter outline to a separate file
            for chapter_num, chapter_content in chapters.items():
                chapter_file = chapter_outlines_dir / f"chapter_{chapter_num:02d}_outline.md"
                chapter_outline = TextFile(chapter_file, config=self.config)
                chapter_outline.replace_content(chapter_content)
                
                # Add reference to the main outline
                chapter_outline.add_reference(str(outline.filepath))
                chapter_outline.save()
                
                logger.info(f"Saved chapter {chapter_num} outline")
            
            # Update the original outline with a reference to the split files
            outline.metadata["split_into"] = ", ".join([f"chapter_{i:02d}_outline.md" for i in chapters.keys()])
            outline.save()
            
            self._git_commit(f"Split outline into {len(chapters)} chapter outlines")
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Split outline into {len(chapters)} chapter outlines")
            return chapters.keys()
            
        except Exception as e:
            logger.error(f"Error splitting outline: {e}")
            raise BookBotError(f"Failed to split outline: {e}")
    
    def _extract_chapters(self, content: str) -> Dict[int, str]:
        """Extract chapter sections from the split content
        
        Returns:
            Dict mapping chapter numbers to chapter content
        """
        chapters = {}
        
        # Split by the chapter separator
        chapter_sections = re.split(r'```\s*\n---\s*\n#\s*Chapter\s+(\d+):', content)
        
        # Process sections
        if len(chapter_sections) > 1:
            # Skip the first element which is before the first separator
            for i in range(1, len(chapter_sections), 2):
                if i+1 < len(chapter_sections):
                    chapter_num = int(chapter_sections[i].strip())
                    chapter_content = f"# Chapter {chapter_num}:{chapter_sections[i+1]}"
                    chapters[chapter_num] = chapter_content
        else:
            # Alternative format
            chapter_sections = re.split(r'---\s*\n#\s*Chapter\s+(\d+):', content)
            if len(chapter_sections) > 1:
                # Skip the first element which is before the first separator
                for i in range(1, len(chapter_sections), 2):
                    if i+1 < len(chapter_sections):
                        chapter_num = int(chapter_sections[i].strip())
                        chapter_content = f"# Chapter {chapter_num}:{chapter_sections[i+1]}"
                        chapters[chapter_num] = chapter_content
        
        return chapters
    
    def split_chapter_outline(self, chapter_num: int):
        """Split a chapter outline into sections for focused writing"""
        try:
            # Load the chapter outline
            chapter_outlines_dir = COMMON_DIR / "chapter_outlines"
            chapter_outline_path = chapter_outlines_dir / f"chapter_{chapter_num:02d}_outline.md"
            
            if not chapter_outline_path.exists():
                # Check if we need to split the outline first
                if not (COMMON_DIR / "outline.md").exists():
                    raise BookBotError("Outline not found. Please generate an outline first.")
                    
                # Split the outline
                self.split_outline()
                
                # Check again
                if not chapter_outline_path.exists():
                    raise BookBotError(f"Chapter {chapter_num} outline not found after splitting.")
            
            chapter_outline = TextFile(chapter_outline_path, config=self.config)
            
            # Create a directory for section outlines
            sections_dir = chapter_outlines_dir / f"chapter_{chapter_num:02d}_sections"
            sections_dir.mkdir(parents=True, exist_ok=True)
            
            # Split the chapter using split_chapter bot
            content, _, _ = self._call_llm(
                f"common/chapter_{chapter_num:02d}_outline_split",
                "split_chapter",
                {
                    "chapter_outline": chapter_outline.content
                },
                command=f"split_chapter_{chapter_num}"
            )
            
            # Process the split chapter to extract section outlines
            sections = self._extract_sections(content)
            
            # Save each section to a separate file
            for section_num, section_content in sections.items():
                section_file = sections_dir / f"section_{section_num:02d}.md"
                section_outline = TextFile(section_file, config=self.config)
                section_outline.replace_content(section_content)
                
                # Add reference to the chapter outline
                section_outline.add_reference(str(chapter_outline.filepath))
                section_outline.save()
                
                logger.info(f"Saved chapter {chapter_num}, section {section_num} outline")
            
            # Update the chapter outline with a reference to the section files
            chapter_outline.metadata["split_into"] = ", ".join([f"section_{i:02d}.md" for i in sections.keys()])
            chapter_outline.save()
            
            self._git_commit(f"Split chapter {chapter_num} into {len(sections)} sections")
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Split chapter {chapter_num} into {len(sections)} sections")
            return sections.keys()
            
        except Exception as e:
            logger.error(f"Error splitting chapter {chapter_num}: {e}")
            raise BookBotError(f"Failed to split chapter {chapter_num}: {e}")
    
    def _extract_sections(self, content: str) -> Dict[int, str]:
        """Extract section content from the split chapter outline
        
        Returns:
            Dict mapping section numbers to section content
        """
        sections = {}
        
        # Split by the section separator
        section_parts = re.split(r'```\s*\n---\s*\n##\s*Section\s+(\d+):', content)
        
        # Process sections
        if len(section_parts) > 1:
            # Skip the first element which is before the first separator
            for i in range(1, len(section_parts), 2):
                if i+1 < len(section_parts):
                    section_num = int(section_parts[i].strip())
                    section_content = f"## Section {section_num}:{section_parts[i+1]}"
                    sections[section_num] = section_content
        else:
            # Alternative format
            section_parts = re.split(r'---\s*\n##\s*Section\s+(\d+):', content)
            if len(section_parts) > 1:
                # Skip the first element which is before the first separator
                for i in range(1, len(section_parts), 2):
                    if i+1 < len(section_parts):
                        section_num = int(section_parts[i].strip())
                        section_content = f"## Section {section_num}:{section_parts[i+1]}"
                        sections[section_num] = section_content
        
        return sections
        
    def write_section(self, chapter_num: int, section_num: int):
        """Write a specific section of a chapter"""
        try:
            # Load necessary context
            setting = TextFile(COMMON_DIR / "setting.md", config=self.config)
            characters = TextFile(COMMON_DIR / "characters.md", config=self.config)
            
            # Load the section outline
            chapter_outlines_dir = COMMON_DIR / "chapter_outlines"
            sections_dir = chapter_outlines_dir / f"chapter_{chapter_num:02d}_sections"
            section_outline_path = sections_dir / f"section_{section_num:02d}.md"
            
            if not section_outline_path.exists():
                # Check if we need to split the chapter first
                if not (chapter_outlines_dir / f"chapter_{chapter_num:02d}_outline.md").exists():
                    raise BookBotError(f"Chapter {chapter_num} outline not found. Please generate it first.")
                    
                # Split the chapter
                self.split_chapter_outline(chapter_num)
                
                # Check again
                if not section_outline_path.exists():
                    raise BookBotError(f"Section {section_num} of Chapter {chapter_num} not found after splitting.")
            
            section_outline = TextFile(section_outline_path, config=self.config)
            
            # Get previous section content if it exists
            previous_section = ""
            if section_num > 1:
                prev_section_path = sections_dir / f"section_{section_num-1:02d}.md"
                if prev_section_path.exists():
                    prev_section = TextFile(prev_section_path, config=self.config)
                    previous_section = prev_section.content
            
            # Create the output directory
            content_sections_dir = CHAPTERS_DIR / f"chapter_{chapter_num:02d}_sections"
            content_sections_dir.mkdir(parents=True, exist_ok=True)
            
            # Write the section using write_section bot
            content, _, _ = self._call_llm(
                f"chapters/chapter_{chapter_num:02d}_sections/section_{section_num:02d}",
                "write_section",
                {
                    "chapter_number": chapter_num,
                    "section_number": section_num,
                    "section_outline": section_outline.content,
                    "setting": setting.content,
                    "characters": characters.content,
                    "previous_section": previous_section
                },
                command=f"write_chapter_{chapter_num}_section_{section_num}"
            )
            
            # Access the written file
            section_file_path = content_sections_dir / f"section_{section_num:02d}.md"
            section_file = TextFile(section_file_path, config=self.config)
            
            # Add references
            section_file.add_reference(str(section_outline_path))
            section_file.add_reference(str(COMMON_DIR / "setting.md"))
            section_file.add_reference(str(COMMON_DIR / "characters.md"))
            if section_num > 1 and prev_section_path.exists():
                section_file.add_reference(str(prev_section_path))
            
            section_file.save()
            
            self._git_commit(f"Written chapter {chapter_num}, section {section_num}")
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Section {section_num} of Chapter {chapter_num} written successfully")
            
            return section_file_path
            
        except Exception as e:
            logger.error(f"Error writing section {section_num} of chapter {chapter_num}: {e}")
            raise BookBotError(f"Failed to write section: {e}")
            
    def assemble_chapter_from_sections(self, chapter_num: int):
        """Combine all sections into a complete chapter"""
        try:
            # Find all sections for this chapter
            content_sections_dir = CHAPTERS_DIR / f"chapter_{chapter_num:02d}_sections"
            if not content_sections_dir.exists():
                raise BookBotError(f"No sections found for chapter {chapter_num}")
                
            # Get all section files and sort them
            section_files = sorted(
                content_sections_dir.glob("section_*.md"),
                key=lambda p: int(p.stem.split('_')[1])
            )
            
            if not section_files:
                raise BookBotError(f"No sections found for chapter {chapter_num}")
                
            # Load all sections
            sections = []
            for section_file in section_files:
                section = TextFile(section_file, config=self.config)
                sections.append(section.content)
                
            # Combine into a complete chapter
            chapter_content = f"# Chapter {chapter_num}\n\n" + "\n\n".join(sections)
            
            # Create the chapter file
            chapter_path = CHAPTERS_DIR / f"chapter_{chapter_num:02d}.md"
            chapter = TextFile(chapter_path, config=self.config)
            
            # If the file exists, reset it first
            if chapter_path.exists():
                chapter.reset()
                
            chapter.replace_content(chapter_content)
            
            # Add references to each section
            for section_file in section_files:
                chapter.add_reference(str(section_file))
                
            chapter.metadata["assembled_from_sections"] = "true"
            chapter.metadata["section_count"] = str(len(section_files))
            chapter.save()
            
            self._git_commit(f"Assembled chapter {chapter_num} from {len(section_files)} sections")
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Chapter {chapter_num} assembled from {len(section_files)} sections")
            
        except Exception as e:
            logger.error(f"Error assembling chapter {chapter_num}: {e}")
            raise BookBotError(f"Failed to assemble chapter: {e}")

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
                
            # Check if chapter already exists and handle versioning
            chapter_path = CHAPTERS_DIR / f"chapter_{chapter_num:02d}.md"
            if chapter_path.exists():
                # If we're rewriting an existing chapter, handle versioning
                chapter = TextFile(chapter_path, config=self.config)
                chapter.reset()  # Save existing version to history
                logger.info(f"Rewriting existing chapter {chapter_num} (creating version {chapter.metadata.get('version', '?')})")

            # Generate chapter using write_chapter bot
            content, input_tokens, output_tokens = self._call_llm(
                f"chapters/chapter_{chapter_num:02d}",
                "write_chapter_simple", #TODO FIXME temporarily set to use the simple writing prompt
                {
                    "chapter_number": chapter_num,
                    "outline": outline.content,
                    "setting": setting.content,
                    "characters": characters.content,
                    "previous_chapter": prev_chapter_content or "No previous chapter available."
                },
                command=f"write_chapter_{chapter_num}"
            )
            
            # If chapter was rewritten, update references
            if chapter_path.exists():
                chapter = TextFile(chapter_path, config=self.config)
                # Add references to source materials
                chapter.add_reference(str(COMMON_DIR / "outline.md"))
                chapter.add_reference(str(COMMON_DIR / "setting.md"))
                chapter.add_reference(str(COMMON_DIR / "characters.md"))
                if prev_chapter_content:
                    prev_path = CHAPTERS_DIR / f"chapter_{chapter_num-1:02d}.md"
                    chapter.add_reference(str(prev_path))
                chapter.save()

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
            
            # Load the chapter and create a backup with reset
            chapter = TextFile(chapter_path, config=self.config)
            
            # Store version before editing
            old_version = chapter.metadata.get('version', '1')
            logger.info(f"Editing chapter {chapter_num} (version {old_version})")
            
            # Reset before editing - this saves the current version to history
            chapter.reset()

            # Edit chapter using edit_chapter bot
            content, input_tokens, output_tokens = self._call_llm(
                f"chapters/chapter_{chapter_num:02d}",
                "edit_chapter",
                {
                    "chapter_number": chapter_num,
                    "content": chapter.content,
                    "edit_notes": "No previous edit notes available."  # Could store previous edits in future
                },
                command=f"edit_chapter_{chapter_num}"
            )
            
            # Set the content from the LLM output
            chapter.replace_content(content)
            
            # Update metadata with edit information
            chapter.metadata["editor_bot"] = "edit_chapter"
            
            # Save the updated chapter
            chapter.save()

            self._git_commit(f"Edited chapter {chapter_num}")
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Chapter {chapter_num} edited successfully (version {chapter.metadata.get('version', '?')})")
            
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
            content, _, _ = self._call_llm(
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

    def self_edit(self, editor_bot: str, file: str, editor_step_name: str):
        """Self-edit a file. In a self-edit, only one Bot is used to edit an existing file.
        The file is loaded, and the Bot is called with the file content to generate a new edited file.
        Uses versioning to track history of edits.
        """
        try:
            initial = TextFile(Path("initial.md"), config=self.config)
            setting = TextFile(COMMON_DIR / "setting.md", config=self.config)
            characters = TextFile(COMMON_DIR / "characters.md", config=self.config)

            # Load the file to be edited
            if file.endswith(".md"):
                file = file[:-3]
                # Need the path without extension since it's used to make other filenames
            file_path = Path(file + ".md")
            if not file_path.exists():
                raise BookBotError(f"File not found: {file}")
                
            # Load the original file and create a backup with reset
            orig_file = TextFile(file_path, config=self.config)
            
            # Store version before editing
            old_version = orig_file.metadata.get('version', '1')
            logger.info(f"Self-editing {file} (version {old_version})")
            
            # Reset before editing - this saves the current version to history
            orig_file.reset()
            
            # Run the LLM to update the file with a new version
            content, input_tokens, output_tokens = self._call_llm(
                file,
                editor_bot,
                {
                    "initial": initial.content,
                    "setting": setting.content,
                    "characters": characters.content,
                    "content": orig_file.content,
                },
                command=f"edit_{editor_bot}"
            )
            
            # Set the content from the LLM output
            orig_file.replace_content(content)
            
            # Add references to the files used in this edit
            orig_file.add_reference(str(Path("initial.md")))
            orig_file.add_reference(str(COMMON_DIR / "setting.md"))
            orig_file.add_reference(str(COMMON_DIR / "characters.md"))
            
            # Update metadata with edit information
            orig_file.metadata["editor_bot"] = editor_bot
            if editor_step_name:
                orig_file.metadata["editor_step"] = editor_step_name
            
            # Generate a diff message
            diff_message = self._generate_diff_message(orig_file.content, content)
            logger.info(f"Diff: {diff_message}")
            
            # Commit the changes
            commit_msg = f"Edited {file} with {editor_bot}"
            if editor_step_name:
                commit_msg += f" - {editor_step_name}"
            self._git_commit(commit_msg)
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Edited successfully (version {orig_file.metadata.get('version', '?')})")
        except Exception as e:
            logger.error(f"Error editing with {editor_bot}: {e}")
            # Print traceback
            import traceback
            traceback.print_exc()
            raise BookBotError(f"Failed to edit: {e}")

    def revise(self, reviewer_bot: str, editor_bot: str, file: str, revise_step_name: str):
        """Review and edit a file using two different bots.
        First, loads the file, which can be a chapter file or commons file specified by its path.
        Then call the LLM with the reviewer bot and the file to generate a new review file.
        Then call the LLM with the editor bot and the review file to edit the original file.
        
        Uses versioning to track history of edits and maintain references between files.
        
        Since there may be multiple rounds of revision with the same reviewer and file, revise_step_name is 
        an optional value that lets you specify the step name to use in the file name, logs, and git commit message."""
        try:
            # Load initial, setting, and characters files
            # NOTE: Because they are substituted in as variables it doesn't make sense to revise these files
            initial = TextFile(Path("initial.md"), config=self.config, ensure_exists=True)
            setting = TextFile(COMMON_DIR / "setting.md", config=self.config, ensure_exists=True)
            characters = TextFile(COMMON_DIR / "characters.md", config=self.config, ensure_exists=True)
            outline = TextFile(COMMON_DIR / "outline.md", config=self.config, ensure_exists=True)

            # Note: Commons review bots do NOT include the outline as a separate template var,
            # because they are editing the outline. However there's no harm in loading the outline
            # and passing it in as a template var, which will simply not be used.

            # Load the file to be reviewed
            if file.endswith(".md"):
                file = file[:-3]
                # Need the path without extension since it's used to make other filenames
            file_path = Path(file + ".md") 
            if not file_path.exists():
                raise BookBotError(f"File not found: {file}")
                
            # Load the original file to be revised
            orig_file = TextFile(file_path, config=self.config)
            
            # Store version before revising
            old_version = orig_file.metadata.get('version', '1')
            logger.info(f"Revising {file} (version {old_version})")

            # Generate review file path
            if revise_step_name:
                review_file = self.config["review_dir"] + f"/{file_path.stem}_{revise_step_name}_review"
            else:
                review_file = self.config["review_dir"] + f"/{file_path.stem}_{reviewer_bot}_review"
            logger.info(f"REVISING WITH REVIEW BOT {reviewer_bot}")

            # Create a new review file
            self._call_llm(
                review_file,
                reviewer_bot,
                {
                    "initial": initial.content,
                    "setting": setting.content,
                    "characters": characters.content,
                    "outline": outline.content,
                    "content": orig_file.content,
                },
                command=f"review_{reviewer_bot}"
            )

            # Load the review file
            review = TextFile(Path(review_file + ".md"), config=self.config, ensure_exists=True)
            if review.content == "":
                raise BookBotError(f"Review file is empty: {review_file}")
                
            # Add reference to the original file in the review
            review.add_reference(str(file_path))
            review.save()

            # Reset the original file before editing - this saves current version to history
            orig_file.reset()
            
            # Edit the original file using the editor bot
            content, input_tokens, output_tokens = self._call_llm(
                file,
                editor_bot,
                {
                    "initial": initial.content,
                    "setting": setting.content,
                    "characters": characters.content,
                    "content": orig_file.content,
                    "outline": outline.content,
                    "review": review.content
                },
                command=f"edit_{reviewer_bot}"
            )
            
            # Set the content from the LLM output
            orig_file.replace_content(content)
            
            # Add references to all files used in this revision
            orig_file.add_reference(str(Path("initial.md")))
            orig_file.add_reference(str(COMMON_DIR / "setting.md"))
            orig_file.add_reference(str(COMMON_DIR / "characters.md"))
            orig_file.add_reference(str(COMMON_DIR / "outline.md"))
            orig_file.add_reference(str(review_file + ".md"))
            
            # Update metadata with revision information
            orig_file.metadata["reviewer_bot"] = reviewer_bot
            orig_file.metadata["editor_bot"] = editor_bot
            if revise_step_name:
                orig_file.metadata["revise_step"] = revise_step_name

            # Generate a diff message
            diff_message = self._generate_diff_message(orig_file.content, content)
            logger.info(f"Diff: {diff_message}")

            # Commit the changes
            commit_msg = f"Reviewed and edited {file} with {reviewer_bot} and {editor_bot}"
            if revise_step_name:
                commit_msg += f" - {revise_step_name}"
            self._git_commit(commit_msg)
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Reviewed and edited successfully (version {orig_file.metadata.get('version', '?')})")
            
        except Exception as e:
            logger.error(f"Error reviewing and editing with 2 bots: {e}")
            # Print traceback
            import traceback
            traceback.print_exc()
            raise BookBotError(f"Failed to review and edit: {e}")

    def _generate_diff_message(self, old_text: str, new_text: str) -> str:
        """Generate a summary of the diff between two texts"""
        from difflib import unified_diff
        
        diff = list(unified_diff(old_text.splitlines(), new_text.splitlines(), lineterm=''))
        if not diff:
            return "No changes detected."
        else:
            # Summarize the diff as lines added, lines removed
            added_lines = sum(1 for line in diff if line.startswith('+ ') and not line.startswith('+++'))
            removed_lines = sum(1 for line in diff if line.startswith('- ') and not line.startswith('---'))
            summary = f"Changes detected: {added_lines} lines added, {removed_lines} lines removed."
            return summary
            
    def list_versions(self, file_path: str):
        """List all versions of a file"""
        try:
            # Standardize file path handling
            if file_path.endswith(".md"):
                file_path = file_path[:-3]
            file_path = Path(file_path + ".md")
            
            if not file_path.exists():
                # Check if this is an archived file
                history_dir = file_path.parent / "history"
                archive_files = list(history_dir.glob(f"{file_path.stem}.*{file_path.suffix}"))
                if archive_files:
                    console.print(f"[yellow]Note:[/yellow] {file_path} is archived (no current version exists)")
                else:
                    raise BookBotError(f"File not found: {file_path}")
            else:
                # Load the file to get its current version
                file = TextFile(file_path, config=self.config)
                current_version = file.metadata.get('version', '1')
                console.print(f"Current version: {current_version}")
            
            # Check for history directory
            history_dir = file_path.parent / "history"
            if not history_dir.exists() or not history_dir.is_dir():
                console.print(f"No history directory found for {file_path}")
                return
            
            # Get all version files - support both naming patterns for backward compatibility
            basename = file_path.stem
            parent_dir = file_path.parent.name
            unique_basename = f"{parent_dir}_{basename}" if parent_dir else basename
            
            # Try both naming patterns
            version_files = sorted(
                list(history_dir.glob(f"{basename}.v*{file_path.suffix}")) + 
                list(history_dir.glob(f"{unique_basename}.v*{file_path.suffix}")),
                key=lambda p: int(p.stem.split('.v')[1])
            )
            
            if not version_files:
                console.print(f"No version history found for {file_path}")
                return
                
            # Display version information
            console.print(f"\n[bold]Version history for {file_path}:[/bold]")
            console.print("\nAvailable versions:")
            
            for v_file in version_files:
                v_num = v_file.stem.split('.v')[1]
                v_stats = os.stat(v_file)
                v_timestamp = datetime.fromtimestamp(v_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                # Load the file to get additional metadata if available
                try:
                    v_text = TextFile(v_file, config=self.config)
                    # Get word count and any notable metadata
                    word_count = len(v_text.content.split())
                    metadata_info = []
                    
                    # Important metadata keys to display
                    important_keys = [
                        'reviewer_bot', 'editor_bot', 'revise_step', 'editor_step', 
                        'expansion_count', 'expansion_types', 'archived'
                    ]
                    
                    for key in important_keys:
                        if key in v_text.metadata:
                            metadata_info.append(f"{key}={v_text.metadata[key]}")
                    
                    metadata_str = f" ({', '.join(metadata_info)})" if metadata_info else ""
                    console.print(f"  Version {v_num}: {v_timestamp} - {word_count} words{metadata_str}")
                except Exception as e:
                    console.print(f"  Version {v_num}: {v_timestamp} - Error reading file: {e}")
            
            console.print("\n[blue]Available commands:[/blue]")
            console.print("  revert - Restore a specific version")
            console.print("  archive - Archive the current version")
            console.print("  find-refs - Find files that reference this file")
            console.print("  get-refs - Find files referenced by this file")
        
        except Exception as e:
            logger.error(f"Error listing versions: {e}")
            raise BookBotError(f"Failed to list versions: {e}")
            
    def revert_to_version(self, file_path: str, version: int):
        """Revert a file to a specific version"""
        try:
            # Standardize file path handling
            if file_path.endswith(".md"):
                file_path = file_path[:-3]
            file_path = Path(file_path + ".md")
            
            if not file_path.exists():
                raise BookBotError(f"File not found: {file_path}")
                
            # Load the file and revert
            file = TextFile(file_path, config=self.config)
            if file.revert_to_version(version):
                # Commit the changes
                self._git_commit(f"Reverted {file_path.name} to version {version}")
                console.print(f"\n[green]✓[/green] Successfully reverted {file_path} to version {version}")
            else:
                console.print(f"\n[red]![/red] Failed to revert {file_path} to version {version}")
                
        except Exception as e:
            logger.error(f"Error reverting to version: {e}")
            raise BookBotError(f"Failed to revert to version: {e}")
            
    def create_derived_file(self, source_path: str, suffix: str):
        """Create a new file derived from an existing one"""
        try:
            # Standardize file path handling
            if source_path.endswith(".md"):
                source_path = source_path[:-3]
            source_path = Path(source_path + ".md")
            
            if not source_path.exists():
                raise BookBotError(f"Source file not found: {source_path}")
                
            # Create derived file
            derived_file = TextFile.create_derived_file(source_path, suffix)
            derived_file.save()
            
            console.print(f"\n[green]✓[/green] Created derived file: {derived_file.filepath}")
            
        except Exception as e:
            logger.error(f"Error creating derived file: {e}")
            raise BookBotError(f"Failed to create derived file: {e}")
    
    def archive_file(self, file_path: str):
        """Archive a file - save to history but remove current version"""
        try:
            # Standardize file path handling
            if file_path.endswith(".md"):
                file_path = file_path[:-3]
            file_path = Path(file_path + ".md")
            
            if not file_path.exists():
                raise BookBotError(f"File not found: {file_path}")
                
            # Load the file and save to history
            file = TextFile(file_path, config=self.config)
            
            # Add archived flag to metadata
            file.metadata["archived"] = "true"
            file.metadata["archived_at"] = datetime.now().isoformat()
            
            # Save to history
            file._save_to_history()
            
            if not DRY_RUN:
                # Delete the file and associated files
                file_path.unlink()
                
                # Delete associated history and stats files if they exist
                history_path = file_path.with_suffix('.history.json')
                stats_path = file_path.with_suffix('.stats.json')
                
                if history_path.exists():
                    history_path.unlink()
                    
                if stats_path.exists():
                    stats_path.unlink()
            else:
                logger.info(f"DRY RUN: Would delete {file_path} and associated files")
                
            self._git_commit(f"Archived {file_path.name}")
            
            console.print(f"\n[green]✓[/green] Archived {file_path}")
            
        except Exception as e:
            logger.error(f"Error archiving file: {e}")
            raise BookBotError(f"Failed to archive file: {e}")
    
    def list_archived_files(self):
        """List all archived files"""
        try:
            archived_files = []
            
            # Check all history directories in all content directories
            for dir_name in ['common', 'chapters', 'reviews']:
                content_dir = BOOK_DIR / dir_name
                history_dir = content_dir / "history"
                
                if history_dir.exists() and history_dir.is_dir():
                    # Find files with archived flag in metadata
                    for history_file in history_dir.glob("*.md"):
                        try:
                            file = TextFile(history_file, config=self.config)
                            if file.metadata.get("archived") == "true":
                                archived_files.append((history_file, file))
                        except Exception as e:
                            logger.warning(f"Error reading history file {history_file}: {e}")
            
            if not archived_files:
                console.print("No archived files found")
                return
                
            # Display archived files
            console.print(f"\n[bold]Archived Files:[/bold]")
            for file_path, file in archived_files:
                # Get metadata of interest
                archive_date = file.metadata.get("archived_at", "Unknown date")
                version = file.metadata.get("version", "Unknown")
                words = len(file.content.split())
                
                # Extract date for display
                try:
                    parsed_date = datetime.fromisoformat(archive_date)
                    archive_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
                
                # Get original path
                original_path = file.metadata.get("original_path", file_path.name)
                
                console.print(f"  {original_path} (v{version}, {words} words, archived on {archive_date})")
            
            console.print("\n[blue]Use 'revert' command to restore an archived file[/blue]")
            
        except Exception as e:
            logger.error(f"Error listing archived files: {e}")
            raise BookBotError(f"Failed to list archived files: {e}")
    
    def find_references_to(self, file_path: str):
        """Find all files that reference the specified file"""
        try:
            # Standardize file path handling
            if file_path.endswith(".md"):
                file_path = file_path[:-3]
            file_path = Path(file_path + ".md")
            
            # Get real path to handle symlinks
            file_path = file_path.resolve()
            file_path_str = str(file_path)
            
            references = []
            
            # Look in all content directories
            for dir_name in ['common', 'chapters', 'reviews']:
                content_dir = BOOK_DIR / dir_name
                if not content_dir.exists():
                    continue
                    
                # Scan all markdown files
                for md_file in content_dir.glob("**/*.md"):
                    # Skip history directory
                    if "history" in md_file.parts:
                        continue
                        
                    try:
                        # Load the file and check references
                        file = TextFile(md_file, config=self.config)
                        if 'references' not in file.metadata:
                            continue
                            
                        # Extract references
                        refs = file.metadata['references'].split(', ')
                        
                        # Check if our file is referenced
                        for ref in refs:
                            # Handle version specification in reference
                            ref_path = ref.split('#')[0]
                            
                            # Check if paths match
                            if os.path.samefile(ref_path, file_path_str):
                                references.append((md_file, file))
                                break
                    except Exception as e:
                        logger.warning(f"Error checking references in {md_file}: {e}")
            
            # Display results
            if not references:
                console.print(f"No files reference {file_path}")
                return
                
            console.print(f"\n[bold]Files that reference {file_path}:[/bold]")
            
            for ref_file_path, ref_file in references:
                words = len(ref_file.content.split())
                version = ref_file.metadata.get("version", "1")
                
                console.print(f"  {ref_file_path} (v{version}, {words} words)")
                
        except Exception as e:
            logger.error(f"Error finding references: {e}")
            raise BookBotError(f"Failed to find references: {e}")
    
    def get_file_references(self, file_path: str):
        """Find all files referenced by the specified file"""
        try:
            # Standardize file path handling
            if file_path.endswith(".md"):
                file_path = file_path[:-3]
            file_path = Path(file_path + ".md")
            
            if not file_path.exists():
                raise BookBotError(f"File not found: {file_path}")
                
            # Load the file and extract references
            file = TextFile(file_path, config=self.config)
            
            if 'references' not in file.metadata:
                console.print(f"{file_path} does not reference any files")
                return
                
            # Extract references
            refs = file.metadata['references'].split(', ')
            if not refs:
                console.print(f"{file_path} does not reference any files")
                return
                
            console.print(f"\n[bold]Files referenced by {file_path}:[/bold]")
            
            for ref in refs:
                # Handle version specification in reference
                parts = ref.split('#')
                ref_path = parts[0]
                ref_version = parts[1] if len(parts) > 1 else None
                
                console.print(f"  {ref_path}" + (f" (v{ref_version})" if ref_version else ""))
                
                # Check if the referenced file exists
                try:
                    if Path(ref_path).exists():
                        ref_file = TextFile(ref_path, config=self.config)
                        words = len(ref_file.content.split())
                        console.print(f"    [green]Exists: {words} words[/green]")
                    else:
                        console.print(f"    [red]Does not exist[/red]")
                except Exception as e:
                    console.print(f"    [red]Error: {e}[/red]")
                
        except Exception as e:
            logger.error(f"Error getting references: {e}")
            raise BookBotError(f"Failed to get references: {e}")

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
        """Generate HTML preview of all content using the enhanced preview generator"""
        try:
            # Collect all files by category using the paths from self.dirs
            files = {
                "Chapters": sorted(
                    [TextFile(p, config=self.config) for p in self.dirs['chapters'].glob("*.md")],
                    key=lambda f: int(f.filepath.stem.split('_')[1]) if f.filepath.stem.split('_')[1].isdigit() else 0
                ),
                "Common": [TextFile(p, config=self.config) for p in self.dirs['common'].glob("*.md")],
                "Reviews": [TextFile(p, config=self.config) for p in self.dirs['reviews'].glob("*.md")]
            }
            
            # Generate preview with the book directory
            preview = PreviewGenerator(preview_dir=self.dirs['preview'])
            preview.generate(files)
            
            console.print(f"\n[green]✓[/green] Generated preview at {self.dirs['preview']}")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error generating preview: {e}")
            console.print(f"[red]![/red] Failed to generate preview: {e}")

    def expand_chapter(self, chapter_num: int):
        """Expand an existing chapter by adding specialized section tags and improving content"""
        try:
            chapter_path = CHAPTERS_DIR / f"chapter_{chapter_num:02d}.md"
            if not chapter_path.exists():
                raise BookBotError(f"Chapter {chapter_num} not found")
            
            # Load the chapter and create a backup with reset
            chapter = TextFile(chapter_path, config=self.config)
            
            # Store version before editing
            old_version = chapter.metadata.get('version', '1')
            logger.info(f"Expanding chapter {chapter_num} (version {old_version})")
            
            # Reset before editing - this saves the current version to history
            chapter.reset()

            # Use a dedicated expand_chapter bot from YAML files
            # Instead of hardcoding the prompt, we'll use the Bot system
            content, input_tokens, output_tokens = self._call_llm(
                f"chapters/chapter_{chapter_num:02d}",
                "expand_chapter",  # This should be defined in bots/expand_chapter.yaml
                {
                    "chapter_number": chapter_num,
                    "content": chapter.content
                },
                command=f"expand_chapter_{chapter_num}"
            )
            
            # Set the content from the LLM output
            chapter.replace_content(content)
            
            # Update metadata with edit information
            chapter.metadata["editor_bot"] = "expand_chapter"
            chapter.metadata["expansion_prepared"] = "true"
            
            # Save the updated chapter
            chapter.save()

            # Process expansion tags
            if self.config.get('expansion', {}).get('enabled', False):
                logger.info(f"Processing expansion tags in chapter {chapter_num}")
                expanded_content, expansion_stats = self._process_expansion_tags(content)
                
                if expansion_stats and expansion_stats.get("count", 0) > 0:
                    # Create a new version with expanded content
                    if not DRY_RUN:
                        chapter.reset()  # Save the tagged version to history
                    chapter.replace_content(expanded_content)
                    chapter.metadata["expansion_applied"] = "true"
                    chapter.metadata["expansion_count"] = str(expansion_stats.get("count", 0))
                    chapter.metadata["expanded_at"] = datetime.now().isoformat()
                    chapter.metadata["last_operation"] = "expansion"
                    
                    # Add type-specific expansion counts
                    type_counts = {}
                    for detail in expansion_stats.get("details", []):
                        exp_type = detail.get("type", "UNKNOWN")
                        if exp_type not in type_counts:
                            type_counts[exp_type] = 0
                        type_counts[exp_type] += 1
                    
                    if type_counts:
                        chapter.metadata["expansion_types"] = ", ".join(type_counts.keys())
                        for exp_type, count in type_counts.items():
                            chapter.metadata[f"expansion_{exp_type.lower()}_count"] = str(count)
                    
                    # Log expansion stats
                    logger.info(f"Applied {expansion_stats.get('count', 0)} expansions to chapter {chapter_num}")
                    for exp_type, count in type_counts.items():
                        logger.info(f"  {exp_type}: {count} sections")
                    
                    # Save the expanded chapter
                    chapter.save()
                    
                    self._git_commit(f"Expanded chapter {chapter_num} with {expansion_stats.get('count', 0)} specialized sections")
                else:
                    logger.info(f"No expansion tags found or processed in chapter {chapter_num}")
                    self._git_commit(f"Prepared chapter {chapter_num} for expansion (no tags processed)")
            else:
                self._git_commit(f"Prepared chapter {chapter_num} for expansion (expansion disabled)")
            
            self._generate_preview()
            
            console.print(f"\n[green]✓[/green] Chapter {chapter_num} expanded successfully (version {chapter.metadata.get('version', '?')})")
            
        except Exception as e:
            logger.error(f"Error expanding chapter {chapter_num}: {e}")
            raise BookBotError(f"Failed to expand chapter: {e}")
    
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

def task_gen_outline(bot):
    """Task to generate the outline"""
    bot.write_settings()
    bot.write_characters()
    bot.write_outline()

def task_revise_outline(bot):
    """Apply all of the possible outline revisions. Trying to start with the lowest quality ones 
    on the theory that higher-quality ones will fix any errors introduced."""
    # This whole thing is fairly expensive. All of them use DeepSeek and either 1500 words (most)
    # or 3000 words (some). Need to figure out if cost can be reduced somehow.
    # Also could pull out the big guns (o3-mini-high) for some content.
    dir="common"
    # First do a self-edit to give it a little more time to work
    bot.self_edit("self_edit_outline", dir+"/outline", "revise_outline")
    # First do a plot hole edit to make sure the story makes sense to begin wtih
    bot.revise("review_outline_plot_hole", "edit_outline", dir+"/outline", "revise_plot_hole_1")
    # Genre edits to add more drama
    bot.revise("review_outline_romance", "edit_outline", dir+"/outline", "revise_romance")
    bot.revise("review_outline_mystery", "edit_outline", dir+"/outline", "revise_mystery")
    bot.revise("review_outline_action", "edit_outline", dir+"/outline", "revise_action")
    # Historical accuracy and realism
    bot.revise("review_outline_realism", "edit_outline", dir+"/outline", "revise_realism")
    # Story structure and pacing
    bot.revise("review_outline_pov", "edit_outline", dir+"/outline", "revise_pov")
    bot.revise("review_outline_motivation", "edit_outline", dir+"/outline", "revise_motivation")
    bot.revise("review_outline_foreshadowing", "edit_outline", dir+"/outline", "revise_foreshadowing")
    bot.revise("review_outline_pacing", "edit_outline", dir+"/outline", "revise_pacing")
    # Another plot hole edit
    bot.revise("review_outline_plot_hole", "edit_outline", dir+"/outline", "revise_plot_hole_2")
    # Diversity edits with Claude and o3
    bot.revise("review_outline_claude", "edit_outline", dir+"/outline", "revise_claude")
    bot.revise("review_outline_o3", "edit_outline", dir+"/outline", "revise_o3")

def main():
    """Main entry point for BookBot"""
    parser = argparse.ArgumentParser(description="BookBot - Automated Book Writing Tool")
    
    # Global arguments
    parser.add_argument('--book-dir', '-d', type=str, default='.', 
                        help='Directory containing the book project (default: current directory)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run without making API calls or modifying files')
    parser.add_argument('--cheap-mode', '-c', action='store_true',
                        help='Use a cheaper model for testing')
    
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Initial setup commands
    subparsers.add_parser('init', help='Initialize a new book project in the specified directory')
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
    
    # Expand chapter command
    expand_parser = subparsers.add_parser('expand-chapter', help='Expand an existing chapter with specialized tagged sections')
    expand_parser.add_argument('number', type=int, help='Chapter number')

    # Review command
    subparsers.add_parser('review', help='Generate a review of the book')
    
    # Revise commands
    revise_parser = subparsers.add_parser('revise', help='Revise a file using two different bots')
    revise_parser.add_argument('reviewer_bot', type=str, help='Reviewer bot name')
    revise_parser.add_argument('editor_bot', type=str, help='Editor bot name')
    revise_parser.add_argument('file', type=str, help='File to revise')
    revise_parser.add_argument('revise_step_name', type=str, nargs='?', help='Revision step name (optional)')

    # Self-edit command
    self_edit_parser = subparsers.add_parser('self-edit', help='Self-edit a file')
    self_edit_parser.add_argument('editor_bot', type=str, help='Editor bot name')
    self_edit_parser.add_argument('file', type=str, help='File to self-edit')
    self_edit_parser.add_argument('editor_step_name', type=str, nargs='?', help='Editor step name (optional)')

    # Version control commands
    version_parser = subparsers.add_parser('list-versions', help='List all versions of a file')
    version_parser.add_argument('file', type=str, help='File to list versions for')
    
    revert_parser = subparsers.add_parser('revert', help='Revert a file to a previous version')
    revert_parser.add_argument('file', type=str, help='File to revert')
    revert_parser.add_argument('version', type=int, help='Version number to revert to')
    
    # File relationship commands
    find_refs_parser = subparsers.add_parser('find-refs', help='Find files that reference a specific file')
    find_refs_parser.add_argument('file', type=str, help='File to find references to')
    
    get_refs_parser = subparsers.add_parser('get-refs', help='Show files referenced by a specific file')
    get_refs_parser.add_argument('file', type=str, help='File to get references from')
    
    # File management commands
    archive_parser = subparsers.add_parser('archive', help='Archive a file (remove but save to history)')
    archive_parser.add_argument('file', type=str, help='File to archive')
    
    subparsers.add_parser('list-archived', help='List all archived files')
    
    derived_parser = subparsers.add_parser('create-derived', help='Create a new derived file')
    derived_parser.add_argument('source', type=str, help='Source file path')
    derived_parser.add_argument('suffix', type=str, help='Suffix to add to filename')
    
    # Split content commands
    split_outline_parser = subparsers.add_parser('split-outline', help='Split the book outline into chapter outlines')
    
    split_chapter_parser = subparsers.add_parser('split-chapter', help='Split a chapter outline into sections')
    split_chapter_parser.add_argument('chapter_num', type=int, help='Chapter number')
    
    write_section_parser = subparsers.add_parser('write-section', help='Write a specific section of a chapter')
    write_section_parser.add_argument('chapter_num', type=int, help='Chapter number')
    write_section_parser.add_argument('section_num', type=int, help='Section number')
    
    assemble_chapter_parser = subparsers.add_parser('assemble-chapter', help='Assemble a chapter from its sections')
    assemble_chapter_parser.add_argument('chapter_num', type=int, help='Chapter number')

    # Task revise outline command
    task_revise_outline_parser = subparsers.add_parser('task-revise-outline', help='Apply all possible outline revisions')

    # Finalize command
    subparsers.add_parser('finalize', help='Create final versions of all content')
    
    # Preview command
    subparsers.add_parser('preview', help='Generate HTML preview of all content')
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        console.print("[red]Error:[/red] OPENROUTER_API_KEY environment variable not set")
        return 1
    
    # Set up logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug(f"Verbose logging enabled")
    
    try:
        # Set DRY_RUN mode if specified
        global DRY_RUN
        if args.dry_run:
            DRY_RUN = True
            logger.info("Running in DRY RUN mode - no API calls or file modifications will be made")
            console.print("[yellow]Running in DRY RUN mode - no API calls or file modifications will be made[/yellow]")
        
        global CHEAP_MODE
        if args.cheap_mode:
            CHEAP_MODE = True
            logger.info("Running in CHEAP MODE - using cheaper models for testing")
            console.print("[yellow]Running in CHEAP MODE - using cheaper models for testing[/yellow]")

        # Create BookBot with specified directory
        book_dir = Path(args.book_dir).resolve()
        
        # Special handling for init command
        if args.command == 'init':
            if book_dir.exists() and any(book_dir.iterdir()):
                console.print(f"[yellow]Warning:[/yellow] Directory {book_dir} already exists and is not empty.")
                proceed = console.input("Do you want to proceed anyway? [y/N]: ").lower()
                if proceed != 'y' and proceed != 'yes':
                    console.print("[red]Aborted.[/red]")
                    return 1
            
            # Initialize the directory structure
            bot = BookBot(api_key, book_dir=book_dir)
            console.print(f"[green]✓[/green] Initialized new book project in {book_dir}")
            return 0
        
        # For all other commands, create BookBot with the specified directory
        bot = BookBot(api_key, book_dir=book_dir)
        
        # Execute the appropriate command
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
        elif args.command == 'expand-chapter':
            bot.expand_chapter(args.number)
        elif args.command == 'review':
            bot.review_book()
        elif args.command == 'revise':
            bot.revise(args.reviewer_bot, args.editor_bot, args.file, args.revise_step_name)
        elif args.command == 'self-edit':
            bot.self_edit(args.editor_bot, args.file, args.editor_step_name)
        elif args.command == 'list-versions':
            bot.list_versions(args.file)
        elif args.command == 'revert':
            bot.revert_to_version(args.file, args.version)
        elif args.command == 'create-derived':
            bot.create_derived_file(args.source, args.suffix)
        elif args.command == 'find-refs':
            bot.find_references_to(args.file)
        elif args.command == 'get-refs':
            bot.get_file_references(args.file)
        elif args.command == 'archive':
            bot.archive_file(args.file)
        elif args.command == 'list-archived':
            bot.list_archived_files()
        elif args.command == 'split-outline':
            bot.split_outline()
        elif args.command == 'split-chapter':
            bot.split_chapter_outline(args.chapter_num)
        elif args.command == 'write-section':
            bot.write_section(args.chapter_num, args.section_num)
        elif args.command == 'assemble-chapter':
            bot.assemble_chapter_from_sections(args.chapter_num)
        elif args.command == 'task-revise-outline':
            task_revise_outline(bot)
        elif args.command == 'finalize':
            bot.finalize()
        elif args.command == 'preview':
            bot._generate_preview()
        elif not args.command:
            parser.print_help()
            return 1
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if args.verbose:
            # Print full traceback in verbose mode
            import traceback
            console.print(traceback.format_exc())
        return 1


if __name__ == '__main__':
    exit(main())