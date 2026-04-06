# SQL Data Analyst Agent

> A production-grade, containerized Reinforcement Learning environment for evaluating LLM-powered Data Analysts on real SQL business intelligence tasks.

**OpenEnv Hackathon Submission**

---

## Real-World Utility (Motivation)

This environment is **not a toy game**. It simulates a mission-critical enterprise task: an AI agent querying a production SQL database to extract business intelligence. In real-world enterprises, data analysts spend countless hours writing SQL queries to answer ad-hoc business questions from stakeholders. This environment provides a standardized benchmark to evaluate whether LLM agents can safely and accurately perform this task autonomously, measuring both correctness and efficiency.

The environment implements **production-grade security safeguards** that mirror real enterprise database access controls. Our Layer 5 Security includes a **Mutation Blocker** (regex-based blocking of `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE` operations) and **OOM Protection** (`cursor.fetchmany(50)` instead of `fetchall()` to prevent memory exhaustion on large result sets). A 2-second timeout wrapper prevents runaway queries from consuming resources. These safeguards ensure the agent operates in a read-only sandbox, making this environment suitable for evaluating untrusted LLM agents against real database schemas without risk of data corruption or resource exhaustion.

---

## Environment Design (OpenEnv Spec)

### Observation Space

The agent receives an `Observation` object containing four fields:

| Field | Type | Description |
|-------|------|-------------|
| `schema_info` | `str` | Database schema information (tables, columns, types) |
| `current_question` | `str` | The business question the agent must answer |
| `last_query_result` | `str` | Result from the most recent SQL query execution (markdown table format) |
| `error_message` | `str` | Any error from the last action (empty string if none) |

### Action Space

The agent submits an `Action` object with exactly **one** of two fields:

| Field | Type | Description |
|-------|------|-------------|
| `sql_query` | `Optional[str]` | Execute a SQL query against the database |
| `submit_answer` | `Optional[str]` | Submit a final answer for grading |

**Mutual Exclusivity Enforced**: A Pydantic `@model_validator` ensures the agent provides **exactly one** of `sql_query` or `submit_answer`. Providing both or neither raises a `ValueError`, preventing ambiguous actions and ensuring clean state transitions.

### Reward Shaping

The environment implements precise partial reward signals to guide learning:

| Event | Reward | Episode Ends? |
|-------|--------|---------------|
| Successful, error-free SQL query | `+0.1` | No |
| SQLite syntax error | `-0.1` | No |
| Destructive action detected (mutation blocked) | `-1.0` | **Yes** |
| Step count >= 15 (infinite loop shield) | `-0.5` | **Yes** |
| Correct answer submitted | `+1.0` | **Yes** |
| Incorrect answer submitted | `0.0` | **Yes** |

**Final Score Calculation**: Correctness is primary (score = 0.0 if incorrect). For correct answers, base score is 0.7 with an efficiency bonus up to 0.3 based on fewer steps taken: `final_score = 0.7 + (1 - steps/15) * 0.3`

---

## Tasks & Graders

The environment includes **3 deterministic tasks** of increasing difficulty, each with a ground-truth answer and reference SQL query:

### Easy: User Count
- **Task ID**: `easy_user_count`
- **Question**: "How many users are registered in the system? Provide the total count as a single number."
- **Ground Truth**: `15`
- **SQL Complexity**: Single table `COUNT` query
- **Reference SQL**: `SELECT COUNT(*) FROM users`

### Medium: USA Revenue
- **Task ID**: `medium_usa_revenue`
- **Question**: "What is the total revenue (sum of total_amount) from purchases made by users in the USA? Provide the total as a number (rounded to 2 decimal places if needed)."
- **Ground Truth**: `2423.87`
- **SQL Complexity**: Two-table `JOIN` with `SUM` aggregation filtered by country
- **Reference SQL**: `SELECT ROUND(SUM(p.total_amount), 2) FROM purchases p JOIN users u ON p.user_id = u.user_id WHERE u.country = 'USA'`

### Hard: Top Spender
- **Task ID**: `hard_top_spender`
- **Question**: "Who is the top spender (user with highest total purchase amount)? Provide the username of the user who spent the most money in total."
- **Ground Truth**: `"alice"`
- **SQL Complexity**: Complex query with `JOIN`, `GROUP BY`, `ORDER BY`, and `LIMIT`
- **Reference SQL**: `SELECT u.username FROM users u JOIN purchases p ON u.user_id = p.user_id GROUP BY u.user_id, u.username ORDER BY SUM(p.total_amount) DESC LIMIT 1`

