
# Performance Results of PostgreSQL Queries

This document presents the results of a performance study comparing two different SQL queries on a PostgreSQL database. The study involves executing queries to find movies featuring specific actors and analyzing the performance metrics provided by `EXPLAIN ANALYZE`.

## Queries Executed

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

## Performance Results

### Query to Find Shared Movies by Specific Actors Using Joins

```plaintext
Nested Loop  (cost=37283.61..37342.34 rows=1 width=106) (actual time=399.282..400.611 rows=3 loops=1)
  ->  Merge Join  (cost=37283.05..37291.01 rows=6 width=22) (actual time=398.848..399.004 rows=3 loops=1)
        Merge Cond: ((tp1.tconst)::text = (tp2.tconst)::text)
        ->  Sort  (cost=18641.52..18643.50 rows=790 width=11) (actual time=7.196..7.221 rows=762 loops=1)
              Sort Key: tp1.tconst
              Sort Method: quicksort  Memory: 42kB
              ->  Bitmap Heap Scan on title_principals tp1  (cost=56.22..18603.50 rows=790 width=11) (actual time=0.643..6.754 rows=762 loops=1)
                    Recheck Cond: ((nconst)::text = 'nm00000955'::text)
                    Filter: ((category)::text = ANY ('{actor,actress}'::text[]))
                    Rows Removed by Filter: 3861
                    Heap Blocks: exact=4618
                    ->  Bitmap Index Scan on idx_title_principals_nconst  (cost=0.00..56.02 rows=4727 width=0) (actual time=0.259..0.259 rows=4623 loops=1)
                          Index Cond: ((nconst)::text = 'nm00000955'::text)
        ->  Sort  (cost=18641.52..18643.50 rows=790 width=11) (actual time=391.611..391.630 rows=814 loops=1)
              Sort Key: tp2.tconst
              Sort Method: quicksort  Memory: 44kB
              ->  Bitmap Heap Scan on title_principals tp2  (cost=56.22..18603.50 rows=790 width=11) (actual time=3.074..390.872 rows=814 loops=1)
                    Recheck Cond: ((nconst)::text = 'nm18960716'::text)
                    Filter: ((category)::text = ANY ('{actor,actress}'::text[]))
                    Rows Removed by Filter: 3863
                    Heap Blocks: exact=4676
                    ->  Bitmap Index Scan on idx_title_principals_nconst  (cost=0.00..56.02 rows=4727 width=0) (actual time=1.674..1.674 rows=4684 loops=1)
                          Index Cond: ((nconst)::text = 'nm18960716'::text)
  ->  Index Scan using idx_title_basics_tconst on title_basics tb  (cost=0.56..8.55 rows=1 width=106) (actual time=0.534..0.534 rows=1 loops=3)
        Index Cond: ((tconst)::text = (tp1.tconst)::text)
        Filter: ((titletype)::text = 'movie'::text)
Planning Time: 0.318 ms
Execution Time: 400.637 ms
```

### Query to Find Shared Movies by Specific Actors Using Group By

```plaintext
Nested Loop  (cost=36968.99..37067.18 rows=8 width=128) (actual time=484.339..485.160 rows=3 loops=1)
  ->  GroupAggregate  (cost=36968.43..36998.56 rows=8 width=11) (actual time=483.767..483.945 rows=3 loops=1)
        Group Key: title_principals.tconst
        Filter: (count(*) = 2)
        Rows Removed by Filter: 1569
        ->  Sort  (cost=36968.43..36972.21 rows=1514 width=11) (actual time=483.664..483.703 rows=1575 loops=1)
              Sort Key: title_principals.tconst
              Sort Method: quicksort  Memory: 85kB
              ->  Bitmap Heap Scan on title_principals  (cost=112.81..36888.46 rows=1514 width=11) (actual time=3.174..482.442 rows=1575 loops=1)
                    Recheck Cond: (((nconst)::text = 'nm00001667'::text) OR ((nconst)::text = 'nm66549147'::text))
                    Filter: (((category)::text = 'actor'::text) OR ((category)::text = 'actress'::text))
                    Rows Removed by Filter: 7886
                    Heap Blocks: exact=9451
                    ->  BitmapOr  (cost=112.81..112.81 rows=9454 width=0) (actual time=1.985..1.986 rows=0 loops=1)
                          ->  Bitmap Index Scan on idx_title_principals_nconst  (cost=0.00..56.02 rows=4727 width=0) (actual time=0.336..0.337 rows=4736 loops=1)
                                Index Cond: ((nconst)::text = 'nm00001667'::text)
                          ->  Bitmap Index Scan on idx_title_principals_nconst  (cost=0.00..56.02 rows=4727 width=0) (actual time=1.648..1.648 rows=4730 loops=1)
                                Index Cond: ((nconst)::text = 'nm66549147'::text)
  ->  Index Scan using idx_title_basics_tconst on title_basics basics  (cost=0.56..8.58 rows=1 width=117) (actual time=0.403..0.403 rows=1 loops=3)
        Index Cond: ((tconst)::text = (title_principals.tconst)::text)
Planning Time: 0.123 ms
Execution Time: 485.188 ms
```

## Analysis

### Query to Find Shared Movies by Specific Actors Using Joins

- **Execution Time:** 400.637 ms
- **Planning Time:** 0.318 ms
- **Total Rows Retrieved:** 3
- **Key Operations:**
    - **Nested Loop Join**
    - **Merge Join**
    - **Bitmap Heap Scan**
    - **Index Scan**

### Query to Find Shared Movies by Specific Actors Using Group By

- **Execution Time:** 485.188 ms
- **Planning Time:** 0.123 ms
- **Total Rows Retrieved:** 3
- **Key Operations:**
    - **Nested Loop Join**
    - **GroupAggregate**
    - **Bitmap Heap Scan**
    - **Index Scan**

### Summary


Summary
The study compared the performance of two SQL queries with the same objective: finding movies featuring specific actors. The execution times for the queries were 400.637 ms and 485.188 ms, respectively. Both queries retrieved the same number of rows (3) but involved different key operations.

Performance: The query using joins performed better with an execution time of 400.637 ms compared to 485.188 ms for the query using GROUP BY and HAVING. Although this difference of approximately 85 ms is noticeable, it may not be significant in real-world scenarios with smaller data volumes.

Intuitiveness and Simplicity: The query using joins is more straightforward and easier to understand for those familiar with SQL joins. The GROUP BY and HAVING query, while still readable, introduces additional complexity with the aggregation logic.

Filtering Efficiency: The GROUP BY and HAVING query filters more results before the final join, potentially reducing the amount of data processed in the final steps. This can be beneficial in scenarios with larger datasets, as it reduces the intermediate result set size.

Resource Utilization: Both queries involve similar key operations such as nested loops and index scans. However, the query using GROUP BY and HAVING performs additional sorting and aggregation steps, which could lead to higher resource utilization under certain conditions.

Real-World Relevance: Considering the test scenario involved a significantly larger dataset (20 million movies) than what is typically encountered in real-world applications, the observed performance difference may be even less significant in practice. A difference of 85 ms is unlikely to impact user experience in most applications, especially when dealing with smaller datasets.

In conclusion, while the query using joins demonstrated better performance in this study, both queries are valid approaches for retrieving movies featuring specific actors. The choice between them should consider factors such as dataset size, query complexity, and maintainability.
