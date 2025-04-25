# -*- coding: utf-8 -*-

"""
normalise_string.py: Flattens a string using the following algorithms:
- flatten unicode to ascii
- normalise tokens, e.g ".." => "."
- normalise white space, e.g , "\xc2\xa0" # Non-breaking space => " "
- cast to lower case

BASE
generates/dates/datetime/custom_formatter.py

USAGE
python3 normalise_string.py "ABC  äbc" # => abc abc

edward | 2023-07-28

BACKLOG
        
"""

# locals
from normalise_whitespace import NormaliseWhitespace
from normalise_tokens import NormaliseTokens
from normalise_unicode import NormaliseUnicode


class NormaliseString:

    """
    NormaliseString: Flattens a string using the following algorithms:
        - flatten unicode
        - normalise tokens, e.g ".." => "."
        - normalise white space, e.g , "\xc2\xa0" # Non-breaking space => " "
        - cast to lower case
    """

    def __init__(self, normalise : bool = True):
        """
        :param normalise: apply full normalisation
            # 1. unicode
            # 2. tokens (e.g convert .. to .)
            # 3. whitespace (e.g "\u202f" to " ")
            # 4. convert to lower case
        
        """

        self.normalise = normalise

        self.normalise_tokens = NormaliseTokens()
        self.normalise_whitespace = NormaliseWhitespace()
        self.normalise_unicode = NormaliseUnicode()


    def normalise_string(self, s : str, strip : bool = True, to_lower : bool = True) -> str:
        """
        normalise_string: apply full normalisation to a string

        :param s: a string to be normalised

        :param strip: True if strip should be applied as a lest step
            set to False in cases where a single whitespace character e.g ' ' is a valid normalised string that should not be stripped
            else ' ' gets stripped to ''

        :param to_lower: set to True to cast string to lower case

        :return: normalised string
        
        """
        s0 = self.normalise_whitespace.normalise(self.normalise_tokens.normalise(self.normalise_unicode.normalise(s)))
            
        s1 = s0.lower() if to_lower else s0

        if strip:
            return s1.strip()
        else:
            return s1
    
    
   
if __name__ == '__main__':

    from argparse import ArgumentParser
    

    def main():

        # init command line arguments
        cmd_line_parser = ArgumentParser(description='driver for NormaliseString')
        cmd_line_parser.add_argument('input_string', type=str, default=None, help='string to be normalised')
        cmd_line_parser.add_argument('--debug', default=False, dest='debug', action='store_true', help='debugging')
        args = cmd_line_parser.parse_args()

        normalise_string = NormaliseString()

        output_string = normalise_string.normalise_string(args.input_string)
        print(output_string)



    # main entry point
    main()