import collections
if not hasattr(collections, 'Callable'):
    import collections.abc
    collections.Callable = collections.abc.Callable

import requests
from bs4 import BeautifulSoup

# Define headers to simulate a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/90.0.4430.93 Safari/537.36'
}

def get_player_profile_url(player_name):
    """
    1) Hits the ESPNcricinfo search endpoint for the given player_name.
    2) Parses the search results page to find the first link that points
       to a player profile.
    3) Returns the full URL to that player profile, or None if not found.
    """
    search_url = f"https://search.espncricinfo.com/ci/content/player/search.html?search={player_name}"
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve data from search endpoint: HTTP {response.status_code}")
        return None
    
    # Parse the search results page
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for the first link that points to a player profile
    a_tags = soup.find_all('a', href=True)
    for a in a_tags:
        href = a['href']
        if '/player/' in href:
            # Construct a full URL in case the link is relative
            if href.startswith('http'):
                full_url = href
            else:
                full_url = "https://www.espncricinfo.com" + href
                print(full_url)
            
            return full_url

    print("Player not found in search results.")
    return None

def get_player_role_from_profile_url(profile_url):
    """
    Takes a player profile URL and attempts to parse the role
    from that page's HTML.
    """
    response = requests.get(profile_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve player profile data: HTTP {response.status_code}")
        return None
    
    # Parse the player profile page
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # The player's role might be contained in a label "Role"
    # or in the new ESPNcricinfo layout, we might look for specific selectors
    # (e.g., <div data-cricket-player-role="...">). Adjust as needed.
    
    # Example heuristic: find any span/div that has "Role" in the text
    role_label = soup.find(lambda tag: tag.name in ["span", "p"] and "Playing Role" in tag.get_text())
    if role_label:
        # Try to get the next element that holds the actual role
        role_element = role_label.find_next_sibling(text=True)
        if role_element:
            return role_element.strip()
        else:
            # Alternatively, if the structure is different, try to get parent text
            return role_label.parent.get_text(strip=True).replace("Role", "").strip()
    
    print("Role information not found in profile.")
    return None

def get_player_role(player_name):
    """
    High-level function:
    1) Get the player's profile URL by searching for the player_name.
    2) "Click" on that URL by making a GET request.
    3) Parse the returned page for the player's role.
    """
    profile_url = get_player_profile_url(player_name)
    if not profile_url:
        return None
    role = get_player_role_from_profile_url(profile_url)
    return role

# Example usage:
if __name__ == "__main__":
    player_name = 'Virat Kohli'
    role = get_player_role(player_name)
    if role:
        print(f"Player role for '{player_name}': {role}")
    else:
        print(f"Could not determine role for '{player_name}'.")
