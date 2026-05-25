# Fitness-Metrics

This project uses a Genetic Algorithm (GA) framework to automatically evaluate and optimize the quality of generated educational course files

## Baseline Metric
To unblock the GA loop execution, we have implemented the first version of our automated evaluation metrics:

1. **Readability Metric:**
   * Evaluates text complexity on a 1–5 scale.
   * Uses word counts and character-to-word density to ensure content is substantial but accessible.

3. **Structural Heuristics Metric:**
   * Evaluates the layout of the course on a 1–5 scale.
   * Tracks Markdown header hierarchy (`#`, `##`, `###`) to ensure proper organization and penalize skipped formatting levels.
