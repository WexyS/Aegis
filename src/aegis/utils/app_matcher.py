import logging
from difflib import get_close_matches
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

def find_best_app_match(query: str, app_dict: Dict[str, str], cutoff: float = 0.6) -> Tuple[Optional[str], Optional[str]]:
    """
    Finds the best matching application.
    Returns (matched_name, matched_path) or (None, None).
    """
    if not query or not app_dict:
        return None, None
        
    query_clean = query.lower().strip()
    names = list(app_dict.keys())
    
    # 1. Exact match check
    if query_clean in app_dict:
        return query_clean, app_dict[query_clean]
        
    # 2. Substring match
    for name in names:
        if query_clean in name:
            return name, app_dict[name]
            
    # 3. Fuzzy match (strict cutoff)
    matches = get_close_matches(query_clean, names, n=1, cutoff=cutoff)
    if matches:
        match_name = matches[0]
        return match_name, app_dict[match_name]
        
    return None, None
