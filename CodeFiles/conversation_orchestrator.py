import re
import json
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class ConversationOrchestrator:
    def __init__(self, groq_client):
        self.groq_client = groq_client
        self.active_autonomous_chats = {}  # {group_id: conversation_config}
        
        # Trigger patterns for autonomous conversations
        self.debate_triggers = [
            r'debate about (.+)', r'argue about (.+)', r'discuss (.+)', 
            r'what do you think about (.+)', r'(.+) vs (.+)',
            r'fight about (.+)', r'talk about (.+)'
        ]
        
        self.autonomous_patterns = [
            r'let them (.+)', r'start (.+)', r'begin (.+)',
            r'continue (.+)', r'keep (.+)'
        ]

    def detect_autonomous_trigger(self, user_message: str, character_ids: List[str]) -> Optional[Dict]:
        """Detect if user wants characters to interact autonomously"""
        message_lower = user_message.lower().strip()
        
        # Check for debate triggers
        for pattern in self.debate_triggers:
            match = re.search(pattern, message_lower)
            if match:
                topic = match.group(1).strip()
                return {
                    'type': 'debate',
                    'topic': topic,
                    'participants': character_ids[:2] if len(character_ids) >= 2 else character_ids,
                    'duration': 'until_stop',
                    'max_rounds': 8,
                    'current_round': 0
                }
        
        # Check for general discussion triggers
        discussion_keywords = ['discuss', 'talk', 'chat', 'conversation']
        if any(keyword in message_lower for keyword in discussion_keywords):
            return {
                'type': 'discussion',
                'topic': user_message,
                'participants': character_ids,
                'duration': 'until_stop',
                'max_rounds': 6,
                'current_round': 0
            }
        
        return None

    def start_autonomous_conversation(self, conversation_config: Dict, group_id: str):
        """Start an autonomous conversation between characters"""
        conversation_config['started_at'] = datetime.now().isoformat()
        conversation_config['last_speaker'] = None
        conversation_config['conversation_history'] = []
        
        self.active_autonomous_chats[group_id] = conversation_config

    def generate_autonomous_response(self, group_id: str, character_database: Dict) -> List[Dict]:
        """Generate next response in autonomous conversation"""
        if group_id not in self.active_autonomous_chats:
            return []
        
        config = self.active_autonomous_chats[group_id]
        
        # Check if conversation should end
        if self.should_end_conversation(config):
            self.end_autonomous_conversation(group_id)
            return [{
                'character_id': 'system',
                'character_name': 'System',
                'response': f"🏁 {config['type'].title()} concluded after {config['current_round']} rounds!"
            }]
        
        # Determine next speaker
        next_speaker_id = self.select_next_speaker(config)
        if not next_speaker_id or next_speaker_id not in character_database:
            return []
        
        character = character_database[next_speaker_id]
        
        # Generate response
        response_text = self.generate_character_autonomous_response(
            character, config, character_database
        )
        
        if response_text:
            # Update conversation state
            config['last_speaker'] = next_speaker_id
            config['current_round'] += 0.5  # Each response is half a round
            config['conversation_history'].append({
                'speaker': next_speaker_id,
                'response': response_text,
                'timestamp': datetime.now().isoformat()
            })
            
            return [{
                'character_id': next_speaker_id,
                'character_name': character['name'],
                'response': response_text,
                'autonomous': True
            }]
        
        return []

    def select_next_speaker(self, config: Dict) -> Optional[str]:
        """Select who should speak next in autonomous conversation"""
        participants = config['participants']
        last_speaker = config.get('last_speaker')
        
        if not last_speaker:
            # First response - pick randomly or first character
            return participants[0] if participants else None
        
        if config['type'] == 'debate':
            # Alternate between participants in debate
            try:
                current_index = participants.index(last_speaker)
                next_index = (current_index + 1) % len(participants)
                return participants[next_index]
            except ValueError:
                return participants[0]
        
        elif config['type'] == 'discussion':
            # More natural selection for discussions
            available_speakers = [p for p in participants if p != last_speaker]
            return random.choice(available_speakers) if available_speakers else participants[0]
        
        return participants[0]

    def generate_character_autonomous_response(self, character: Dict, config: Dict, character_database: Dict) -> str:
        """Generate character response for autonomous conversation"""
        try:
            # Build context about other participants
            other_participants = []
            for char_id in config['participants']:
                if char_id != character.get('name', '').lower().replace(' ', '_'):
                    if char_id in character_database:
                        other_participants.append(character_database[char_id]['name'])
            
            # Get recent conversation history
            recent_history = config.get('conversation_history', [])[-4:]
            history_text = ""
            if recent_history:
                history_text = "\nRecent conversation:\n"
                for entry in recent_history:
                    speaker_name = "You" if entry['speaker'] == character.get('name', '').lower().replace(' ', '_') else entry['speaker']
                    history_text += f"{speaker_name}: {entry['response']}\n"
            
            # Create conversation-type specific prompt
            if config['type'] == 'debate':
                prompt = f"""You are {character['name']} in an autonomous debate about "{config['topic']}" with {', '.join(other_participants)}.

Your personality: {character.get('personality', 'Engaging debater')}
Your speaking style: {character.get('speaking_style', 'Confident and clear')}

{history_text}

This is round {int(config['current_round'] + 1)} of the debate. Present your argument passionately but respectfully. 
Be specific, use examples, and try to counter previous points if relevant.
Respond in 1-2 sentences that show your character's unique perspective.

Your response:"""

            else:  # discussion
                prompt = f"""You are {character['name']} in an autonomous discussion about "{config['topic']}" with {', '.join(other_participants)}.

Your personality: {character.get('personality', 'Thoughtful conversationalist')}
Your speaking style: {character.get('speaking_style', 'Natural and engaging')}

{history_text}

Continue the discussion naturally. Share your thoughts, ask questions, or respond to what others have said.
Stay true to your character while keeping the conversation flowing.
Respond in 1-2 sentences.

Your response:"""

            # Generate response using Groq
            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.8
            )
            
            if response and response.choices:
                response_text = response.choices[0].message.content.strip()
                
                # Clean up response
                if response_text.startswith('"') and response_text.endswith('"'):
                    response_text = response_text[1:-1]
                
                return response_text
            
        except Exception as e:
            print(f"Error generating autonomous response: {e}")
        
        # Fallback response
        return f"*{character['name']} is thinking about {config['topic']}...*"

    def should_end_conversation(self, config: Dict) -> bool:
        """Determine if autonomous conversation should end"""
        # End if max rounds reached
        if config['current_round'] >= config.get('max_rounds', 6):
            return True
        
        # End if conversation is getting repetitive
        recent_responses = config.get('conversation_history', [])[-4:]
        if len(recent_responses) >= 4:
            # Simple repetition check
            response_texts = [r['response'].lower() for r in recent_responses]
            unique_responses = set(response_texts)
            if len(unique_responses) < len(response_texts) * 0.7:  # Too much repetition
                return True
        
        return False

    def end_autonomous_conversation(self, group_id: str):
        """End autonomous conversation"""
        if group_id in self.active_autonomous_chats:
            del self.active_autonomous_chats[group_id]

    def is_autonomous_active(self, group_id: str) -> bool:
        """Check if autonomous conversation is active for group"""
        return group_id in self.active_autonomous_chats

    def get_autonomous_status(self, group_id: str) -> Optional[Dict]:
        """Get current autonomous conversation status"""
        return self.active_autonomous_chats.get(group_id)

    def handle_user_interruption(self, user_message: str, group_id: str) -> bool:
        """Handle user interruption of autonomous chat"""
        interruption_keywords = ['stop', 'enough', 'pause', 'end', 'quit', 'finish']
        
        if any(keyword in user_message.lower() for keyword in interruption_keywords):
            self.end_autonomous_conversation(group_id)
            return True
        
        return False