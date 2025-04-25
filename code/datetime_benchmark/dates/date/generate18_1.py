# -*- coding: utf-8 -*-
"""
generate18_1.py: Generate a sample of dates

USAGE
python3 generate18_1.py format 10
python3 generate18_1.py format 10 --month_schema "arabic"
python3 generate18_1.py format 10 --month_schema "roman"
python3 generate18_1.py format 10 --month_schema "unambiguous"


"""

# -------
# imports
# -------

from collections import namedtuple
from datetime import date, datetime, time, timedelta
from random import choice
from typing import Any, List, Set, Dict, Tuple, Optional, Union, Iterable, Iterator

# 3rd party
from babel.localedata import locale_identifiers
from babel.dates import format_date

# locals
from random_datetime import random_date
from config import Config
from training_pair import TrainingPair
from custom_formatter import CustomFormatter


# -----
# class
# -----

class Generate:

    """
    Generate a sample of dates for training
    """

    def __init__(self, month_schema : str = "all"):
        """
        :param month_schema: specifies the month formats
            possible values:
            - "all": arabic and roman numerals
            - "arabic": arabic numerals only (1, 2, 3, ...)
            - "roman" : (i, ii, iii, ...)
            - unambiguous : MMM and MMMM
        """

        self.config = Config() # self.default_encoding_character = "?"

        # generate17: CustomFormatter
        self.custom_formatter = CustomFormatter()

        # the core datalake type being generated (see Config.core_pandas_type_map)
        self.model_name = "DATE"
        self.date_model_name = "date" # model required to process the date, currently in def_file/infer_dates/...

        # for NER (named entity resolution)
        self.entity = "date"

        # when the output (value to be predicted) is iso8601, generate the following format
        # NOTE: the preditions of the model must be generated using a fully conformant ISO8601 date:
        # 4-digit year
        # 2-digit month
        # 2-digit day
        # otherwise, at inference time, the datetime.date.fromisoformat(prediction) function will not work
        #self.iso_format_date = "Y-M-d" 
        self.iso_format_date = "YYYY-MM-dd" 

        # time parts for iso8601:dt:start and iso8601:dt:end
        self.start_end_of_day = time(0, 0, 0) 
        self.time_end_of_day = time(23, 59, 59) 

         # generate17.1: iterate on all formats locales available in Babel; currently 789 locales in Babel
        self.all_locales = locale_identifiers() # all locales in Babel


        self.locale_schemas = { "all" : self.all_locales, 
                                "mini.10" : self.config.locales, # 10 basic/common locales
                                "en_US" : ["en_US"],
                                }
        
        # normalisation

        # replace {whitespace} tokens in the formats below with this character
        # important: we don't want to use a space as a whitespace character, because then we cannot parse tokens correctly
        # e.g 01:12:31 da tarde 
        # the above string is not trivual to parse using space as a delimiter, because da tarde belongs together as a single token
        # thus we use a token such as ? to facilitate the parsing
        # -> 01:12:31?a tarde 
        self.whitespace_character = ' ' 

        # {whitespace} token is replaced with the values from whitespace_characters
        # BACKLOG: the 'at' does not get localised
        
        # generate15.py | added "no separator" to generate dates with no spaces between tokens, e.g 111212
        #self.separators = [' ', '.', '/', '-', '#', '|', '']
        # generate17.py: removed no separator, it's too aggressive and generates really tough pairs
        self.separators = [' ', '.', '/', '-', '#', '|']

        # generate12.py: list of tokens used for the patterns
        # generate17.py: added patterns from CustomFormatter
        # {C(day)}        one
        # {O(day)}        first
        # {ON(day)}       1st
        # {X(month)}      IV
        # {X(year)}       MMVII
        self.day_tokens = [ r"{d}", r"{dd}", r"{C(day)}", r"{O(day)}", r"{ON(day)}" ]

        # month tokens
        # generate18_1: month_tokens is a dict with different schemas, allowing control over the month formatting
        # NOTE: {MMM} creates many issues with some locales (weird formats, empty strings, ...)
        # see /Dropbox/programming/python/babel : python3 bug_month_1.py
        self.all_month_tokens = {
            "all" : [ r"{M}", r"{MM}", r"{MMM}", r"{MMMM}", r"{X(month)}" ]
            , "arabic" : [ r"{M}", r"{MM}", r"{MMM}", r"{MMMM}"]
            , "unambiguous" : [ r"{MMM}", r"{MMMM}"]
            , "roman" : [ r"{X(month)}" ]
        }

        # generate18_1: month_tokens is a dict with different schemas, allowing control over the month formatting
        self.set_month_schema(month_schema)
        
        # BACKLOG: year in romand numerals r"{X(year)}"
        # NOTE! don't forget to keep generate16.12 in sync with tokens that have century
        self.year_tokens = [ r"{yy}", r"{yyyy}" ] 

        # doc; https://babel.pocoo.org/en/latest/dates.html#date-fields
        self.format_spec = { 
            
                            # schema day-month: day represented before month
                            "day-month-yy" : [  

                                # day, month, year
                                # 1 digit day
                                r"{day}{separator}{month}{separator}{yy}" 

                                # year, day, month
                                # 1 digit day
                                , r"{yy}{separator}{day}{separator}{month}" 


                            ] # day-month-plain
                            
                            , "day-month-weekday-yy" : [  

                                # day of week, day, month, year
                                # E: Day of week. Use one through three letters for the short day, or four for the full name, or five for the narrow name.
                                # doc: https://babel.pocoo.org/en/latest/dates.html#date-fields
                                r"{E}{whitespace}{day}{separator}{month}{separator}{yy}"
                                , r"{EE}{whitespace}{day}{separator}{month}{separator}{yy}"
                                , r"{EEE}{whitespace}{day}{separator}{month}{separator}{yy}"
                                , r"{EEEE}{whitespace}{day}{separator}{month}{separator}{yy}"   # vrijdag 19 jan. 1990

                            ] # day-month-weekday
                            
                            # schema month-day: month represented before day
                            , "month-day-yy" : [

                                # month, day, year
                                # 1 digit day
                                r"{month}{separator}{day}{separator}{yy}" 

                                 # year, month, day
                                # 1 digit day
                                , r"{yy}{separator}{month}{separator}{day}" 


                            ] # month-day-plain

                            , "month-day-weekday-yy" : [

                                # day of week, e.g Friday 19 Jun 2011
                                # day of week, day, month, year
                                # E: Day of week. Use one through three letters for the short day, or four for the full name, or five for the narrow name.
                                # doc: https://babel.pocoo.org/en/latest/dates.html#date-fields
                                r"{E}{whitespace}{month}{separator}{day}{separator}{yy}"
                                , r"{EE}{whitespace}{month}{separator}{day}{separator}{yy}"
                                , r"{EEE}{whitespace}{month}{separator}{day}{separator}{yy}"
                                , r"{EEEE}{whitespace}{month}{separator}{day}{separator}{yy}"

                                , r"{month}{separator}{E}{whitespace}{day}{separator}{yy}"
                                , r"{month}{separator}{EE}{whitespace}{day}{separator}{yy}"
                                , r"{month}{separator}{EEE}{whitespace}{day}{separator}{yy}"
                                , r"{month}{separator}{EEEE}{whitespace}{day}{separator}{yy}"

                            ] # month-day-weekday

                            # schema day-month: day represented before month
                            , "day-month-yyyy" : [  

                                # day, month, year
                                # 1 digit day
                                r"{day}{separator}{month}{separator}{yyyy}" 

                                # year, day, month
                                # 1 digit day
                                , r"{yyyy}{separator}{day}{separator}{month}" 


                            ] # day-month-plain
                            
                            , "day-month-weekday-yyyy" : [  

                                # day of week, day, month, year
                                # E: Day of week. Use one through three letters for the short day, or four for the full name, or five for the narrow name.
                                # doc: https://babel.pocoo.org/en/latest/dates.html#date-fields
                                r"{E}{whitespace}{day}{separator}{month}{separator}{yyyy}"
                                , r"{EE}{whitespace}{day}{separator}{month}{separator}{yyyy}"
                                , r"{EEE}{whitespace}{day}{separator}{month}{separator}{yyyy}"
                                , r"{EEEE}{whitespace}{day}{separator}{month}{separator}{yyyy}"   # vrijdag 19 jan. 1990

                            ] # day-month-weekday
                            
                            # schema month-day: month represented before day
                            , "month-day-yyyy" : [

                                # month, day, year
                                # 1 digit day
                                r"{month}{separator}{day}{separator}{yyyy}" 

                                 # year, month, day
                                # 1 digit day
                                , r"{yyyy}{separator}{month}{separator}{day}" 


                            ] # month-day-plain

                            , "month-day-weekday-yyyy" : [

                                # day of week, e.g Friday 19 Jun 2011
                                # day of week, day, month, year
                                # E: Day of week. Use one through three letters for the short day, or four for the full name, or five for the narrow name.
                                # doc: https://babel.pocoo.org/en/latest/dates.html#date-fields
                                r"{E}{whitespace}{month}{separator}{day}{separator}{yyyy}"
                                , r"{EE}{whitespace}{month}{separator}{day}{separator}{yyyy}"
                                , r"{EEE}{whitespace}{month}{separator}{day}{separator}{yyyy}"
                                , r"{EEEE}{whitespace}{month}{separator}{day}{separator}{yyyy}"

                                , r"{month}{separator}{E}{whitespace}{day}{separator}{yyyy}"
                                , r"{month}{separator}{EE}{whitespace}{day}{separator}{yyyy}"
                                , r"{month}{separator}{EEE}{whitespace}{day}{separator}{yyyy}"
                                , r"{month}{separator}{EEEE}{whitespace}{day}{separator}{yyyy}"

                            ] # month-day-weekday



                        } # self.format_spec


        self.all_schemas = list(self.format_spec.keys())

        # generate18: dict of possible components and their possible formats
        # required for output "visible_components" (the actual components of the datetime in the output string)
        self.possible_components = {
            "year" : self.year_tokens
            , "month" : self.month_tokens
            , "day" : self.day_tokens
        }

    
    def set_month_schema(self, month_schema : str):
        """
        :param month_schema: specifies the month formats
            possible values:
            - "all": arabic and roman numerals
            - "arabic": arabic numerals only (1, 2, 3, ...)
            - "roman" : (i, ii, iii, ...)
            - unambiguous : MMM and MMMM
        """
        
        if month_schema not in self.all_month_tokens:
            raise ValueError(f"month schema {month_schema} not found")
        
        self.month_tokens = self.all_month_tokens[month_schema]
        self.month_schema = month_schema



    def resolve_dmy_tokens(self, raw_format_spec : str) -> str:

        """
        resolve_dmy_tokens: replace a string with generic tokens "{day} {month} {year}" to a string with implementable tokens
            e.g "{dd} {MMM} {YYYY}"

        
        :param faw_format_spec: a string with generic tokens, e.g "{day} {month} {year}" 

        :return: a string with implementable tokens, e.g "{dd} {MMM} {YYYY}"
        
        """

        # generate17: resolve {day}, {month} and {year} tokens
        assert r"{day}" in raw_format_spec
        assert r"{month}" in raw_format_spec
        

        day_token = choice(self.day_tokens)
        month_token = choice(self.month_tokens)
        

        raw_format_spec = raw_format_spec.replace(r"{day}", day_token)
        raw_format_spec = raw_format_spec.replace(r"{month}", month_token)

        # generate18: {year} no long present in the formats, but we can generalise the code
        if r"{year}" in raw_format_spec:
            year_token = choice(self.year_tokens)
            raw_format_spec = raw_format_spec.replace(r"{year}", year_token)

        return raw_format_spec


    def generate(self
                , output : str
                , num_observations : int
                , start_date : datetime = None
                , schemas : List[str] = None
                , locale_schema : str = None
                ) -> Iterator[ Tuple[ TrainingPair, datetime] ]:

        """

        :param output: what do generate: iso8601, pattern

        :param num_observations: number of dates to generate; each date will be generated in N(locales) and N(format_spec)

        :param start_date: optional; start date(time) of the dates; a default value will be generated if None

        :param schemas: optional; list schemas to be used; at the moment only month-day and day-month are supported
            a schema is a group of formats, grouped according to some logic, e.g day first, month first, etc
            if None, all available schemas are used

        :return: function is a generator -> an iterator of 2-tuples
            1. TrainingPairs (namedtuple)
            2. the input date

        """

        assert isinstance(output, str)

        #print(__file__, ">>", output, num_observations)
        
        # set start date
        # NOTE: datetime with no tzinfo in the constructor, datetime assumes the local timezone of the computer
        # in turn, Babel interprets this as the local timezone of the locale
        # thus, with the current code logic (no tzinfo in the constructor), each locale show's it's own timezone
        if start_date is None:
            start_date = datetime(1990, 1, 1, 0, 0, 0)

        d = start_date

        # generate11: resolve schemas to be used
        # by default, use all schemas available

        if schemas is not None:
            assert type(schemas) is list

            final_schemas = []

            # check we know this schema
            for schema in schemas:
                # NOTE: simply ignore it if we can't handle it
                #assert schema in self.format_spec
                if schema in self.format_spec:
                    final_schemas.append(schema)
        
            schemas = final_schemas
        else:
            schemas = self.all_schemas

        
        num_schemas = len(schemas)
        if num_schemas == 0:
            raise RuntimeError(f"no schemas supported")

        # generate12: resolve locales to be used
        locale_schema_name = "all"
        
        if locale_schema is not None:
            if locale_schema not in self.locale_schemas:
                raise RuntimeError(f"locale_schema '{locale_schema}' not found in {self.locale_schemas.keys()}")
            locale_schema_name = locale_schema

        locales = self.locale_schemas[locale_schema_name]


        

        # built-in formats
        for idx in range(0, num_observations):
            
            # generate16: generate a random date in the range [start_date; ...] with UTC timezone
            d = random_date(start_date)
         
            # generate11: iterate on requested schemas

            # generate16: randomised output
            schema = choice(schemas)
            locale = choice(locales)
                
            # iterate on date formats in this schema
            raw_format_spec1 = choice(self.format_spec[schema])

            # generate17: resolve {day}, {month} and {year} tokens
            raw_format_spec = self.resolve_dmy_tokens(raw_format_spec1)

            # iterate on separators
            separator_character = choice(self.separators)

            # replace {whitespace} token with some token
            format_spec = raw_format_spec.replace(r"{whitespace}", self.whitespace_character)
            
            # replace {separator} token with some token
            format_spec = format_spec.replace(r"{separator}", separator_character)

            # generate 17: apply custom formatting 
            # NOTE: custom_formatter also applies Babel formatting
            input_str_unicode = self.custom_formatter.apply(format_spec, d, locale=locale)
        
            # BUG FIX | edward | 2022-11-25 | generate15 | not all outputs applied normalisation
            # => apply full normalisation
            # 1. unicode
            # 2. tokens (e.g convert .. to .)
            # 3. whitespace (e.g "\u202f" to " ")
            # 4. convert to lower case
            input_str = self.custom_formatter.normalise_string(input_str_unicode)

            # Override: remove short dates comprised only of digits, such as "12121"; this is really too tough at the moment
            # BACKLOG: should this override be relaxed for more generality?
            if len(input_str) < 6 and input_str.isdigit():
                continue

            # different outputs can be specified
            # for NER (named entity resolution)
            if output == "entity": 
                output_str = self.entity

            elif output == "format": 
                output_str = raw_format_spec

            else:
                raise RuntimeError(f"unhandled output '{output}'")
            

            
            yield (TrainingPair(input_str, output_str, locale), d)
            

         



