import requests
import re
import geocoder
from rich.console import Console
from rich.panel import Panel
import typer

app=typer.Typer()

def style_text(text):
  console = Console()
  panel = Panel(text, title='WeatherCli ⛅️ by @swadhinbiswas', style='bold green', border_style='bold green',title_align="center")
  console.print(panel, justify="center")



def findcity():
    g = geocoder.ip('me')
    return g.city
  
def findcountry():
    g = geocoder.ip('me')
    nameofcountry = g.country.lower()
    return nameofcountry

def remove_text(text, pattern):
  return re.sub(pattern, '', text)


def weather():
  city = findcity()
  url=f'https://wttr.in/{city}'
  try:
    response = requests.get(url,verify=False)
  except:
    print('Could not get weather forecast for',city)
    return
  if response.status_code == 200:
    text = response.text[:-127]
    style_text(f"Weather forecast for {city}")
    print(text)
    
  else:
    print('Could not get weather forecast for',city)

weather()