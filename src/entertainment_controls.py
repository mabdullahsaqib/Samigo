import os
import subprocess
import webbrowser

import pyttsx3
import speech_recognition as sr
import spotipy
from googleapiclient.discovery import build
from spotipy.oauth2 import SpotifyOAuth
from word2number import w2n

from config import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, YOUTUBE_API_KEY

# Initialize recognizer and text-to-speech
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 250)  # Adjust speaking rate if needed

# Initialize Spotify and YouTube APIs
scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=scope))
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


# Function for local media playback
def play_local_media(file_path):
    if os.path.isfile(file_path):
        subprocess.Popen(file_path, shell=True)
    else:
        print("File does not exist:", file_path)


# YouTube functions
def search_youtube_video(query):
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=1
    )
    response = request.execute()
    if response["items"]:
        video_id = response["items"][0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={video_id}"
    else:
        return None


def open_youtube_video(query):
    video_url = search_youtube_video(query)
    if video_url:
        webbrowser.open(video_url)
    else:
        print("Video not found.")


# Spotify control functions
def play_spotify_track(track_name):
    results = sp.search(q=track_name, type="track", limit=1)
    if results["tracks"]["items"]:
        track_uri = results["tracks"]["items"][0]["uri"]
        sp.start_playback(uris=[track_uri])


def pause_spotify():
    sp.pause_playback()


def resume_spotify():
    sp.start_playback()


def skip_spotify_track():
    sp.next_track()


def previous_spotify_track():
    sp.previous_track()


def volume_up():
    sp.volume(10)


def volume_down():
    sp.volume(-10)


def repeat_track():
    sp.repeat("track")


# Handle dynamic commands
def handle_command(command, input_text=None):
    command = command.lower()

    if "play" in command:
        if "spotify" in input_text.lower():
            play_spotify_track(input_text.replace("play", "").replace("on spotify", "").strip())
        elif "youtube" in input_text.lower():
            open_youtube_video(input_text.replace("play", "").replace("on youtube", "").strip())
        elif "local" in input_text.lower():
            play_local_media(input_text.replace("play", "").replace("on local", "").strip())

    elif "pause" in command or "stop" in command:
        pause_spotify()

    elif "resume" in command:
        resume_spotify()

    elif "skip" in command or "next" in command:
        skip_spotify_track()

    elif "previous" in command:
        previous_spotify_track()

    elif "volume up" in command or "increase" in command:
        volume_up()

    elif "volume down" in command or "decrease" in command:
        volume_down()

    elif "repeat" in command or "loop" in command:
        repeat_track()

    elif "seek" in command or "jump" in command:
        try:
            speak("Tell the position to seek to :")
            input_text = listen()
            if input_text.isdigit():
                minutes = input_text[0]  # Extract time in seconds from input
                seconds = input_text[1:] if len(input_text) > 1 else 0
                seconds = int(minutes) * 60 + int(seconds)
            else:
                input_text = input_text.split()
                minutes = w2n.word_to_num(input_text[0])
                s = ' '.join(input_text[1:])
                seconds = w2n.word_to_num(s)
                seconds = minutes * 60 + seconds

            sp.seek_track(seconds * 1000)  # Spotify API uses milliseconds

        except Exception as e:
            print("Invalid seek time:", e)

    else:
        print(f"Unknown command: {command}")


def speak(text):
    engine.say(text)
    engine.runAndWait()


def listen():
    with sr.Microphone() as source:
        while True:
            print("Listening...")
            audio = recognizer.listen(source)
            try:
                command = recognizer.recognize_google(audio)
                print("Command : " + command)
                return command
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                speak("Voice service unavailable.")
                return ""


def entertainment_control_voice_interaction(command):
    # Listen for media-related commands

    if "play" in command:
        speak("What do you want to play today?")
        media_name = listen()
        speak("Where do you want to play it (Spotify, YouTube, local)?")
        platform = listen()

        if "spotify" in platform.lower():
            handle_command("play", media_name + " on Spotify")
        elif "youtube" in platform.lower():
            handle_command("play", media_name + " on YouTube")
        elif "local" in platform.lower() or "locally" in platform.lower():
            handle_command("play", media_name + " on local")

    else:
        handle_command(command)
