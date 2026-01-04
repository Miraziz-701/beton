from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="admin")

def get_address(lat, lon):
    location = geolocator.reverse((lat, lon), language="uz")
    return location.address if location else "Manzil topilmadi"