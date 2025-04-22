import json
from tqdm import tqdm

def read_config(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    return config

def load_db(db_engine, db_file_path):


    file=open(db_file_path, "r")
    queries_list = file.readlines()
    db_engine.query("drop database rdb;")
    db_engine.query("create database rdb;")
    db_engine.query("use rdb;")

    for line in tqdm(queries_list):
        db_engine.query(line)
