from flask import Flask, request, jsonify
from gtts import gTTS
import os
import uuid
import moviepy.editor as mp
from moviepy.editor import TextClip, CompositeVideoClip
import requests
from io import BytesIO

app = Flask(__name__)

# Pexels API for stock videos
PEXELS_API_KEY = "your_pexels_api_key"  # Replace with your Pexels API key
def get_stock_video(query="nature"):
    headers = {"Authorization": PEXELS_API_KEY}
    response = requests.get(
        f"https://api.pexels.com/videos/search?query={query}&per_page=1",
        headers=headers
    )
    if response.status_code == 200:
        video_url = response.json()["videos"][0]["video_files"][0]["link"]
        video_data = requests.get(video_url).content
        return BytesIO(video_data)
    return None

# Simple script generator (replace with AI model for better results)
def generate_script(topic):
    return f"Explore {topic} in this quick video! Amazing facts await!"

# Create video optimized for mobile (lower resolution)
def create_video(script, topic):
    tts = gTTS(text=script, lang="en")
    audio_path = f"temp_{uuid.uuid4()}.mp3"
    tts.save(audio_path)

    video_data = get_stock_video(topic)
    if not video_data:
        return None
    video_path = f"temp_{uuid.uuid4()}.mp4"
    with open(video_path, "wb") as f:
        f.write(video_data.read())

    video = mp.VideoFileClip(video_path).resize(height=720)  # Optimize for mobile
    audio = mp.AudioFileClip(audio_path)
    duration = min(video.duration, audio.duration)
    video = video.set_duration(duration)
    audio = audio.set_duration(duration)

    txt_clip = TextClip(script, fontsize=20, color="white", size=video.size, bg_color="black")
    txt_clip = txt_clip.set_position(("center", "bottom")).set_duration(duration)

    final_video = CompositeVideoClip([video, txt_clip]).set_audio(audio)
    output_path = f"static/output_{uuid.uuid4()}.mp4"
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", bitrate="1000k")

    os.remove(audio_path)
    os.remove(video_path)
    return output_path

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    topic = data.get("topic", "default")
    script = generate_script(topic)
    video_path = create_video(script, topic)
    if video_path:
        return jsonify({"video_url": f"/{video_path}"})
    return jsonify({"error": "Failed to generate video"}), 500

if __name__ == "__main__":
    app.run(debug=True)
