"""iMessage reaction type mappings and utilities."""

from typing import Dict, Optional

# Apple iMessage reaction type mapping
# Based on associated_message_type values in Messages database
REACTION_TYPE_MAP: Dict[int, str] = {
    2000: "love",      # ❤️ Heart
    2001: "like",      # 👍 Thumbs up
    2002: "dislike",   # 👎 Thumbs down  
    2003: "laugh",     # 😂 Laughing
    2004: "emphasize", # ❗ Exclamation marks
    2005: "question",  # ❓ Question mark
}

# Reverse mapping for validation
REACTION_NAME_MAP: Dict[str, int] = {v: k for k, v in REACTION_TYPE_MAP.items()}


def get_reaction_type(associated_message_type: int) -> Optional[str]:
    """Convert Apple reaction type code to canonical reaction name.
    
    Args:
        associated_message_type: Apple's reaction type code (2000-2005+ for custom reactions)
        
    Returns:
        Canonical reaction name or None if not a reaction
    """
    # Traditional tapbacks (iOS < 16)
    if associated_message_type in REACTION_TYPE_MAP:
        return REACTION_TYPE_MAP[associated_message_type]
    
    # Custom emoji reactions (iOS 16+) - these use higher type codes
    # The actual emoji is typically stored in the message text field
    # Based on observation, custom reactions seem to use codes 3000-3999 range
    if 3000 <= associated_message_type <= 3999:
        return "custom"  # Will extract actual emoji from message text
    
    return None


def is_reaction(associated_message_type: int) -> bool:
    """Check if message type indicates a reaction.
    
    Args:
        associated_message_type: Apple's message type code
        
    Returns:
        True if this is a reaction (tapback or custom emoji)
    """
    # Traditional tapbacks (2000-2005)
    if 2000 <= associated_message_type <= 2005:
        return True
    
    # Custom emoji reactions (iOS 16+) - these typically use codes 3000-3999 range
    if 3000 <= associated_message_type <= 3999:
        return True
        
    return False


def is_reply(associated_message_type: int, has_associated_guid: bool) -> bool:
    """Check if message is a reply to another message.
    
    Args:
        associated_message_type: Apple's message type code
        has_associated_guid: Whether associated_message_guid is present
        
    Returns:
        True if this is a reply message
    """
    return associated_message_type == 0 and has_associated_guid