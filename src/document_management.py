import os
import shutil
from pathlib import Path

import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
from firebase_admin import firestore

from config import GEMINI_API_KEY

# Initialize recognizer and text-to-speech
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 250)  # Adjust speaking rate if needed

# Initialize Firestore
db = firestore.client()

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Common folders as base directories for searches
COMMON_FOLDERS = {
    "documents": Path.home() / "Documents",
    "downloads": Path.home() / "Downloads",
    "desktop": Path.home() / "Desktop",
    "pictures": Path.home() / "Pictures",
    "videos": Path.home() / "Videos",
    "music": Path.home() / "Music",
}


def create_document(file_name, content, base_folder_name, target_folder_name):
    """
    Creates a new document with the specified content.

    Parameters:
        file_name (str): The name of the file to create.
        content (str): The content to write to the file.
    """
    base_directory = COMMON_FOLDERS.get(base_folder_name.lower(), Path(base_folder_name))

    if not base_directory.exists():
        print(f"Base directory '{base_directory}' does not exist.")
        return

    if base_folder_name == target_folder_name:
        target_path = base_directory
    else:
        # Search for the target folder within the base directory
        target_path = find_folder(base_directory, target_folder_name)

    if target_path:
        file_path = target_path / file_name
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Document '{file_name}' created in '{target_path}'.")


def edit_document(file_name, new_content, base_folder_name):
    """
    Edits an existing document by appending new content.

    Parameters:
        file_name (str): The name of the file to edit.
        new_content (str): The new content to append.
    """
    base_directory = COMMON_FOLDERS.get(base_folder_name.lower(), Path(base_folder_name))

    if not base_directory.exists():
        print(f"Base directory '{base_directory}' does not exist.")
        return

    file_path = findfile(file_name, base_directory)
    if file_path:
        with open(file_path, 'w') as file:
            file.write(new_content)
        print(f"Document '{file_name}' edited successfully.")
    else:
        print(f"Document '{file_name}' not found.")


def delete_document(file_name, base_folder_name):
    """
    Deletes a document.

    Parameters:
        file_name (str): The name of the file to delete.
    """
    base_directory = COMMON_FOLDERS.get(base_folder_name.lower(), Path(base_folder_name))

    if not base_directory.exists():
        print(f"Base directory '{base_directory}' does not exist.")
        return

    file_path = findfile(file_name, base_directory)
    if file_path:
        file_path.unlink()
        print(f"Document '{file_name}' deleted.")
    else:
        print(f"Document '{file_name}' not found.")


def summarize_document(file_name, base_folder_name):
    """
    Summarizes the content of a document using Gemini.

    Parameters:
        file_name (str): The name of the file to summarize.

    Returns:
        str: The summary of the document.
    """
    base_directory = COMMON_FOLDERS.get(base_folder_name.lower(), Path(base_folder_name))

    if not base_directory.exists():
        print(f"Base directory '{base_directory}' does not exist.")
        return

    file_path = findfile(file_name, base_directory)
    if file_path:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        response = model.generate_content("Summarize the following file content: " + content)
        return response.text
    else:
        print(f"Document '{file_name}' not found.")


def classify_document(file_name, base_folder_name):
    """
    Classifies a document based on its content using Gemini.

    Parameters:
        file_name (str): The name of the file to classify.

    Returns:
        str: The classification of the document.
    """
    base_directory = COMMON_FOLDERS.get(base_folder_name.lower(), Path(base_folder_name))

    if not base_directory.exists():
        print(f"Base directory '{base_directory}' does not exist.")
        return

    file_path = findfile(file_name, base_directory)
    if file_path:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        response = model.generate_content(
            "Classify this file content to a category, say only work or personal: " + content)
        print(f"Document '{file_name}' classified as: {response.text.strip()}")
        return response.text.strip()
    else:
        print(f"Document '{file_name}' not found.")


def retrieve_document(file_name, base_folder_name):
    """
    Retrieves the path of a specific document within a target folder in a base folder.

    Parameters:
        base_folder_name (str): The name of the base folder to start searching from.
        target_folder_name (str): The name of the folder containing the document.
        document_name (str): The name of the document to retrieve.

    Returns:
        Path: The path of the document if found, or None if not found.
    """

    base_directory = COMMON_FOLDERS.get(base_folder_name.lower(), Path(base_folder_name))

    if not base_directory.exists():
        print(f"Base directory '{base_directory}' does not exist.")
        return

    file_path = findfile(file_name, base_directory)
    if file_path:
        with open(file_path, "r") as file:
            content = file.read()
        print(f"\nContent of '{file_name}':\n{content}")
        return content
    else:
        print(f"Document '{file_name}' not found.")


def findfile(name, path):
    """Searches for a file by name in a specified base directory."""
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            if Path(filename).stem.lower() == name:
                return Path(dirpath) / filename

    print(f"File '{name}' not found in '{path}'.")
    return None


