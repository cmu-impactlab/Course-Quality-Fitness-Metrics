# Fitness-Metrics

This project uses a Genetic Algorithm (GA) framework to automatically evaluate and optimize the quality of generated educational course files

## Baseline Metrics
To unblock the GA loop execution, we have implemented automated evaluation metrics that return a 1-5 scale on the following criteria:

1. **Readability Metric:**
   * Evaluates text complexity.
   * Uses word counts and character-to-word density to ensure content is substantial but accessible.

2. **Structural Heuristics Metric:**
   * Evaluates the layout of the course.
   * Tracks header hierarchy (`#`, `##`, `###`) to ensure proper organization

3. **Text Embeddings Metric:**
   * Measures semantic simiularity.
   * Uses a pre-trained SBERT text embeddings model (`all-MiniLM-L6-v2`) to measure consecutively between sequential 4-sentence text chunks.

4. **Interaction Opportunity Density (IOD) Metric:**
   * Measures how often a learner is asked to actively engage with the course material.
   * Calculates the ratio of interactive elements (quizzes, exercises, tasks) relative to total word count.

---

## Hybrid Metrics
Unlike readability or text emeddings, **Hybrid Metrics** bridge mathematical calculations and generative AI. They leverage an LLM (using strict, zero-error JSON schemas) to extract pedagogical features and relational data from the curriculum. Once extracted, text embeddings (`all-MiniLM-L6-v2`) mathematically compute semantic relationships, allowing the Genetic Algorithm to score structural and content quality against advanced educational rubrics like Learnpack.

### 1. Example-Exercise Similarity (EES) Metric
   * Evaluates pedagogical alignment between educational explanations (examples) and corresponding practice tasks (exercises) within a single lesson.
   * Extracts explicit example-exercise pairs using a strict LLM schema and assesses their proximity using cosine similarity.
   * Modifies scores by scaling as the following:
     * Perfect scores ($1.0$) are awarded exclusively within a balanced threshold ($0.725 \le \text{similarity} \le 0.775$).
     * Deviations below $0.725$ drop linearly, penalizing exercises that are too disconnected from what was taught.
     * Deviations above $0.775$ drop symmetrically, penalizing repetitive copy-paste tasks that fail to challenge the student.

### 2. Conceptual Continuity Metric
   * Measures the sequential narrative arc and flow of the curriculum across the entire course run (inspired by the Learnpack `COH-02` standard).
   * Processes all lessons chronologically, prompting the LLM to cleanly isolate newly **introduced** technical terms versus previously **discussed** prerequisites per file.
   * For each sequential step, the metric concatenates all previously taught concepts into a list. It then compares the concepts discussed with all previous consecutive concepts introduced, evaluating whether the lesson successfully build on what was previously discussed.
