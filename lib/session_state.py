import streamlit as st

class SessionStateManager:
    """
    Manages interactive filtering state across pages.
    Allows cross-filtering (click in one chart, affects others).
    """
    
    @staticmethod
    def init_filters():
        """Initialize filter session state."""
        filters = {
            'selected_category': None,
            'selected_drug_id': None,
            'selected_abc_class': None,
            'date_range_start': None,
            'date_range_end': None,
            'search_query': '',
        }
        
        for key, default in filters.items():
            if key not in st.session_state:
                st.session_state[key] = default
    
    @staticmethod
    def set_filter(key: str, value):
        """Set a filter value."""
        st.session_state[key] = value
    
    @staticmethod
    def get_filter(key: str):
        """Get a filter value."""
        return st.session_state.get(key)
    
    @staticmethod
    def clear_filters():
        """Clear all filters."""
        SessionStateManager.init_filters()

# Usage:
# SessionStateManager.init_filters()
# SessionStateManager.set_filter('selected_category', 'Antibiotics')