def find_folder(base_directory, target_folder_name):
    """
    Recursively searches for a folder by name starting from a base directory.

    Parameters:
        base_directory (Path): The directory to start searching from.
        target_folder_name (str): The name of the folder to search for.

    Returns:
        Path: The full path to the target folder if found, or None if not found.
    """
    for root, dirs, _ in os.walk(base_directory):
        for dir_name in dirs:
            if dir_name.lower() == target_folder_name.lower():
                return Path(root) / dir_name
    print(f"Folder '{target_folder_name}' not found in '{base_directory}'.")
    return None


def move_document(file_name, current_base_folder_name, target_folder_name):
    """
    Moves a document to a target folder, searching within a base folder.

    Parameters:
        file_name (str): The name of the file to move.
        base_folder_name (str): The name of the base folder to start searching from.
        target_folder_name (str): The name of the folder to move the file into.
    """

    current_base_directory = COMMON_FOLDERS.get(current_base_folder_name.lower(), Path(current_base_folder_name))

    if not current_base_directory.exists():
        print(f"Base directory '{current_base_directory}' does not exist.")
        return

    if current_base_folder_name == target_folder_name:
        file_path = current_base_directory / file_name
    else:
        # search for the file in the current folder
        file_path = findfile(file_name, current_base_directory)

    target_base_directory = current_base_directory

    if target_base_directory == target_folder_name:
        target_path = target_base_directory
    else:
        # Search for the target folder within the base directory
        target_path = find_folder(target_base_directory, target_folder_name)

    if target_path:
        try:
            shutil.move(file_path, target_path / Path(file_name).name)
            print(f"Document '{file_name}' moved to '{target_path}' successfully.")
        except FileNotFoundError:
            print(f"Document '{file_name}' not found.")
        except Exception as e:
            print(f"An error occurred while moving the document: {e}")
    else:
        print(f"Target folder '{target_folder_name}' not found.")


def list_documents(base_folder_name, target_folder_name):
    """
    Lists all documents in a target folder within a specified base folder.

    Parameters:
        base_folder_name (str): The name of the base folder to start searching from.
        target_folder_name (str): The name of the folder to list documents from.

    Returns:
        list: A list of document paths within the target folder.
    """
    base_directory = COMMON_FOLDERS.get(base_folder_name.lower(), Path(base_folder_name))

    if not base_directory.exists():
        print(f"Base directory '{base_directory}' does not exist.")
        return

    if base_folder_name == target_folder_name:
        target_path = base_directory
    else:
        # Search for the target folder within the base directory
        target_path = find_folder(base_directory, target_folder_name)

    if target_path and target_path.exists():
        documents = [file for file in target_path.iterdir() if file.is_file()]
        print(f"Documents in '{target_path}':")
        for doc in documents:
            print(doc.name)
        return documents
    else:
        print(f"Target folder '{target_folder_name}' not found.")
        return []


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


def document_management_voice_interaction(command):
    speak("What is the name of the document or file?")
    file_name = listen().lower()
    if "create" in command or "add" in command or "make" in command:
        file_name += ".txt"
        speak("What content would you like to add to the file?")
        content = listen().lower()
        speak("Which base folder is the target folder in?")
        base_folder = listen().lower()
        speak("What target folder should I use?")
        target_folder = listen().lower()
        create_document(file_name, content, base_folder, target_folder)
        speak(f"Document {file_name} created successfully.")

    elif "edit" in command or "append" in command or "update" in command or "modify" in command:
        speak("What new content would you like to append?")
        new_content = listen().lower()
        speak("Which base folder is the target folder or document in?")
        base_folder = listen().lower()
        edit_document(file_name, new_content, base_folder)
        speak(f"Document {file_name} edited successfully.")

    elif "delete" in command or "remove" in command or "erase" in command or "trash" in command:
        speak("Which base folder is this document in?")
        base_folder = listen().lower()
        delete_document(file_name, base_folder)
        speak(f"Document {file_name} deleted successfully.")

    elif "summarize" in command or "summary" in command or "abstract" in command:
        speak("Which base folder is this document in?")
        base_folder = listen().lower()
        summary = summarize_document(file_name, base_folder)
        speak(f"The summary of {file_name} is: {summary}")

    elif "classify" in command or "category" in command or "categorize" in command:
        speak("Which base folder is this document in?")
        base_folder = listen().lower()
        classify_document(file_name, base_folder)
        speak(f"Document {file_name} classified successfully.")

    elif "move" in command or "transfer" in command or "shift" in command:
        speak("Which current base folder is this file in?")
        current_base_folder = listen().lower()
        speak("Which target folder should this file move to?")
        target_folder = listen().lower()
        move_document(file_name, current_base_folder, target_folder)
        speak(f"Document {file_name} moved successfully.")

    elif "retrieve" in command or "get" in command or "open" in command or "read" in command or "show" in command or "display" in command or "look" in command:
        speak("Which base folder is the document in?")
        base_folder = listen().lower()
        retrieve_document(file_name, base_folder)
        speak(f"Document {file_name} retrieved successfully. Check the console for details")

    elif "list" in command:
        speak("Which base folder would you like to list documents from?")
        base_folder = listen().lower()
        speak("Which target folder would you like to list documents from?")
        target_folder = listen().lower()
        list_documents(base_folder, target_folder)
        speak("Listing documents complete.")

    else:
        speak("I didn't understand that command. Please try again.")
