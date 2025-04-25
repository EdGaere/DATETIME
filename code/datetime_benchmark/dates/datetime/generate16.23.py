# -*- coding: utf-8 -*-
"""
generate16.23.py: Generate datetimes for DATETIME benchmark

USAGE
python3 generate16.23.py iso8601 1000 --month_schema "unambiguous" --locale_schema en_US --schemas "day-month-yyyy, day-month-weekday-yyyy"

"""

# -------
# imports
# -------

from datetime import date, datetime, time, timedelta
from random import choice, uniform, randint
from re import compile
from typing import Any, List, Set, Dict, Tuple, Optional, Union, Iterable, Iterator

# 3rd party
from babel.localedata import locale_identifiers
from babel import Locale
from pytz import timezone, all_timezones

# locals
from config import Config
from random_datetime import random_utc_datetime
from training_pair import TrainingPair
from custom_formatter import CustomFormatter

# generators
from dates.date.generate18_1 import Generate as GenerateDate
from dates.time.generate14 import Generate as GenerateTime


# -----
# class
# -----

class Generate:

    """
    Generate a sample of dates for training
    """

    def __init__(self, month_schema : str = "all"):

        # the core datalake type being generated (see Config.core_pandas_type_map)
        self.model_name = "DATETIME"

        # for NER (named entity resolution)
        self.entity = "datetime"

        # when the output (value to be predicted) is iso8601, generate the following format
        # H: Hour [0-23].
        # see http://babel.pocoo.org/en/latest/dates.html#time-fields
        self.iso_format_date = "Y-M-dTH:m:s z" 

        # configs
        self.config = Config() # self.default_encoding_character = "?"

        # generate16.12: CustomFormatter
        self.custom_formatter = CustomFormatter()
        
        #self.locales = list(locale_identifiers())
        self.locales = { 
            "en_US" : ["en_US"]
            , "mini.10" : self.config.mini10_locales # hand-curated list of 10 locales
            , "babel.all" : list(locale_identifiers()) # all locales available in Babel
            }
        
        # generate 16.9: added no delimiter to whitespaces
        #self.whitespace_characters = [' ', '']
        # generate 16.12: no whitespace is really too aggressive, at least for now
        self.whitespace_characters = [' ']


        # datetime is a combination of date and time models
        # important: items that should NOT be interpreted by Babel need to be escaped in single quotes
        # e.g at -> 'at'
        # the single quotes are then removed if output == "parsestr" (line 153)

        # generate 16.4: iterate on different datetime delimiters
        
        # NOTE: there is no point in using delimiters with two or more spaces because there are normalised
        # before training using NormaliseSpace
        
        # NOTE: adding some 1, 2 and 3-length characters so the LSTM cannot rely on absolute positions of characters in the string
        # but should build a smart parser using relative positions
        # generate16.9: simplified delimiters between date and time parts: removed , "?", "@", "@@", "@@@"
        #self.datetime_delimiters = [" ", ",", ", ", " ,", "?", "@", "@@", "@@@"]
        self.datetime_delimiters = [" ", ",", ", ", " ,"]

        self.format_spec = [   r"{date}{datetime_delimiter}{time}"
                              , r"{time}{datetime_delimiter}{date}"
                            ]

        # models
        self.date_model = GenerateDate(month_schema=month_schema)
        self.time_model = GenerateTime()

        
        # generate 16.11: regex pattern to find components with curly braces, e.g {s}
        # NOTE: the regex returns the components still containing the curly braces
        # see /Dropbox/programming/python/regex/values_between_curly_braces.py
        self.regex_find_component_string = r"{(?:[^{}])*}"
        self.regex_find_component = compile(self.regex_find_component_string)

        # generate 16.12: lists of outputs
        self.year_outputs = ["year", "year_int", "century", "decade"]
        self.month_outputs = ["month", "month_int", "month_str"]
        self.day_outputs = ["day", "day_int"]
        self.hour_outputs = ["hour", "hour_int"]
        self.minute_outputs = ["minute", "minute_int"]
        self.second_outputs = ["second", "second_int"]
        self.microsecond_outputs =  ["microsecond", "has_microsecond"]
        self.timezone_outputs =  ["timezone", "has_timezone"]
        self.time_modifier_outputs =  ["time_modifier", "has_time_modifier"]


        # generate16.22: dict of possible components and their possible formats
        # required for output "visible_components" (the actual components of the datetime in the output string)
        self.possible_components = {
            "year" : self.date_model.year_tokens
            , "month" : self.date_model.month_tokens
            , "day" : self.date_model.day_tokens

            , "hour" : self.time_model.hour_tokens
            , "minute" : self.time_model.minute_tokens
            , "second" : self.time_model.second_tokens

            , "microsecond" : self.time_model.microsecond_formats
            , "timezone" : self.time_model.timezone_formats
            , "time_modifier" : self.time_model.time_modifier_formats
        }

        

    
    def verify_null_components(self, format_spec : str, dt : datetime, locale : str) -> Tuple[bool, str]:

        """
        verify_null_components: verify that each component in the string generated a value;

        this is because some of the generating libraries (babel, num2words, roman) produce empty strings for certains dates/locales

        example; below you can see there is no string generated for {EEEE}
            format_spec: {h}:{mm}:{s} {a} {ZZ} {MMMM}#{EEEE} {ON(day)}#{yyyy}

            => 11:57:37 +0700 #  #4860

        :param format_spec: a format string, e.g {h} {a} {m}:{ss} {zzzz} {d} {M} {yy}

        :return: 2-tuple
            1.  True if none of the components generated a not null, zero length or a single space
                False if any one component is null, zero length or a single space
            
            2.  if False, an error message
        
        """

        # identify all components
        # NOTE: the regex returns the components still containing the curly braces
        components = self.regex_find_component.findall(format_spec) 
        assert len(components) > 0

        # resolve each component one at a time; fail if null, zero length or a single space
        for component in components:
            s = self.custom_formatter.apply(component, dt=dt, locale=locale)
            if s is None or len(s) == 0 or s == ' ':
                return False, f"Failed verify_null_components | {dt.isoformat()} | format_spec : {format_spec} | locale : {locale} | component : {component}"



        return True, None


    def remove_random_component(self, format_spec : str) -> Tuple[str, str]:
        """
        remove a random component, e.g {ss}; the component is simply replaced with a blank string

        :param format_spec: a format string, e.g {h} {a} {m}:{ss} {zzzz} {d} {M} {yy}
         
        :return: 2-tuple
            1. a new format string with a component randomly removed, e.g {h} {a} {m}: {zzzz} {d} {M} {yy}
            2. the removed component (NOTE: still contains the curly braces)
                e.g {ss}
        """

        # identify all components
        components = self.regex_find_component.findall(format_spec) 
        assert len(components) > 0

        # check no duplicate components
        assert len(components) == len(set(components))

        # get a random component
        # NOTE: random_component still contains the curly braces, e.g {ss}
        random_component = choice(components)

        # remove it
        return format_spec.replace(random_component, ""), random_component

    
    def get_visible_components(self, format_spec : str) -> Dict:
        """

        Get the components that are visible in the output string. 

        For example, the input datetime may have microseconds, but if they are not in the output string

        :param format_spec: the format of the datetime; 
            format_spec: {h}:{mm}:{s} {a} {ZZ} {MMMM}#{EEEE} {ON(day)}#{yyyy}



        :return: a dict with visible components and the format 
            e.g 
            {   "year" : "{yyyy}"
                ,  "month" : "{MM}"
                , ...
                , "timezone" : "{z}"
                }
        
        
        """

        visible_components = {}

        for possible_component, possible_component_formats in self.possible_components.items():
            for possible_component_format in possible_component_formats:
                if possible_component_format in format_spec:
                    if possible_component not in visible_components:
                        visible_components[possible_component] = possible_component_format
                    else:
                        raise RuntimeError(f"Found the component {possible_component} more than once in the format {format_spec}. Token is '{possible_component_format}'.")

        return visible_components
    
    def generate(self
                , output : str
                , num_observations : int
                , start_date : datetime = None
                , end_date : datetime = None
                , schemas : List[str] = None
                , month_schema : str = None
                , locale_schema : str = "mini.10"
                , remove_random_component_probability : float = 0.05
                , incremental : bool = False
                , microseconds : bool = True
                , add_timezone : bool = True
                , store_visible_components : bool = False
                ) -> Iterator[ Tuple[ TrainingPair, datetime] ]:

        """

        :param output: what do generate: iso8601, pattern

        :param num_observations: number of dates to generate; each date will be generated in N(locales) and N(format_spec)

        :param start_date: optional; start date(time) of the dates; a default value will be generated if None

        :param end_date: optional; end date(time) of the dates; a default value will be generated if None

        :param schemas: optional; list schemas to be used; at the moment only month-day and day-month are supported
            a schema is a group of formats, grouped according to some logic, e.g day first, month first, etc
            if None, all available schemas are used

        :param month_schema: specifies the month formats
            possible values:
            - "all": arabic and roman numerals
            - "arabic": arabic numerals only (1, 2, 3, ...)
            - "roman" : (i, ii, iii, ...)
            - unambiguous : MMM and MMMM

        :param locale_schema: optional; locale schema
            - mini.10
            - babel.all

        :param remove_random_component_probability: generate16.11; probability for removing a component at random
            - default is 0.05
            - if None, no component is remove (equivalent to probability = 0.0)

        :param incremental: optional; if True, datetimes are not generated randomly but using a random positive increment
            in order to generate a more realistic ascending datetime series

        :param microseconds: if True, random microseconds are added
            if False, no microseconds are added (set to 0)

        :param add_timezone: if True, a random timezone is added
            if False, a UTC datetime is generated

        :return: function is a generator -> an iterator of 2-tuples
            1. TrainingPairs (namedtuple)
            2. the input date

        """

     

        if locale_schema not in self.locales:
            raise RuntimeError(f"Locale schema '{locale_schema}' not found")

        # month_schema
        if month_schema is not None:
            self.date_model.set_month_schema(month_schema)
        
        # set start date
        if start_date is None:
            start_date = datetime(1970, 1, 1, 0, 0, 0)
        else:
            if not isinstance(start_date, datetime):
                raise RuntimeError(f"start_date {start_date} is not a datetime")
        

        # generate16.2: resolve schemas to be used
        if schemas is not None:
            if type(schemas) is not list:
                raise RuntimeError(f"schemas should be a list; {schemas} | got '{type(schemas)}")

            # check we know this schema
            for schema in schemas:
                if schema not in self.date_model.format_spec:
                    raise RuntimeError(f"unknown schema: '{schema}'")

        else:
            # no schema(s) provided -> use all available
            schemas = self.date_model.all_schemas
        
        num_schemas = len(schemas)
        
       
        if num_schemas == 0:
            raise RuntimeError(f"No schemas found; schemas = {schemas}")

        # NOTE: use a while loop because we may have to skip certain pairs (see continue statements)
        idx = 0
        while idx < num_observations:

            # auxilliary information for TrainingPair.aux
            aux_info = None 


            # generate16.9: generate a random datetime in the range [start_date; ...] with UTC timezone
            if not incremental:
                dt_utc = random_utc_datetime(start_date, end_date, microseconds=microseconds, timezone=add_timezone)
            else:
                # incremental mode: choose a random datetime to start, then ascending increments
                if idx == 0:
                    dt_utc = random_utc_datetime(start_date, end_date, microseconds=microseconds, timezone=add_timezone)
                else:
                    dt_utc += timedelta(seconds=randint(1000, 10000))



            # generate16.9: apply a random timezone
            # NOTE: calls to astimezone() on certain dates generate OverflowError errors
            # HACK: select another timezone if this conversion does not work
            d = None
            if not add_timezone:
                d = dt_utc
            else:
                random_timezone_attempt = 0
                while d is None:
                    
                    this_timezone_name = choice(all_timezones)

                    try:
                        this_timezone =  timezone(this_timezone_name)

                        # move the UCT datetime to this timezone
                        d = dt_utc.astimezone(this_timezone)
                        assert d.tzinfo is not None
                    
                    except OverflowError as e:

                        # only show a warning every 10 errors
                        random_timezone_attempt += 1
                        
                        if random_timezone_attempt == 10:
                            random_timezone_attempt = 0
            

            # iterate on the list of schemas determined above
            # current schemas in date/generate18: day-month-yy, day-month-weekday-yy, month-day-yy, month-day-weekday-yy
            # day-month-yyyy, day-month-weekday-yyyy, month-day-yyyy, month-day-weekday-yyyy
            schema = choice(schemas)
         
            # -- iterate on date formats --
            raw_date_format_spec =choice(self.date_model.format_spec[schema])

            # iterate on self.whitespace_characters
            whitespace_character = choice(self.whitespace_characters)
            date_format_spec1 = raw_date_format_spec.replace(r"{whitespace}", whitespace_character)
            
            # generate 10: iterate on date separators: space . / -
            date_separator = choice(self.date_model.separators)
            date_format_spec0 = date_format_spec1.replace(r"{separator}", date_separator)

            # generate16.12: date/generate17 create day/month and year tokens that need to be resolved
            date_format_spec = self.date_model.resolve_dmy_tokens(date_format_spec0)

            # -- iterate on time formats --
            # NOTE: time generate8 'format_specs' is a list of formats, with 1 and 2-digit minutes
            raw_time_format_spec_list = choice(self.time_model.format_specs)
            raw_time_format_spec = choice(raw_time_format_spec_list)

            time_separator = choice(self.time_model.separators)

            # generate16.10: iterate on microsecond format
            microsecond_format = choice(self.time_model.microsecond_formats)
                
            raw_time_format_spec = raw_time_format_spec.replace(r"{separator}", time_separator)
            time_format_spec2 = raw_time_format_spec.replace(r"{whitespace}", whitespace_character)            
            time_format_spec1 = time_format_spec2.replace(r"{microsecond}", microsecond_format)

            # generate16.12: iterate on timezone formats
            timezone_format = choice(self.time_model.timezone_formats)
            time_format_spec = time_format_spec1.replace(r"{timezone}", timezone_format)

            # finally, combine date and time by iterating on datetime formats ( date+time or time+date)
            raw_datetime_format_spec = choice(self.format_spec)

            # generate 16.4: iterate on different datetime delimiters
            datetime_delimiter = choice(self.datetime_delimiters)
    
            datetime_format_spec = raw_datetime_format_spec.replace(r"{datetime_delimiter}", datetime_delimiter)
            datetime_format_spec = datetime_format_spec.replace(r"{date}", date_format_spec )
            datetime_format_spec = datetime_format_spec.replace(r"{time}", time_format_spec )

            _format_spec = datetime_format_spec

            # choose a random locale
            locale = choice(self.locales[locale_schema])


            # check that no components are missing; some of the underlying generators create empty strings for some locales
            _check, _msg = self.verify_null_components(_format_spec, dt=d, locale=locale)

            if not _check:
                # invalid format
                continue

            # generate16.11: randomly remove a part. e.g {ss}
            component_removed = False
            removed_component = None

            if remove_random_component_probability is not None and uniform(0.0, 1.0) < remove_random_component_probability:
                # NOTE: format_spec will have a random component removed
                format_spec, removed_component = self.remove_random_component(_format_spec)
                component_removed = True # sanity check below

                # debugging
                #input_str = self.custom_formatter.apply(format_spec, d, locale=locale)
                #print(f"Removed component {removed_component} | in : {_format_spec} | out : {format_spec} | input_str : {input_str}")
            else:
                format_spec = _format_spec

          

            # generate 16.12: apply custom formatting before Babel
            # NOTE: custom_formatter also applies Babel formatting
            # NOTE: custom_formatter also applies full normalisation
            # r"{ZZ}" - creates key errors => ignore
            try:
                input_str = self.custom_formatter.apply(format_spec, d, locale=locale)
            except:
                continue

           
            # Override: remove short dates comprised only of digits, such as "12121"; this is really too tough at the moment
            # BACKLOG: should this override be relaxed for more generality?
            if len(input_str) < 6 and input_str.isdigit():
                continue


            
            # for NER (named entity resolution)
            if output == "entity": 
                output_str = self.entity

            elif output == "model":
                output_str = self.model_name

          

            elif output == "iso8601":
                """
                Simplified ISO 8601 without microseconds and without timezone; e.g 7942-01-22T23:41:06

                EXAMPLES
                TrainingPair(input='22:16 ettermiddag ,iv twenty-seven 5557', output='5557-04-27T22:16:00', locale='nn_NO', aux=None)
                TrainingPair(input='8 am 19:26 gmt-05:00,september/tuesday 21st/6528', output='6528-09-21T08:19:26', locale='en_US', aux=None)
                TrainingPair(input='dec/seventh/5769, 8 am', output='5769-12-07T08:00:00', locale='en_GB', aux=None)
                TrainingPair(input='9:34:52.533542 a.m.,april.18.5938', output='5938-04-18T09:34:52.533542', locale='nl_NL', aux=None)

                NOTE: if tokens are not present, e.g if the minute is missing in the format, we must set it to zero in the output string
                e.g "11 pm,thu i.22.7942" has no minute and no seconds displayed,  so the ISO 8601 output must be 7942-01-22T23:00:00

                NOTE: timezone is not taken into consideration
                Consier the following input: 3483#twenty-two#2 ,6:58:43.666178 am -0900
                    
                The output ISO8601 string (without taking into account the timezone) is 3483-02-22T06:58:43

                This makes it easier for simpler models to deal with timezones, until we can sort them out

                EXAMPLES
                14:39:43 pm gmt-06:00,sat twenty-one 1 9105   | 9105-01-21T14:39:43
                23rd.oct.8477 ,1:58:19 am america/chicago     | 8477-10-23T01:58:19
                
                NOTE: no microseconds
                NOTE: no timezone

                """
                contains_hour = any([True for substr in self.time_model.hour_tokens if substr in format_spec])
                contains_minute = any([True for substr in self.time_model.minute_tokens if substr in format_spec])
                contains_second = any([True for substr in self.time_model.second_tokens if substr in format_spec])

                # BACKLOG: add microseconds
                contains_microsecond = False #any([True for substr in self.time_model.microsecond_formats if substr in format_spec])

               
                output_str = datetime(d.year
                                    , d.month
                                    , d.day
                                    , d.hour if contains_hour else 0
                                    , d.minute if contains_minute else 0
                                    , d.second if contains_second else 0
                                    , d.microsecond if contains_microsecond else 0
                                    , tzinfo=None
                                    ).isoformat()
            
            elif output == "identity":
                output_str = input_str

            elif output == "format_spec":
                output_str = format_spec

            elif output == "format":
                output_str = format_spec

               
            # -- year formats --
            elif output in self.year_outputs:

                # extract the year, in some shape or form
                # in common, these formats require getting the year format in the format spec

                # determine which year spec is currently used for the year; and check the year spec only appears once in the format string
                # NOTE: we must check if the year is present because it may have been randomly removed in remove_random_component()
                year_format_spec = None

                # generate16.12: we can use the exact list specified in the date model
                for _year_format in self.date_model.year_tokens:

                    if _year_format in format_spec:
                        assert year_format_spec is None # check no duplicates
                        year_format_spec = _year_format

                
                year_removed = False
                if year_format_spec is None:
                    # oups: could not find the a year... maybe we removed it above?
                    if component_removed is not None and removed_component in self.date_model.year_tokens:
                        # there is no year since it was removed
                        # generate16.20: handle missing components by generating NULL/empty bit vectors
                        year_removed = True
                    else:
                        # this is a bug
                        raise RuntimeError(f"no year token found in format_spec {format_spec}")


                # -- century --
                if output == "year":
                    output_str = str(d.year) if not year_removed else None
                
                elif output == "year_int":
                    # year_int : the year as an integer
                    output_str = d.year if not year_removed else None

                elif output == "century":

                    # generate16.20: handle missing components by generating NULL/empty bit vectors
                    if year_removed:
                        output_str = None
                    else:

                        # Conditions
                        # 1. only if year is present in the string (checked above)
                        # 2. only if year is specified with 4 digits

                        # NOTE: keep in sync with formats that generate centuries in the date generator
                        if year_format_spec == r"{yyyy}":
                            year_str = str(d.year)
                            assert len(year_str) == 4
                            
                            output_str = year_str[0:2] + "00"
                            assert len(output_str) == 4

                        else:
                            # ignore this date as year does not contain a century
                            continue
                
                # if output == "has_century": 
                # NOTE: keep in sync with formats that generate centuries in the date generator
                # output_str = "1" if year_format_spec == r"{yyyy}" else "0"

                # -- decade --
                elif output == "decade":

                    # generate16.20: handle missing components by generating NULL/empty bit vectors
                    if year_removed:
                        output_str = None
                    else:
                
                        # Conditions
                        # 1. only if year is present in the string (checked above)
                        year_str = str(d.year)
                        assert len(year_str) == 4
                        
                        output_str = year_str[2:]
                        assert len(output_str) == 2

                # elif output == "has_decade": 
                # Conditions
                # 1. only if year is present in the string (checked above)

                # output_str = "1"

               


                else:
                    raise NotImplementedError(f"Unhandled output format '{output}'")

            
            # -- month formats --
            elif output in self.month_outputs:

                # extract the month, in some shape or form
                # in common, these formats require getting the month format in the format spec

                # determine which month spec is currently used for the month; and check the month spec only appears once in the format string
                # NOTE: we must check if the month is present because it may have been randomly removed in remove_random_component()
                month_format_spec = None

                # generate16.12: we can use the exact list specified in the date model
                for _month_format in self.date_model.month_tokens:

                    if _month_format in format_spec:
                        assert month_format_spec is None # check no duplicates
                        month_format_spec = _month_format

                
                month_removed = False
                if month_format_spec is None:
                    # oups: could not find the a month... maybe we removed it above?
                    if component_removed is not None and removed_component in self.date_model.month_tokens:
                        # there is no month since it was removed
                        # generate16.20: handle missing components by generating NULL/empty bit vectors
                        month_removed = True
                    else:
                        raise RuntimeError(f"no month token found in format_spec {format_spec}")



                # now we can proceed with the specific format
                if output == "month":
                    # month: for seq2class models
                    output_str = str(d.month) if not month_removed else None
                    aux_info = { "component" : "month", "str" : None, "value" : None }

                elif output == "month_int":
                    # month_int: the month as an integer
                    output_str = d.month if not month_removed else None
                    aux_info = { "component" : "month", "str" : None, "value" : None }

                elif output == "month_str":
                    # month_str : for seq2seq models
                    # the month as a string, exactly as represented in the input string; use for seq2seq models
                    # example
                    # '0:00:00.0 Koordinerad universell tid@1-januari-1970' => 'januari'

                    if month_removed:
                        output_str = None
                        aux_info = { "component" : "month", "str" : None, "value" : None }
                    else:
                    
                        # format the month using the input format
                        output_str = self.custom_formatter.apply(month_format_spec, d, locale=locale)

                        assert output_str in input_str

                        aux_info = { "component" : "month", "str" : output_str, "value" : d.month }

               
              
                else:
                    raise NotImplementedError(f"Unhandled output format '{output}'")

                
              

            # -- day formats --
            elif output in self.day_outputs:
                # extract the day, in some shape or form
                # in common, these formats require getting the day format in the format spec

                # determine which day spec is currently used for the day; and check the day spec only appears once in the format string
                # NOTE: we must check if the day is present because it may have been randomly removed in remove_random_component()
                day_format_spec = None

                # generate16.12: we can use the exact list specified in the date model
                for _day_format in self.date_model.day_tokens:

                    if _day_format in format_spec:
                        assert day_format_spec is None # check no duplicates
                        day_format_spec = _day_format

                day_removed = False
                if day_format_spec is None:
                    # oups: could not find the a day... maybe we removed it above?
                    if component_removed is not None and removed_component in self.date_model.day_tokens:
                        # there is no day since it was removed => skip this pair
                        day_removed = True
                    else:
                        raise RuntimeError(f"no day token found in format_spec {format_spec}")

                if output == "day":
                    # day: for seq2class models
                    output_str = str(d.day) if not day_removed else None

                elif output == "day_int":
                    # day as an integer
                    output_str = d.day if not day_removed else None
                
         

                else:
                    raise NotImplementedError(f"Unhandled output format '{output}'")


            # -- hour formats --
            elif output in self.hour_outputs:
                
                # extract the hour, in some shape or form
                # in common, these formats require getting the hour format in the format spec

                # determine which hour spec is currently used for the hour; and check the hour spec only appears once in the format string
                # NOTE: we must check if the hour is present because it may have been randomly removed in remove_random_component()
                hour_format_spec = None

                # generate16.12: we can use the exact list specified in the time model
                for _hour_format in self.time_model.hour_tokens:

                    if _hour_format in format_spec:
                        assert hour_format_spec is None # check no duplicates
                        hour_format_spec = _hour_format


                hour_removed = False
                if hour_format_spec is None:
                    # oups: could not find the an hour... maybe we removed it above?
                    if component_removed is not None and removed_component in self.time_model.hour_tokens:
                        # there is no hour since it was removed => skip this pair
                        hour_removed = True
                    else:
                        raise RuntimeError(f"no hour token found in format_spec {format_spec}")

                if output == "hour":
                    # hour: for seq2class models
                    # NOTE: returns the 24hour representation (0-23), even if the string may not contain the 24hour representation
                    # example: '6 pm 57:26 -0100,8066-jun-26th' => output='18'
                    output_str = str(d.hour) if not hour_removed else None

                elif output == "hour_int":
                    # hour_int : the hour as an integer 0-59
                    output_str = d.hour if not hour_removed else None
                
               
                
                else:
                    raise NotImplementedError(f"Unhandled output format '{output}'")

            # -- minute formats --
            elif output in self.minute_outputs:
                
                # extract the minute, in some shape or form
                # in common, these formats require getting the minute format in the format spec

                # determine which minute spec is currently used for the minute; and check the minute spec only appears once in the format string
                # NOTE: datetimes may not necessarily have a minute, see patterns in time/generate14
                # NOTE: we must check if the minute is present because it may have been randomly removed in remove_random_component()
                minute_format_spec = None

                # generate16.12: we can use the exact list specified in the time model
                for _minute_format in self.time_model.minute_tokens:

                    if _minute_format in format_spec:
                        assert minute_format_spec is None # check no duplicates
                        minute_format_spec = _minute_format


                minute_removed = False
                if minute_format_spec is None:
                    # NOTE: datetimes may not necessarily have a minute, see patterns in time/generate14
                    # NOTE: minute could also have been removed by remove_random_component()
                    minute_removed = True

                if output == "minute":
                    # minute: for seq2class models
                    output_str = str(d.minute) if not minute_removed else None

                elif output == "minute_int":
                    # minute: for seq2class models
                    output_str = d.minute if not minute_removed else None
                
           
                else:
                    raise NotImplementedError(f"Unhandled output format '{output}'")

            # -- second formats --
            elif output in self.second_outputs:
                
                # extract the second, in some shape or form
                # in common, these formats require getting the second format in the format spec

                # determine which second spec is currently used for the second; and check the second spec only appears once in the format string
                # NOTE: datetimes may not necessarily have a second, see patterns in time/generate14
                # NOTE: we must check if the second is present because it may have been randomly removed in remove_random_component()
                second_format_spec = None

                # generate16.12: we can use the exact list specified in the time model
                for _second_format in self.time_model.second_tokens:

                    if _second_format in format_spec:
                        assert second_format_spec is None # check no duplicates
                        second_format_spec = _second_format

                second_removed = False
                if second_format_spec is None:
                    # NOTE: datetimes may not necessarily have a second, see patterns in time/generate14
                    # NOTE: second could also have been removed by remove_random_component()
                    second_removed = True

                if output == "second":
                    # second: for seq2class models
                    output_str = str(d.second) if not second_removed else None

                elif output == "second_int":
                    # second as an integer
                    output_str = d.second if not second_removed else None

       
                else:
                    raise NotImplementedError(f"Unhandled output format '{output}'")
            
            
            
            # -- microsecond formats --
            elif output in self.microsecond_outputs:
                
                # extract the microsecond, in some shape or form
                # in common, these formats require getting the microsecond format in the format spec

                # determine which microsecond spec is currently used for the microsecond; and check the microsecond spec only appears once in the format string
                # NOTE: datetimes may not necessarily have a microsecond, see patterns in time/generate14
                # NOTE: we must check if the microsecond is present because it may have been randomly removed in remove_random_component()
                microsecond_format_spec = None

                # generate16.12: we can use the exact list specified in the time model
                for _microsecond_format in self.time_model.microsecond_formats:

                    if _microsecond_format in format_spec:
                        assert microsecond_format_spec is None # check no duplicates
                        microsecond_format_spec = _microsecond_format

                microsecond_removed = False
                if microsecond_format_spec is None:
                    # NOTE: datetimes may not necessarily have a microsecond, see patterns in time/generate14
                    # NOTE: microsecond could also have been removed by remove_random_component()
                    microsecond_removed = True

                if output == "microsecond":
                    # microsecond: for seq2class models
                    output_str = str(d.microsecond) if not microsecond_removed else None

                elif output == "has_microsecond":
                    # has_microseconds: for seq2class models
                    output_str = "1" if not microsecond_removed else "0"

          
                else:
                    raise NotImplementedError(f"Unhandled output format '{output}'")
            
           


            # -- timezone formats --
            elif output in self.timezone_outputs:
                
                # extract the timezone, in some shape or form
                # in common, these formats require getting the timezone format in the format spec

                # determine which timezone spec is currently used for the timezone; and check the timezone spec only appears once in the format string
                # NOTE: datetimes may not necessarily have a timezone, see patterns in time/generate14
                # NOTE: we must check if the timezone is present because it may have been randomly removed in remove_random_component()
                timezone_format_spec = None

                # generate16.12: we can use the exact list specified in the time model
                for _timezone_format in self.time_model.timezone_formats:

                    if _timezone_format in format_spec:
                        assert timezone_format_spec is None # check no duplicates
                        timezone_format_spec = _timezone_format

                timezone_removed = False
                if timezone_format_spec is None:
                    # NOTE: datetimes may not necessarily have a timezone, see patterns in time/generate14
                    # NOTE: timezone could also have been removed by remove_random_component()
                    timezone_removed = True

                if output == "timezone":
                    # timezone: for seq2class models
                    output_str = this_timezone if not timezone_removed else None

                elif output == "has_timezone":
                    # has_timezone: for seq2class models
                    output_str = "1" if not timezone_removed else "0"

             
                        
                else:
                    raise NotImplementedError(f"Unhandled output format '{output}'")
           
                   

           
            elif output == "has_minute":
                
                """
                generate 16.7: "1" if datetime contains minutes, else "0"
                examples:
                - input='0 AM,1 1 70', output=0
                - input='1-1-70@12 AM', output=0
                - input='0:00:00 GMT+00:00 ,1.1.70', output=1
                - input='12 AM 0:00 +0000@@1/1/70', output=1
                """

                # NOTE: for generalisation, we enforce that target classes are specified 
                # by their name (not their integer id)
                # BACKLOG: placed list of tokens in time generator
                if r"{m}" in time_format_spec or r"{mm}" in time_format_spec:
                    output_str = "1"
                else:
                    output_str = "0"

            elif output == "has_second":
                
                """
                generate 16.7: "1" if datetime contains seconds, else "0"
                examples:
                    - input='12 AM ,1 1 70', output='0'
                    - input='1 1 70@@@0:0 AM', output='0'
                    - input='0:0:00 1 1 70', output='1'
                    - input='1.1.70 ,0:0:00 +0000', output='1'

                """
                # NOTE: for generalisation, we enforce that target classes are specified 
                # by their name (not their integer id)
                # BACKLOG: placed list of tokens in time generator
                if r"{s}" in time_format_spec or r"{ss}" in time_format_spec:
                    output_str = "1"
                else:
                    output_str = "0"

      
            elif output == "locale":
                output_str = locale

           
        
            else:
                raise RuntimeError(f"unhandled output '{output}'")
            

            # add visible_components to aux
            if store_visible_components:
                
                if aux_info is None:
                    aux_info = {}
                aux_info["visible_components"] = self.get_visible_components(format_spec)

            # v7: generator function
            idx += 1
            yield (TrainingPair(input=input_str, output=output_str, locale=locale, aux=aux_info), d)


