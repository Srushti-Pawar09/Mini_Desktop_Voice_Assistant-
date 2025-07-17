import pyttsx3
import speech_recognition as sr
import webbrowser
import datetime
import wikipedia
import os
import socket
from pydub import AudioSegment
from pydub.effects import normalize
import spacy  # Import spaCy
from fuzzywuzzy import process  # Import fuzzywuzzy for fuzzy matching
from vosk import Model, KaldiRecognizer
import json
import sounddevice as sd
import threading
import time
import sys
import subprocess

# Load the spaCy English language model
nlp = spacy.load("en_core_web_sm")

# Initialize the pyttsx3 engine
engine = pyttsx3.init()
vosk_model_english_path = r"D:\Python\vosk-model-small-en-in-0.4\vosk-model-small-en-in-0.4"
vosk_model_hindi_path = r"D:\Python\vosk-model-small-hi-0.22\vosk-model-small-hi-0.22"

vosk_model_en = Model(vosk_model_english_path)
vosk_model_hi = Model(vosk_model_hindi_path)

# List of known commands to match with fuzzywuzzy
known_commands = [
    'open google', 'search google for', 'open chrome', 'open wikipedia', 'search wikipedia for',
    'open youtube', 'search youtube for', 'open spotify', 'open mail', 'open docs', 'time',
    'open notepad', 'open calculator', 'withdraw', 'leave', 'open calci', 'open file explorer',
    'open settings', 'exit', 'go back', 'leo', 'switch to hindi', 'switch to english', 'open chatbot',
    'गुगल खोलो', 'गुगल पर खोलो', 'क्रोम खोलो', 'विकिपीडिया खोलो',
    'यूट्यूब खोलो', 'यूट्यूब पर खोजो', 'स्पॉटिफाई खोलें', 'मेल खोलो', 'दस्तावेज़ खोलो', 'समय',
    'नोटपैड खोलो', 'कैलकुलेटर खोलो', 'निकासी लें', 'छोड़ें', 'कैल्सी खोलो', 'फ़ाइल एक्सप्लोरर खोलो',
    'सेटिंग्स खोलो', 'बाहर निकलो', 'वापस जाओ', 'लियो', 'हिंदी में स्विच करो', 'अंग्रेजी में स्विच करो'
]

# Wake word
WAKE_WORD = "tom"
INACTIVITY_TIMEOUT = 120  # Timeout duration in seconds (2 minutes)
current_language = "en"

