#!/bin/python
from flask import Flask, request

app = Flask(__name__)

@app.route('/{{api_name}}')
def main():
    return '{{api_name}}'
