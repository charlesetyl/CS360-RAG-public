from src.rag import answer_gen
from src.setup.utils import read_config, load_db
from src.setup.sql_database import SQLDatabase
import json
import time

# ANSI escape codes for terminal colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

if __name__ == "__main__":
    config = read_config("./data/config.json")

    # database setup
    db_file_path = "./data/mysql.sql"
    db_name = "rdb"
    db_config = config['MYSQL']
    db_engine = SQLDatabase.from_uri(
        f"mysql+pymysql://{db_config['USER']}:{db_config['PASSWORD']}@{db_config['HOST']}/{db_name}"
    )
    load_db(db_engine, db_file_path)

    model_name = "qwen2.5-coder:1.5b"

    # load questions and answers from jsonl file
    questions = []
    with open("./data/questions.jsonl", "r") as f:
        for line in f:
            questions.append(json.loads(line))

    total_questions = len(questions)
    score = 0
    correct_time = 0.0
    correct_count = 0

    for item in questions:
        question_text = item["question"]
        expected_answer = item.get("answer", None)
        
        # Run three attempts for each question.
        correct_found = False
        best_time = None
        
        for attempt in range(3):
            start = time.time()
            generated_answer = answer_gen(question_text, db_engine, model_name)
            elapsed = time.time() - start
            
            # Check if the generated answer is correct.
            if expected_answer is not None and expected_answer == generated_answer:
                correct_found = True
                # Record the minimum correct time.
                if best_time is None or elapsed < best_time:
                    best_time = elapsed
        
        # Check the result of the three attempts.
        if expected_answer is not None:
            if correct_found:
                print(f"Question: {question_text} -> {GREEN}Correct{RESET}")
                score += 1
                correct_time += best_time
                correct_count += 1
            else:
                print(f"Question: {question_text} -> {RED}Incorrect{RESET}")
        else:
            print(f"Question: {question_text} -> No answer provided.")
    
    print(f"Final Score: {score} out of {total_questions}")
    if correct_count > 0:
        avg_time = correct_time / correct_count
        print(f"Average time for correct answers: {avg_time:.2f} seconds over {correct_count} correct answers")
    else:
        print("No correct answers, average time cannot be computed.")