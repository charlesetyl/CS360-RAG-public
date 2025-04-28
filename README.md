# CS360 RAG Project

### Server Connection

You can connect to the assigned server using the provided IP address and password:

```bash
ssh root@{server IP} -p
```

### Installation Instructions

Once connected to the server, follow the steps below.

**Install Conda:**

```bash
sudo apt update
sudo apt install curl -y
curl -O https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Linux-x86_64.sh
bash ~/Anaconda3-2024.10-1-Linux-x86_64.sh
```

After reconnecting, you should see the conda environment prompt:

```bash
(base) root@cs360-1:~#
```

**Install MySQL:**

```bash
# For Ubuntu
apt install mysql-client-core-8.0
sudo apt install -y mysql-server
```

After installation, create a new database:

```bash
sudo mysql -u root
mysql> CREATE DATABASE rdb;
mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '1234';
mysql> FLUSH PRIVILEGES;
mysql> EXIT;
```

Going forward, connect to MySQL with:

```bash
sudo mysql -u root -p
# (password: 1234)
```

**Clone the CS360 RAG Project Repository:**

```bash
git clone https://github.com/asmath472/CS360-RAG.git
cd CS360-RAG
export PYTHONPATH=.
```
You may apply `export PYTHONPATH=.` for each terminal.

**Set Up the RAG Project Virtual Environment:**

```bash
conda create -n ragproj python=3.9
conda activate ragproj

pip install -r requirements.txt
```

**Install Ollama:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama run qwen2.5-coder:1.5b
```

### Preliminaries

**Large Language Models (LLMs):**

LLMs are deep learning models trained on massive text datasets. They perform various tasks such as question answering, summarization, translation, and code generation.  
In this project, we use `qwen2.5-coder:1.5b`, a small, open-weight LLM that runs locally through the **Ollama** framework. It generates SQL queries based on database schemas and natural language questions.

**Retrieval-Augmented Generation (RAG):**

RAG combines two processes to enhance LLM outputs:

1. **Retrieval**: Fetch relevant data from an external source (e.g., a SQL database).
2. **Generation**: Use the retrieved information alongside the user prompt to produce accurate, grounded responses.

Our RAG system works as follows:

- The LLM takes a **database schema** and a **natural language question** as input.
- It generates a **SQL query** to retrieve the answer from the database.
- The result is **post-processed** and returned as the final output.

### Project Objective

**Your task is to modify the `answer_gen()` function inside `./src/rag.py` so that the RAG system works correctly.**

The workflow:

1. The LLM receives the database schema and the question, then generates a SQL query.
2. The generated query is executed to retrieve an answer.

There are 13 test cases: 2 open and 11 hidden cases.  
You can find the open cases in `./data/question.jsonl`. Note: Three hidden cases are intentionally challenging.

Students are free to modify `answer_gen()` as they see fit, provided the following rules are respected:

1. You must use **only** the `qwen2.5-coder:1.5b` model in the Ollama environment. Accessing external APIs (e.g., OpenAI) is strictly prohibited. Grading will be conducted offline.
2. No additional libraries beyond those listed in `requirements.txt` may be installed.
3. Directly printing answers based on question strings (e.g., via simple `if` statements) is prohibited.
4. Incorporating the hidden test cases into prompts or few-shot examples in any form is forbidden.

### Evaluation and Tips

**Submit your final `rag.py` file for grading.**

Use the following commands to run evaluations:

```bash
# Open test cases
python ./src/main.py

# Hidden test cases
python ./eval/hidden_eval.py
```

*Note*: `hidden_eval.py` restricts any behavior (e.g., print statements) that might reveal hidden test cases. Attempts to "leak" hidden test data into the model input will result in disqualification (score of 0).

**Scoring Breakdown:**

- The total score is 20 points (**capped** at 20 points if 20+ are achieved):
    - **Accuracy (13 Points)**:
        - 1 point per correct answer.
    - **Execution Time (10 Points)**:
        - The average execution time for correct answers will be measured, and points will be awarded according to the table below. If more than 10 questions are answered correctly, points will be calculated based on the fastest responses in order:

        | **Time per Query** | **Points** |
        | --- | --- |
        | <10 sec | 1.00 |
        | <20 sec | 0.75 |
        | <30 sec | 0.50 |
        | <40 sec | 0.25 |
        | >40 sec | 0.00 |

- For multiple answers, answer should be selected by `ORDER BY {answer} DESC LIMIT 1`. For example:
    - For text: Choose the lexicographically **last** string.
    - For numbers: Choose the **largest** value.
- For decimal answers, round(반올림) to three decimal places (e.g., 123.456->123.46).
- Your returned answer must maintain its correct data type.

**Grading Note:**
- Each question will be tested three times.
- If your code produces the correct answer at least once, it will be marked as correct.
- The fastest correct execution time among the three runs will be recorded for timing points.

**Tips:**

1. **Post-processing the LLM output is critical.** Build a parser to refine the generated SQL or answers as needed.
2. **Handling generated results carefully is strongly recommended.**  You might need to fix queries or clean data at the dataframe level.
3. **Set temperature to 0** during generation to ensure consistent output:

```python
response: ChatResponse = chat(model=model_name, options={'temperature': 0}, messages=[
    {
        'role': 'user',
        'content': prompt,
    }
])
```
4. You can run `hidden_eval` individually via `--id`. For example, following code shows how you can examine question number `5` individually:
```bash
python ./eval/hidden_eval.py --id 5
```
