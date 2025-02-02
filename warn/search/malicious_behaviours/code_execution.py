#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of Androwarn.
#
# Copyright (C) 2012, 2019, Thomas Debize <tdebize at mail.com>
# All rights reserved.
#
# Androwarn is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androwarn is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androwarn.  If not, see <http://www.gnu.org/licenses/>.

# Global imports
import logging

# Androwarn modules import
from warn.core.core import *
from warn.util.util import *

# Logguer
log = logging.getLogger('log')

def detect_Library_loading(x) :
    """
        @param x : a Analysis instance
        
        @rtype : a list of formatted strings
    """
    formatted_str = []
    if len(gather_loaded_libraries(x)) > 0:
        formatted_str = ["LoadLibrary"]

    return sorted(formatted_str)

def detect_UNIX_command_execution(x) :
    """
        @param x : a Analysis instance
        
        @rtype : a list of formatted strings
    """
    method_name = "exec"
    formatted_str = []
    
    structural_analysis_results = structural_analysis_search_method("Ljava/lang/Runtime", method_name, x)
    
    for registers in data_flow_analysis(structural_analysis_results, x):
        local_formatted_str = "This application executes a UNIX command" 
        
        # If we're lucky enough to have the arguments
        if len(registers) >= 2 :
            local_formatted_str = "%s containing this argument: '%s'" % (local_formatted_str, get_register_value(1, registers))

        # we want only one occurence
        if not(local_formatted_str in formatted_str) :
            formatted_str.append(local_formatted_str)

    # Mod
    if len(formatted_str) > 0:
        formatted_str = [method_name]
        
    return sorted(formatted_str)

def detect_reflection(x):

    method_name = "invoke"
    dex_class_name = convert_canonical_to_dex("java.lang.reflect.Method")

    structural_analysis_results = structural_analysis_search_method(dex_class_name, method_name, x)

    formatted_str = []
    for registers in data_flow_analysis(structural_analysis_results, x):
        local_formatted_str = "Reflection"

        #print(len(registers))
        if len(registers) >= 2 :
            local_formatted_str = "%s containing this argument: '%s' '%s'" % (local_formatted_str, get_register_value(1, registers), get_register_value(2, registers))

        # we want only one occurence
        if not(local_formatted_str in formatted_str) :
            formatted_str.append(local_formatted_str)

    if len(formatted_str) > 0:
        formatted_str = ["Reflection"]

    return sorted(formatted_str)

def detect_cryptography(x):

    dex_class_name = "Ljavax/crypto/.*"

    structural_analysis_results = structural_analysis_search_class(dex_class_name, x) 

    formatted_str = []
    for c in structural_analysis_results:
        local_formatted_str = "Cryptography"

        if not(local_formatted_str in formatted_str) :
            formatted_str.append(local_formatted_str)

    return sorted(formatted_str)

def gather_code_execution(x) :
    """
        @param x : a Analysis instance
    
        @rtype : a list strings for the concerned category, for exemple [ 'This application makes phone calls', "This application sends an SMS message 'Premium SMS' to the '12345' phone number" ]
    """
    result = []
    
    result.extend( detect_UNIX_command_execution(x) )
    result.extend( detect_reflection(x) )
    result.extend( detect_cryptography(x) )
    result.extend( detect_Library_loading(x) )
        
    return result

def gather_loaded_libraries(x):

    results = []

    method_name = "loadLibrary"
    structural_analysis_results = structural_analysis_search_method("Ljava/lang/System", method_name, x)
    
    for registers in data_flow_analysis(structural_analysis_results, x):        
        # If we're lucky enough to directly have the library's name
        if len(registers) == 1:
            local_formatted_str = get_register_value(0, registers)

            # we want only one occurence
            if not(local_formatted_str in results) :
                results.append(local_formatted_str)

    return results
