from Plugins.NGHUD.classes import HUDWidget
from ETS2LA.Utils.translator import _
from Plugins.AR.classes import *
import time
import math

class Widget(HUDWidget):
    name = _("Speed")
    description = _("Enhanced speed display with dynamic visual feedback, speed limit warnings, and compliance indicators.")
    fps = 5  # Higher FPS for smoother animations
    
    last_speedlimit = 0
    last_limit_time = 0
    
    def __init__(self, plugin):
        super().__init__(plugin)
    
    def settings(self):
        return super().settings()
    
    def get_speed_status(self, current_speed, speed_limit):
        """Determine speed compliance status."""
        if speed_limit <= 0:
            return "no_limit"
        
        speed_ratio = current_speed / speed_limit
        
        if speed_ratio <= 0.85:
            return "safe"
        elif speed_ratio <= 1.0:
            return "approaching"
        elif speed_ratio <= 1.15:
            return "over"
        else:
            return "excessive"
    
    def get_status_colors(self, status):
        """Get colors for different speed statuses."""
        colors = {
            "safe": {
                "bg": Color(150, 255, 150, 30),
                "border": Color(100, 200, 100, 60),
                "text": Color(255, 255, 255, 200)
            },
            "approaching": {
                "bg": Color(255, 255, 150, 35),
                "border": Color(200, 200, 100, 70),
                "text": Color(255, 255, 255, 220)
            },
            "over": {
                "bg": Color(255, 200, 150, 40),
                "border": Color(255, 150, 100, 80),
                "text": Color(255, 255, 255, 240)
            },
            "excessive": {
                "bg": Color(255, 150, 150, 50),
                "border": Color(255, 100, 100, 100),
                "text": Color(255, 255, 255, 255)
            },
            "no_limit": {
                "bg": Color(255, 255, 255, 15),
                "border": Color(255, 255, 255, 25),
                "text": Color(255, 255, 255, 200)
            }
        }
        return colors.get(status, colors["no_limit"])
        
    def draw(self, offset_x, width, height=60):  # Increased height for more info
        if not self.plugin.data:
            return
        
        raw_speed = abs(self.plugin.data["truckFloat"]["speed"])
        game = self.plugin.data["scsValues"]["game"]
        if game == "ATS":
            speed = raw_speed * 3.6 * 0.621371
            unit = "mph"
        else:
            speed = raw_speed * 3.6
            unit = "km/h"

        # Update speed limit tracking
        current_limit = abs(self.plugin.data["truckFloat"]["speedLimit"])
        if current_limit != self.last_speedlimit:
            self.last_speedlimit = current_limit
            self.last_limit_time = time.time()
        
        # Convert speed limit to display units
        limit = self.last_speedlimit
        if game == "ATS":
            limit = limit * 3.6 * 0.621371
        else:
            limit = limit * 3.6
        
        # Determine speed status
        status = self.get_speed_status(speed, limit)
        colors = self.get_status_colors(status)
        
        # Add pulsing effect for excessive speed and approaching limit
        pulse_multiplier = 1.0
        if status == "excessive":
            pulse_multiplier = 0.7 + 0.3 * (math.sin(time.time() * 6) + 1) / 2
        elif status == "over":
            # Gentler pulse for "over" status
            pulse_multiplier = 0.9 + 0.1 * (math.sin(time.time() * 3) + 1) / 2
        
        # Apply pulse to colors if needed
        if status in ["excessive", "over"]:
            border_color = Color(
                int(colors["border"].r * pulse_multiplier),
                int(colors["border"].g * pulse_multiplier), 
                int(colors["border"].b * pulse_multiplier),
                colors["border"].a
            )
            bg_color = Color(
                int(colors["bg"].r * pulse_multiplier),
                int(colors["bg"].g * pulse_multiplier),
                int(colors["bg"].b * pulse_multiplier),
                colors["bg"].a
            )
        else:
            border_color = colors["border"]
            bg_color = colors["bg"]
        
        self.data = []
        
        # Main background with status-based coloring
        self.data.append(
            Rectangle(
                Point(offset_x, 0, anchor=self.plugin.anchor),
                Point(width + offset_x, height, anchor=self.plugin.anchor),
                color=border_color,
                fill=bg_color,
                rounding=8,
            )
        )
        
        # Speed limit progress bar (only if limit exists)
        if limit > 0 and status != "no_limit":
            progress_width = width - 20
            progress_height = 4
            progress_y = height - 8
            
            # Background bar
            self.data.append(
                Rectangle(
                    Point(offset_x + 10, progress_y, anchor=self.plugin.anchor),
                    Point(offset_x + 10 + progress_width, progress_y + progress_height, anchor=self.plugin.anchor),
                    color=Color(100, 100, 100, 100),
                    fill=Color(50, 50, 50, 50),
                    rounding=2,
                )
            )
            
            # Progress fill
            progress_ratio = min(speed / limit, 1.5)  # Cap at 150% for visual purposes
            fill_width = progress_width * min(progress_ratio, 1.0)
            
            # Color based on progress
            if progress_ratio <= 0.85:
                progress_color = Color(100, 255, 100, 150)
            elif progress_ratio <= 1.0:
                progress_color = Color(255, 255, 100, 150)
            else:
                progress_color = Color(255, 100, 100, 180)
            
            self.data.append(
                Rectangle(
                    Point(offset_x + 10, progress_y, anchor=self.plugin.anchor),
                    Point(offset_x + 10 + fill_width, progress_y + progress_height, anchor=self.plugin.anchor),
                    color=Color(0, 0, 0, 0),
                    fill=progress_color,
                    rounding=2,
                )
            )
            
            # Overflow indicator for excessive speed
            if progress_ratio > 1.0:
                overflow_width = progress_width * min(progress_ratio - 1.0, 0.5)
                self.data.append(
                    Rectangle(
                        Point(offset_x + 10, progress_y - 2, anchor=self.plugin.anchor),
                        Point(offset_x + 10 + overflow_width, progress_y + progress_height + 2, anchor=self.plugin.anchor),
                        color=Color(255, 50, 50, 200),
                        fill=Color(255, 50, 50, 100),
                        rounding=3,
                    )
                )
        
        # Current speed (large, prominent)
        speed_size = 28 if status != "excessive" else 32
        self.data.append(
            Text(
                Point(10 + offset_x, 5, anchor=self.plugin.anchor),
                text=f"{speed:.0f}",
                color=colors["text"],
                size=speed_size
            )
        )
        
        # Unit display
        self.data.append(
            Text(
                Point(width-35 + offset_x, height-25, anchor=self.plugin.anchor),
                text=f"{unit}",
                color=Color(200, 200, 200, 180),
                size=12
            )
        )
        
        # Speed limit and status display
        if limit > 0:
            # Speed limit value
            limit_text_color = Color(255, 255, 255, 180) if time.time() - self.last_limit_time > 5 else Color(255, 255, 100, 220)
            self.data.append(
                Text(
                    Point(10 + offset_x, 35, anchor=self.plugin.anchor),
                    text=f"{_('Limit')}: {limit:.0f}",
                    color=limit_text_color,
                    size=12
                )
            )
            
            # Status indicator
            status_texts = {
                "safe": "✓",
                "approaching": "⚠",
                "over": "!",
                "excessive": "!!!"
            }
            
            if status in status_texts:
                status_color = Color(100, 255, 100, 200) if status == "safe" else Color(255, 150, 100, 220)
                if status == "excessive":
                    status_color = Color(255, 100, 100, 255)
                
                self.data.append(
                    Text(
                        Point(width-20 + offset_x, 8, anchor=self.plugin.anchor),
                        text=status_texts[status],
                        color=status_color,
                        size=16 if status != "excessive" else 20
                    )
                )
            
            # Speed difference indicator
            speed_diff = speed - limit
            if abs(speed_diff) > 1:  # Only show if significant difference
                diff_color = Color(100, 255, 100, 180) if speed_diff < 0 else Color(255, 150, 100, 200)
                if speed_diff > limit * 0.2:  # More than 20% over
                    diff_color = Color(255, 100, 100, 220)
                
                diff_text = f"{speed_diff:+.0f}"
                self.data.append(
                    Text(
                        Point(width-55 + offset_x, height-25, anchor=self.plugin.anchor),
                        text=diff_text,
                        color=diff_color,
                        size=10
                    )
                )
        
        # New speed limit notification
        if time.time() - self.last_limit_time < 3 and limit > 0:
            self.data.append(
                Text(
                    Point(width//2 + offset_x - 25, height + 5, anchor=self.plugin.anchor),
                    text=f"{_('New Limit')}: {limit:.0f}",
                    color=Color(255, 255, 100, 200),
                    size=11
                )
            )