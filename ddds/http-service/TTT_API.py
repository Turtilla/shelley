from bs4 import BeautifulSoup
import requests
import csv

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

def get_plant_list(url):
    # a function for retrieving solely the English names of the plants on some page on TTT
    all_plants = []
    # retrieving the html website
    website = requests.get(url=url).text
    # turning it into a BeautifulSoup object
    soup = BeautifulSoup(website, 'html.parser')
    plant_contents = list(soup.find(id='content').stripped_strings)[3:]
    temporary_plant = []
    # the elements can be edibility, plant name, alternative names, Latin
    # names, and 'See More'
    for element in plant_contents:
        if element != 'See More':  # 'See More' delineates separate plants
            temporary_plant.append(element)
        else:  # if it is 'See More'
            if len(temporary_plant) > 4:
                temporary_plant = temporary_plant[3:]  # first line is different
            all_plants.append(temporary_plant[1])
            temporary_plant = []

    return all_plants
    

def get_plant_csv(filename):
    # a function utilizing get_plant_list to obtain the list of all the plants that are described on TTT
    # in order for it to be used for training RASA at detecting plant names.
    
    # all the categories in TTT
    websites = [
        'https://www.thetortoisetable.org.uk/plant-database/wild-flowers/#.Y00t73ZByUk',  # wild flowers
        'https://www.thetortoisetable.org.uk/plant-database/garden-and-house-plants/#.Y00uBnZByUk',  # garden and house plants
        'https://www.thetortoisetable.org.uk/plant-database/trees-shrubs-climbers/#.Y00uCHZByUk',  # trees and shrubs
        'https://www.thetortoisetable.org.uk/plant-database/cacti-succulents/#.Y00uCXZByUk',  # cacti and succulents
        'https://www.thetortoisetable.org.uk/plant-database/grasses-ferns/#.Y00uCXZByUk',  # grasses and ferns
        'https://www.thetortoisetable.org.uk/plant-database/fruit-vegetables/#.Y00uCnZByUk',  # fruit and vegetables
        'https://www.thetortoisetable.org.uk/plant-database/aquatic-and-semi-aquatic-plants/#.Y00uC3ZByUk',  # aquatic and semiaquatic plants
    ]

    # gathering the plants from each category
    all_plants = []
    for link in websites:
        plants = get_plant_list(link)
        all_plants += plants

    ### this would be useful IF THE WEBSITE understood plurals, which it does not :(
    # generating and adding plurals
    # plural_plants = []
    # sibilants = ['s', 'z', 'sh', 'x', 'ch']
    # for plant in all_plants:
    #    if plant[-1] == 'y':
    #        plural = plant[:-1] + 'ies'
    #    elif plant[-1] in sibilants:
    #        plural = plant + 'es'
    #    elif plant[-2:] in sibilants:
    #        plural = plant + 'es'
    #    else:
    #        plural = plant + 's'
    #    plural_plants.append(plural)
    # all_plants += plural_plants

    # sorting the plants alphabetically for a more aesthetically pleasing CSV file
    sorted_plants = sorted(all_plants)

    # writing to the CSV file
    with open(filename, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        for plant in sorted_plants:
            writer.writerow([plant])
            writer.writerow([plant.lower()])
