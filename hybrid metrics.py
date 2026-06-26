import requests
import json

from sentence_transformers import SentenceTransformer

import os
import glob

from collections import defaultdict

from pathlib import Path


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
            #Format: {"pairs": [["example1", "exercise1"], ["example2", "exercise2"], ...]}
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




def conceptual_continuity(course_quality):
    #My request for the model is to generate a list of lessons with their introduced and discussed concepts
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
                    "content": f"""You are analyzing an entire sequential curriculum course.
                     Analyze the lessons provided in order. For each sequential lesson, extract:
                     1. 'introduced': Core technical concepts taught/defined for the first time in that specific lesson.
                     2. 'discussed': Prerequisites or existing concepts that are mentioned, used, or built upon.
                     
                     Course Materials:
                     {course_quality}"""
                }
            ],
            #Format: {"course_data": [{"lesson": 1, "introduced": ["concept1", "concept2"], "discussed": ["concept1", "concept2"]}, ...]}
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "concept_continuity_extractor",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "course_data": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "lesson": {"type": "integer"},
                                        "introduced": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "discussed": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    },
                                    "required": ["lesson", "introduced", "discussed"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["course_data"],
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
    
    #Converts string to a list of dictionaries
    data_list = json.loads(raw_text)
    data_list = data_list["course_data"]

    #List to keep track of every introduced concept in each lesson
    all_concepts_introduced = []

    #List to keep track of scores of each lesson's concept discussion and previous lessons' introductions
    scores = []

    for item in data_list:
        lesson_num = item["lesson"]
        introduced = item["introduced"]
        discussed = item["discussed"]
        
        #If it's lesson 1 or no concepts discussed in the lesson, extend its introductions and skip it
        if (lesson_num == 1 or not discussed):
            all_concepts_introduced.extend(introduced)
            continue

        else:
            if (not all_concepts_introduced):
                score = 0.0
            else:
                chunk_introduced = " ".join(all_concepts_introduced)
                chunk_discussed = " ".join(discussed)
                
                embedding1 = model.encode(chunk_introduced)
                embedding2 = model.encode(chunk_discussed)
                
                similarity = model.similarity(embedding1, embedding2)
                score = similarity.item()
        
        scores.append(score)
        
        all_concepts_introduced.extend(introduced)

    # Return the average continuity score across the entire course
    if (len(scores) == 0):
        return 0.0
    return sum(scores)/len(scores)





#TESTING (Metrics are tested one by one)
# --- METRIC 2: TRANSITION METRIC (Conceptual Continuity) ---
#Change the path to the folder containing the courses
folder_path = Path("/Users/ms3ood/Desktop/Uni/Summer 26'/SURA/learnpack-generator-6fd80dd/typescript-the-basics-20260526024515-gpt5mini/lessons")
all_files = sorted(list(folder_path.glob('*.md')))

# Create a list to store the actual text content of every file
all_lesson_texts = []

# Loop to read all the files upfront
for path in all_files:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            all_lesson_texts.append(file_content)
    except Exception as e:
        print(f"❌ Error reading {path.name}: {e}")

print(f"Successfully read {len(all_lesson_texts)} files. Sending to LLM...")

# Pass the array of text contents directly into your function
conceptual_continuity_score = conceptual_continuity(all_lesson_texts)
print(f"  ➡️ Conceptual Continuity score Score: {conceptual_continuity_score}")
print()
print()
print()



root_generated_path = "/Users/ms3ood/Desktop/Uni/Summer 26'/SURA/learnpack-generator-6fd80dd"
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
    try:
        ees_score = EES(current_text)
        print(f"  ➡️ EES Score: {ees_score}")
    except Exception as e:
        print(f"  ❌ Skipping EES due to error: {e}")

    # Update history tracking variables for the next iteration step
    prev_text = current_text
    prev_file_name = file_name
    prev_lesson_name = lesson_name
