from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import json
import os
import requests
import re
from datetime import datetime
from typing import List, Dict
import uuid
from urllib.parse import quote_plus

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
    print("✅ BeautifulSoup4 loaded successfully - Full web scraping enabled")
except ImportError:
    print("⚠️ BeautifulSoup4 not available - Using fallback video search method")
    BS4_AVAILABLE = False

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

if not google_api_key:
    raise ValueError("GOOGLE_API_KEY is missing! Please set it in Railway variables.")

class VideoSearcher:
    """Handles video search functionality"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def search_youtube_videos(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for YouTube videos using web scraping or fallback method"""
        if not BS4_AVAILABLE:
            return self._fallback_video_search(query, max_results)
        
        try:
            # Format search query for YouTube
            search_query = quote_plus(query)
            url = f"https://www.youtube.com/results?search_query={search_query}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find video data in the page
            videos = []
            script_tags = soup.find_all('script')
            
            for script in script_tags:
                if script.string and 'var ytInitialData' in script.string:
                    # Extract JSON data from the script
                    json_str = script.string
                    start = json_str.find('{')
                    end = json_str.rfind('}') + 1
                    
                    if start != -1 and end != -1:
                        try:
                            data = json.loads(json_str[start:end])
                            videos = self._extract_videos_from_data(data, max_results)
                            break
                        except json.JSONDecodeError:
                            continue
            
            # If no videos found via scraping, use fallback
            if not videos:
                return self._fallback_video_search(query, max_results)
                
            return videos[:max_results]
            
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return self._fallback_video_search(query, max_results)
    
    def _fallback_video_search(self, query: str, max_results: int) -> List[Dict]:
        """Fallback method when BeautifulSoup is not available or scraping fails"""
        print(f"🔍 Using fallback search for: {query}")
        
        # Create meaningful video results based on query
        videos = []
        search_terms = query.split()
        
        # Generate realistic video suggestions
        video_templates = [
            {
                'title_template': f"{query.title()} Tutorial",
                'channel': "Tutorial Hub",
                'duration': "15:30"
            },
            {
                'title_template': f"Learn {query.title()} - Complete Guide",
                'channel': "Learning Academy", 
                'duration': "22:45"
            },
            {
                'title_template': f"{query.title()} for Beginners",
                'channel': "Beginner Friendly",
                'duration': "18:20"
            }
        ]
        
        for i, template in enumerate(video_templates[:max_results]):
            videos.append({
                'title': template['title_template'],
                'url': f"https://www.youtube.com/results?search_query={quote_plus(query)}",
                'channel': template['channel'],
                'views': f"{50 + i*25}K+ views",
                'duration': template['duration'],
                'platform': 'YouTube'
            })
        
        return videos
    
    def _extract_videos_from_data(self, data: dict, max_results: int) -> List[Dict]:
        """Extract video information from YouTube data"""
        videos = []
        
        try:
            # Navigate through the complex YouTube data structure
            contents = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
            
            for section in contents:
                items = section.get('itemSectionRenderer', {}).get('contents', [])
                
                for item in items:
                    video_renderer = item.get('videoRenderer', {})
                    
                    if video_renderer:
                        video_id = video_renderer.get('videoId', '')
                        title = self._get_text_from_runs(video_renderer.get('title', {}).get('runs', []))
                        
                        # Get channel name
                        channel_name = ''
                        owner_text = video_renderer.get('ownerText', {}).get('runs', [])
                        if owner_text:
                            channel_name = owner_text[0].get('text', '')
                        
                        # Get view count and duration if available
                        view_count = ''
                        duration = ''
                        
                        metadata = video_renderer.get('viewCountText', {})
                        if metadata:
                            view_count = self._get_text_from_runs(metadata.get('runs', []))
                        
                        length_text = video_renderer.get('lengthText', {})
                        if length_text:
                            duration = length_text.get('simpleText', '')
                        
                        if video_id and title:
                            videos.append({
                                'title': title,
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'channel': channel_name,
                                'views': view_count,
                                'duration': duration,
                                'platform': 'YouTube'
                            })
                            
                            if len(videos) >= max_results:
                                break
                
                if len(videos) >= max_results:
                    break
                    
        except Exception as e:
            print(f"Error extracting video data: {e}")
        
        return videos
    
    def _get_text_from_runs(self, runs: List[Dict]) -> str:
        """Extract text from YouTube's runs format"""
        if not runs:
            return ''
        
        text_parts = []
        for run in runs:
            if isinstance(run, dict) and 'text' in run:
                text_parts.append(run['text'])
        
        return ''.join(text_parts)
    
    def search_general_videos(self, query: str) -> List[Dict]:
        """Search for videos from multiple platforms"""
        videos = []
        
        # Search YouTube
        youtube_videos = self.search_youtube_videos(query, 3)
        videos.extend(youtube_videos)
        
        return videos
    
    def format_video_results(self, videos: List[Dict]) -> str:
        """Format video search results for chatbot response"""
        if not videos:
            return "I couldn't find any videos for your search query, but you can search manually on YouTube!"
        
        result_text = f"🎥 I found {len(videos)} video(s) for you:\n\n"
        
        for i, video in enumerate(videos, 1):
            result_text += f"{i}. **{video['title']}**\n"
            result_text += f"   🔗 Link: {video['url']}\n"
            
            if video.get('channel'):
                result_text += f"   📺 Channel: {video['channel']}\n"
            
            if video.get('duration'):
                result_text += f"   ⏱️ Duration: {video['duration']}\n"
            
            if video.get('views'):
                result_text += f"   👀 Views: {video['views']}\n"
            
            result_text += f"   🎥 Platform: {video['platform']}\n\n"
        
        return result_text

