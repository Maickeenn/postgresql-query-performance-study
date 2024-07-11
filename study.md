## Setup PostgreSQL with Docker

1. Create a Docker container for PostgreSQL:

    ```bash
    docker run --name postgres-performance-study -e POSTGRES_PASSWORD=mysecretpassword -d postgres
    ```

2. Access the PostgreSQL instance:

    ```bash
    docker exec -it postgres-performance-study psql -U postgres
    ```

3. Create the necessary database and tables:

    ```sql
    CREATE DATABASE performance_study;
    \c performance_study;

    CREATE TABLE title_basics (
        tconst VARCHAR(10) NOT NULL CONSTRAINT pk_title_basics PRIMARY KEY,
        titletype VARCHAR(20),
        primarytitle VARCHAR(500),
        originaltitle VARCHAR(500),
        isadult BOOLEAN,
        startyear INTEGER,
        endyear INTEGER,
        runtimeminutes INTEGER,
        genres VARCHAR(200)
    );

    CREATE TABLE name_basics (
        nconst VARCHAR(10) NOT NULL CONSTRAINT pk_name_basics PRIMARY KEY,
        primaryname VARCHAR(110),
        birthyear INTEGER,
        deathyear INTEGER,
        primaryprofession VARCHAR(200),
        knownfortitles VARCHAR(100)
    );

    CREATE TABLE title_principals (
        tconst VARCHAR(10) NOT NULL REFERENCES title_basics,
        ordering INTEGER NOT NULL,
        nconst VARCHAR(10) NOT NULL REFERENCES name_basics,
        category VARCHAR(100),
        job VARCHAR(300),
        characters VARCHAR(500),
        PRIMARY KEY (tconst, ordering, nconst)
    );
    ```

## Data Insertion Script

Use the provided Python script to create tables and insert sample data into the tables. Download the script here: [insertion_script.py](insertion_script.py)

**Note:** Adjust the number of actors, movies, and threads in the Python script according to your requirements. The default values are set to 100,000 actors, 20,000,000 movies, and 24 threads.
```python
# Example of where to change the values in insertion_script.py

# Insert 100,000 actors
num_actors = 100000  # Change this value as needed

# Insert 20,000,000 movies using 24 threads
insert_random_data(20000000, 24)  # Change the number of movies and threads as needed
```


## Queries for Performance Testing

The following queries are used to test the performance. Note that different pairs of actors are used to avoid caching effects:

### Query to Find Shared Movies by Specific Actors Using Joins

```sql
EXPLAIN ANALYZE
SELECT 
    tb.tconst,
    tb.primarytitle,
    tb.originaltitle,
    tb.startyear,
    tb.runtimeminutes,
    tb.genres
FROM 
    title_basics tb
JOIN 
    title_principals tp1 ON tb.tconst = tp1.tconst
JOIN 
    title_principals tp2 ON tb.tconst = tp2.tconst
WHERE 
    tb.titletype = 'movie'
    AND tp1.nconst = 'nm00000955'
    AND tp2.nconst = 'nm18960716'
    AND tp1.category IN ('actor', 'actress')
    AND tp2.category IN ('actor', 'actress');
```

### Query to Find Shared Movies by Specific Actors Using Group By

```sql
EXPLAIN ANALYZE
SELECT *
FROM title_basics as basics
JOIN (SELECT title_principals.tconst
       FROM title_principals
       WHERE (nconst = 'nm00001667' OR nconst = 'nm66549147')
         AND (category = 'actor' OR category = 'actress')
       GROUP BY title_principals.tconst
       HAVING COUNT(*) = 2) as resultTable
ON basics.tconst = resultTable.tconst;
```

## Additional Script for Finding Actors

Use the following script to find pairs of actors who have worked together in more than two films:

```sql
SELECT tp1.nconst AS actor1, tp2.nconst AS actor2, COUNT(*) AS films_together
FROM title_principals tp1
JOIN title_principals tp2 ON tp1.tconst = tp2.tconst
WHERE tp1.nconst < tp2.nconst
AND tp1.category IN ('actor', 'actress')
AND tp2.category IN ('actor', 'actress')
GROUP BY tp1.nconst, tp2.nconst
HAVING COUNT(*) > 2
LIMIT 2;
```

## Results and Analysis

### Clearing Cache

To ensure accurate performance testing, the system and PostgreSQL caches should be cleared between query executions. This can be done using the following commands (Linux):

1. Sync and clear OS cache:

    ```bash
    sudo sync
    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
    ```

2. Restart PostgreSQL:

    ```bash
    sudo systemctl restart postgresql
    ```

### Query Performance

Execute the queries and analyze the results using the following command:

```sql
EXPLAIN (ANALYZE, BUFFERS) <YOUR_QUERY_HERE>;
```

### Example of Execution

```bash
# Sync and clear OS cache
sudo sync
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

# Restart PostgreSQL
sudo systemctl restart postgresql

# Connect to PostgreSQL and run the query
psql -U postgres -d performance_study -c "EXPLAIN (ANALYZE, BUFFERS) <YOUR_QUERY_HERE>"
```

By using different pairs of actors for each query, we ensure that the results are not influenced by PostgreSQL's caching mechanisms. Analyze the output of `EXPLAIN ANALYZE` to compare the performance of both queries.
