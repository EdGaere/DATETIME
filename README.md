# DATETIME
A new benchmark to measure LLM reasoning capabilities

## Benchmarks

### a.2
* N : 1000 datetimes
* Input : datetime in natural form, e.g '11th.february.5951 ,1:12:31.446879 +0100'
* Target : ISO-8601 in simplified form without microseconds and without timezone

#### Sample
| input  | target   |
|---|---|
| 11th.february.5951 ,1:12:31.446879 +0100  | 5951-02-11T01:12:31 |
| nineteenth-aug-3037, 1 pm 58:54  | 3037-08-19T13:58:54 |
| 3555-14th-sep ,17:38:24.667 +1200  | 3555-09-14T17:38:24 |
