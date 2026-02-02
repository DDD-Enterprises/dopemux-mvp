"""
Voice Assistant Integration for ADHD Engine

Provides voice interface for:
- Status queries ("how's my focus?", "what's my energy?")
- Break acknowledgments ("ok, taking a break")
- Task queries ("what should I work on?")

Platform: macOS (uses 'say' command), extensible to other TTS
ADHD Benefit: Hands-free status checking, reduces context switching
"""
import subprocess
import asyncio
import logging
from typing import Optional, Dict, Any
import re

logger = logging.getLogger(__name__)


class VoiceAssistant:
    """
    Voice interface for ADHD engine.
    
    Supports:
    - Text-to-speech output (macOS 'say' command)
    - Command processing (natural language → API calls)
    - Gentle, encouraging tone
    """
    
    def __init__(self, adhd_engine, default_rate: int = 175):
        """
        Initialize voice assistant.
        
        Args:
            adhd_engine: ADHDAccommodationEngine instance
            default_rate: Speech rate (words per minute, default 175)
        """
        self.engine = adhd_engine
        self.default_rate = default_rate
        
        # Check if TTS is available
        self.tts_available = self._check_tts_available()
        
        if not self.tts_available:
            logger.warning("⚠️ TTS not available - voice output will be logged only")
    
    def _check_tts_available(self) -> bool:
        """Check if text-to-speech is available on this system."""
        try:
            subprocess.run(
                ['which', 'say'],
                capture_output=True,
                check=True,
                timeout=1
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def speak(self, message: str, rate: Optional[int] = None, voice: Optional[str] = None) -> bool:
        """
        Speak message using TTS.
        
        Args:
            message: Text to speak
            rate: Optional speech rate override (words per minute)
            voice: Optional voice name (macOS voices: Samantha, Alex, etc.)
        
        Returns:
            True if speech was successful
        """
        if not self.tts_available:
            logger.info(f"🔊 [TTS unavailable] {message}")
            return False
        
        try:
            cmd = ['say', '-r', str(rate or self.default_rate)]
            
            if voice:
                cmd.extend(['-v', voice])
            
            cmd.append(message)
            
            subprocess.run(cmd, check=True, timeout=30)
            logger.info(f"🔊 Spoke: {message}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("TTS timeout")
            return False
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return False
    
    async def handle_command(self, command: str, user_id: str = "default") -> str:
        """
        Process voice command and return spoken response.
        
        Args:
            command: User's voice command
            user_id: User identifier
        
        Returns:
            Response text (which can be spoken)
        """
        command_lower = command.lower().strip()
        
        try:
            # Focus/attention queries
            if any(phrase in command_lower for phrase in ['focus', 'attention', 'concentrate']):
                return await self._handle_focus_query(user_id)
            
            # Energy queries
            elif any(phrase in command_lower for phrase in ['energy', 'tired', 'awake']):
                return await self._handle_energy_query(user_id)
            
            # Task recommendations
            elif any(phrase in command_lower for phrase in ['what should', 'work on', 'task', 'next']):
                return await self._handle_task_query(user_id)
            
            # Break queries
            elif any(phrase in command_lower for phrase in ['break', 'rest', 'pause']):
                return await self._handle_break_query(user_id)
            
            # Status summary
            elif any(phrase in command_lower for phrase in ['status', 'how am i', 'summary']):
                return await self._handle_status_query(user_id)
            
            # Unknown command
            else:
                return "I can tell you about your focus, energy, suggested tasks, or breaks. What would you like to know?"
            
        except Exception as e:
            logger.error(f"Command handling failed: {e}")
            return "Sorry, I couldn't process that request"
    
    async def _handle_focus_query(self, user_id: str) -> str:
        """Handle focus/attention state query."""
        try:
            state = await self.engine.get_attention_state(user_id)
            
            attention = state.get('state', 'unknown')
            confidence = state.get('confidence', 0.5)
            
            responses = {
                'focused': f"You're nicely focused right now, with {confidence:.0%} confidence. Keep it up!",
                'scattered': f"You seem a bit scattered. Detected with {confidence:.0%} confidence. Maybe close some tabs or take a quick break?",
                'hyperfocus': f"You're in hyperfocus mode! {confidence:.0%} confidence. Great for deep work, but remember to take breaks.",
                'unknown': "I'm not sure about your focus right now. Keep working and I'll learn your patterns."
            }
            
            return responses.get(attention, "I can't determine your focus state right now.")
            
        except Exception as e:
            logger.error(f"Focus query failed: {e}")
            return "Sorry, couldn't check your focus state"
    
    async def _handle_energy_query(self, user_id: str) -> str:
        """Handle energy level query."""
        try:
            energy_data = await self.engine.get_energy_level(user_id)
            
            energy = energy_data.get('energy_level', 'unknown')
            
            responses = {
                'high': "Your energy is high! Great time for complex tasks or creative work.",
                'medium': "You have medium energy. Good for most tasks.",
                'low': "Your energy is running low. Consider easier tasks or taking a break soon.",
                'very_low': "Your energy is very low. Strongly recommend taking a break or wrapping up for the day.",
                'unknown': "I don't have a clear read on your energy yet."
            }
            
            return responses.get(energy, "Couldn't determine your energy level.")
            
        except Exception as e:
            logger.error(f"Energy query failed: {e}")
            return "Sorry, couldn't check your energy level"
    
    async def _handle_task_query(self, user_id: str) -> str:
        """Handle task recommendation query."""
        try:
            # Get current state
            energy_data = await self.engine.get_energy_level(user_id)
            attention_data = await self.engine.get_attention_state(user_id)
            
            energy = energy_data.get('energy_level', 'medium')
            attention = attention_data.get('state', 'focused')
            
            # Generate recommendation
            if energy == 'high' and attention == 'focused':
                return "Perfect conditions! Tackle your most complex task: architecture design, difficult algorithms, or deep debugging."
            elif energy == 'high' and attention == 'scattered':
                return "High energy but scattered focus. Try moderate tasks: code review, refactoring, or feature implementation."
            elif energy == 'low' and attention == 'focused':
                return "Low energy but still focused. Good for: documentation, writing tests, or small bug fixes."
            elif energy == 'low':
                return "Low energy and scattered. Best to take a break or do very simple tasks like organizing notes."
            else:
                return "I recommend working on moderate difficulty tasks right now."
                
        except Exception as e:
            logger.error(f"Task query failed: {e}")
            return "Sorry, couldn't generate a task recommendation"
    
    async def _handle_break_query(self, user_id: str) -> str:
        """Handle break suggestion query."""
        try:
            # Check if break is recommended
            break_rec = await self.engine.should_suggest_break(user_id)
            
            if break_rec and break_rec.get('recommend_break', False):
                priority = break_rec.get('priority', 'normal')
                
                if priority == 'high':
                    return "Yes, you definitely need a break. Your cognitive load is high. Take 10-15 minutes."
                else:
                    return "A break would be good soon. Maybe finish your current task and then take 5-10 minutes."
            else:
                return "You don't need a break right now. Keep working if you're in flow!"
                
        except Exception as e:
            logger.error(f"Break query failed: {e}")
            return "Sorry, couldn't determine break recommendation"
    
    async def _handle_status_query(self, user_id: str) -> str:
        """Handle overall status summary query."""
        try:
            # Get all status
            energy_data = await self.engine.get_energy_level(user_id)
            attention_data = await self.engine.get_attention_state(user_id)
            
            energy = energy_data.get('energy_level', 'unknown')
            attention = attention_data.get('state', 'unknown')
            
            return f"Here's your status: Energy is {energy}, attention is {attention}. You're doing great, keep it up!"
            
        except Exception as e:
            logger.error(f"Status query failed: {e}")
            return "Sorry, couldn't get your status"
    
    async def speak_and_wait(self, message: str) -> None:
        """
        Speak message and wait for it to complete (async).
        
        Args:
            message: Text to speak
        """
        # Run TTS in background thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.speak, message)
