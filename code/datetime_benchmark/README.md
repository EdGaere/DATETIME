Instructions for generating new data for DATETIME benchmarks.

edward | 2025-04-22

## NOTES

* Data generated using Python3.12

* Data is randomly generated; you will therefore not be able to reproduce the benchmark data as used on the publication. But you can create new data.

* The data for the experiments in the publication is persisted in the respective folders 

## Python
```
python3.12 -m venv ~/.virtualenvs/datetime_benchmark
source ~/.virtualenvs/datetime_benchmark/bin/activate
export PYTHONPATH=~/code/datetime_benchmark
```


## PACKAGES

You should install the following Python packages:

```
pip3 install Babel==2.9.1
pip3 install num2words==0.5.10
pip3 install roman==3.3
```

For exact reproducibility, the full list of packages is available in requirements.txt.


## DATA GENERATION

### Translation Tasks

Here are the commands for generating new training pairs similar to the DATETIME Translation tasks.

ISO-8601
    
    python3 dates/datetime/generate16.23.py iso8601 1000 --month_schema "unambiguous" --locale_schema en_US --schemas "day-month-yyyy, day-month-weekday-yyyy"

Year

    python3 dates/datetime/generate16.23.py year_int 1000 --month_schema "unambiguous" --locale_schema en_US --schemas "day-month-yyyy, day-month-weekday-yyyy"

Month

    python3 dates/datetime/generate16.23.py month_int 1000 --month_schema "unambiguous" --locale_schema en_US --schemas "day-month-yyyy, day-month-weekday-yyyy"

Day

    python3 dates/datetime/generate16.23.py day_int 1000 --month_schema "unambiguous" --locale_schema en_US --schemas "day-month-yyyy, day-month-weekday-yyyy"

Hour

    python3 dates/datetime/generate16.23.py hour_int 1000 --month_schema "unambiguous" --locale_schema en_US --schemas "day-month-yyyy, day-month-weekday-yyyy"

Minute

    python3 dates/datetime/generate16.23.py minute_int 1000 --month_schema "unambiguous" --locale_schema en_US --schemas "day-month-yyyy, day-month-weekday-yyyy"

Second

    python3 dates/datetime/generate16.23.py second_int 1000 --month_schema "unambiguous" --locale_schema en_US --schemas "day-month-yyyy, day-month-weekday-yyyy"

### Computation Tasks

And here are the commands for generating new training pairs similar to the DATETIME Computation tasks.

Add-1

    python3 special/phd/iso8601_tasks.py add.day.1 1000 --same_month 0 --locale_schema "en_US"

Add-10

    python3 special/phd/iso8601_tasks.py add.day.10 1000 --same_month 0 --locale_schema "en_US"

Add-20

    python3 special/phd/iso8601_tasks.py add.day.20 1000 --same_month 0 --locale_schema "en_US"

Add-50

    python3 special/phd/iso8601_tasks.py add.day.50 1000 --same_month 0 --locale_schema "en_US"

Add-100

    python3 special/phd/iso8601_tasks.py add.day.100 1000 --same_month 0 --locale_schema "en_US"

Add-250

    python3 special/phd/iso8601_tasks.py add.day.250 1000 --same_month 0 --locale_schema "en_US"


### Mixed Tasks

Finally, here are the commands for generating new training pairs similar to the DATETIME Mixed tasks.

Add-1

    python3 special/phd/datetime_natural_form_tasks.py add.day.1 1000 --schemas "day-month-yyyy, day-month-weekday-yyyy" --same_month 0 --locale_schema "en_US" --month_schema "unambiguous"

Add-10

    python3 special/phd/datetime_natural_form_tasks.py add.day.10 1000 --schemas "day-month-yyyy, day-month-weekday-yyyy" --same_month 0 --locale_schema "en_US" --month_schema "unambiguous"

Add-20

    python3 special/phd/datetime_natural_form_tasks.py add.day.20 1000 --schemas "day-month-yyyy, day-month-weekday-yyyy" --same_month 0 --locale_schema "en_US" --month_schema "unambiguous"

Add-50

    python3 special/phd/datetime_natural_form_tasks.py add.day.50 1000 --schemas "day-month-yyyy, day-month-weekday-yyyy" --same_month 0 --locale_schema "en_US" --month_schema "unambiguous"

Add-100

    python3 special/phd/datetime_natural_form_tasks.py add.day.100 1000 --schemas "day-month-yyyy, day-month-weekday-yyyy" --same_month 0 --locale_schema "en_US" --month_schema "unambiguous"

Add-250

    python3 special/phd/datetime_natural_form_tasks.py add.day.250 1000 --schemas "day-month-yyyy, day-month-weekday-yyyy" --same_month 0 --locale_schema "en_US" --month_schema "unambiguous"

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
```
