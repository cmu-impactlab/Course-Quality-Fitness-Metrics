import requests
import json

from sentence_transformers import SentenceTransformer

import os
import glob

from collections import defaultdict


#Loading the pretrained Sentence Transformer model I used for the text embeddings metric
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def EES(course_quality):
    #My request for the model to generate a list of tuples of example exercise pair
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer <OPENROUTER_API_KEY>",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "google/gemini-2.5-flash-lite-preview-09-2025",
            "messages": [
                {
                    "role": "user",
                    "content": f"Extract example-exercise pairs from this material: {course_quality}"
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                "name": "exercise_extractor",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "pairs": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    },
                    "required": ["pairs"],
                    "additionalProperties": False
                    }
                }
            }
        })
    )
        
    #Converts API response to a Python dictionary 
    response_dict = response.json()

    #Extracts the text content as a string 
    raw_text = response_dict["choices"][0]["message"]["content"].strip()

    #Strips excess newlines, quotes, or whitespace
    raw_text = raw_text.replace("```json", "").replace("", "").strip()
    raw_text = raw_text.strip("` \n\r\t")
    
    #Converts string to 2d list
    data_list = json.loads(raw_text)
    data_list = data_list["pairs"]

    #Converts 2d list to a list of tuples
    tuple_list = [tuple(item) for item in data_list] 
    
    #List to store the transition scores between chunks    
    scores = []
    
    #Loop and compare pairs
    for pair in tuple_list:
        #Safely check
        if (not isinstance(pair, (list, tuple)) or len(pair) < 2):
            continue  

        example = pair[0]
        exercise = pair[1]
        
        embedding1 = model.encode(example)
        embedding2 = model.encode(exercise)
        
        similarities = model.similarity(embedding1, embedding2)
        scores.append(similarities.item())
        
    if (len(scores) == 0):
        return 0.0
    
    avg = sum(scores)/len(scores)
    
    if 0.725 <= avg <= 0.775:
        #Perfectly in the sweet spot
        return 1.0
    elif avg < 0.725:
        #Too different (penalize the distance downward)
        return max(0.0, avg / 0.725)
    else:
        #Too similar (penalize the distance upward)
        return max(0.0, 1.0 - ((avg - 0.775) / (1.0 - 0.775)))



def conceptual_continuity(course_quality, course_quality2):
    #My request for the model to generate a list of concepts for both arguments
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            #Replace <OPENROUTER_API_KEY> with actual API key
            "Authorization": "Bearer <OPENROUTER_API_KEY>",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "google/gemini-2.5-flash-lite-preview-09-2025",
            "messages": [
                {
                    "role": "user",
                    "content": f"""Analyze these two sequential lesson materials.
                     Extract a list of the main concepts discussed in each individual lesson.
                     Return ONLY a raw JSON dictionary with exactly two keys:
                     'lesson1' and 'lesson2'. The value for each key must be a
                     flat array of strings.
                     Example format: {{'lesson1': ['c1', 'c2'],
                     'lesson2': ['c3', 'c4']}} Absolutely no markdown text,
                     backticks, or conversational filler
                     \n\nLesson Material: \n{course_quality}
                     \n\nLesson Material2: \n{course_quality2}"""
                    
                    
                }
            ],
        })
    )
    
    #Convert API response to a Python dictionary and extract the text content
    raw_text = response.json()["choices"][0]["message"]["content"].strip()

    #Strips markdown backticks if the model includes them
    #Example: ```json [{"example": "text"}] ```
    if "```" in raw_text:
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
    
    #More stripping of any lingering trailing brackets, quotes, or whitespace
    raw_text = raw_text.strip("` \n\r\t")
    
    #Convert string to Python list
    data_list = json.loads(raw_text)
    
    #Getting the values from the keys (lesson1 and lesson2)
    lesson1_list = data_list["lesson1"]
    lesson2_list = data_list["lesson2"]
    
    if (len(lesson1_list) == 0 or len(lesson2_list) == 0):
        return 0.0
    
    #Merging concepts into one string 
    chunk1 = " ".join(lesson1_list)
    chunk2 = " ".join(lesson2_list)
    
    #Calculating embeddings
    embedding1 = model.encode([chunk1])
    embedding2 = model.encode([chunk2])
        
    #Calculating the embedding similarities
    similarities = model.similarity(embedding1, embedding2)
    
    return similarities.item()





#TESTING
# TESTING BOTH METRICS SIMULTANEOUSLY
root_generated_path = "/Users/ms3ood/Desktop/learnpack-generator-6fd80dd"
search_pattern = os.path.join(root_generated_path, "*", "lessons", "**", "*")

# 1. Gather all markdown files and ensure they are sorted in perfect order
all_files = [f for f in glob.glob(search_pattern, recursive=True) if os.path.isfile(f) and f.endswith('.md')]
all_files.sort()

print(f"Found {len(all_files)} files to evaluate across all runs.\n")

# Keep track of the previous file text and name to calculate continuity transitions
prev_text = None
prev_file_name = None
prev_lesson_name = None

for file_path in all_files:
    file_name = os.path.basename(file_path)
    path_parts = file_path.split(os.sep)
    
    try:
        lesson_name = path_parts[-2]  # e.g., 00_introduction_to_typescript
        course_run = path_parts[-4]   # e.g., learnpack-generator-6fd80dd
    except IndexError:
        lesson_name, course_run = "Unknown", "Unknown"
        
    # Read the current file's content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            current_text = f.read()
    except Exception as e:
        print(f"❌ Error reading file {file_name}: {e}")
        continue

    print(f"\n==================================================")
    print(f"📄 FILE: {file_name} | Lesson: {lesson_name} | Run: {course_run}")
    print(f"==================================================")

    # --- METRIC 1: SINGLE FILE METRIC (EES) ---
    error = None
    for i in range(3):
        try:
            ees_score = EES(current_text)
            if (0.0 <= ees_score <= 1.0):
                error = None
                break
        except Exception as e:
            error = e
           
    if (error == None):
        print(f"  ➡️ EES Score: {ees_score}")
    else:
        ees_score = 0.0
        print(f"  ‼️ There was an error: {ees_score}")

    # --- METRIC 2: TRANSITION METRIC (Conceptual Continuity) ---
    # Only calculate continuity if there is a previous file AND it belongs to the same lesson run module
    if prev_text is not None and prev_lesson_name == lesson_name:
        try:
            print(f"  🔗 Evaluating Continuity: {prev_file_name} ➔ {file_name}")
            continuity_score = conceptual_continuity(prev_text, current_text)
            print(f"  ➡️ Conceptual Continuity Score: {continuity_score}")
        except Exception as e:
            print(f"  ❌ Skipping Continuity due to error: {e}")
    elif prev_text is not None and prev_lesson_name != lesson_name:
        print(f"  🛑 New lesson folder detected. Skipping continuity bridge across different modules.")

    # Update history tracking variables for the next iteration step
    prev_text = current_text
    prev_file_name = file_name
    prev_lesson_name = lesson_name
