# DATETIME
A new benchmark to measure LLM translation and computation capabilities.

* Croissant metadata is available in the file DATETIME Croissant - v0.4.4.json

* Code and instructions for generating new data is in code/datetime_benchmark


## Tasks in the Benchmarks

### Measure LLM datetime translation capabilities
* a.2: Translation from natural representation to ISO-8601 representation
* year.2: Extract the year from natural representation and translate to 4 digits
* month.2: Extract the year from natural representation and translate to 2 digits
* day.2: Extract the year from natural representation and translate to 2 digits
* hour.2: Extract the year from natural representation and translate to 2 digits
* minute.2: Extract the year from natural representation and translate to 2 digits
* second.2: Extract the year from natural representation and translate to 2 digits

### Measure LLM datetime computation capabilities
* iso8601.add.day.1.x : Add 1 day to an ISO-8601 datetime and generate a new ISO-8601 datetime
* iso8601.add.day.10.x : Add 10 days to an ISO-8601 datetime and generate a new ISO-8601 datetime
* iso8601.add.day.20.x : Add 20 days to an ISO-8601 datetime and generate a new ISO-8601 datetime
* iso8601.add.day.50.x : Add 50 days to an ISO-8601 datetime and generate a new ISO-8601 datetime
* iso8601.add.day.100.x : Add 100 days to an ISO-8601 datetime and generate a new ISO-8601 datetime
* iso8601.add.day.250.x : Add 250 days to an ISO-8601 datetime and generate a new ISO-8601 datetime

### Measure LLM datetime translation + computation capabilities
* natural_form.add.day.1.x : Add 1 day to a natural representation datetime and generate a new ISO-8601 datetime
* natural_form.add.day.10.x : Add 10 days to a natural representation ISO-8601 datetime and generate a new ISO-8601 datetime
* natural_form.add.day.20.x : Add 20 days to a natural representation ISO-8601 datetime and generate a new ISO-8601 datetime
* natural_form.add.day.50.x : Add 50 days to a natural representation ISO-8601 datetime and generate a new ISO-8601 datetime
* natural_form.add.day.100.x : Add 100 days to a natural representation ISO-8601 datetime and generate a new ISO-8601 datetime
* natural_form.add.day.250.x : Add 250 days to a natural representation ISO-8601 datetime and generate a new ISO-8601 datetime

## Citation
```
@misc{gaere2025datetimenewbenchmarkmeasure,
      title={DATETIME: A new benchmark to measure LLM translation and reasoning capabilities}, 
      author={Edward Gaere and Florian Wangenheim},
      year={2025},
      eprint={2504.16155},
      archivePrefix={arXiv},
      primaryClass={cs.NE},
      url={https://arxiv.org/abs/2504.16155}, 
}
``

