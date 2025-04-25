# -*- coding: utf-8 -*-
"""
iso8601_tasks.py: Various tasks based on an ISO-8601 input datetime


USAGE
python3 iso8601_tasks.py add.day.1 10

# only observations where the month has changed
python3 iso8601_tasks.py add.day.1 10 --same_month -1
"""

# -------
# imports
# -------

from collections import namedtuple
from datetime import date, datetime, time, timedelta
from typing import Any, List, Set, Dict, Tuple, Optional, Union, Iterable, Iterator


# locals
from random_datetime import random_utc_datetime
from training_pair import TrainingPair



# -----
# class
# -----

class Generate:

    """
    Generate a sample of dates for training
    """

    def __init__(self):

        # the core datalake type being generated (see Config.core_pandas_type_map)
        self.model_name = "ISO-8601-TASKS"

      
    def generate(self
                , output : str
                , num_observations : int
                , same_month : Optional[int] = None
                , start_date = None # for compatibility with the generic signature of the generate() function
                , schemas : List[str] = None
                , locale_schema : str = "en_US"
                ) -> Iterator[ Tuple[ TrainingPair, Any] ]:

        """

        :param output: what do generate: pattern

        :param num_observations: amount of numbers to generate; each numner will be generated in various scales, locales, formats, etc.

        :param same_month: define what do to if the month of the output datetime is different to the month of the input datetime
            * 0 or None: all observations are kept, regardless if output month is the same or different from the input month
            
            * 1: only the observations are kept where the output month is the same the input month
            
            * -1: only the observations are kept where the output month is different to the input month
                if the year is different, observation is discarded   

        :param start_date: optional; start date(time) of the dates; a default value will be generated if None

        :return: function is a generator -> an iterator of 2-tuples
            1. TrainingPairs (namedtuple)
            2. the input number

        """


        if same_month is None:
            same_month = 0

        # set start date
        if start_date is None:
            start_date = datetime(1970, 1, 1, 0, 0, 0)
        else:
            if not isinstance(start_date, datetime):
                raise RuntimeError(f"start_date {start_date} is not a datetime")
            
        assert isinstance(output, str)
       
        idx = 0
        while idx != num_observations:

            # NOTE: align with generate16.23 "iso8601" format
            # no microseconds and no timezone => ISO8601 output is '7648-09-12 02:24:13'
            input_dt = random_utc_datetime(start_datetime=start_date, microseconds=False, timezone=False)
            
            # same ISO8601 format as generate16.23, using isoformat()
            input_str = input_dt.isoformat()
            
            if output == "model":
                output_str = self.model_name
            
            elif output == "add.day.1":
                output_dt = input_dt + timedelta(days=1)
                output_str = output_dt.isoformat()

            elif output == "add.day.2":
                output_dt = input_dt + timedelta(days=2)
                output_str = output_dt.isoformat()

            elif output == "add.day.10":
                output_dt = input_dt + timedelta(days=10)
                output_str = output_dt.isoformat()

            elif output == "add.day.20":
                output_dt = input_dt + timedelta(days=20)
                output_str = output_dt.isoformat()

            elif output == "add.day.50":
                output_dt = input_dt + timedelta(days=50)
                output_str = output_dt.isoformat()

            elif output == "add.day.100":
                output_dt = input_dt + timedelta(days=100)
                output_str = output_dt.isoformat()
            
            elif output == "add.day.250":
                output_dt = input_dt + timedelta(days=250)
                output_str = output_dt.isoformat()

            elif output == "subtract.day.1":
                output_dt = input_dt - timedelta(days=1)
                output_str = output_dt.isoformat()

            elif output == "subtract.day.2":
                output_dt = input_dt - timedelta(days=2)
                output_str = output_dt.isoformat()

            else:
                raise NotImplementedError(f"Unhandled output format '{output}'")
            
            # same month filters
            accepted = False
            if same_month == 0:
                accepted = True
            
            elif same_month == 1:
                accepted = input_dt.month == output_dt.month

            elif same_month == -1:
                # NOTE: if the year is different, observation is discarded
                accepted = (input_dt.month != output_dt.month) and (input_dt.year == output_dt.year)

            else:
                raise ValueError(f"Unhandled 'same_month' : {same_month} ({type(same_month)})")



            if not accepted:
                continue
            
            idx += 1
            yield (TrainingPair(input=input_str, output=output_str, locale=None, aux=None), input_dt)


# -----
# main
# -----

if __name__ == "__main__":

    from argparse import ArgumentParser

    def main():

        # --- command line args ---
        cmd_line_parser = ArgumentParser(description='driver for Generates')
        cmd_line_parser.add_argument('output', type=str, default=None, help='iso8601, parsestr, model')
        cmd_line_parser.add_argument('num_observations', type=int, default=None, help='number of observations to generate')

        # parameters
        cmd_line_parser.add_argument('--same_month', type=int, help='define behavior if months are different', default=0)
        cmd_line_parser.add_argument('--locale_schema', type=str, help='locale', default="en_US")
        

        # output
        cmd_line_parser.add_argument('--preview_rows', type=int, help='number of rows to preview', default=None)
        cmd_line_parser.add_argument('--inputs', default=False, dest='inputs', action='store_true', help='show inputs only')
        cmd_line_parser.add_argument('--targets', default=False, dest='targets', action='store_true', help='only show targetsuts in compact form')
        cmd_line_parser.add_argument('--outputs', default=False, dest='outputs', action='store_true', help='show outputs only')
        
        cmd_line_parser.add_argument('--debug', default=False, dest='debug', action='store_true', help='debugging')
        cmd_line_parser.add_argument('--debug2', default=False, dest='debug2', action='store_true', help='debugging')
        args = cmd_line_parser.parse_args()

        assert not (args.inputs and args.outputs)

        # create generator
        generator = Generate()
        generator.debug = args.debug
        generator.debug2 = args.debug2

        results = generator.generate(args.output
                                    , num_observations=args.num_observations
                                    , same_month=args.same_month
                                    )

        # show output
        if args.preview_rows:
            print(f"\nfirst {args.preview_rows} rows")
        first = True
        
        for idx, (training_pair, raw_input_value) in enumerate(results, start=1):

            if args.inputs:
                print(training_pair.input)
            elif args.targets:
                print(training_pair.output)
            elif args.outputs:
                print(training_pair.output)
            else:

                # show a sample from the start
                if first and args.preview_rows is None or idx <= args.preview_rows:
                    print(raw_input_value, "->", training_pair)

                    if idx == args.preview_rows:
                        first = False
                        print(f"\nlast {args.preview_rows}")

                # show a sample from the end
                if not first and idx >= args.num_observations - args.preview_rows:
                    print(raw_input_value, "->", training_pair)

                    #if idx == args.num_observations:
                    #    break

    main()