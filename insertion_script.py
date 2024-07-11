import psycopg2
from faker import Faker
import random
import logging
import time
import csv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Faker for generating random data
fake = Faker()

# Function to create temporary CSV files
def create_temp_csv(file_path, data, headers):
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)

# Function to load data from CSV to the database and remove the file after insertion
def copy_from_csv(file_path, table_name, columns, cur):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            cur.copy_expert(f"COPY {table_name} ({', '.join(columns)}) FROM STDIN WITH CSV HEADER", file)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# Function to create a list of actors
def generate_actors(num_actors):
    actors = {}
    actor_data = []
    for _ in range(num_actors):
        nconst = fake.unique.bothify(text='nm########')
        primaryname = fake.name()
        birthyear = fake.year()
        deathyear = None if random.choice([True, False]) else fake.year()
        primaryprofession = ','.join(fake.words(nb=3, ext_word_list=None, unique=True))
        knownfortitles = ','.join(fake.words(nb=3, ext_word_list=None, unique=True))
        actors[nconst] = (nconst, primaryname, birthyear, deathyear, primaryprofession, knownfortitles)
        actor_data.append((nconst, primaryname, birthyear, deathyear, primaryprofession, knownfortitles))
    return actors, actor_data

# Function to generate random data for the tables
def generate_data(batch_size, actors, actor_pairs, actor_keys):
    categories = [
        'actor', 'actress', 'archive_footage', 'archive_sound', 'cinematographer',
        'composer', 'director', 'editor', 'producer', 'production_designer', 'self', 'writer'
    ]

    movie_data = []
    principal_data = []

    for j in range(batch_size):
        tconst = fake.unique.bothify(text='tt########')
        titletype = 'movie'
        primarytitle = fake.catch_phrase()
        originaltitle = primarytitle
        isadult = fake.boolean()
        startyear = fake.year()
        endyear = None if random.choice([True, False]) else fake.year()
        runtimeminutes = random.randint(60, 180)
        genres = ','.join(fake.words(nb=3, ext_word_list=None, unique=True))

        movie_data.append((tconst, titletype, primarytitle, originaltitle, isadult, startyear, endyear, runtimeminutes, genres))

        num_actors = random.randint(10, 50)
        ordering = 1

        # Adding pairs of actors who act together in multiple movies
        if j < batch_size * 0.1:  # 10% of movies will have two actors acting together
            actor_pair = random.choice(actor_pairs)
            for nconst in actor_pair:
                category = random.choice(categories)
                job = None if category in ['actor', 'actress', 'self'] else fake.job()
                characters = fake.catch_phrase() if category in ['actor', 'actress'] else None
                principal_data.append((tconst, ordering, nconst, category, job, characters))
                ordering += 1

        for _ in range(num_actors):
            nconst = random.choice(actor_keys)
            category = random.choice(categories)
            job = None if category in ['actor', 'actress', 'self'] else fake.job()
            characters = fake.catch_phrase() if category in ['actor', 'actress'] else None
            principal_data.append((tconst, ordering, nconst, category, job, characters))
            ordering += 1

    return movie_data, principal_data

# Function to insert data using COPY
def insert_data(batch_id, batch_size, actors, actor_pairs, actor_keys):
    logging.info(f"Starting data generation for batch {batch_id}")
    movie_data, principal_data = generate_data(batch_size, actors, actor_pairs, actor_keys)
    logging.info(f"Data generated for batch {batch_id}, starting insertion")
    with psycopg2.connect(
        dbname="performance_study",
        user="postgres",
        password="mysecretpassword",
        host="localhost",
        port="5432"
    ) as conn:
        with conn.cursor() as cur:
            movie_file_path = f'temp_movie_data_{batch_id}.csv'
            principal_file_path = f'temp_principal_data_{batch_id}.csv'

            create_temp_csv(movie_file_path, movie_data, ["tconst", "titletype", "primarytitle", "originaltitle", "isadult", "startyear", "endyear", "runtimeminutes", "genres"])
            create_temp_csv(principal_file_path, principal_data, ["tconst", "ordering", "nconst", "category", "job", "characters"])

            copy_from_csv(movie_file_path, "title_basics", ["tconst", "titletype", "primarytitle", "originaltitle", "isadult", "startyear", "endyear", "runtimeminutes", "genres"], cur)
            copy_from_csv(principal_file_path, "title_principals", ["tconst", "ordering", "nconst", "category", "job", "characters"], cur)

            logging.info(f"Batch {batch_id} successfully inserted")
            conn.commit()
            logging.info(f"Batch {batch_id} committed")

# Function to insert actors into the name_basics table
def insert_actors(actor_data):
    logging.info("Starting insertion of actors into the name_basics table")
    with psycopg2.connect(
        dbname="performance_study",
        user="postgres",
        password="mysecretpassword",
        host="localhost",
        port="5432"
    ) as conn:
        with conn.cursor() as cur:
            actor_file_path = 'temp_actor_data.csv'
            create_temp_csv(actor_file_path, actor_data, ["nconst", "primaryname", "birthyear", "deathyear", "primaryprofession", "knownfortitles"])
            copy_from_csv(actor_file_path, "name_basics", ["nconst", "primaryname", "birthyear", "deathyear", "primaryprofession", "knownfortitles"], cur)
            conn.commit()
            logging.info("Actor insertion completed")

# Main function to parallelize data insertion
def insert_random_data(num_movies, num_threads):
    batch_size = 1000  # Reduced batch size to 1,000
    total_batches = (num_movies + batch_size - 1) // batch_size
    num_actors = 100000  # Setting a large number of actors
    logging.info("Generating list of actors...")
    actors, actor_data = generate_actors(num_actors)
    logging.info(f"{num_actors} actors generated.")

    insert_actors(actor_data)  # Insert actors into the name_basics table

    # Measuring time to generate actor_pairs
    logging.info("Starting generation of actor_pairs...")
    start_time = time.time()
    actor_keys = list(actors.keys())
    actor_pairs = [(random.choice(actor_keys), random.choice(actor_keys)) for _ in range(num_actors // 2)]
    end_time = time.time()
    logging.info(f"Time to generate actor_pairs: {end_time - start_time:.2f} seconds")

    logging.info("Starting movie processing...")
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(total_batches):
            futures.append(executor.submit(insert_data, i + 1, batch_size, actors, actor_pairs, actor_keys))

        for future in as_completed(futures):
            future.result()
            logging.info("Thread finished")

start_time = time.time()

# Insert 20,000,000 movies using 24 threads
insert_random_data(20000000, 24)

end_time = time.time()
logging.info(f"Total execution time: {(end_time - start_time) / 3600:.2f} hours")
