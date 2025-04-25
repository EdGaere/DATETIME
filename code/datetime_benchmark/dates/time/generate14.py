# -*- coding: utf-8 -*-
"""
generate14.py: Generate a sample of times

USAGE
python3 generate14.py format 10 --inputs
"""

# -------
# imports
# -------

from collections import namedtuple
from datetime import date, datetime, time, timedelta
from random import choice
from typing import Any, List, Set, Dict, Tuple, Optional, Union, Iterable, Iterator

# 3rd party
from babel.dates import format_time
from pytz import timezone, all_timezones

# locals
from config import Config as DateConfig
from random_datetime import random_utc_datetime
from custom_formatter import CustomFormatter
from normalise_whitespace import NormaliseWhitespace
from normalise_tokens import NormaliseTokens
from normalise_tokens import NormaliseTokens as NormaliseLDMLTokens
from normalise_unicode import NormaliseUnicode
from training_pair import TrainingPair

# -----
# class
# -----

class Generate:

    """
    Generate a sample of dates for training
    """

    def __init__(self):

        self.name = "generate14"

        # the core datalake type being generated (see Config.core_pandas_type_map)
        self.model_name = "TIME"

        # for NER (named entity resolution)
        self.entity = "time"

        # when the output (value to be predicted) is iso8601, generate the following format
        # H: Hour [0-23].
        # see http://babel.pocoo.org/en/latest/dates.html#time-fields
        self.iso_format_date = "H:m:s" 

        # default settings for date machine learning models
        self.date_config = DateConfig()

        self.locales = self.date_config.locales

        # generate14: CustomFormatter
        self.custom_formatter = CustomFormatter()
        
        
        # important: we don't want to use a space as a whitespace character, because then we cannot parse tokens correctly
        # e.g 01:12:31 da tarde 
        # the above string is not trivual to parse using space as a delimiter, because da tarde belongs together as a single token
        # thus we use a token such as ? to facilitate the parsing
        # -> 01:12:31?a tarde 
        self.whitespace_character = ' '

        self.normalise_tokens = NormaliseTokens()
        self.normalise_ldml_tokens = NormaliseLDMLTokens()
        self.normalise_whitespace = NormaliseWhitespace()
        self.normalise_unicode = NormaliseUnicode()

        # generate10.py: Added "no separator" to generate datetimes with no spaces between tokens, e.g 111212
        # generate14: I think no space between time elements hour, minute and second is really too aggressive...
        #self.separators = [ ':', ' ', '' ]
        self.separators = [ ':' ]

        # generate12.py: microsecond formats
        # generate14.py: add curly braces to microsecond foramts for consistency with other generators
        self.microsecond_formats = [ r"{S}", r"{SS}", r"{SSS}", r"{SSSS}", r"{SSSSS}", r"{SSSSSS}"]

        # generate14.py: timezone formats to iterate on
        # doc: https://babel.pocoo.org/en/latest/dates.html#time-fields
        # src:  babel/dates.py/format_timezone at line 1435

        # NOTES
        self.timezone_formats = [r"{z}", r"{zz}", r"{zzz}", r"{zzzz}"
                                , r"{Z}", r"{ZZ}" , r"{ZZZ}", r"{ZZZZ}", r"{ZZZZZ}"
                                
                                , r"{OOOO}"
                                , r"{v}",  r"{vvvv}"
                                , r"{V}",  r"{VV}", r"{VVV}", r"{VVVV}"
                                , r"{X}",  r"{XX}", r"{XXX}", r"{XXXX}", r"{XXXXX}"
                                , r"{x}",  r"{xx}", r"{xxx}", r"{xxxx}", r"{xxxxx}"
                                , r"{T}", r"{TT}"
                                ]

        self.time_modifier_formats = [ r"{a}" ]

        # BACKLOG: hour formats K and k (=> https://babel.pocoo.org/en/latest/dates.html#time-fields)
        self.hour_tokens = [ r"{h}", r"{H}" ]

        self.minute_tokens = [ r"{m}", r"{mm}" ]

        self.second_tokens = [ r"{s}", r"{ss}" ]

        # generate12.py: 
        # - microsecond formats are replaced with a {microsecond} token that ultimatly get replaced with one
        # of the 6 formats above
        # - this generalisation implies we can dispense with the {SSS} and {SSSSSS} formats
        self.format_spec_2digit_minute_2digit_second = [  # Hour [1-12] + AM or PM
                            # NOTE: {a} is the period (AM or PM), which is required for short hours (unless it was forgotten)
                              r"{h}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{h}{separator}{mm}{whitespace}{a}" # short, no seconds
                              , r"{h}{separator}{mm}{separator}{ss}{whitespace}{a}" # medium
                              , r"{h}{separator}{mm}{separator}{ss}{whitespace}{a}{whitespace}{timezone}"

                             # generate7:: 12 AM 13:33
                              , r"{h}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{h}{whitespace}{a}{whitespace}{mm}" # short, no seconds
                              , r"{h}{whitespace}{a}{whitespace}{mm}{separator}{ss}" # medium
                              , r"{h}{whitespace}{a}{whitespace}{mm}{separator}{ss}{whitespace}{timezone}"

                            # generate7:: 12AM 13:33
                            # NOTE: removed because the trainer (currently) has no splitter so a possible solution cannot be found

                            
                            #  , r"{h}{a}" # short, no minutes (added generate6)
                            #  , r"{h}{a}{whitespace}{mm}" # short, no seconds
                            #  , r"{h}{a}{whitespace}{mm}{separator}{ss}" # medium
                            #  , r"{h}{a}{whitespace}{mm}{separator}{ss}{whitespace}{z}" # long
                            #  , r"{h}{a}{whitespace}{mm}{separator}{ss}{whitespace}{ZZZZ}" # long
                            #  , r"{h}{a}{whitespace}{mm}{separator}{ss}{whitespace}{Z}" # long
                            #  , r"{h}{a}{whitespace}{mm}{separator}{ss}{whitespace}{zzzz}" # full


                              # Hour [0-23].
                              , r"{H}" # short, no minutes (added generate6)
                              , r"{H}{separator}{mm}" # short, no seconds
                              , r"{H}{separator}{mm}{separator}{ss}" # medium
                              , r"{H}{separator}{mm}{separator}{ss}{whitespace}{timezone}"

                              # generate7: Hour [0-23] + AM or PM
                              , r"{H}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{H}{separator}{mm}{whitespace}{a}" # short, no seconds
                              , r"{H}{separator}{mm}{separator}{ss}{whitespace}{a}" # medium
                              , r"{H}{separator}{mm}{separator}{ss}{whitespace}{a}{whitespace}{timezone}" # long

                              # generate9: 1/10 seconds (S) => 6:19:37.1
                              # {microsecond}: The decisecond (ds) is a unit of time. It is part of the International System of Units. 
                              # A decisecond is 10−1 second. It is one tenth of a second. There are ten deciseconds in one second. 
                              # Hour [1-12]. + AM or PM
                              ,r"{h}{separator}{mm}{separator}{ss}.{microsecond}{whitespace}{a}" # medium
                              ,r"{h}{separator}{mm}{separator}{ss}.{microsecond}{whitespace}{a}{whitespace}{timezone}" # long
                              # Hour [0-23].
                              ,r"{H}{separator}{mm}{separator}{ss}.{microsecond}" # medium
                              ,r"{H}{separator}{mm}{separator}{ss}.{microsecond}{whitespace}{timezone}" # long

                           

                            ]

        # generate8: single digit month
        self.format_spec_1digit_minute_2digit_second = [  # Hour [1-12] + AM or PM
                            # NOTE: {a} is the period (AM or PM), which is required for short hours (unless it was forgotten)
                              r"{h}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{h}{separator}{m}{whitespace}{a}" # short, no seconds
                              , r"{h}{separator}{m}{separator}{ss}{whitespace}{a}" # medium
                              , r"{h}{separator}{m}{separator}{ss}{whitespace}{a}{whitespace}{timezone}" # long

                             # generate7:: 12 AM 13:33
                              , r"{h}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{h}{whitespace}{a}{whitespace}{m}" # short, no seconds
                              , r"{h}{whitespace}{a}{whitespace}{m}{separator}{ss}" # medium
                              , r"{h}{whitespace}{a}{whitespace}{m}{separator}{ss}{whitespace}{timezone}" # long

                            # generate7:: 12AM 13:33
                            # NOTE: removed because the trainer (currently) has no splitter so a possible solution cannot be found

                            
                            #  , r"{h}{a}" # short, no minutes (added generate6)
                            #  , r"{h}{a}{whitespace}{m}" # short, no seconds
                            #  , r"{h}{a}{whitespace}{m}{separator}{ss}" # medium
                            #  , r"{h}{a}{whitespace}{m}{separator}{ss}{whitespace}{z}" # long
                            #  , r"{h}{a}{whitespace}{m}{separator}{ss}{whitespace}{ZZZZ}" # long
                            #  , r"{h}{a}{whitespace}{m}{separator}{ss}{whitespace}{Z}" # long
                            #  , r"{h}{a}{whitespace}{m}{separator}{ss}{whitespace}{zzzz}" # full


                              # Hour [0-23].
                              , r"{H}" # short, no minutes (added generate6)
                              , r"{H}{separator}{m}" # short, no seconds
                              , r"{H}{separator}{m}{separator}{ss}" # medium
                              , r"{H}{separator}{m}{separator}{ss}{whitespace}{timezone}"

                              # generate7: Hour [0-23] + AM or PM
                              , r"{H}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{H}{separator}{m}{whitespace}{a}" # short, no seconds
                              , r"{H}{separator}{m}{separator}{ss}{whitespace}{a}" # medium
                              , r"{H}{separator}{m}{separator}{ss}{whitespace}{a}{whitespace}{timezone}" 

                              # generate9: 1/10 seconds (S) => 6:19:37.1
                              # {microsecond}: The decisecond (ds) is a unit of time. It is part of the International System of Units. 
                              # A decisecond is 10−1 second. It is one tenth of a second. There are ten deciseconds in one second. 
                              # Hour [1-12]. + AM or PM
                              ,r"{h}{separator}{m}{separator}{ss}.{microsecond}{whitespace}{a}" # medium
                              ,r"{h}{separator}{m}{separator}{ss}.{microsecond}{whitespace}{a}{whitespace}{timezone}"
                              
                              # Hour [0-23].
                              ,r"{H}{separator}{m}{separator}{ss}.{microsecond}" # medium
                              ,r"{H}{separator}{m}{separator}{ss}.{microsecond}{whitespace}{timezone}"
                    
                            ]

        
        self.format_spec_2digit_minute_1digit_second = [  # Hour [1-12] + AM or PM
                            # NOTE: {a} is the period (AM or PM), which is required for short hours (unless it was forgotten)
                              r"{h}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{h}{separator}{mm}{whitespace}{a}" # short, no seconds
                              , r"{h}{separator}{mm}{separator}{s}{whitespace}{a}" # medium
                              , r"{h}{separator}{mm}{separator}{s}{whitespace}{a}{whitespace}{timezone}"

                             # generate7:: 12 AM 13:33
                              , r"{h}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{h}{whitespace}{a}{whitespace}{mm}" # short, no seconds
                              , r"{h}{whitespace}{a}{whitespace}{mm}{separator}{s}" # medium
                              , r"{h}{whitespace}{a}{whitespace}{mm}{separator}{s}{whitespace}{timezone}" # long

                            # generate7:: 12AM 13:33
                            # NOTE: removed because the trainer (currently) has no splitter so a possible solution cannot be found

                            
                            #  , r"{h}{a}" # short, no minutes (added generate6)
                            #  , r"{h}{a}{whitespace}{mm}" # short, no seconds
                            #  , r"{h}{a}{whitespace}{mm}{separator}{s}" # medium
                            #  , r"{h}{a}{whitespace}{mm}{separator}{s}{whitespace}{z}" # long
                            #  , r"{h}{a}{whitespace}{mm}{separator}{s}{whitespace}{ZZZZ}" # long
                            #  , r"{h}{a}{whitespace}{mm}{separator}{s}{whitespace}{Z}" # long
                            #  , r"{h}{a}{whitespace}{mm}{separator}{s}{whitespace}{zzzz}" # full


                              # Hour [0-23].
                              , r"{H}" # short, no minutes (added generate6)
                              , r"{H}{separator}{mm}" # short, no seconds
                              , r"{H}{separator}{mm}{separator}{s}" # medium
                              , r"{H}{separator}{mm}{separator}{s}{whitespace}{timezone}" # long

                              # generate7: Hour [0-23] + AM or PM
                              , r"{H}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{H}{separator}{mm}{whitespace}{a}" # short, no seconds
                              , r"{H}{separator}{mm}{separator}{s}{whitespace}{a}" # medium
                              , r"{H}{separator}{mm}{separator}{s}{whitespace}{a}{whitespace}{timezone}" # long

                              # generate9: 1/10 seconds (S) => 6:19:37.1
                              # {microsecond}: The decisecond (ds) is a unit of time. It is part of the International System of Units. 
                              # A decisecond is 10−1 second. It is one tenth of a second. There are ten deciseconds in one second. 
                              # Hour [1-12]. + AM or PM
                              ,r"{h}{separator}{mm}{separator}{s}.{microsecond}{whitespace}{a}" # medium
                              ,r"{h}{separator}{mm}{separator}{s}.{microsecond}{whitespace}{a}{whitespace}{timezone}" # long

                              # Hour [0-23].
                              ,r"{H}{separator}{mm}{separator}{s}.{microsecond}" # medium
                              ,r"{H}{separator}{mm}{separator}{s}.{microsecond}{whitespace}{timezone}" # long

                            ]

        # generate8: single digit month
        self.format_spec_1digit_minute_1digit_second = [  # Hour [1-12] + AM or PM
                            # NOTE: {a} is the period (AM or PM), which is required for short hours (unless it was forgotten)
                              r"{h}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{h}{separator}{m}{whitespace}{a}" # short, no seconds
                              , r"{h}{separator}{m}{separator}{s}{whitespace}{a}" # medium
                              , r"{h}{separator}{m}{separator}{s}{whitespace}{a}{whitespace}{timezone}" # long

                             # generate7:: 12 AM 13:33
                              , r"{h}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{h}{whitespace}{a}{whitespace}{m}" # short, no seconds
                              , r"{h}{whitespace}{a}{whitespace}{m}{separator}{s}" # medium
                              , r"{h}{whitespace}{a}{whitespace}{m}{separator}{s}{whitespace}{timezone}" # long

                            # generate7:: 12AM 13:33
                            # NOTE: removed because the trainer (currently) has no splitter so a possible solution cannot be found

                            
                            #  , r"{h}{a}" # short, no minutes (added generate6)
                            #  , r"{h}{a}{whitespace}{m}" # short, no seconds
                            #  , r"{h}{a}{whitespace}{m}{separator}{s}" # medium
                            #  , r"{h}{a}{whitespace}{m}{separator}{s}{whitespace}{z}" # long
                            #  , r"{h}{a}{whitespace}{m}{separator}{s}{whitespace}{ZZZZ}" # long
                            #  , r"{h}{a}{whitespace}{m}{separator}{s}{whitespace}{Z}" # long
                            #  , r"{h}{a}{whitespace}{m}{separator}{s}{whitespace}{zzzz}" # full


                              # Hour [0-23].
                              , r"{H}" # short, no minutes (added generate6)
                              , r"{H}{separator}{m}" # short, no seconds
                              , r"{H}{separator}{m}{separator}{s}" # medium
                              , r"{H}{separator}{m}{separator}{s}{whitespace}{timezone}" # long

                              # generate7: Hour [0-23] + AM or PM
                              , r"{H}{whitespace}{a}" # short, no minutes (added generate6)
                              , r"{H}{separator}{m}{whitespace}{a}" # short, no seconds
                              , r"{H}{separator}{m}{separator}{s}{whitespace}{a}" # medium
                              , r"{H}{separator}{m}{separator}{s}{whitespace}{a}{whitespace}{timezone}" # long

                              # generate9: 1/10 seconds (S) => 0:0:0.0
                              # {microsecond}: The decisecond (ds) is a unit of time. It is part of the International System of Units. 
                              # A decisecond is 10−1 second. It is one tenth of a second. There are ten deciseconds in one second. 
                              # Hour [1-12]. + AM or PM
                              ,r"{h}{separator}{m}{separator}{s}.{microsecond}{whitespace}{a}" # medium
                              ,r"{h}{separator}{m}{separator}{s}.{microsecond}{whitespace}{a}{whitespace}{timezone}" # long

                              # Hour [0-23].
                              ,r"{H}{separator}{m}{separator}{s}.{microsecond}" # medium
                              ,r"{H}{separator}{m}{separator}{s}.{microsecond}{whitespace}{timezone}" # long
                            ]


        
        self.format_specs = [
                            self.format_spec_2digit_minute_2digit_second
                            , self.format_spec_1digit_minute_2digit_second
                            , self.format_spec_2digit_minute_1digit_second
                            , self.format_spec_1digit_minute_1digit_second
                            ]

        

        
       
    def generate(self
                , output : str
                , num_observations : int
                , start_date : datetime = None 
                , schemas : List[str] = None
                , locale_schema : str = None
                ) -> Iterator[ Tuple[ TrainingPair, datetime] ]:

        """

        :param output: what do generate: iso8601, parsestr

        :param num_observations: number of dates to generate; each date will be generated in N(locales) and N(format_spec)

        :param start_date: optional; start date(time) of the dates; a default value will be generated if None

        :return: function is a generator -> an iterator of 2-tuples
            1. TrainingPairs (namedtuple)
            2. the input date

        """

        assert isinstance(output, str)
        
        # set start date
        if start_date is None:
            start_date = datetime(1990, 1, 1, 0, 0, 0)

        d = start_date

        # built-in formats
        for idx in range(0, num_observations):

            # generate11: generate a random time in the range [start_date; ...] with UTC timezone
            dt_utc = random_utc_datetime(start_date)

            # generate11: iterate on timezones
            # NOTE: calls to astimezone() on certain dates generate OverflowError errors
            # HACK: select another timezone if this conversion does not work
            d = None
            while d is None:
                
                this_timezone_name = choice(all_timezones)
                try:
                    this_timezone =  timezone(this_timezone_name)

                    # move the UCT datetime to this timezone
                    d = dt_utc.astimezone(this_timezone)
                
                except OverflowError as e:
                    pass

            
         
            locale = choice(self.locales)
                
            # generate8: iterate on 1-digit and 2-digit minutes
            format_spec_list = choice(self.format_specs)
            raw_format_spec = choice(format_spec_list)
            separator_character = choice(self.separators)

            # generate12: iterate on microsecond format
            microsecond_format = choice(self.microsecond_formats)

            # generate14: iterate on timezone formats
            timezone_format = choice(self.timezone_formats)
                        
            # {whitespace} token is replaced with the values from whitespace_characters
            format_spec = raw_format_spec.replace(r"{whitespace}", self.whitespace_character)

            # replace {separator} token with some token
            format_spec = format_spec.replace(r"{separator}", separator_character)

            # generate12: replace {microsecond} token with some token
            # NOTE: microsecond_format already contains encapsulating curly braces
            format_spec = format_spec.replace(r"{microsecond}", microsecond_format)

            # generate14: replace {timezone} token with some token
            # NOTE: microsecond_format already contains encapsulating curly braces
            format_spec = format_spec.replace(r"{timezone}", timezone_format)

            # generate 17: apply custom formatting before Babel
            # NOTE: custom_formatter also applies Babel formatting
            input_str_unicode = self.custom_formatter.apply(format_spec, d, locale=locale)
        
            # BUG FIX | edward | 2022-11-25 | generate10 | not all outputs applied normalisation
            # => apply full normalisation
            # 1. unicode
            # 2. tokens (e.g convert .. to .)
            # 3. whitespace (e.g "\u202f" to " ")
            # 4. convert to lower case

            # mod | edward | 2023-03-07 | for normalisation of the input string, use the normalisation in custom formatter 
            #input_str = self.normalise_whitespace.normalise(self.normalise_tokens.normalise(self.normalise_unicode.normalise(input_str_unicode))).lower()
            input_str = self.custom_formatter.normalise_string(input_str_unicode)

            # the output can be specified
            # for NER (named entity resolution)
            if output == "entity": 
                output_str = self.entity

            elif output == "format": 
                output_str = format_spec


         

            else:
                raise RuntimeError(f"unhandled output '{output}'")
            

            yield (TrainingPair(input_str, output_str, locale), d)

# -----
# main
# -----

if __name__ == "__main__":

    from argparse import ArgumentParser

    def main():

        # --- command line args ---
        cmd_line_parser = ArgumentParser(description='driver for Generate')
        cmd_line_parser.add_argument('output', type=str, default=None, help='iso8601, parsestr, model')
        cmd_line_parser.add_argument('num_observations', type=int, default=None, help='number of observations to generate')
        
        cmd_line_parser.add_argument('--start_date', type=str, help='start datetime', default=None)
        cmd_line_parser.add_argument('--inputs', default=False, dest='inputs', action='store_true', help='only print input sequences')

        cmd_line_parser.add_argument('--debug', default=False, dest='debug', action='store_true', help='debugging')
        args = cmd_line_parser.parse_args()

        # create generator
        generator = Generate()
        generator.debug = args.debug

        start_date = datetime.fromisoformat(args.start_date) if args.start_date is not None else None
        print(f"start_date : {start_date}")

        results = generator.generate(args.output, args.num_observations, start_date=start_date)

        # show output
        for idx, (training_pair, _) in enumerate(results, start=1):
            if not args.inputs:
                print(training_pair)
            else:
                print(training_pair.input)

        
    main()