# lib/colors.py
from lib.theme import ThemeManager


class ColorPalette:
    """Unified color palette for all charts (aligns with ThemeManager spec)."""

    @staticmethod
    def get_chart_colors():
        palette = ThemeManager.get_palette()
        return {
            'primary': palette['positive_chart_1'],
            'secondary': palette['positive_chart_2'],
            'tertiary': palette['positive_chart_3'],
            'success': palette['success'],
            'warning': palette['warning'],
            'danger': palette['danger'],
            'bg': palette['chart_bg'],
            'grid': palette['chart_grid'],
            'text': palette['text_primary'],
        }

    @staticmethod
    def get_status_colors():
        return {
            'Safe': '#1BBD6D',
            'Yellow': '#FFA940',
            'Red': '#D42E1B',
        }

    @staticmethod
    def get_abc_colors():
        return {
            'A': '#FF6B6B',
            'B': '#FFA940',
            'C': '#5DD27D',
        }


# Usage:
# colors = ColorPalette.get_chart_colors()
# fig.update_layout(
#     plot_bgcolor=colors['bg'],
#     paper_bgcolor=colors['bg'],
#     font=dict(color=colors['text']),
# )