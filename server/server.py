from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
from urllib.parse import urlparse, parse_qs
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import threading
import queue
import time
# Queue for download requests
download_queue = queue.Queue()

# Lock for managing active download status
active_download = threading.Lock()

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes
#database 
# Configure MySQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://pluginuser:Godverdomme@localhost/projecthunt'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize SQLAlchemy
db = SQLAlchemy(app)

# visit database
class Visit(db.Model):
    __tablename__ = 'visits'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)  # Foreign key linking to profiles
    visited_url = db.Column(db.String(255), nullable=False)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow)  # Automatically records the time of visit
    mostrecentvideo = db.Column(db.String(255), nullable=True)  # URL or identifier of the most recent video
    dateofmostrecentvideo = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of the most recent video
    
    # Define a relationship to the Profile model
    profile = db.relationship('Profile', backref='visits', lazy=True)

# Define the Profiles model
class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(255), nullable=False)
    platform = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(255), nullable=True)
    dateposted = db.Column(db.DateTime, default=datetime.utcnow)
    datelastvisit = db.Column(db.DateTime, default=datetime.utcnow)
    dateofbirth = db.Column(db.DateTime, default=datetime.utcnow)
    userid = db.Column(db.String(255), nullable=True)
    username = db.Column(db.String(255), nullable=True)
    comments = db.Column(db.String(1000), nullable=True)
    deleted = db.Column(db.Boolean, default=False)

    # Define a relationship to videos
    videos = db.relationship('Video', backref='profile', lazy=True)

# Define the Videos model
class Video(db.Model):
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    videoid = db.Column(db.String(255), nullable=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=True)
    url = db.Column(db.String(255), nullable=False)
    platform = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(255), nullable=False)
    dateposted = db.Column(db.DateTime, default=datetime.utcnow)
    datesaved = db.Column(db.DateTime, default=datetime.utcnow)
    thumbnail = db.Column(db.String(255), nullable=True)
    downloadedintheoldways = db.Column(db.Boolean, default=False)

