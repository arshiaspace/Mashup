import json
import os
import shutil
import tempfile
import re
import zipfile
import base64
import requests
from http.server import BaseHTTPRequestHandler
from yt_dlp import YoutubeDL
from pydub import AudioSegment


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_inputs(data):
    """Validate input data"""
    errors = []
    
    if 'singer' not in data or not data['singer'].strip():
        errors.append("Singer name is required")
    
    if 'num_videos' not in data:
        errors.append("Number of videos is required")
    else:
        try:
            num_videos = int(data['num_videos'])
            if num_videos <= 10:
                errors.append("Number of videos must be greater than 10")
        except (ValueError, TypeError):
            errors.append("Number of videos must be a valid integer")
    
    if 'duration' not in data:
        errors.append("Duration is required")
    else:
        try:
            duration = int(data['duration'])
            if duration <= 20:
                errors.append("Duration must be greater than 20 seconds")
        except (ValueError, TypeError):
            errors.append("Duration must be a valid integer")
    
    if 'email' not in data or not validate_email(data['email']):
        errors.append("Valid email address is required")
    
    return errors


def download_and_convert(singer, num_videos, temp_dir):
    """Download videos and convert to MP3"""
    downloads_dir = os.path.join(temp_dir, 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    
    search_query = f"ytsearch{num_videos}:{singer}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',  # Lower quality for faster processing
        }],
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': True,
        'noplaylist': True,
        'max_downloads': num_videos,
        'socket_timeout': 30,
        'retries': 2,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if not info:
                raise Exception(f"Could not find videos for '{singer}'")
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")
    
    return downloads_dir


def trim_and_merge(downloads_dir, duration, temp_dir):
    """Trim audio files and merge them"""
    trimmed_dir = os.path.join(temp_dir, 'trimmed')
    os.makedirs(trimmed_dir, exist_ok=True)
    
    mp3_files = [f for f in os.listdir(downloads_dir) if f.endswith('.mp3')]
    
    if not mp3_files:
        raise Exception("No audio files were downloaded")
    
    # Trim each file
    trimmed_files = []
    for idx, file in enumerate(mp3_files, 1):
        file_path = os.path.join(downloads_dir, file)
        try:
            audio = AudioSegment.from_mp3(file_path)
            trimmed_audio = audio[:duration * 1000]  # Convert to milliseconds
            
            output_path = os.path.join(trimmed_dir, f"trimmed_{idx}.mp3")
            trimmed_audio.export(output_path, format="mp3")
            trimmed_files.append(output_path)
        except Exception as e:
            print(f"Error trimming {file}: {e}")
            continue
    
    if not trimmed_files:
        raise Exception("No audio files could be processed")
    
    # Merge all trimmed files
    final_audio = AudioSegment.empty()
    for file in trimmed_files:
        audio = AudioSegment.from_mp3(file)
        final_audio += audio
    
    # Export final mashup
    output_file = os.path.join(temp_dir, 'mashup.mp3')
    final_audio.export(output_file, format="mp3")
    
    return output_file


def create_zip(mp3_file, temp_dir):
    """Create ZIP file containing the mashup"""
    zip_path = os.path.join(temp_dir, 'mashup.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(mp3_file, 'mashup.mp3')
    
    return zip_path


def send_email(zip_file, recipient_email, singer):
    """Send ZIP file via email using Resend API"""
    
    # Get Resend API key from environment variable
    api_key = os.environ.get('RESEND_API_KEY')
    
    if not api_key:
        raise Exception("RESEND_API_KEY environment variable not set")
    
    # Read and encode ZIP file as base64
    with open(zip_file, 'rb') as f:
        zip_content = base64.b64encode(f.read()).decode('utf-8')
    
    # Prepare email data
    email_data = {
        "from": "Mashup Generator <onboarding@resend.dev>",  # Use verified domain in production
        "to": [recipient_email],
        "subject": f"🎵 Your {singer} Mashup is Ready!",
        "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #667eea;">Your Mashup is Ready! 🎉</h2>
                <p>Hi there!</p>
                <p>Your <strong>{singer}</strong> mashup has been successfully created.</p>
                <p>Please find the attached ZIP file containing your mashup MP3.</p>
                <p>Enjoy your music! 🎵</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #888; font-size: 12px;">This is an automated email from Mashup Generator</p>
            </div>
        """,
        "attachments": [
            {
                "filename": "mashup.zip",
                "content": zip_content
            }
        ]
    }
    
    # Send email via Resend API
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=email_data
        )
        
        if response.status_code == 200:
            return True
        else:
            raise Exception(f"Resend API error: {response.text}")
    
    except Exception as e:
        print(f"Email error: {e}")
        raise Exception(f"Failed to send email: {str(e)}")


def create_mashup(singer, num_videos, duration, email):
    """Main mashup creation function"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Note: Vercel free tier has 10-second timeout
        # Pro tier has 60 seconds - may need upgrade for larger requests
        
        # Download videos
        downloads_dir = download_and_convert(singer, num_videos, temp_dir)
        
        # Trim and merge
        mashup_file = trim_and_merge(downloads_dir, duration, temp_dir)
        
        # Create ZIP
        zip_file = create_zip(mashup_file, temp_dir)
        
        # Send email
        send_email(zip_file, email, singer)
        
        return True
    
    except Exception as e:
        error_msg = str(e)
        # Provide helpful timeout message
        if "timeout" in error_msg.lower() or "time" in error_msg.lower():
            raise Exception("Request timed out. Try reducing number of videos to 3-5, or upgrade to Vercel Pro for longer timeout.")
        raise e
    
    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""
    
    def _send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        """Handle OPTIONS request (CORS preflight)"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET request"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        response = {
            'message': 'Mashup API - Use POST method with JSON data',
            'status': 'running'
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST request"""
        try:
            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))
            else:
                data = {}
            
            # Validate inputs
            errors = validate_inputs(data)
            if errors:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self._send_cors_headers()
                self.end_headers()
                response = {
                    'success': False,
                    'error': '; '.join(errors)
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Extract data
            singer = data['singer'].strip()
            num_videos = int(data['num_videos'])
            duration = int(data['duration'])
            email = data['email'].strip()
            
            # Create mashup
            create_mashup(singer, num_videos, duration, email)
            
            # Success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            response = {
                'success': True,
                'message': f'Mashup created and sent to {email}'
            }
            self.wfile.write(json.dumps(response).encode())
        
        except Exception as e:
            # Error response
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            response = {
                'success': False,
                'error': str(e)
            }
            self.wfile.write(json.dumps(response).encode())