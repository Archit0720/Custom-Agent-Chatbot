Author - Archit Dogra

# Custom-Agent-Chatbot 
# 🎭 AI Ctharacter Chat Studio

An advanced AI-powered application that brings fictional characters to life for immersive conversations. Create, chat, and interact with any fictional character using state-of-the-art language models.

## ✨ Features

### 🎨 Character Creation
- **Intelligent Character Profiles**: Enter any fictional character name and AI generates detailed personalities, backgrounds, and speaking styles
- **Dynamic Avatar Generation**: Automatic character image fetching from multiple sources with fallback avatar creation
- **Rich Character Data**: Comprehensive profiles including personality traits, famous quotes, backstories, and abilities

### 💬 Individual Chat Mode
- **Authentic Conversations**: Chat one-on-one with characters who maintain their unique personalities
- **Context-Aware Responses**: Characters remember conversation history and respond appropriately
- **Character Consistency**: Each character maintains their established traits, speaking style, and background

### 👥 Group Chat Mode
- **Multi-Character Interactions**: Create group chats with 2-4 characters
- **Smart Response Selection**: AI determines which characters should respond based on message context
- **Character Interactions**: Characters can respond to and reference each other naturally
- **Dynamic Conversations**: Realistic group dynamics with varying participation levels

### 🤖 Autonomous Conversations
- **Character Debates**: Let characters debate topics autonomously
- **Group Discussions**: Characters can continue conversations without user input
- **Smart Orchestration**: AI manages conversation flow and determines when to end discussions

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Groq API key (free from [Groq Console](https://console.groq.com/keys))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-character-chat-studio.git
   cd ai-character-chat-studio
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key**
   
   Create a `.streamlit/secrets.toml` file:
   ```toml
   GROQ_API_KEY = "your-groq-api-key-here"
   ```
   
   Or set as environment variable:
   ```bash
   export GROQ_API_KEY="your-groq-api-key-here"
   ```

4. **Run the application**
   ```bash
   streamlit run main.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:8501`

## 🐳 Docker Setup

### Build and run with Docker
```bash
# Build the image
docker build -t ai-character-chat .

# Run the container
docker run -p 8501:8501 -e GROQ_API_KEY="your-api-key" ai-character-chat
```

### Using Docker Compose
```bash
# Create .env file with your API key
echo "GROQ_API_KEY=your-api-key-here" > .env

# Run with docker-compose
docker-compose up
```

## 📖 Usage Guide

### Creating Characters
1. Enter any fictional character name in the sidebar
2. Click "🎨 Create Character"
3. Wait for AI to generate the character profile
4. Character will appear in your character list

### Individual Chat
1. Select "Individual Chat" mode
2. Choose a character from the sidebar
3. Start chatting with your selected character
4. Each character maintains their unique personality and speaking style

### Group Chat
1. Select "Group Chat" mode
2. Create a new group by selecting 2-4 characters
3. Give your group a name
4. Start group conversations where multiple characters can participate

### Autonomous Conversations
1. In group chat mode, trigger autonomous conversations with phrases like:
   - "Debate about [topic]"
   - "Discuss [topic]"
   - "What do you all think about [topic]"
2. Characters will continue the conversation autonomously
3. Use "Stop" button to end autonomous mode

## 🏗️ Project Structure

```
ai-character-chat-studio/
├── main.py                     # Main Streamlit application
├── conversation_orchestrator.py # Handles autonomous conversations
├── smart_character_selector.py # Intelligent character response selection
├── requirements.txt            # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
├── .gitignore                # Git ignore rules
├── .streamlit/
│   └── config.toml           # Streamlit configuration
└── README.md                 # This file
```

## 🔧 Configuration

### Streamlit Configuration
The app includes optimized Streamlit settings for better performance:
- Memory management for large conversations
- Optimized caching for character data
- Enhanced UI responsiveness

### API Configuration
- **Groq API**: Used for character generation and conversations
- **Model**: llama3-70b-8192 (can be configured)
- **Rate Limiting**: Built-in handling for API limits

## 🎨 Customization

### Adding New Character Sources
Extend the `CharacterImageFetcher` class to add new image sources:

```python
def get_from_new_source(self, character_name: str) -> str:
    # Your custom image fetching logic
    pass
```

### Custom Character Templates
Modify character generation prompts in `CharacterCreator.generate_character_profile()` to customize how characters are created.

### UI Themes
Customize the CSS in the main application to change the visual theme and styling.

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `pytest tests/`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8 .

# Format code
black .
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**API Connection Issues**
- Ensure your Groq API key is valid
- Check your internet connection
- Verify API key is properly set in secrets or environment

**Character Creation Fails**
- Check API key permissions
- Ensure stable internet connection
- Try creating a simpler character name

**Group Chat Not Working**
- Ensure you have at least 2 characters created
- Check that all selected characters exist in the database

### Getting Help
- 📧 **Email**: [your-email@example.com]
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/ai-character-chat-studio/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/ai-character-chat-studio/discussions)

## 🙏 Acknowledgments

- **Groq** for providing the powerful language model API
- **Streamlit** for the excellent web framework
- **Character Image Sources**: Various APIs and services for character avatars
- **Community** for feedback and contributions

## 🔮 Roadmap

- [ ] Voice chat integration
- [ ] Character memory persistence
- [ ] Custom character import/export
- [ ] Multi-language support
- [ ] Character personality fine-tuning
- [ ] Integration with more LLM providers
- [ ] Mobile app version

---

**Made with ❤️ by [Your Name]**

*Bring your favorite fictional characters to life with AI!*