def get_channel_id(url):
    """This is once a channel is renamed, it wont be aviailable anymroe. So we link all channelnames top channel ids and then c
    once a channel gets demleted, we check if the channel id is is still up (in that case they just renamed their channel
    ) So in the begining ill just push channelname to the database;, but later we implement that channel id gets saved to in case
    thge channel gets renamed."""
    ydl_opts = {
        'quiet': True,  # Suppress verbose output
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            
            # Extract channel ID from the metadata if available
            channel_id = info_dict.get('channel_id', None)
            
            if channel_id:
                print(f"Channel ID: {channel_id}")
                return channel_id
            else:
                print("Channel ID not found.")
                return None
    except Exception as e:
        print(f"Error extracting channel ID: {e}")
        return None

def profile_exists_in_db(url):
    """returns true if the profile already exiusts in the database"""
    return db.session.query(Profile.id).filter_by(url=url).first() is not None

def video_exists_in_db(url):
    """check if youtuber or insta, youtube, check with id"""
    """returns true if the profile already exiusts in the database"""
    return db.session.query(Video.id).filter_by(url=url).first() is not None

def add_video_to_db(video_data):

   # Get JSON data from the request
    url = video_data.get('url')  # Extract the URL from the data
    platform = video_data.get('platform', 'YouTube')  # Default to 'YouTube' if not provided
    category = video_data.get('category', 'EP')  # Default to 'YouTube' if not provided
    print("yo in add_video_to_db")
    if not url:
        print("URL is required!")
        return

    # Check if the video URL already exists in the database
    if video_exists_in_db(url):
        print("Video with this URL already exists!")
        return

    # Create a new video instance with platform info
    new_video = Video(url=url, platform=platform, category=category)
    db.session.add(new_video)  # Add the instance to the session
    db.session.commit()  # Commit the session to save to the database
    
    print('Profile URL added successfully!')

def is_valid_youtube_url(url):
    """Validate that the URL is a proper YouTube URL with a video ID."""
    parsed_url = urlparse(url)
    if parsed_url.netloc == 'www.youtube.com' and parsed_url.path == '/watch':
        query_params = parse_qs(parsed_url.query)
        return 'v' in query_params  # Ensure there's a video ID
    elif parsed_url.netloc == 'www.youtube.com' and '/shorts/' in parsed_url.path:
        return True  # It's a valid YouTube Shorts URL
    elif parsed_url.netloc in ['www.instagram.com', 'instagram.com']:
        # Instagram video URLs generally contain '/p/' or '/reel/' followed by a unique ID
        if '/p/' in parsed_url.path or '/reel/' in parsed_url.path:
            return True  # It's a valid Instagram post or reel URL
    return False



def extract_video_links(url):
    ydl_opts = {
        'extract_flat': True,  # Extract the list of videos without downloading them
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=False)
        print(f"this is the result {result}")
        # Safely get video links, handling cases where 'url' might not exist
        video_links = []
        for entry in result.get('entries', []):
            if 'url' in entry:
                video_links.append(entry['url'])
            else:
                print(f"Warning: No 'url' found for entry: {entry}")  # Log the problematic entry
        print(f"trhis are the videolinks {video_links}")
        return video_links
    
def download_video_worker():
    """Worker function to process the download queue."""
    while True:
        # Get the next URL from the queue
        videotodl = download_queue.get()
        url = videotodl.get('url')
        if url is None:
            break  # Exit condition for the thread

        with active_download:
            try:
                print(f"Starting download for: {url}")
                # yt-dlp options for downloading
                ydl_opts = {
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                    'outtmpl': '/home/andy/Documents/%(title)s.%(ext)s',
                    'restrictfilenames': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                    with app.app_context():
                        add_video_to_db(videotodl)
                print(f"Download complete for: {url}")
            except Exception as e:
                print(f"Error downloading video: {e}")
        # Mark the current task as done
        download_queue.task_done()



@app.route('/videos')
def list_videos():
    videos = Video.query.all()  #
    print(videos)
    return {video.ID: video.url for video in videos}

@app.route('/test_channel')
def test_channel():
    url = "https://www.youtube.com/watch?v=Q-kqm0AgJZ8"
    channel_id = get_channel_id(url)
    return channel_id 

@app.route('/check_or_add_profile', methods=['POST'])
def check_or_add_profile():
    data = request.json
    url = data.get('url')
    platform = data.get('platform')
    category = data.get('category', 'Uncategorized')
    username = data.get('username', 'Unknown')

    # Check if the profile already exists in the database
    profile = Profile.query.filter_by(url=url).first()

    if profile:
        # Profile exists, return its ID
        return jsonify({'status': 'success', 'profile_id': profile.id}), 200
    else:
        # Profile does not exist, create a new one
        new_profile = Profile(url=url, platform=platform, category=category, username=username)
        db.session.add(new_profile)
        db.session.commit()
        return jsonify({'status': 'success', 'profile_id': new_profile.id}), 201

# Add visit route
@app.route('/add_visit', methods=['POST'])
def add_visit():
    data = request.json
    profile_id = data.get('profile_id')
    visited_url = data.get('visited_url')

    # Create a new visit entry
    new_visit = Visit(profile_id=profile_id, visited_url=visited_url)
    db.session.add(new_visit)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Visit recorded successfully!'}), 201




@app.route('/post_profile' , methods=['POST'])
def post_profile():
    data = request.json  # Get JSON data from the request
    url = data.get('url')  # Extract the URL from the data
    platform = data.get('platform', 'YouTube')  # Default to 'YouTube' if not provided
    print("yo")
    if not url:
        return jsonify({'status': 'error', 'message': 'URL is required!'}), 400
    
    # Check if the profile URL already exists in the database
    if profile_exists_in_db(url):
        return jsonify({'status': 'error', 'message': 'Profile with this URL already exists!'}), 409

    # Create a new Profile instance with platform info
    new_profile = Profile(url=url, platform=platform)
    db.session.add(new_profile)  # Add the instance to the session
    db.session.commit()  # Commit the session to save to the database
    
    return jsonify({'status': 'success', 'message': 'Profile URL added successfully!'}), 201

    

@app.route('/download_video', methods=['POST'])

def download_video():
    data = request.json
    url = data.get('url')
    platform = data.get('platform', 'YouTube')  # Default to 'YouTube' if not provided
    video_data = {
        'url': url,
        'platform': platform
    }
    if url and is_valid_youtube_url(url):
        # Add the download request to the queue
        download_queue.put(video_data)
        return jsonify({'status': 'success', 'message': 'Download added to the queue'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Invalid YouTube URL'}), 400

# Start the download worker thread
worker_thread = threading.Thread(target=download_video_worker, daemon=True)
worker_thread.start()

@app.route('/get_videos', methods=['POST'])
def get_video_links():
    data = request.json
    url = data.get('url')
    
    video_links = extract_video_links(url)
    return jsonify({'links': video_links})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=5000)
