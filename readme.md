# EthicalLogix AI Chatbot 🤖

A sophisticated Flask-based AI chatbot application with persistent conversation storage, session management, and intelligent context handling. Built with modern web technologies and powered by Google's Gemini AI model.

## 🌟 Features

### Core Functionality
- **Persistent Conversation Storage** - All conversations are automatically saved to JSON files
- **Session Management** - Create, load, and switch between multiple chat sessions
- **Context-Aware Responses** - AI maintains conversation context across messages
- **Real-time Chat Interface** - Responsive web-based chat UI
- **Conversation History** - Browse and search through past conversations
- **Statistics Tracking** - Monitor usage patterns and conversation metrics

### AI Capabilities
- Powered by **Google Gemini 2.0 Flash Experimental** model
- Intelligent response cleaning and formatting
- Context retention across conversations
- Error handling with graceful degradation

### Storage & Data Management
- JSON-based persistent storage
- Automatic conversation backups
- Session organization and management
- Statistics and analytics tracking

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Google AI API key (for Gemini model)
- Flask and required dependencies

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ethicallogix-chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install flask python-dotenv langchain-google-genai
   ```

3. **Environment Setup**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_google_ai_api_key_here
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the chatbot**
   Open your browser and navigate to `http://localhost:5000`

## 📁 Project Structure

```
ethicallogix-chatbot/
├── app.py                          # Main Flask application
├── .env                            # Environment variables (create this)
├── conversation_history.json       # Auto-generated conversation storage
├── ethicallogix_conversations.json # Backup conversation storage
├── templates/
│   └── index.html                  # Web interface (create this)
└── static/                         # CSS/JS files (create as needed)
```

## 🔧 API Endpoints

### Chat Operations
- `POST /api/chat` - Send message and get AI response
- `GET /api/history` - Retrieve current session history
- `GET /api/sessions` - Get list of all sessions
- `POST /api/load-session` - Load specific session by ID
- `POST /api/new-session` - Create new chat session
- `GET /api/all-conversations` - Export all conversation data

### Request/Response Examples

**Send Message:**
```json
POST /api/chat
{
  "message": "Hello, how can you help me today?"
}

Response:
{
  "response": "Hello! I'm EthicalLogix AI assistant...",
  "timestamp": "14:30"
}
```

**Load Session:**
```json
POST /api/load-session
{
  "session_id": 1
}

Response:
{
  "success": true,
  "history": [...],
  "message": "Loaded session 1"
}
```

## 🏗️ Architecture

### Core Classes

#### `ConversationStorage`
- Handles persistent storage of conversation history
- Manages session creation and loading
- Provides statistics and analytics
- Automatic data backup and recovery

#### `PersistentChatbot`
- Main chatbot logic and AI integration
- Context management and conversation flow
- Response processing and cleaning
- Session coordination

### Key Features Implementation

#### Context Management
The chatbot maintains conversation context by:
- Storing last 10 messages for context
- Formatting conversation history for AI model
- Preserving context across session switches

#### Response Processing
- Automatic removal of unwanted markdown formatting
- Text cleaning and normalization
- Error handling and fallback responses

#### Session Management
- Unique session IDs and timestamps
- Automatic session titling based on first message
- Session switching without data loss

## 🎯 Configuration

### Environment Variables
```env
GOOGLE_API_KEY=your_api_key_here    # Required: Google AI API key
FLASK_ENV=development               # Optional: Flask environment
FLASK_DEBUG=True                    # Optional: Enable debug mode
```

### Storage Configuration
- Default storage file: `ethicallogix_conversations.json`
- Backup storage: `conversation_history.json`
- JSON format with UTF-8 encoding
- Automatic file creation and recovery

## 🛠️ Customization

### Modifying AI Behavior
Edit the system prompt in the `chat()` method:
```python
response = self.model.invoke(f'you are a ethicallogix AI assistant named Hasi made by Ethicallogix{prompt_with_context}')
```

### Storage Options
Change storage filename:
```python
self.storage = ConversationStorage("custom_filename.json")
```

### Context Window
Adjust context message count:
```python
self.conversation_context = self.storage.get_recent_messages(20)  # Increase from 10 to 20
```

## 📊 Data Structure

### Conversation Storage Format
```json
{
  "sessions": [
    {
      "id": 1,
      "start_time": "2024-01-01T10:00:00",
      "end_time": "2024-01-01T11:00:00",
      "title": "First conversation...",
      "messages": [
        {
          "role": "human",
          "content": "Hello!",
          "timestamp": "2024-01-01T10:00:00"
        }
      ]
    }
  ],
  "current_session": {...},
  "statistics": {
    "total_sessions": 5,
    "total_messages": 150
  }
}
```

## 🔒 Security Considerations

- API keys stored in environment variables
- Session management with Flask sessions
- Input validation and sanitization
- Error handling without exposing system details

## 🚨 Troubleshooting

### Common Issues

**API Key Error:**
- Ensure Google AI API key is set in `.env` file
- Verify API key has proper permissions
- Check for typos in environment variable name

**Storage Issues:**
- Check file permissions in application directory
- Ensure sufficient disk space for JSON files
- Verify JSON file integrity if corruption occurs

**Connection Issues:**
- Confirm internet connectivity for API calls
- Check firewall settings for port 5000
- Verify Flask is running on correct host/port

## 📈 Future Enhancements

- [ ] Add user authentication system
- [ ] Implement conversation search functionality
- [ ] Add export/import features for conversations
- [ ] Create mobile-responsive interface
- [ ] Add conversation sharing capabilities
- [ ] Implement conversation analytics dashboard
- [ ] Add support for file uploads and processing
- [ ] Create conversation backup to cloud storage

## 📝 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

**Muhammad Haseeb**
- Email: hasiraza511@gmail.com
- GitHub: https://github.com/hasiraza
- LinkedIn: [\[Your LinkedIn Profile\]](https://www.linkedin.com/in/muhammad-haseeb-raza-71987a366/)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📞 Support

If you encounter any issues or have questions, please:
1. Check the troubleshooting section above
2. Search existing issues on GitHub
3. Contact the author at hasiraza511@gmail.com
4. Create a new issue with detailed information

---

**Built with ❤️ by Muhammad Haseeb using Flask, Google Gemini AI, and modern web technologies.**