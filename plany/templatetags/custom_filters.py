from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter that returns the value for a given key from a dictionary.

    Example usage in template:
        {{ my_dict|get_item:"some_key" }}

    Args:
        dictionary (dict): The dictionary to retrieve the value from.
        key (str): The key to look up in the dictionary.

    Returns:
        Any: The value associated with the key, or None if not found.
    """
    return dictionary.get(key)
