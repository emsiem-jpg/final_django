import logging
from django import template

register = template.Library()
logger = logging.getLogger(__name__)

@register.filter
def dict_get(dictionary, key):
    """
    Template filter that returns a value from a dictionary by the given key.

    Usage in templates:
        {{ my_dict|dict_get:"my_key" }}

    Args:
        dictionary (dict): The dictionary to look in.
        key: The key to retrieve the value for.

    Returns:
        The value associated with the key, or None if the key does not exist.
    """
    try:
        return dictionary.get(key)
    except AttributeError:
        logger.warning(f"dict_get użyty na obiekcie, który nie jest dict: {type(dictionary)}")
        return None

@register.filter
def get_item(dictionary, key):
    """
    Template filter that retrieves a value from a dictionary by key.

    Usage in templates:
        {{ my_dict|get_item:"some_key" }}

    Args:
        dictionary (dict): The dictionary to search.
        key: The key to find in the dictionary.

    Returns:
        The value for the given key, or None if not found or input invalid.
    """
    try:
        return dictionary.get(key)
    except AttributeError:
        logger.warning(f"get_item użyty na obiekcie, który nie jest dict: {type(dictionary)}")
        return None
