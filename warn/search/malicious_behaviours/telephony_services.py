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
import sys
import logging
from io import BytesIO
from xml.etree.ElementTree import ElementTree

# Androwarn modules import
from warn.core.core import *
from warn.util.util import *

# Logguer
log = logging.getLogger('log')

# -- SMS Abuse -- #
def detect_Telephony_SMS_abuse(x) :
    """
        @param x : a Analysis instance
        
        @rtype : a list of formatted strings
    """
    method_name = "sendTextMessage"
    formatted_str = []
    
    structural_analysis_results = structural_analysis_search_method("Landroid/telephony/SmsManager","sendTextMessage", x)
    
    for registers in data_flow_analysis(structural_analysis_results, x):   
        if len(registers) > 3 :
            target_phone_number = get_register_value(1, registers)
            sms_message         = get_register_value(3, registers)
            
            local_formatted_str = "This application sends an SMS message '%s' to the '%s' phone number" % (sms_message, target_phone_number)
            if not(local_formatted_str in formatted_str) :
                formatted_str.append(local_formatted_str)
    
    # Mod
    if len(formatted_str) > 0:
        formatted_str = [method_name]

    return sorted(formatted_str)

def detect_SMS_interception(a,x) :
    """
        @param a : an APK  instance
        @param x : a Analysis instance
        
        @rtype : a list of formatted strings
    """
    formatted_str = []
    tree = ElementTree()
    
    try :
        manifest  = a.get_android_manifest_axml().get_xml()
        tree.parse(BytesIO(manifest))
        root = tree.getroot()
                    
        for parent, child, grandchild in get_parent_child_grandchild(root):
            
            # Criteria 1: "android.provider.Telephony.SMS_RECEIVED" + "intentfilter 'android:priority' a high number" => SMS interception
            if '{http://schemas.android.com/apk/res/android}name' in grandchild.attrib.keys() :
                
                if grandchild.attrib['{http://schemas.android.com/apk/res/android}name'] == "android.provider.Telephony.SMS_RECEIVED" :
                    
                    if child.tag == 'intentfilter' and '{http://schemas.android.com/apk/res/android}priority' in child.attrib.keys() :
                        formatted_str.append("This application intercepts your incoming SMS")
                        
                        # Grab the interceptor's class name
                        class_name = parent.attrib['{http://schemas.android.com/apk/res/android}name']
                        package_name = a.get_package()
                        
                        # Convert("com.test" + "." + "interceptor") to "Lcom/test/interceptor"
                        class_name = convert_canonical_to_dex(package_name + "." + class_name[1:])
                        
                        # Criteria 2: if we can find 'abortBroadcast()' call => notification deactivation
                        structural_analysis_results = structural_analysis_search_method(class_name, "abortBroadcast", x)
                        if structural_analysis_results :
                            formatted_str.append("This application disables incoming SMS notifications")
                    
    except Exception as e:
        log.error("detect_SMS_interception(): %s" % e)  
    
    if len(formatted_str) > 0:
        formatted_str = ["SMSInterception"]

    return sorted(formatted_str)

def detect_Telephony_Phone_Call_abuse(x) :
    """
        @param x : a Analysis instance
        
        @rtype : a list of formatted strings
    """
    formatted_str = []
    
    detector_1 = structural_analysis_search_string("android.intent.action.CALL", x)
    detector_2 = structural_analysis_search_string("android.intent.action.DIAL", x)
    
    detectors = detector_1 + detector_2
    
    if detectors:
        formatted_str.append('This application makes phone calls')
        log_result_path_information(detectors)

    if len(formatted_str) > 0:
        formatted_str = ["PhoneCall"]
        
    return sorted(formatted_str)


def gather_telephony_services_abuse(a,x) :
    """
        @param a : an APK  instance
        @param x : a Analysis instance
    
        @rtype : a list strings for the concerned category, for exemple [ 'This application makes phone calls', "This application sends an SMS message 'Premium SMS' to the '12345' phone number" ]
    """
    result = []
    
    result.extend( detect_Telephony_Phone_Call_abuse(x) )
    result.extend( detect_SMS_interception(a,x) )
    result.extend( detect_Telephony_SMS_abuse(x) )
    
    return result
