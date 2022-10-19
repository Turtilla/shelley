# -*- coding: utf-8 -*-

import json

from flask import Flask, request
from jinja2 import Environment
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)
environment = Environment()


def jsonfilter(value):
    return json.dumps(value)


environment.filters["json"] = jsonfilter


def error_response(message):
    response_template = environment.from_string("""
    {
      "status": "error",
      "message": {{message|json}},
      "data": {
        "version": "1.0"
      }
    }
    """)
    payload = response_template.render(message=message)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def query_response(value, grammar_entry):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": {{value|json}},
            "confidence": 1.0,
            "grammar_entry": {{grammar_entry|json}}
          }
        ]
      }
    }
    """)
    payload = response_template.render(value=value, grammar_entry=grammar_entry)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def multiple_query_response(results):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
        {% for result in results %}
          {
            "value": {{result.value|json}},
            "confidence": 1.0,
            "grammar_entry": {{result.grammar_entry|json}}
          }{{"," if not loop.last}}
        {% endfor %}
        ]
      }
    }
     """)
    payload = response_template.render(results=results)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def validator_response(is_valid):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "is_valid": {{is_valid|json}}
      }
    }
    """)
    payload = response_template.render(is_valid=is_valid)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/dummy_query_response", methods=['POST'])
def dummy_query_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": "dummy",
            "confidence": 1.0,
            "grammar_entry": null
          }
        ]
      }
    }
     """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/action_success_response", methods=['POST'])
def action_success_response():
    response_template = environment.from_string("""
   {
     "status": "success",
     "data": {
       "version": "1.1"
     }
   }
   """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response

@app.route("/edibility", methods=['POST'])
def edibility():
    payload = request.get_json()
    # exctracting the plant name
    plant = payload["request"]["parameters"]["wh_plant"]["grammar_entry"].lower()

    # making the request
    plant_dict = get_plant_dict(plant) 

    # retrieving the information from the dict
    if len(plant_dict) == 0:
      # if there are no results in the search
      return query_response(value='I have no information about such a plant. Just to be safe, please do not feed it to the tortoise.', grammar_entry=None)
    elif plant in plant_dict:
      # if the plant name is present in the dictionary
      answer = plant_dict[plant]['edibility']
      return query_response(value=f'{plant} has the status {answer}', grammar_entry=None)
    else:
      # if there are results but none of them match 1:1; the first one is then selected (as that one is often the best match, I am unsure how the website's search works)
      plant_guess = next(iter(plant_dict.items()))[0]
      answer = plant_dict[plant_guess]['edibility']
      return query_response(value=f'I found {plant_guess}. It has the status {answer}. If you meant another plant, try giving me its full name or latin name.', grammar_entry=None)

# I was getting errors when importing my own script so I copied the relevant function here
def get_plant_dict(plant_name):
    # a function intended for retrieving information about plants matching
    # the user request in a dictionary format name:edibility
    
    # the url/website from which the results are sources
    website = requests.get(url=f"https://www.thetortoisetable.org.uk/plant-database/viewplants/search/?searchtogglestatus=&searchchoice=exactwords&searchtxt={plant_name}&x=0&y=0#.YxI5UXZBzD4").text
    
    # turning the website into a BeautifulSoup object
    soup = BeautifulSoup(website, 'html.parser')  
    # retrieving a list of text elements only pertaining to plants
    plant_contents = list(soup.find(id='content').stripped_strings)[3:]
    
    # creating a list of lists, where every element is one plant
    all_plants = []
    temporary_plant = []
    # the elements can be edibility, plant name, alternative names, Latin
    # names, and 'See More'
    for element in plant_contents:
        if element != 'See More':  # 'See More' delineates separate plants
            temporary_plant.append(element)
        else:  # if it is 'See More'
            all_plants.append(temporary_plant)
            temporary_plant = []
    
    # creating the dictionary to be returned
    plant_dict = {}
    for entry in all_plants:
        edibility = entry[0].lower()
        name = entry[1].lower()
        latin = entry[-1].lower()  # it is always the last entry, but some plants have alternative names as [2] and some do not
        plant_dict[name] = {"edibility":edibility, "latin":latin}
        
    return plant_dict