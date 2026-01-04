import re

def extract_coords_google(url: str):
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return lat, lon
    return None

def extract_coords_google_q(url: str):
    import urllib.parse as up
    parsed = up.urlparse(url)
    qs = up.parse_qs(parsed.query)

    if "q" in qs and "," in qs["q"][0]:
        lat, lon = qs["q"][0].split(",")
        return float(lat), float(lon)
    return None

def extract_coords_yandex(url: str):
    import urllib.parse as up
    parsed = up.urlparse(url)
    qs = up.parse_qs(parsed.query)

    if "ll" in qs:
        lon, lat = qs["ll"][0].split(",")
        return float(lat), float(lon)
    return None