#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Brad McDonald, Mejbah ul Alam, Justin Gottschlich, Abdullah Muzahid
# *****************************************************************************/
"""Appends the `libperfpoint.so` dir to $(LIBRARY_PATH) + $(LD_LIBRARY_PATH)."""
# from autoperf.utils import library_prepare
# library_prepare()
from autoperf.utils import add_environment_variable
add_environment_variable('TF_CPP_MIN_LOG_LEVEL', '', '3')
