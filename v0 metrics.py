#Imported a class (textatistic) to calculate text complexity and readability scores
from textatistic import Textatistic

#METRIC 1: READABILITY (Flesch-Kincaid)
""" Resource used for implementation
https://youtu.be/tw7sEhfRZxM?si=znk3iABTSrdmKPXk """
def readability(course_quality):
    #Score based on Flesch-Kincaid formula
    score = Textatistic(course_quality).scores['flesch_score']
    
    #Scaled the score to give a readability score from 1 (difficult) to 3 (easy)
    return score/(100/3)



#METRIC 2: STRUCTURE HEURISTICS
''' Basic (not complete) implementaion of counting the number of appearnces
    of the title, heading, sub-heading and returning a score based on it '''
def structure(course_quality):
    levels_found = set()
    
    ''' 1 for #, 2 for ##, 3 for ### '''
    prev_level = 0 
    
    lines = course_quality.splitlines()
    
    for l in lines:
        line = l.strip()
        currentl_level = 0
        
        if (line.startswith("### ")):
            currentl_level = 3
            
        elif (line.startswith("## ")):
            currentl_level = 2
            
        elif (line.startswith("# ")):
            currentl_level = 1
        
        # Check the order immediately
        if (current_level > 0):
            ''' CRITICAL CHECK: You can never skip a level going down (e.g.,
                going from the tile straight to sub-heading is not allowed) '''
            if prev_level == 1 and current_level == 3:
                return 1
            
            levels_found.add(current_level)
            prev_level = current_level
            
    # Returning a score from 1 to 3 based on logic based on our counts
    calculated_score = 1 + len(levels_found)
    if (calculated_score == 4):
        return 3
    return calculated_score






#TESTING
"""
INSTRUCTIONS: to test with files, you must convert them manually to a
block of strings
"""
    
#METRIC 1
easy = "this is for testing."
hard = "pneumonoultramicroscopicsilicovolanoconiosis."
print("Score 1: ", readability(easy))
print("Score 2: ", readability(hard))    
    

    
