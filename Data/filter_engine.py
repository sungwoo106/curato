# filters by distance, rating, price, congestion, etc.

from typing import List, Dict, Any, Optional

def filter_results(
        results: List[Dict[str, Any]],
        *,
        min_rating: Optional[float] = None,
        max_distance: Optional[float] = None,
        max_price: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Filters a list of results based on specified criteria.
    
    @param results: List of results to filter.
    @param min_rating: Minimum rating to filter by (optional).
    @param max_distance: Maximum distance to filter by (optional).
    @param max_price: Maximum price to filter by (optional).
    @return: Filtered list of results.
    """
    
    filtered_results = []
    
    for item in results:

        rating = item.get('rating', None)
        distance = item.get('distance', None)
        price = item.get('price', None)
        
        if min_rating is not None:
            if rating is None or rating < min_rating:
                continue
        if max_distance is not None:
            if distance is None or distance > max_distance:
                continue
        if max_price is not None:
            if price is None or price > max_price:
                continue

        filtered_results.append(item)
    
    return filtered_results