# PostgreSQL Query Performance Study

This repository contains a performance study comparing two different SQL queries on a PostgreSQL database. The objective is to evaluate the execution time, simplicity, and resource utilization of each query when retrieving movies featuring specific actors.

## Overview

The study involves:
- Setting up a PostgreSQL database using Docker.
- Inserting a large dataset of 20,000,000 movies.
- Executing and analyzing two different queries using `EXPLAIN ANALYZE`.

## Queries

1. **Query using Joins**:
    ```sql
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

2. **Query using Group By and Having**:
    ```sql
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

## Results Summary

- **Execution Time**:
    - Joins: 400.637 ms
    - Group By and Having: 485.188 ms

- **Analysis**:
    - The query using joins performed better with an execution time of 400.637 ms compared to 485.188 ms.
    - The difference in execution time (~85 ms) is not significant in real-world scenarios with smaller data volumes.
    - The query using joins is simpler and more intuitive.
    - The query using `GROUP BY` and `HAVING` filters more results before the final join, which can be beneficial with larger datasets.

## Setup and Execution

1. **Setup PostgreSQL with Docker**:
    ```bash
    docker run --name postgres-performance-study -e POSTGRES_PASSWORD=mysecretpassword -d postgres
    docker exec -it postgres-performance-study psql -U postgres
    ```

2. **Create Database and Tables**:
    ```sql
    CREATE DATABASE performance_study;
    \c performance_study;

    CREATE TABLE title_basics (
        tconst VARCHAR(10) NOT NULL PRIMARY KEY,
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
        nconst VARCHAR(10) NOT NULL PRIMARY KEY,
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

3. **Insert Data**:
    - Use the provided Python script `insertion_script.py` to insert sample data into the tables.

4. **Run Queries and Analyze**:
    - Execute the queries and use `EXPLAIN ANALYZE` to get performance metrics.
    - Compare and analyze the results.

## Additional Information

- For more detailed results and analysis, refer to `performance_results.md`.
- The dataset used for this study is significantly larger than typical real-world datasets to stress test the queries.

## License

This project is licensed under the MIT License.
