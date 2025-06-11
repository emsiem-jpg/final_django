def get_koszyk(request):
    """
    Retrieves the current cart from the user's session.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        list: List of attraction IDs currently in the cart.
    """
    return request.session.get('koszyk', [])


def save_koszyk(request, koszyk):
    """
    Saves the updated cart to the user's session.

    Args:
        request (HttpRequest): The HTTP request object.
        koszyk (list): List of attraction IDs to store in session.
    """
    request.session['koszyk'] = koszyk


def add_to_koszyk(request, atrakcja_id):
    """
    Adds an attraction ID to the user's cart if it's not already there.

    Args:
        request (HttpRequest): The HTTP request object.
        atrakcja_id (int): The ID of the attraction to add.

    Returns:
        bool: True if added, False if it was already in the cart.
    """
    koszyk = get_koszyk(request)
    if atrakcja_id not in koszyk:
        koszyk.append(atrakcja_id)
        save_koszyk(request, koszyk)
        return True
    return False


def remove_from_koszyk(request, atrakcja_id):
    """
    Removes an attraction ID from the user's cart if it exists.

    Args:
        request (HttpRequest): The HTTP request object.
        atrakcja_id (int): The ID of the attraction to remove.

    Returns:
        bool: True if removed, False if the ID was not in the cart.
    """
    koszyk = get_koszyk(request)
    if atrakcja_id in koszyk:
        koszyk.remove(atrakcja_id)
        save_koszyk(request, koszyk)
        return True
    return False
