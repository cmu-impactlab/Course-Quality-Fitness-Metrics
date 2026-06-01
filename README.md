# Fitness-Metrics

This project uses a Genetic Algorithm (GA) framework to automatically evaluate and optimize the quality of generated educational course files

## Baseline Metric
To unblock the GA loop execution, we have implemented automated evaluation metrics that return a 1-5 scale on the following criteria:

1. **Readability Metric:**
   * Evaluates text complexity.
   * Uses word counts and character-to-word density to ensure content is substantial but accessible.

2. **Structural Heuristics Metric:**
   * Evaluates the layout of the course.
   * Tracks header hierarchy (`#`, `##`, `###`) to ensure proper organization

3. **Text Embeddings Metric:**
   * Measures semantic simiularity.
   * Uses SBERT text embeddings (`all-MiniLM-L6-v2`) to do the measure consecutively between sequential 4-sentence text chunks.

4. **Interaction Opportunity Density (IOD) Metric:**
   * Measures how often a learner is asked to actively engage with the course material.
   * Calculates the ratio of interactive elements (quizzes, exercises, tasks) relative to total word count.
