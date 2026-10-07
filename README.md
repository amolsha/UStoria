# Evaluate–Reason–Repair: An LLM-Based Automated Approach for User Story Quality Evaluation

Welcome to the repository for the paper **"Evaluate–Reason–Repair: An LLM-Based Automated Approach for User Story Quality Evaluation"**. This repository contains the complete implementation of the automated evaluation framework, web application blueprints, backend database, experimental datasets, and reported results.

---

## Repository Architecture

The project is structured as a modular web application utilizing Flask Blueprints for clean separation of concerns:

* **`blueprints/api/`**: Provides RESTful API endpoints for programmatic evaluation and system integration.
* **`blueprints/dashboard/`**: Powers the administrative dashboard and analytics interface for monitoring quality metrics.
* **`blueprints/evaluation/`**: Implements the core **Evaluate–Reason–Repair** pipeline, evaluation forms, and iterative quality improvement logic.
* **`blueprints/projects/`**: Handles multi-project organization and user story grouping.
* **`data/`**: Contains the SQLite database (`evaluations.db`) storing historical evaluations and repair logs.
* **`results/`**: Houses the evaluation datasets and Excel spreadsheets containing the detailed experimental results reported in the paper.

---

## Getting Started

### Prerequisites
* Python 3.12 or higher
* Pip package manager

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com//amolsha/UStoria.git
   cd UStoria
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

---

## Dataset & Experimental Results

Reviewers and researchers can navigate to the **`results/`** directory to inspect the Excel files containing:
* The finalized user story evaluation dataset used in the study.
* User story quality evaluation results
* Reason Adequacy Score (RAS) results.
* Repair Success Rate (RSR) results.

---