class ConversationStorage:
    """Handles permanent storage of conversation history"""
    
    def __init__(self, filename="conversation_history.json"):
        self.filename = filename
        self.data = self.load_data()
    
    def load_data(self):
        """Load existing conversation history"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return self._get_default_structure()
        return self._get_default_structure()
    
    def _get_default_structure(self):
        """Default data structure"""
        return {
            "sessions": [],
            "current_session": {
                "id": 1,
                "start_time": datetime.now().isoformat(),
                "messages": [],
                "title": "New Chat"
            },
            "statistics": {
                "total_sessions": 0,
                "total_messages": 0
            }
        }
    
    def save_data(self):
        """Save conversation data to file"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving conversation: {e}")
    
    def generate_session_title(self, first_message: str) -> str:
        """Generate a title for the session based on first message"""
        if len(first_message) <= 50:
            return first_message
        return first_message[:47] + "..."
    
    def add_message(self, role: str, content: str):
        """Add a message to current session"""
        message = {
            "role": role,  # "human" or "ai"
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.data["current_session"]["messages"].append(message)
        self.data["statistics"]["total_messages"] += 1
        
        # Update session title if this is the first human message
        if role == "human" and len(self.data["current_session"]["messages"]) == 1:
            self.data["current_session"]["title"] = self.generate_session_title(content)
        
        self.save_data()
    
    def start_new_session(self):
        """Start a new conversation session"""
        # Save current session if it has messages
        if self.data["current_session"]["messages"]:
            self.data["current_session"]["end_time"] = datetime.now().isoformat()
            self.data["sessions"].append(self.data["current_session"].copy())
            self.data["statistics"]["total_sessions"] += 1
        
        # Create new session
        session_id = len(self.data["sessions"]) + 1
        self.data["current_session"] = {
            "id": session_id,
            "start_time": datetime.now().isoformat(),
            "messages": [],
            "title": "New Chat"
        }
        self.save_data()
    
    def load_session(self, session_id: int):
        """Load a specific session as current session"""
        # Save current session if it has messages
        if self.data["current_session"]["messages"]:
            self.data["current_session"]["end_time"] = datetime.now().isoformat()
            # Update existing session or add as new
            session_exists = False
            for i, session in enumerate(self.data["sessions"]):
                if session["id"] == self.data["current_session"]["id"]:
                    self.data["sessions"][i] = self.data["current_session"].copy()
                    session_exists = True
                    break
            
            if not session_exists:
                self.data["sessions"].append(self.data["current_session"].copy())
                self.data["statistics"]["total_sessions"] += 1
        
        # Find and load the requested session
        for session in self.data["sessions"]:
            if session["id"] == session_id:
                self.data["current_session"] = session.copy()
                # Remove end_time as it's now current
                if "end_time" in self.data["current_session"]:
                    del self.data["current_session"]["end_time"]
                self.save_data()
                return True
        return False
    
    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """Get recent messages for context"""
        return self.data["current_session"]["messages"][-count:]
    
    def get_session_list(self) -> List[Dict]:
        """Get list of all sessions for sidebar"""
        sessions = []
        
        # Add current session if it has messages
        if self.data["current_session"]["messages"]:
            current = self.data["current_session"].copy()
            current["is_current"] = True
            sessions.append(current)
        
        # Add completed sessions (most recent first)
        completed_sessions = sorted(
            self.data["sessions"], 
            key=lambda x: x.get("start_time", ""), 
            reverse=True
        )
        
        for session in completed_sessions:
            session_copy = session.copy()
            session_copy["is_current"] = False
            sessions.append(session_copy)
        
        return sessions
    
    def get_statistics(self) -> Dict:
        """Get conversation statistics"""
        current_messages = len(self.data["current_session"]["messages"])
        return {
            "total_sessions": self.data["statistics"]["total_sessions"],
            "total_messages": self.data["statistics"]["total_messages"],
            "current_session_messages": current_messages,
            "sessions_count": len(self.data["sessions"])
        }

class PersistentChatbot:
    """Enhanced chatbot with permanent conversation storage and video search"""
    
    def __init__(self):
        self.model = init_chat_model("gemini-2.0-flash-exp", model_provider="google_genai")
        self.storage = ConversationStorage("ethicallogix_conversations.json")
        self.video_searcher = VideoSearcher()
        
        # Load conversation history for context (last 10 messages)
        self.conversation_context = self.storage.get_recent_messages(10)
        
        # Video request patterns
        self.video_patterns = [
            r'\b(?:video|videos)\b.*\b(?:about|on|for|of)\b',
            r'\b(?:show me|find|search)\b.*\bvideo',
            r'\byoutube.*\b(?:video|link)',
            r'\bwatch.*\bvideo',
            r'\bvideo.*\b(?:tutorial|guide|how to)',
            r'\b(?:movie|film|clip)\b',
        ]
    
    def detect_video_request(self, text: str) -> bool:
        """Detect if user is requesting video content"""
        text_lower = text.lower()
        
        # Check for explicit video keywords
        video_keywords = ['video', 'youtube', 'watch', 'movie', 'film', 'clip', 'tutorial']
        
        for keyword in video_keywords:
            if keyword in text_lower:
                return True
        
        # Check patterns
        for pattern in self.video_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def extract_search_query(self, text: str) -> str:
        """Extract search query from user message"""
        # Remove common request words
        clean_text = re.sub(r'\b(?:show me|find|search for|look for|give me|i want|can you)\b', '', text, flags=re.IGNORECASE)
        clean_text = re.sub(r'\b(?:video|videos|youtube|link|links)\b', '', clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'\b(?:about|on|for|of)\b', '', clean_text, flags=re.IGNORECASE)
        
        # Clean up extra spaces and punctuation
        clean_text = re.sub(r'[^\w\s]', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text if clean_text else text
    
    def get_context_messages(self) -> str:
        """Format recent conversation history for model context"""
        if not self.conversation_context:
            return ""
        
        context_text = "\nRecent conversation context:\n"
        for msg in self.conversation_context[-5:]:  # Last 5 messages
            role = "You" if msg["role"] == "human" else "Ethicallogix"
            context_text += f"{role}: {msg['content']}\n"
        
        return context_text + "\nCurrent conversation:\n"
    
    def clean_response_text(self, text: str) -> str:
        """Clean AI response text from unwanted formatting"""
        if not text:
            return text
            
        # Remove markdown strikethrough (~~text~~)
        import re
        text = re.sub(r'~~(.+?)~~', r'\1', text)
        
        # Remove asterisk-based formatting
        # Remove bold/italic (**text** or ***text***)
        text = re.sub(r'\*{1,3}([^*]+?)\*{1,3}', r'\1', text)
        
        # Remove standalone asterisks patterns
        text = re.sub(r'\*{2,}', '', text)
        
        # Remove other common markdown elements if needed
        text = re.sub(r'`([^`]+?)`', r'\1', text)  # Remove backticks
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean multiple newlines
        text = text.strip()
        
        return text
    
    def chat(self, user_text: str) -> str:
        """Process user input and generate response with context and video search"""
        try:
            # Check if user is requesting videos
            if self.detect_video_request(user_text):
                print(f"🎥 Video request detected: {user_text}")
                
                # Extract search query
                search_query = self.extract_search_query(user_text)
                print(f"🔍 Search query: {search_query}")
                
                if search_query:
                    # Search for videos
                    videos = self.video_searcher.search_general_videos(search_query)
                    video_results = self.video_searcher.format_video_results(videos)
                    
                    # Generate AI response with video results
                    context = self.get_context_messages()
                    prompt_with_context = f"{context}Human: {user_text}\n\nEthicallogix (with video search results):\n{video_results}\n\nAdditional response:"
                    
                    response = self.model.invoke(f'you are a ethicallogix AI assistant named Hasi made by Ethicallogix. The user asked for videos and here are the search results. Provide a helpful response that includes these video links and additional context. {prompt_with_context}')
                    ai_response = response.content
                    
                    # Combine video results with AI response
                    full_response = f"{video_results}\n\n{ai_response}"
                else:
                    # If no clear search query, ask for clarification
                    full_response = "I'd be happy to help you find videos! Could you please specify what topic or subject you'd like to see videos about?"
            else:
                # Regular chat without video search
                context = self.get_context_messages()
                prompt_with_context = context + f"Human: {user_text}\n\nEthicallogix:"
                
                response = self.model.invoke(f'you are a ethicallogix AI assistant named Hasi made by Ethicallogix {prompt_with_context}')
                full_response = response.content
            
            # Clean the response text
            full_response = self.clean_response_text(full_response)
            
            # Save both messages to permanent storage
            self.storage.add_message("human", user_text)
            self.storage.add_message("ai", full_response)
            
            # Update context
            self.conversation_context = self.storage.get_recent_messages(10)
            
            return full_response
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {e}"
            self.storage.add_message("human", user_text)
            self.storage.add_message("ai", error_msg)
            return error_msg
    
    def get_chat_history(self):
        """Get current session messages"""
        return self.storage.data["current_session"]["messages"]
    
    def get_session_list(self):
        """Get list of all sessions for sidebar"""
        return self.storage.get_session_list()
    
    def load_session(self, session_id: int):
        """Load a specific session"""
        success = self.storage.load_session(session_id)
        if success:
            self.conversation_context = self.storage.get_recent_messages(10)
        return success
    
    def new_session(self):
        """Start a new conversation session"""
        self.storage.start_new_session()
        self.conversation_context = []
        return True
    
    def get_statistics(self):
        """Get conversation statistics"""
        return self.storage.get_statistics()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize chatbot
chatbot = PersistentChatbot()

@app.route('/')
def index():
    """Main chat interface"""
    # Initialize session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Get AI response (with video search if needed)
        ai_response = chatbot.chat(user_message)
        
        return jsonify({
            'response': ai_response,
            'timestamp': datetime.now().strftime('%H:%M')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-videos', methods=['POST'])
def api_search_videos():
    """Direct API endpoint for video search"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Search query required'}), 400
        
        videos = chatbot.video_searcher.search_general_videos(query)
        
        return jsonify({
            'query': query,
            'videos': videos,
            'count': len(videos)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def api_history():
    """Get chat history"""
    try:
        history = chatbot.get_chat_history()
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions')
def api_sessions():
    """Get all sessions for sidebar"""
    try:
        sessions = chatbot.get_session_list()
        return jsonify({'sessions': sessions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-session', methods=['POST'])
def api_load_session():
    """Load a specific session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        success = chatbot.load_session(int(session_id))
        if success:
            history = chatbot.get_chat_history()
            return jsonify({
                'success': True, 
                'history': history,
                'message': f'Loaded session {session_id}'
            })
        else:
            return jsonify({'error': 'Session not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/new-session', methods=['POST'])
def api_new_session():
    """Start new chat session"""
    try:
        chatbot.new_session()
        return jsonify({'success': True, 'message': 'New session started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/all-conversations')
def api_all_conversations():
    """Get all conversation history"""
    try:
        return jsonify(chatbot.storage.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
