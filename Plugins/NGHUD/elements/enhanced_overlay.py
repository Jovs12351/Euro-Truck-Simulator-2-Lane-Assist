"""
Enhanced AR Overlay Renderer for ETS2LA NGHUD
Advanced road guidance, distance markers, lane indicators, and environmental awareness features.
"""

from Plugins.NGHUD.classes import HUDRenderer
from Plugins.NGHUD.themes import get_current_theme, VisualEffects, AnimationHelper
from ETS2LA.Utils.translator import _
from Plugins.AR.classes import *
import math
import time

class Renderer(HUDRenderer):
    name = _("Enhanced Overlay")
    description = _("Advanced AR overlay with road guidance, distance markers, lane indicators, and environmental awareness.")
    fps = 10  # Higher FPS for smooth animations
    
    def __init__(self, plugin):
        super().__init__(plugin)
        self.last_position = None
        self.distance_markers = []
        self.path_points = []
        self.hazard_zones = []
        
    def settings(self):
        return super().settings()
    
    def calculate_forward_positions(self, truck_data, distances=[25, 50, 100, 200]):
        """Calculate positions ahead of the truck for distance markers."""
        truck_x = truck_data["truckPlacement"]["coordinateX"]
        truck_y = truck_data["truckPlacement"]["coordinateY"]
        truck_z = truck_data["truckPlacement"]["coordinateZ"]
        truck_rotation_y = truck_data["truckPlacement"]["rotationY"] * 360
        
        forward_positions = []
        for distance in distances:
            # Calculate position ahead based on truck rotation
            forward_x = truck_x + distance * math.sin(math.radians(truck_rotation_y))
            forward_z = truck_z + distance * math.cos(math.radians(truck_rotation_y))
            
            forward_positions.append({
                "distance": distance,
                "position": Coordinate(forward_x, truck_y, forward_z),
                "coordinate": (forward_x, truck_y, forward_z)
            })
        
        return forward_positions
    
    def create_distance_markers(self, forward_positions, theme):
        """Create distance marker visuals."""
        markers = []
        current_time = time.time()
        
        for pos_data in forward_positions:
            distance = pos_data["distance"]
            position = pos_data["position"]
            
            # Scale marker based on distance
            scale = VisualEffects.get_proximity_scale(distance, 25, 200, 0.5, 1.5)
            marker_size = int(8 * scale)
            text_size = int(12 * scale)
            
            # Color based on distance
            if distance <= 50:
                marker_color = theme.STATUS_WARNING
                bg_color = Color(255, 255, 100, 40)
            elif distance <= 100:
                marker_color = theme.PRIMARY
                bg_color = Color(100, 150, 255, 30)
            else:
                marker_color = theme.TEXT_SECONDARY
                bg_color = Color(200, 200, 200, 20)
            
            # Pulsing effect for close markers
            if distance <= 25:
                pulse = theme.get_pulse_multiplier(frequency=2.0)
                marker_color = Color(
                    int(marker_color.r * pulse),
                    int(marker_color.g * pulse),
                    int(marker_color.b * pulse),
                    marker_color.a
                )
            
            # Main marker circle
            markers.extend([
                # Background glow
                Circle(
                    position,
                    radius=marker_size + 4,
                    color=Color(0, 0, 0, 0),
                    fill=bg_color,
                    fade=theme.FADES["medium"],
                    custom_distance=distance
                ),
                
                # Main marker
                Circle(
                    position,
                    radius=marker_size,
                    color=marker_color,
                    fill=Color(marker_color.r, marker_color.g, marker_color.b, 100),
                    fade=theme.FADES["medium"],
                    custom_distance=distance
                ),
                
                # Distance text
                Text(
                    Point(0, -marker_size - 8, anchor=position),
                    f"{distance}m",
                    size=text_size,
                    color=marker_color,
                    fade=theme.FADES["medium"],
                    custom_distance=distance
                )
            ])
        
        return markers
    
    def create_lane_guidance(self, truck_data, theme):
        """Create lane guidance visualization."""
        truck_x = truck_data["truckPlacement"]["coordinateX"]
        truck_y = truck_data["truckPlacement"]["coordinateY"]
        truck_z = truck_data["truckPlacement"]["coordinateZ"]
        truck_rotation_y = truck_data["truckPlacement"]["rotationY"] * 360
        
        guidance = []
        
        # Create lane boundary lines extending forward
        for side_offset in [-1.5, 1.5]:  # Left and right lane boundaries
            lane_points = []
            for forward_distance in range(10, 101, 10):  # 10m to 100m in 10m steps
                forward_x = truck_x + forward_distance * math.sin(math.radians(truck_rotation_y))
                forward_z = truck_z + forward_distance * math.cos(math.radians(truck_rotation_y))
                
                # Offset for lane boundary
                side_x = forward_x + side_offset * math.sin(math.radians(truck_rotation_y + 90))
                side_z = forward_z + side_offset * math.cos(math.radians(truck_rotation_y + 90))
                
                lane_points.append(Coordinate(side_x, truck_y, side_z))
            
            # Create lane boundary as series of connected lines
            for i in range(len(lane_points) - 1):
                distance = lane_points[i].get_distance_to(truck_x, truck_y, truck_z)
                alpha = max(50, min(150, int(200 - distance * 1.5)))
                
                guidance.append(
                    Line(
                        lane_points[i],
                        lane_points[i + 1],
                        color=Color(255, 255, 255, alpha),
                        thickness=2,
                        fade=theme.FADES["far"],
                        custom_distance=distance
                    )
                )
        
        # Center lane guidance line
        center_points = []
        for forward_distance in range(5, 51, 5):  # 5m to 50m
            forward_x = truck_x + forward_distance * math.sin(math.radians(truck_rotation_y))
            forward_z = truck_z + forward_distance * math.cos(math.radians(truck_rotation_y))
            center_points.append(Coordinate(forward_x, truck_y + 0.1, forward_z))
        
        # Create center guidance line with dynamic coloring
        truck_speed = abs(truck_data["truckFloat"]["speed"]) * 3.6  # km/h
        speed_color = theme.STATUS_SAFE if truck_speed < 60 else theme.STATUS_WARNING if truck_speed < 90 else theme.STATUS_DANGER
        
        for i in range(len(center_points) - 1):
            distance = center_points[i].get_distance_to(truck_x, truck_y, truck_z)
            
            guidance.append(
                Line(
                    center_points[i],
                    center_points[i + 1],
                    color=speed_color,
                    thickness=3,
                    fade=theme.FADES["close"],
                    custom_distance=distance
                )
            )
        
        return guidance
    
    def create_speed_zones(self, truck_data, theme):
        """Create visual speed zone indicators."""
        if not hasattr(self.plugin, 'data') or not self.plugin.data:
            return []
        
        truck_speed = abs(truck_data["truckFloat"]["speed"]) * 3.6  # km/h
        speed_limit = abs(truck_data["truckFloat"]["speedLimit"]) * 3.6
        
        if speed_limit <= 0:
            return []
        
        truck_x = truck_data["truckPlacement"]["coordinateX"]
        truck_y = truck_data["truckPlacement"]["coordinateY"]
        truck_z = truck_data["truckPlacement"]["coordinateZ"]
        truck_rotation_y = truck_data["truckPlacement"]["rotationY"] * 360
        
        zones = []
        
        # Calculate stopping distance
        stopping_distance = (truck_speed * truck_speed) / (2 * 7.5)  # Assuming 7.5 m/s² deceleration
        
        # Create speed zone visualization
        zone_distances = [stopping_distance * 0.5, stopping_distance, stopping_distance * 1.5]
        zone_colors = [theme.STATUS_SAFE, theme.STATUS_WARNING, theme.STATUS_DANGER]
        zone_widths = [3.0, 2.5, 2.0]
        
        for i, (zone_dist, zone_color, zone_width) in enumerate(zip(zone_distances, zone_colors, zone_widths)):
            if zone_dist > 200:  # Cap at reasonable distance
                continue
            
            # Create zone boundary
            forward_x = truck_x + zone_dist * math.sin(math.radians(truck_rotation_y))
            forward_z = truck_z + zone_dist * math.cos(math.radians(truck_rotation_y))
            
            # Create zone marker line across the road
            left_x = forward_x + zone_width * math.sin(math.radians(truck_rotation_y + 90))
            left_z = forward_z + zone_width * math.cos(math.radians(truck_rotation_y + 90))
            right_x = forward_x - zone_width * math.sin(math.radians(truck_rotation_y + 90))
            right_z = forward_z - zone_width * math.cos(math.radians(truck_rotation_y + 90))
            
            alpha = max(80, min(200, int(250 - zone_dist * 1.2)))
            
            zones.extend([
                Line(
                    Coordinate(left_x, truck_y + 0.5, left_z),
                    Coordinate(right_x, truck_y + 0.5, right_z),
                    color=Color(zone_color.r, zone_color.g, zone_color.b, alpha),
                    thickness=4,
                    fade=theme.FADES["medium"],
                    custom_distance=zone_dist
                ),
                
                # Zone label
                Text(
                    Point(0, 5, anchor=Coordinate(forward_x, truck_y + 1, forward_z)),
                    f"Zone {i+1}",
                    size=10,
                    color=Color(zone_color.r, zone_color.g, zone_color.b, alpha),
                    fade=theme.FADES["medium"],
                    custom_distance=zone_dist
                )
            ])
        
        return zones
    
    def create_environmental_indicators(self, truck_data, theme):
        """Create environmental awareness indicators."""
        indicators = []
        
        truck_x = truck_data["truckPlacement"]["coordinateX"]
        truck_y = truck_data["truckPlacement"]["coordinateY"]
        truck_z = truck_data["truckPlacement"]["coordinateZ"]
        
        # Weather indicator (if available in telemetry)
        # This is a placeholder - actual weather data would need to be integrated
        current_time = time.time()
        
        # Compass indicator
        truck_rotation_y = truck_data["truckPlacement"]["rotationY"] * 360
        compass_directions = [
            (0, "N", theme.PRIMARY),
            (90, "E", theme.TEXT_SECONDARY),
            (180, "S", theme.TEXT_SECONDARY),
            (270, "W", theme.TEXT_SECONDARY)
        ]
        
        for angle, direction, color in compass_directions:
            # Calculate position for compass point
            compass_distance = 30  # meters ahead
            compass_angle = truck_rotation_y + angle
            compass_x = truck_x + compass_distance * math.sin(math.radians(compass_angle))
            compass_z = truck_z + compass_distance * math.cos(math.radians(compass_angle))
            
            indicators.extend([
                Text(
                    Point(0, 10, anchor=Coordinate(compass_x, truck_y + 5, compass_z)),
                    direction,
                    size=14,
                    color=color,
                    fade=theme.FADES["close"],
                    custom_distance=30
                )
            ])
        
        # Speed trend indicator
        if hasattr(self, 'last_speed') and hasattr(self, 'last_speed_time'):
            current_speed = abs(truck_data["truckFloat"]["speed"]) * 3.6
            time_diff = current_time - self.last_speed_time
            
            if time_diff > 0.5:  # Update every 0.5 seconds
                speed_change = current_speed - self.last_speed
                trend_text = "↑" if speed_change > 2 else "↓" if speed_change < -2 else "→"
                trend_color = theme.STATUS_WARNING if abs(speed_change) > 5 else theme.TEXT_SECONDARY
                
                # Position trend indicator ahead of truck
                trend_x = truck_x + 15 * math.sin(math.radians(truck_rotation_y))
                trend_z = truck_z + 15 * math.cos(math.radians(truck_rotation_y))
                
                indicators.append(
                    Text(
                        Point(10, -10, anchor=Coordinate(trend_x, truck_y + 3, trend_z)),
                        trend_text,
                        size=16,
                        color=trend_color,
                        fade=theme.FADES["close"],
                        custom_distance=15
                    )
                )
                
                self.last_speed = current_speed
                self.last_speed_time = current_time
        else:
            self.last_speed = abs(truck_data["truckFloat"]["speed"]) * 3.6
            self.last_speed_time = current_time
        
        return indicators
    
    def draw(self):
        if not self.plugin.data:
            return
        
        self.data = []
        theme = get_current_theme()
        truck_data = self.plugin.data
        
        # Generate forward positions for distance markers
        forward_positions = self.calculate_forward_positions(truck_data)
        
        # Create all overlay elements
        distance_markers = self.create_distance_markers(forward_positions, theme)
        lane_guidance = self.create_lane_guidance(truck_data, theme)
        speed_zones = self.create_speed_zones(truck_data, theme)
        environmental_indicators = self.create_environmental_indicators(truck_data, theme)
        
        # Combine all elements
        self.data.extend(distance_markers)
        self.data.extend(lane_guidance)
        self.data.extend(speed_zones)
        self.data.extend(environmental_indicators)
        
        # Add performance info overlay (top-right)
        fps_info = f"FPS: {self.fps}"
        element_count = len(self.data)
        
        performance_anchor = Coordinate(0, 0, -5, relative=True, rotation_relative=True)
        self.data.extend([
            Text(
                Point(200, -50, anchor=performance_anchor),
                fps_info,
                size=10,
                color=theme.TEXT_MUTED
            ),
            Text(
                Point(200, -35, anchor=performance_anchor),
                f"Elements: {element_count}",
                size=10,
                color=theme.TEXT_MUTED
            )
        ])