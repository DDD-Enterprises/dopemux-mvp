"""
DØPEMÜX Ritual Prompts

Branded interactive inputs for the CLI.
"""
from rich.prompt import Prompt, Confirm
from .theme import Glyphs

class DopemuxPrompt(Prompt):
    prompt_suffix = " [mint]>[/mint] "
    
    @classmethod
    def ask(cls, prompt: str, **kwargs) -> str:
        branded_prompt = f"[mint]⚡ {prompt}[/mint]"
        return super().ask(branded_prompt, **kwargs)

class DopemuxConfirm(Confirm):
    prompt_suffix = " [mint]>[/mint] "
    
    @classmethod
    def ask(cls, prompt: str, **kwargs) -> bool:
        branded_prompt = f"[gilt.edge]{Glyphs.WARNING} {prompt}[/gilt.edge]"
        return super().ask(branded_prompt, **kwargs)

def dopemux_prompt(message: str, **kwargs) -> str:
    return DopemuxPrompt.ask(message, **kwargs)

def dopemux_confirm(message: str, **kwargs) -> bool:
    return DopemuxConfirm.ask(message, **kwargs)
