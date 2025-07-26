import re
import json
from typing import Dict, List, Tuple

class SmartCharacterSelector:
    def __init__(self, groq_client):
        self.groq_client = groq_client
        
        # Keywords that typically indicate group messages
        self.group_message_indicators = [
            'everyone', 'all', 'guys', 'team', 'group', 'both', 'all of you',
            'what do you all', 'what does everyone', 'tell me about yourselves',
            'introduce yourselves', 'how are you all', 'what are your thoughts'
        ]
        
        # Greeting patterns that usually get group responses
        self.greeting_patterns = [
            r'^(hi|hello|hey|greetings?)(?:\s+(?:everyone|all|guys|team))?[!.]?$',
            r'^good\s+(morning|afternoon|evening|day)(?:\s+(?:everyone|all))?[!.]?$',
            r'^what\'?s\s+up(?:\s+(?:everyone|all|guys))?[!.]?$'
        ]

    def analyze_message_intent(self, user_message: str, character_ids: List[str], character_database: Dict) -> Dict:
        """Analyze user message to determine targeting and intent"""
        message_lower = user_message.lower().strip()
        
        # Detect direct character mentions
        mentioned_characters = self.detect_character_mentions(user_message, character_ids, character_database)
        
        # Detect if it's a group-directed message
        is_group_message = self.is_group_directed_message(message_lower)
        
        # Detect greeting patterns
        is_greeting = self.is_greeting_message(message_lower)
        
        # Use AI analysis for complex messages
        ai_analysis = self.get_ai_intent_analysis(user_message, character_ids, character_database)
        
        return {
            'mentioned_characters': mentioned_characters,
            'is_group_message': is_group_message,
            'is_greeting': is_greeting,
            'ai_analysis': ai_analysis,
            'message_type': self.determine_message_type(message_lower),
            'confidence': self.calculate_confidence(mentioned_characters, is_group_message, is_greeting)
        }

    def detect_character_mentions(self, user_message: str, character_ids: List[str], character_database: Dict) -> List[str]:
        """Detect direct character mentions in the message"""
        mentioned = []
        message_lower = user_message.lower()
        
        for char_id in character_ids:
            if char_id in character_database:
                char_name = character_database[char_id]['name'].lower()
                
                # Direct name mentions
                if char_name in message_lower:
                    mentioned.append(char_id)
                    continue
                
                # @mentions
                if f"@{char_name}" in message_lower:
                    mentioned.append(char_id)
                    continue
                
                # "Hey [character]" patterns
                if re.search(rf'\b(hey|hi|hello)\s+{re.escape(char_name)}\b', message_lower):
                    mentioned.append(char_id)
                    continue
                
                # "[character], what do you think" patterns
                if re.search(rf'\b{re.escape(char_name)},?\s+(what|how|why|where|when)', message_lower):
                    mentioned.append(char_id)
                    continue
                
                # Question directed at character
                if re.search(rf'{re.escape(char_name)}\s+(what|how|do\s+you|are\s+you|can\s+you)', message_lower):
                    mentioned.append(char_id)
                    continue
        
        return mentioned

    def is_group_directed_message(self, message_lower: str) -> bool:
        """Check if message is directed at the group"""
        # Direct group indicators
        if any(indicator in message_lower for indicator in self.group_message_indicators):
            return True
        
        # Question patterns that suggest group response
        group_question_patterns = [
            r'what do you (all )?think',
            r'what are your (thoughts|opinions)',
            r'how do you (all )?feel',
            r'tell me about yourselves',
            r'introduce yourselves',
            r'what can you (all )?do'
        ]
        
        return any(re.search(pattern, message_lower) for pattern in group_question_patterns)

    def is_greeting_message(self, message_lower: str) -> bool:
        """Check if message is a greeting that should get group response"""
        return any(re.match(pattern, message_lower) for pattern in self.greeting_patterns)

    def get_ai_intent_analysis(self, user_message: str, character_ids: List[str], character_database: Dict) -> Dict:
        """Use AI to analyze complex message intent"""
        try:
            # Build character context
            char_names = []
            for char_id in character_ids:
                if char_id in character_database:
                    char_names.append(character_database[char_id]['name'])
            
            analysis_prompt = f"""
Analyze this user message in a group chat context and determine who should respond.

Group members: {', '.join(char_names)}
User message: "{user_message}"

Consider:
1. Is the message directed at specific characters?
2. Is it a general question for everyone?
3. Is it a greeting or casual remark?
4. Does it require expertise from specific characters?

Respond with JSON format:
{{
    "target_type": "specific|group|general",
    "target_characters": ["character_name1", "character_name2"],
    "reasoning": "explanation of why these characters should respond",
    "response_count": 1-3
}}
"""

            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            if response and response.choices:
                try:
                    return json.loads(response.choices[0].message.content)
                except json.JSONDecodeError:
                    pass
        
        except Exception as e:
            print(f"AI analysis error: {e}")
        
        # Fallback analysis
        return {
            "target_type": "general",
            "target_characters": char_names[:2],
            "reasoning": "Default response selection",
            "response_count": 1
        }

    def determine_message_type(self, message_lower: str) -> str:
        """Determine the type of message"""
        if any(re.match(pattern, message_lower) for pattern in self.greeting_patterns):
            return "greeting"
        elif any(word in message_lower for word in ['?', 'what', 'how', 'why', 'where', 'when', 'who']):
            return "question"
        elif any(word in message_lower for word in ['tell', 'explain', 'describe', 'show']):
            return "request"
        elif any(word in message_lower for word in ['debate', 'argue', 'discuss', 'fight']):
            return "debate_trigger"
        else:
            return "statement"

    def calculate_confidence(self, mentioned_characters: List[str], is_group_message: bool, is_greeting: bool) -> float:
        """Calculate confidence in character selection"""
        confidence = 0.5  # Base confidence
        
        if mentioned_characters:
            confidence += 0.4  # High confidence if characters mentioned
        
        if is_group_message:
            confidence += 0.3
        
        if is_greeting:
            confidence += 0.2
        
        return min(confidence, 1.0)

    def select_responding_characters(self, intent_analysis: Dict, character_ids: List[str], character_database: Dict) -> List[str]:
        """Select which characters should respond based on intent analysis"""
        mentioned = intent_analysis['mentioned_characters']
        is_group = intent_analysis['is_group_message']
        is_greeting = intent_analysis['is_greeting']
        message_type = intent_analysis['message_type']
        ai_analysis = intent_analysis['ai_analysis']
        
        # Priority 1: Direct mentions
        if mentioned:
            return mentioned
        
        # Priority 2: Greetings - everyone responds
        if is_greeting:
            return character_ids
        
        # Priority 3: Group messages - all respond
        if is_group:
            return character_ids
        
        # Priority 4: AI analysis recommendations
        if ai_analysis and ai_analysis.get('target_characters'):
            ai_targets = []
            for target_name in ai_analysis['target_characters']:
                for char_id in character_ids:
                    if char_id in character_database:
                        if character_database[char_id]['name'].lower() == target_name.lower():
                            ai_targets.append(char_id)
                            break
            if ai_targets:
                return ai_targets[:ai_analysis.get('response_count', 2)]
        
        # Priority 5: Message type based selection
        if message_type == "debate_trigger":
            return character_ids[:2]  # Two characters for debate
        elif message_type == "question":
            return character_ids[:2]  # Multiple perspectives
        elif message_type == "request":
            return character_ids[:1]  # Single detailed response
        
        # Default: First character responds
        return character_ids[:1] if character_ids else []

    def should_respond_based_on_context(self, char_id: str, message_context: Dict, character_database: Dict) -> bool:
        """Determine if a specific character should respond based on context"""
        if char_id not in character_database:
            return False
        
        character = character_database[char_id]
        
        # Always respond if directly mentioned
        if char_id in message_context.get('mentioned_characters', []):
            return True
        
        # Check character relevance to topic
        message = message_context.get('original_message', '').lower()
        char_keywords = self.extract_character_keywords(character)
        
        # Calculate relevance score
        relevance_score = 0
        for keyword in char_keywords:
            if keyword in message:
                relevance_score += 1
        
        # Respond if relevance is high enough
        return relevance_score > 0

    def extract_character_keywords(self, character: Dict) -> List[str]:
        """Extract relevant keywords from character profile"""
        keywords = []
        
        # Extract from powers/abilities
        if character.get('powers_abilities'):
            keywords.extend(character['powers_abilities'].lower().split()[:5])
        
        # Extract from personality
        if character.get('personality'):
            keywords.extend(character['personality'].lower().split()[:3])
        
        # Clean and filter keywords
        keywords = [k.strip('.,!?') for k in keywords if len(k) > 3]
        
        return keywords