# -*- coding: utf-8 -*-

"""
normalise_tokens.py: normalise the tokens of datetime string to a specifc character, e.g single space

objective is to reduce the dimensionality of the space of datetime representations

tokens that are not part of LDMLTokens are not normalised, e.g EEEE remains EEEE

e.g 29 May  2021, 7:23:11 PM

edward | 2021-06-03

BACKLOG
"""


# locals
from ldml_tokens import LDMLTokens

class NormaliseTokens:

    # training configuration
    def __init__(self):

        self.ldml_tokens = LDMLTokens()

        
    
    def normalise(self, format_spec : str) -> str:
        
        """
        normalise the parsing tokens in format_spec

        :param format_spec: e.g {d}-{M}-{yy} -> {day}-{month}-{year}

        :return: normalised tokens

        """

        # argument checks
        assert isinstance(format_spec, str)

        clean_format = format_spec

        for token in self.ldml_tokens:
            search_pattern = '{' +  token + '}'
            replace_pattern = '{' +  self.ldml_tokens[token] + '}'
            
            clean_format = clean_format.replace(search_pattern, replace_pattern)


        return clean_format
   
