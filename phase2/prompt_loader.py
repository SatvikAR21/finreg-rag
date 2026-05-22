# =============================================================================
# What this file does:
# Loads the prompt configuration from rag_prompt.yaml and provides it to
# other modules in the pipeline. Any module that needs the system prompt,
# model name, or temperature imports from here instead of hardcoding values.
# =============================================================================

import yaml    # PyYAML library for reading .yaml files
import os      # for building the file path

# Path to our prompt config file — relative to project root
# Build an absolute path relative to THIS file's location — works no matter where Python is run from
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))           # folder containing prompt_loader.py
PROMPT_CONFIG_PATH = os.path.join(_THIS_DIR, "prompts", "rag_prompt.yaml")  # absolute path to YAML

def load_prompt_config():
    """
    Reads and parses the YAML prompt config file.
    Returns a dictionary with all config values.
    """
    with open(PROMPT_CONFIG_PATH, "r", encoding="utf-8") as f:  # open the YAML file
        config = yaml.safe_load(f)                               # parse YAML into a Python dict
    return config                                                # return the config dictionary


def get_system_prompt():
    """Returns just the system prompt string from config."""
    config = load_prompt_config()           # load the full config
    return config["system_prompt"]          # return only the system_prompt field


def get_user_prompt(query, source_block):
    """
    Fills in the user prompt template with the actual query and source chunks.
    
    Args:
        query: the user's question string
        source_block: the numbered chunk text block we built in citation_enforcer.py
    
    Returns:
        Filled-in user prompt string ready to send to the LLM
    """
    config = load_prompt_config()                           # load the full config
    template = config["user_prompt_template"]               # get the template string
    filled = template.replace("{query}", query)             # inject the query
    filled = filled.replace("{source_block}", source_block) # inject the source chunks
    return filled                                           # return the completed prompt


def get_model_config():
    """Returns model name, max_tokens, and temperature as a dict."""
    config = load_prompt_config()                           # load the full config
    return {                                                # return only model settings
        "model": config["model"],                          # LLM model name
        "max_tokens": config["max_tokens"],                # token limit
        "temperature": config["temperature"],              # creativity setting
        "cohere_score_threshold": config["cohere_score_threshold"]  # chunk filter threshold
    }


# --- QUICK TEST ---
if __name__ == "__main__":
    print("Loading prompt config...")
    config = load_prompt_config()                           # load everything

    print(f"\nPrompt version: {config['prompt_version']}")  # show version
    print(f"Model: {config['model']}")                      # show model
    print(f"Temperature: {config['temperature']}")          # show temperature
    print(f"Max tokens: {config['max_tokens']}")            # show token limit
    print(f"\nSystem prompt preview:")
    print(config["system_prompt"][:300] + "...")            # show first 300 chars