# -----
# main
# -----

if __name__ == "__main__":

    def main():

        from argparse import ArgumentParser

        # --- command line args ---
        cmd_line_parser = ArgumentParser(description='driver for Generate')
        cmd_line_parser.add_argument('output', type=str, default=None, help='iso8601, parsestr, model')
        cmd_line_parser.add_argument('num_observations', type=int, default=None, help='number of observations to generate')
        cmd_line_parser.add_argument('--start_date', type=str, help='start datetime, in ISO861 format', default=None)
        cmd_line_parser.add_argument('--locale_schema', type=str, help='locale schame', default="mini.10")
        cmd_line_parser.add_argument('--schemas', type=str, help='comma separated list if schemas to use', default=None)
        cmd_line_parser.add_argument('--month_schema', type=str, help='month tokens to use (all, arabic, roman, unambiguous)', default="all")
        
        cmd_line_parser.add_argument('--inputs', default=False, dest='inputs', action='store_true', help='only print input sequences')

        cmd_line_parser.add_argument('--debug', default=False, dest='debug', action='store_true', help='debugging')
        args = cmd_line_parser.parse_args()

        # create generator
        generator = Generate(month_schema=args.month_schema)
        generator.debug = args.debug

        # optional: specify start_date
        start_date = datetime.fromisoformat(args.start_date) if args.start_date is not None else None

        # optional: specify schema(s)
        schemas = None
        if args.schemas is not None:
            schemas = args.schemas.split(",")

        results = generator.generate(args.output
                                , args.num_observations
                                , start_date=start_date
                                , schemas=schemas
                                , locale_schema=args.locale_schema
                                )

        # show output
        first = True
        for idx, (training_pair, _) in enumerate(results, start=1):
            if not args.inputs:
                print(training_pair)
            else:
                print(training_pair.input)

    main()    