**Grading System**: All graders implement **type-agnostic normalization** (whitespace trimming, lowercasing, numeric rounding to 2 decimal places) and output **deterministic scores between 0.0 and 1.0**. Numeric answers within 0.01 absolute tolerance are considered exact matches; answers within 10% receive partial credit (0.5).

---

## Setup & Usage (Containerized Execution)

### Prerequisites
- Docker installed and running
- (Optional) OpenAI API key for inference

### Build & Run

```bash
# Clone the repository
git clone <repository-url>
cd openenv_sql_analyst

# Build the Docker image
docker build -t openenv-sql-analyst .

# Run the container
docker run -p 7860:7860 openenv-sql-analyst
```

### Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run validation
chmod +x validate.sh
./validate.sh
```

### Validation Gates

The `validate.sh` script runs 4 validation gates:
1. **YAML Check**: Validates `openenv.yaml` spec compliance
2. **Dockerfile Check**: Ensures container configuration is correct
3. **Environment Import**: Verifies all Python modules load correctly
4. **Inference Smoke Test**: Runs the baseline agent and verifies output format

---

## Baseline Inference

The `inference.py` script provides a reference implementation of an LLM agent solving tasks in this environment.

### Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | (required) |
| `API_BASE_URL` | OpenAI-compatible API endpoint | `https://api.openai.com/v1` |
| `MODEL_NAME` | Model identifier | `gpt-4o-mini` |

### Running Inference

```bash
# Set environment variables
export OPENAI_API_KEY="your-api-key"
export MODEL_NAME="gpt-4o-mini"

# Run inference
python inference.py
```

### STDOUT Logging Format

The inference script strictly adheres to the hackathon's required logging format:

```
[START] task=<task_id> env=sql_analyst model=<model_name>
[STEP]  step=<n> action=<action_type>=<value> reward=<r.rr> done=<bool> error=<msg>
[STEP]  step=<n> action=<action_type>=<value> reward=<r.rr> done=<bool> error=<msg>
...
[END]   success=<bool> steps=<n> score=<s.ss> rewards=<r1>,<r2>,...
```

**Example Output**:
```
[START] task=easy_user_count env=sql_analyst model=gpt-4o-mini
[STEP]  step=1 action=sql_query=SELECT COUNT(*) FROM users reward=0.10 done=false error=null
[STEP]  step=2 action=submit_answer=15 reward=1.00 done=true error=null
[END]   success=true steps=2 score=0.96 rewards=0.10,1.00
```

---

## Baseline Scores

Expected baseline performance with `gpt-4o-mini`:

| Task | Difficulty | Expected Steps | Expected Score |
|------|------------|----------------|----------------|
| `easy_user_count` | Easy | 2-3 | 0.90-1.00 |
| `medium_usa_revenue` | Medium | 3-5 | 0.85-0.95 |
| `hard_top_spender` | Hard | 4-7 | 0.75-0.90 |

---

## Architecture

```
openenv_sql_analyst/
├── openenv.yaml          # OpenEnv specification
├── Dockerfile            # Container configuration (python:3.10-slim, port 7860)
├── requirements.txt      # Python dependencies
├── validate.sh           # Pre-submission validation script
├── inference.py          # Baseline LLM agent implementation
├── data/
│   └── mock_data.sql     # SQLite mock database (~50 rows, 3 tables)
└── environment/
    ├── __init__.py       # Package exports
    ├── models.py         # Pydantic schemas (Action, Observation, Reward)
    ├── db_engine.py      # SQLite engine with security safeguards
    ├── tasks.py          # Task definitions (Easy, Medium, Hard)
    ├── graders.py        # Deterministic grading system
    └── env.py            # Main SQLAnalystEnv class
```

---

## Technical Specifications

| Specification | Value |
|---------------|-------|
| Python Version | 3.10 |
| Container Port | 7860 |
| vCPU Limit | 2 |
| Memory Limit | 8 GB |
| Max Runtime | 20 minutes |
| Max Steps per Episode | 15 |
| Query Timeout | 2 seconds |
| Max Fetch Rows | 50 |

---

## License

MIT License

---

## Acknowledgments

Built for the **Meta x Scaler OpenEnv Hackathon** - advancing the frontier of LLM agent evaluation through standardized, production-grade reinforcement learning environments.
