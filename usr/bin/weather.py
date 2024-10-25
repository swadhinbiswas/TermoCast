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
  """
  Fetches and displays the weather forecast for a specified city.
  This function retrieves the city name using the `findcity` function,
  constructs a URL for the weather forecast, and makes an HTTP GET request
  to fetch the weather data. If the request is successful, it prints the
  weather forecast. If the request fails, it prints an error message.
  Note:
    The function suppresses SSL certificate verification warnings by setting
    `verify=False` in the `requests.get` call.
  Exceptions:
    Prints an error message if the HTTP request fails.
  Returns:
    None
  """
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