def is_internet_available():
    """Check if an internet connection is available."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)  # Google's DNS
        return True
    except OSError:
        return False

def speak(text):
    """Speak the provided text."""
    engine.say(text)
    engine.runAndWait()

def greet():
    """Greet the user based on the time of day."""
    hour = datetime.datetime.now().hour
    if hour < 12:
        speak("Good morning!")
    elif 12 <= hour < 18:
        speak("Good afternoon!")
    else:
        speak("Good evening!")
    speak("How can I assist you today?")

def listen_for_wake_word(language="en"):
    """Listen for the wake word offline."""
    global current_language
    vosk_model = vosk_model_en if language == "en" else vosk_model_hi
    recognizer = KaldiRecognizer(vosk_model, 16000)
    print("Listening for wake word (offline)...")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1) as stream:
        while True:
            data, overflow = stream.read(4000)
            if overflow:
                print("Buffer overflow occurred.")
                continue
            data_bytes = bytes(data)  # Convert data to bytes
            if recognizer.AcceptWaveform(data_bytes):
                result = json.loads(recognizer.Result())
                command = result.get("text", "").lower()
                print(f"Detected command: {command}")
                if WAKE_WORD in command:
                    print("Wake word detected!")
                    speak("How can I assist you?")
                    return True


def take_command(language="en"):
    """Take a command from the user."""
    vosk_model = vosk_model_en if language == "en" else vosk_model_hi

    # Check for internet availability
    if is_internet_available() and language == "en":
        # Use online recognition for English if the internet is available
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening (online)...")
            recognizer.adjust_for_ambient_noise(source)
            try:
                voice = recognizer.listen(source)
                command = recognizer.recognize_google(voice, language='en' if language == "en" else 'hi-IN').lower()
                print(f"Command received (online): {command}")
                return command
            except sr.UnknownValueError:
                speak("Sorry, I couldn't understand.")
                return "None"
    else:
        # Offline recognition using Vosk
        print(f"Listening in {language} (offline)...")
        recognizer = KaldiRecognizer(vosk_model, 16000)
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1) as stream:
            while True:
                data, overflow = stream.read(4000)
                if overflow:
                    continue  # Skip if there's an overflow issue
                if recognizer.AcceptWaveform(bytes(data)):
                    result = json.loads(recognizer.Result())
                    command = result.get("text", "").lower()
                    print(f"Command received (offline): {command}")
                    return command

def fuzzy_match_command(command):
    """Match the command to known commands using fuzzy logic."""
    best_match = process.extractOne(command, known_commands, score_cutoff=75)
    if best_match:
        return best_match[0]  # Return the best-matching command as a string
    return None

def handle_command(command):
    """Perform actions based on user commands."""
    global current_language
    
    if not command.strip():
        print("No valid command detected.")
        return

    print(f"Handling command: {command}")

    # Match command using fuzzy matching
    matched_command = fuzzy_match_command(command)

    if matched_command:
        print(f"Matched command: {matched_command}")
        # Switch language commands
        if matched_command == "open chatbot":
            speak("Starting the chatbot.")
            print("Launching chatbot...")
            subprocess.run(["python", "chatbot.py"])  # Run chatbot.py using subprocess
            return
        
        if matched_command in ['switch to hindi', 'हिंदी में स्विच करो']:
            current_language = "hi"
            speak("Switched to hindi")
            print("Language switched to Hindi.")
            return
        elif matched_command in ['switch to english', 'अंग्रेजी में स्विच करो']:
            current_language = "en"
            speak("Switched to English.")
            print("Language switched to English.")
            return
        # Handle commands based on current language
        if current_language == "hi":
            # Define Hindi-specific actions
            hindi_actions = {
                'गुगल खोलो': lambda: webbrowser.open("https://www.google.com"),
                'यूट्यूब खोलो': lambda: webbrowser.open("https://www.youtube.com"),
                'स्पॉटिफाई खोलो': lambda: webbrowser.open("https://open.spotify.com"),
                'मेल खोलो': lambda: webbrowser.open("https://mail.google.com"),
                'दस्तावेज़ खोलो': lambda: webbrowser.open("https://docs.google.com"),
                'नोटपैड खोलो': lambda: os.system("notepad"),
                'कैलकुलेटर खोलो': lambda: os.system("calc"),
                'समय': lambda: speak(f"अभी का समय है {datetime.datetime.now().strftime('%I:%M %p')}"),
                'फ़ाइल एक्सप्लोरर खोलो': lambda: os.system("explorer"),
                'सेटिंग्स खोलो': lambda: os.system("start ms-settings:"),
                'विकिपीडिया खोलो': lambda: webbrowser.open("https://www.wikipedia.org/"),
                'बाहर निकलो': lambda: sys.exit(),
            }

            # Execute action for the Hindi command
            if matched_command in hindi_actions:
                print(f"Executing Hindi action for: {matched_command}")
                speak(f"Executing {matched_command.replace('_', ' ').title()}.")
                hindi_actions[matched_command]()
                
            else:
                speak("I didn't understand.")
                print("No action defined for this Hindi command.")
            return
        else:
            # Define English-specific actions
            english_actions = {
                'open google': lambda: webbrowser.open("https://www.google.com"),
                'open youtube': lambda: webbrowser.open("https://www.youtube.com"),
                'open spotify': lambda: webbrowser.open("https://open.spotify.com"),
                'open mail': lambda: webbrowser.open("https://mail.google.com"),
                'open docs': lambda: webbrowser.open("https://docs.google.com"),
                'open notepad': lambda: os.system("notepad"),
                'open calculator': lambda: os.system("calc"),
                'time': lambda: speak(f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}"),
                'open file explorer': lambda: os.system("explorer"),
                'open settings': lambda: os.system("start ms-settings:"),
                'open wikipedia': lambda: webbrowser.open("https://www.wikipedia.org/"),
                
                'exit': lambda: sys.exit(),
            }

            # Execute action for the English command
            if matched_command in english_actions:
                print(f"Executing English action for: {matched_command}")
                speak(f"Executing {matched_command.replace('_', ' ').title()}.")
                english_actions[matched_command]()
            else:
                speak("Command recognized but no action defined.")
        
        # Additional commands for searches
        if 'search google for' in matched_command:
            query = command.replace(matched_command, '').strip()
            if query:
                speak(f"Searching Google for {query}")
                print(f"Executing: Google search for {query}")
                webbrowser.open(f"https://www.google.com/search?q={query}")
            else:
                speak("What should I search on Google?")
            return
        elif 'search youtube for' in matched_command:
            query = command.replace(matched_command, '').strip()
            if query:
                import pywhatkit
                speak(f"Searching YouTube for {query}")
                print(f"Executing: YouTube search for {query}")
                pywhatkit.playonyt(query)
            else:
                speak("What should I search on YouTube?")
            return
        elif 'search wikipedia for' in matched_command:
            query = command.replace(matched_command, '').strip()
            if query:
                speak(f"Searching Wikipedia for {query}")
                print(f"Executing: Wikipedia search for {query}")
                try:
                    summary = wikipedia.summary(query, sentences=2)
                    speak(f"According to Wikipedia, {summary}")
                except wikipedia.DisambiguationError:
                    speak("Multiple results found. Please be more specific.")
            else:
                speak("What should I search on Wikipedia?")
            return

    else:
        speak("Command not recognized.")
        print("No matched command found.")


# Main function to start the assistant
def main():
    greet()
    speak("Starting assistant...")
    inactivity_timer = None  # Timer for inactivity timeout

    def reset_timer():
        """Reset the inactivity timer."""
        nonlocal inactivity_timer
        if inactivity_timer:
            inactivity_timer.cancel()
        inactivity_timer = threading.Timer(INACTIVITY_TIMEOUT, on_inactivity)
        inactivity_timer.start()

    def on_inactivity():
        """Handle inactivity timeout."""
        speak("I've been inactive for a while. Returning to wake word listening mode.")
        print("Inactivity timeout occurred. Returning to wake word detection.")
        listen_for_wake_word()

    def listen_for_commands():
        """Listen for commands continuously for 2 minutes."""
        end_time = time.time() + INACTIVITY_TIMEOUT  # Set a timeout for command listening
        while time.time() < end_time:
            reset_timer()  # Reset the inactivity timer on every loop iteration
            print("Listening for commands...")
            command = take_command(language=current_language)  # Wait for a command
            if command:
                handle_command(command)  # Process the command
                print("Command executed. Waiting for next command...")

    # Start listening for wake word and commands
    while True:
        print("Waiting for wake word...")
        listen_for_wake_word(language=current_language)  # Listen for the wake word
        
        # Once the wake word is detected, start listening for commands
        print("Wake word detected. Listening for commands...")
        listen_for_commands()  # Listen for commands for 2 minutes


if __name__ == "__main__":
    main()
