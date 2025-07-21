"""
Enhanced Theme System for ETS2LA NGHUD
Provides unified visual styling, colors, and effects for consistent UI/UX across all HUD elements.
"""

from Plugins.AR.classes import Color, Fade
import time
import math

class ThemeManager:
    """Centralized theme management for consistent visual design."""
    
    def __init__(self, is_day=True):
        self.is_day = is_day
        self.themes = {
            "day": DayTheme(),
            "night": NightTheme()
        }
    
    def get_theme(self):
        return self.themes["day" if self.is_day else "night"]
    
    def update_time_of_day(self, is_day):
        self.is_day = is_day

class BaseTheme:
    """Base theme class with common styling elements."""
    
    # Animation timing
    PULSE_FREQUENCY = 4.0  # Hz
    FLASH_FREQUENCY = 8.0  # Hz
    FADE_DURATION = 0.5    # seconds
    
    # Common fade configurations
    FADES = {
        "close": Fade(prox_fade_end=5, prox_fade_start=15, dist_fade_start=25, dist_fade_end=60),
        "medium": Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=30, dist_fade_end=100),
        "far": Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=50, dist_fade_end=150),
        "traffic": Fade(prox_fade_end=5, prox_fade_start=15, dist_fade_start=25, dist_fade_end=120)
    }
    
    # Common sizes
    SIZES = {
        "text_tiny": 10,
        "text_small": 12,
        "text_normal": 16,
        "text_large": 24,
        "text_xl": 32,
        "border_thin": 1,
        "border_normal": 2,
        "border_thick": 4,
        "rounding_small": 4,
        "rounding_normal": 6,
        "rounding_large": 12
    }
    
    def get_pulse_multiplier(self, frequency=None):
        """Get a smooth pulse multiplier for animations."""
        freq = frequency or self.PULSE_FREQUENCY
        return 0.7 + 0.3 * (math.sin(time.time() * freq * 2 * math.pi) + 1) / 2
    
    def get_flash_multiplier(self):
        """Get a flash multiplier for urgent alerts."""
        return 0.3 + 0.7 * (math.sin(time.time() * self.FLASH_FREQUENCY * 2 * math.pi) + 1) / 2

class DayTheme(BaseTheme):
    """Light theme optimized for daytime driving."""
    
    # Primary color palette
    PRIMARY = Color(70, 130, 255, 255)      # Blue
    SECONDARY = Color(100, 200, 100, 255)   # Green
    ACCENT = Color(255, 140, 70, 255)       # Orange
    
    # Status colors
    STATUS_SAFE = Color(100, 200, 100, 255)     # Green
    STATUS_WARNING = Color(255, 200, 70, 255)   # Yellow
    STATUS_DANGER = Color(255, 100, 100, 255)   # Red
    STATUS_CRITICAL = Color(255, 50, 50, 255)   # Bright Red
    
    # Background colors (more transparent for day)
    BG_NORMAL = Color(255, 255, 255, 15)
    BG_ACTIVE = Color(255, 255, 255, 25)
    BG_WARNING = Color(255, 255, 150, 20)
    BG_DANGER = Color(255, 150, 150, 25)
    
    # Border colors
    BORDER_NORMAL = Color(255, 255, 255, 40)
    BORDER_ACTIVE = Color(200, 200, 255, 60)
    BORDER_WARNING = Color(255, 200, 100, 70)
    BORDER_DANGER = Color(255, 100, 100, 80)
    
    # Text colors
    TEXT_PRIMARY = Color(255, 255, 255, 220)
    TEXT_SECONDARY = Color(200, 200, 200, 180)
    TEXT_MUTED = Color(160, 160, 160, 140)
    
    # Traffic light specific
    TRAFFIC_RED = Color(255, 80, 80, 255)
    TRAFFIC_YELLOW = Color(255, 220, 80, 255)
    TRAFFIC_GREEN = Color(80, 255, 80, 255)

class NightTheme(BaseTheme):
    """Dark theme optimized for nighttime driving."""
    
    # Primary color palette (more saturated for night visibility)
    PRIMARY = Color(100, 160, 255, 255)     # Brighter Blue
    SECONDARY = Color(120, 255, 120, 255)   # Brighter Green
    ACCENT = Color(255, 160, 100, 255)      # Brighter Orange
    
    # Status colors (more intense)
    STATUS_SAFE = Color(120, 255, 120, 255)
    STATUS_WARNING = Color(255, 220, 100, 255)
    STATUS_DANGER = Color(255, 120, 120, 255)
    STATUS_CRITICAL = Color(255, 80, 80, 255)
    
    # Background colors (less transparent for night)
    BG_NORMAL = Color(40, 40, 40, 60)
    BG_ACTIVE = Color(60, 60, 80, 80)
    BG_WARNING = Color(80, 80, 40, 70)
    BG_DANGER = Color(80, 40, 40, 80)
    
    # Border colors
    BORDER_NORMAL = Color(100, 100, 100, 80)
    BORDER_ACTIVE = Color(120, 120, 200, 120)
    BORDER_WARNING = Color(200, 180, 100, 140)
    BORDER_DANGER = Color(200, 100, 100, 160)
    
    # Text colors (brighter for night visibility)
    TEXT_PRIMARY = Color(255, 255, 255, 255)
    TEXT_SECONDARY = Color(220, 220, 220, 200)
    TEXT_MUTED = Color(180, 180, 180, 160)
    
    # Traffic light specific (more vivid)
    TRAFFIC_RED = Color(255, 100, 100, 255)
    TRAFFIC_YELLOW = Color(255, 240, 100, 255)
    TRAFFIC_GREEN = Color(100, 255, 100, 255)

