# DATETIME
A new benchmark to measure LLM reasoning capabilities

## Benchmarks

### a.2
* __Number of observations__ : 1000
* __Input__ : datetime in natural form, e.g '11th.february.5951 ,1:12:31.446879 +0100'
  * Only day-month schema, to avoid ambiguity
  * Only 4-digit years, to avoid ambiguity
* __Target__ : ISO-8601 in simplified form without microseconds and without timezone


#### Sample
| input  | target   |
|---|---|
| 11th.february.5951 ,1:12:31.446879 +0100  | 5951-02-11T01:12:31 |
| nineteenth-aug-3037, 1 pm 58:54  | 3037-08-19T13:58:54 |
| 3555-14th-sep ,17:38:24.667 +1200  | 3555-09-14T17:38:24 |
