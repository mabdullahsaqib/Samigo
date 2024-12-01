from datetime import datetime

import dateparser
import google.generativeai as genai

from firebase_admin import firestore

from src.config import GEMINI_API_KEY

# Initialize Firestore
db = firestore.client()

# Initialize Gemini model
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")









# Function to infer priority and category using Gemini
def infer_task_details(task_description):
    response = model.generate_content(
        f"What is the priority and category of this task? Only provide the priority (high,medium,low) as priority : and category (work, personal) as category : , nothing else, no description, no extra information. : {task_description}"
    )
    return response.text.lower()


def add_task_from_input(task_description, deadline):
    inferred_details = infer_task_details(task_description)
    priority = "medium"
    category = "personal"

    if "priority" in inferred_details and "category" in inferred_details:
        priority = "high" if "high" in inferred_details else "low" if "low" in inferred_details else "medium"
        category = "work" if "work" in inferred_details else "personal"

    task_data = {
        "title": task_description,
        "category": category,
        "deadline": deadline,
        "priority": priority,
        "created_at": datetime.now(),
    }

    doc_ref = db.collection("tasks").document(task_description)
    doc_ref.set(task_data)
    print(f"Task '{task_description}' added with priority: {priority} and category: {category}")


def get_tasks_by_priority(priority):
    tasks = db.collection("tasks").where("priority", "==", priority).stream()
    task_list = [task.to_dict() for task in tasks]

    print(f"Tasks with priority '{priority}' are being displayed on the console")
    for task in task_list:
        print(f"{task['title']} with deadline on {task['deadline']}")
    return task_list


def get_tasks_by_category(category):
    tasks = db.collection("tasks").where("category", "==", category).stream()
    task_list = [task.to_dict() for task in tasks]

    print(f"Tasks in category '{category}' are being displayed on the console")
    for task in task_list:
        print(f"{task['title']} with deadline on {task['deadline']}")
    return task_list


def get_upcoming_tasks(deadline_date):
    tasks = db.collection("tasks").where("deadline", "<=", deadline_date).order_by("deadline").stream()
    upcoming_tasks = [task.to_dict() for task in tasks]

    print("Here are the upcoming tasks")
    for task in upcoming_tasks:
        print(f"{task['title']} with deadline on {task['deadline']}")
    return upcoming_tasks


def delete_task(task_title):
    db.collection("tasks").document(task_title).delete()
    print(f"Task '{task_title}' deleted successfully!")


def task_voice_interaction(command):
    if "add" in command:
        print("What is the task description?")
        task_description = input()
        print("What is the deadline?")
        deadline_input = input()
        deadline = dateparser.parse(deadline_input) if deadline_input else None
        add_task_from_input(task_description, deadline)

    elif "priority" in command:
        print("What priority level would you like to check? (high, medium, low)")
        priority = input()
        get_tasks_by_priority(priority.lower())

    elif "category" in command:
        print("Which category would you like to check? (work or personal)")
        category = input()
        get_tasks_by_category(category.lower())

    elif "upcoming" in command:
        print("Specify the deadline for upcoming tasks.")
        deadline_input = input()
        deadline_date = dateparser.parse(deadline_input)
        get_upcoming_tasks(deadline_date)

    elif "delete" in command:
        print("What is the title of the task you would like to delete?")
        task_title = input()
        delete_task(task_title)

    else:
        print("Sorry, I didn't understand that command.")
