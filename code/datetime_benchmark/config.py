# -*- coding: utf-8 -*-

"""
config.py: default settings for all machine learning models

base: datalake/mock/b.3/ml/config.py

edward | 2021-08-22 | Initial version
edward | 2021-11-28 | upgraded is_date model to datatype.ovr.date.2
edward | 2021-11-28 | upgraded is_numeric model to datatype.ovr.numeric.2
edward | 2022-02-11 | upgraded is_date model to datatype.ovr.date.3

"""


class Config:

     def __init__(self):

          # what to predict when there is no output available
          # specifically in generate11 with schemas
          self.null_target = "NULL"

          self.mini10_locales = ["en_US", "en_GB", "de_DE", "fr_CH", "sv_SE", "es_ES", "nn_NO", "it_IT", "nl_NL", "pt_PT"]

          # 10 basic/common locales
          # edward | 2022-08-19 | no_NO does not exist, I think it's nn_NO: "Norwegian Nynorsk (Norway)",
          self.locales = ["en_US", "en_GB", "de_DE", "fr_CH", "sv_SE", "es_ES", "nn_NO", "it_IT", "nl_NL", "pt_PT"]

