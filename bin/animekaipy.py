from providers.Animekai.Scraper.searchAnimedetails import searchAnimeandetails, getAnimeDetails
from providers.Animekai.Scraper.searchEpisodedetails import getanimepisode
from providers.Animekai.Scraper.getEpisodestreams import serverextractor
from bs4 import BeautifulSoup
import requests
import json
from config.animekai import configure


name = "Farming Life In Another World"
response=searchAnimeandetails(name)
data=getAnimeDetails(response[0]["Imp"]["Watch Link"])

aaa=getanimepisode(response[0]["Imp"]["Watch Link"])


hianime,animepahe=serverextractor(aaa[0])
print(hianime)
print(animepahe)