# ----
# main
# ----

if __name__ == "__main__":


    from argparse import ArgumentParser

    def main():

        # --- command line args ---
        cmd_line_parser = ArgumentParser(description='driver for Generate')
        cmd_line_parser.add_argument('output', type=str, default=None, help='iso8601, parsestr, model')
        cmd_line_parser.add_argument('num_observations', type=int, default=None, help='number of observations to generate')
        
        cmd_line_parser.add_argument('--schemas', type=str, help='comma separated list of schemas to use, e.g month-day-yyyy,month-day-weekday-yyyy', default=None)
        cmd_line_parser.add_argument('--start_date', type=str, help='start datetime in ISO format, e.g 2022-02-02T06:19:37', default=None)
        cmd_line_parser.add_argument('--end_date', type=str, help='end datetime in ISO format, e.g 2030-12-31T23:59:59', default=None)
        cmd_line_parser.add_argument('--locale_schema', type=str, help='locale schema; e.g en_US, mini.10, ...', default="mini.10")
        cmd_line_parser.add_argument('--preview_rows', type=int, help='number of rows to preview', default=10)
        cmd_line_parser.add_argument('--remove_random_component_probability', type=float, help='probability for removing a component at random', default=0.05)
        cmd_line_parser.add_argument('--month_schema', type=str, help='month tokens to use (all, arabic, roman, unambiguous)', default="all")
        
        cmd_line_parser.add_argument('--csv', type=str, help='output to a quoted csv', default=None)
        cmd_line_parser.add_argument('--incremental', default=False, dest='incremental', action='store_true', help='incremental datetimes')
        cmd_line_parser.add_argument('--inputs', default=False, dest='inputs', action='store_true', help='only show inputs in compact form')
        cmd_line_parser.add_argument('--targets', default=False, dest='targets', action='store_true', help='only show targets in compact form')

        cmd_line_parser.add_argument('--debug', default=False, dest='debug', action='store_true', help='debugging')
        cmd_line_parser.add_argument('--debug2', default=False, dest='debug2', action='store_true', help='debugging')
        args = cmd_line_parser.parse_args()


        # create generator
        generator = Generate()
        generator.debug = args.debug
        generator.debug2 = args.debug2
        
        # optional: specify start and end dates
        # start datetime in ISO format, e.g 2022-02-02T06:19:37
        start_date = datetime.fromisoformat(args.start_date) if args.start_date is not None else None

        # end datetime in ISO format, e.g 2030-12-31T23:59:59
        end_date = datetime.fromisoformat(args.end_date) if args.end_date is not None else None
        
        #print(f"start_date : {start_date}")

        # optional: specify schema(s)
        schemas = None
        if args.schemas is not None:
            schemas = [schema.strip() for schema in args.schemas.split(",")]

            if args.debug:
                print(f"schemas : {schemas}")


        # generate data
        results = generator.generate(args.output
                                    , args.num_observations
                                    , start_date=start_date
                                    , end_date=end_date
                                    , schemas=schemas
                                    , month_schema=args.month_schema
                                    , locale_schema=args.locale_schema
                                    , remove_random_component_probability=args.remove_random_component_probability
                                    , incremental=args.incremental
                                    )


        # open file
        if args.csv:
            file = open(args.csv, "w")

        # show output
        counter = 0
        for _, (training_pair, dt) in enumerate(results, start=1):

            counter += 1

            if args.inputs:
                print(training_pair.input)

            elif args.targets:
                print(training_pair.output)

            elif args.csv:
                output = f'"{training_pair.input}","{training_pair.output}"\n'
                file.write(output)
            
            else:
                print(training_pair, "|", dt)

        if args.csv:
            file.close()


        

    
    main()