class VisualEffects:
    """Collection of reusable visual effects."""
    
    @staticmethod
    def get_proximity_scale(distance, min_distance=20, max_distance=100, min_scale=0.8, max_scale=1.5):
        """Scale elements based on distance for better depth perception."""
        if distance <= min_distance:
            return max_scale
        elif distance >= max_distance:
            return min_scale
        else:
            ratio = (max_distance - distance) / (max_distance - min_distance)
            return min_scale + (max_scale - min_scale) * ratio
    
    @staticmethod
    def get_urgency_pulse(urgency_level, base_alpha=255):
        """Get pulsing alpha based on urgency level."""
        if urgency_level == "critical":
            pulse = (math.sin(time.time() * 6) + 1) * 0.3 + 0.4
            return int(base_alpha * pulse)
        elif urgency_level == "high":
            pulse = (math.sin(time.time() * 3) + 1) * 0.2 + 0.6
            return int(base_alpha * pulse)
        else:
            return base_alpha
    
    @staticmethod
    def get_warning_flash(warning_active, base_color):
        """Get flashing color for warnings."""
        if not warning_active:
            return base_color
        
        flash = (math.sin(time.time() * 4) + 1) * 0.5
        return Color(
            min(255, int(base_color.r + (255 - base_color.r) * flash * 0.3)),
            min(255, int(base_color.g + (255 - base_color.g) * flash * 0.3)),
            min(255, int(base_color.b + (255 - base_color.b) * flash * 0.3)),
            base_color.a
        )

class StatusManager:
    """Manages visual status states for various UI elements."""
    
    STATUS_HIERARCHY = ["normal", "info", "warning", "danger", "critical"]
    
    @staticmethod
    def get_status_colors(status, theme):
        """Get appropriate colors for a given status."""
        color_map = {
            "normal": {
                "bg": theme.BG_NORMAL,
                "border": theme.BORDER_NORMAL,
                "text": theme.TEXT_PRIMARY
            },
            "info": {
                "bg": theme.BG_ACTIVE,
                "border": theme.BORDER_ACTIVE,
                "text": theme.PRIMARY
            },
            "warning": {
                "bg": theme.BG_WARNING,
                "border": theme.BORDER_WARNING,
                "text": theme.STATUS_WARNING
            },
            "danger": {
                "bg": theme.BG_DANGER,
                "border": theme.BORDER_DANGER,
                "text": theme.STATUS_DANGER
            },
            "critical": {
                "bg": theme.BG_DANGER,
                "border": theme.BORDER_DANGER,
                "text": theme.STATUS_CRITICAL
            }
        }
        return color_map.get(status, color_map["normal"])
    
    @staticmethod
    def get_highest_status(statuses):
        """Get the highest priority status from a list."""
        hierarchy_indices = {status: i for i, status in enumerate(StatusManager.STATUS_HIERARCHY)}
        return max(statuses, key=lambda s: hierarchy_indices.get(s, 0))

class AnimationHelper:
    """Helper class for consistent animations across UI elements."""
    
    @staticmethod
    def ease_in_out(t):
        """Smooth ease-in-out animation curve."""
        return t * t * (3 - 2 * t)
    
    @staticmethod
    def ease_out_elastic(t, amplitude=1, period=0.3):
        """Elastic ease-out for bouncy effects."""
        if t == 0 or t == 1:
            return t
        return amplitude * (2 ** (-10 * t)) * math.sin((t - period/4) * (2 * math.pi) / period) + 1
    
    @staticmethod
    def get_transition_value(start_time, duration, start_value, end_value, ease_func=None):
        """Get animated value between start and end based on time."""
        if ease_func is None:
            ease_func = AnimationHelper.ease_in_out
        
        elapsed = time.time() - start_time
        if elapsed >= duration:
            return end_value
        
        t = elapsed / duration
        eased_t = ease_func(t)
        return start_value + (end_value - start_value) * eased_t

# Global theme instance
_theme_manager = ThemeManager()

def get_theme_manager():
    """Get the global theme manager instance."""
    return _theme_manager

def get_current_theme():
    """Get the currently active theme."""
    return _theme_manager.get_theme()