#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 28 14:33:40 2023

@author: nkeeley
"""

# # test function
# def test_this():
    
#     print("hello")
#     return

from dash import Dash, html

def create_dash(flask_app):
    
    dash_instance=Dash(server=flask_app,name="Dashboard",url_base_pathname="/dash/")
    dash_instance.layout = html.Div([
        html.Div(children='Hello World')
    ])

    return dash_instance



