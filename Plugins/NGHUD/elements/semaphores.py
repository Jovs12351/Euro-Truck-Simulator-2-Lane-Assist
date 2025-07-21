from Modules.Semaphores.classes import TrafficLight
from Plugins.NGHUD.classes import HUDRenderer
from ETS2LA.Utils.translator import _
from Plugins.AR.classes import *
import math
import time

class Renderer(HUDRenderer):
    name = _("Traffic Lights")
    description = _("Enhanced traffic light visualization with dynamic indicators and proximity warnings.")
    fps = 5  # Higher FPS for smoother animations
    
    def __init__(self, plugin):
        super().__init__(plugin)
    
    def settings(self):
        return super().settings()
    
    def get_urgency_level(self, time_left, state):
        """Calculate urgency level based on time and state."""
        if state == "red":
            if time_left < 5:
                return "critical"
            elif time_left < 10:
                return "high"
            else:
                return "normal"
        elif state == "yellow":
            return "critical"
        elif state == "green":
            if time_left < 3:
                return "critical"
            elif time_left < 8:
                return "high" 
            else:
                return "normal"
        return "normal"
    
    def get_enhanced_color(self, base_color, urgency, distance):
        """Get enhanced color based on urgency and distance."""
        r, g, b = base_color
        
        # Increase intensity for closer distances
        proximity_multiplier = max(0.5, min(2.0, 100 / max(distance, 20)))
        
        if urgency == "critical":
            # Pulsing effect for critical states
            pulse = (math.sin(time.time() * 4) + 1) * 0.3 + 0.7
            return Color(int(r * pulse * proximity_multiplier), 
                        int(g * pulse * proximity_multiplier), 
                        int(b * pulse * proximity_multiplier), 255)
        elif urgency == "high":
            return Color(int(r * 1.2 * proximity_multiplier), 
                        int(g * 1.2 * proximity_multiplier), 
                        int(b * 1.2 * proximity_multiplier), 220)
        else:
            return Color(int(r * proximity_multiplier), 
                        int(g * proximity_multiplier), 
                        int(b * proximity_multiplier), 180)
        
    def draw(self):
        if not self.plugin.data:
            return

        self.data = []
        semaphores = self.plugin.modules.Semaphores.run()
        traffic_lights = [semaphore for semaphore in semaphores if isinstance(semaphore, TrafficLight)]
        
        truck_x = self.plugin.data["truckPlacement"]["coordinateX"]
        truck_y = self.plugin.data["truckPlacement"]["coordinateY"]
        truck_z = self.plugin.data["truckPlacement"]["coordinateZ"]
        truck_speed = abs(self.plugin.data["truckFloat"]["speed"]) * 3.6  # km/h
        
        data = []
        for traffic_light in traffic_lights:
            traffic_light_anchor = Coordinate(
                traffic_light.position.x + 512 * traffic_light.cx, 
                traffic_light.position.y + 2.5, 
                traffic_light.position.z + 512 * traffic_light.cy
            )
            
            distance = traffic_light_anchor.get_distance_to(truck_x, truck_y, truck_z)
            if distance > 150:  # Extended range for better visibility
                continue
            
            # Determine current state
            state = "red"
            if traffic_light.color() == (0, 255, 0):
                state = "green"
            elif traffic_light.color() == (255, 255, 0):
                state = "yellow"
            
            urgency = self.get_urgency_level(traffic_light.time_left, state)
            enhanced_color = self.get_enhanced_color(traffic_light.color(), urgency, distance)
            
            # Calculate stopping distance
            stopping_distance = (truck_speed * truck_speed) / (2 * 7.5)  # Assuming 7.5 m/s² deceleration
            can_stop_in_time = distance > stopping_distance + 10  # 10m buffer
            
            # Main traffic light indicator (larger and more prominent)
            main_width = 80 + (100 - distance) * 0.5  # Scale with distance
            main_height = 35 + (100 - distance) * 0.3
            
            # Background with dynamic opacity
            bg_alpha = max(50, min(150, int(200 - distance * 1.5)))
            data.extend([
                # Outer glow effect for critical states
                Rectangle(
                    Point(35, -5, anchor=traffic_light_anchor),
                    Point(105, 35, anchor=traffic_light_anchor),
                    color=Color(0, 0, 0, 0),
                    fill=enhanced_color if urgency == "critical" else Color(0, 0, 0, 0),
                    rounding=12,
                    fade=Fade(prox_fade_end=5, prox_fade_start=15, dist_fade_start=25, dist_fade_end=100),
                    custom_distance=distance
                ),
                
                # Main indicator background
                Rectangle(
                    Point(40, 0, anchor=traffic_light_anchor),
                    Point(40 + main_width, main_height, anchor=traffic_light_anchor),
                    color=enhanced_color, 
                    fill=Color(enhanced_color.r, enhanced_color.g, enhanced_color.b, bg_alpha), 
                    rounding=8,
                    fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=30, dist_fade_end=120),
                    custom_distance=distance
                ),
                
                # State indicator circle
                Circle(
                    Point(50, main_height // 2, anchor=traffic_light_anchor),
                    radius=8,
                    color=enhanced_color,
                    fill=enhanced_color,
                    fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=30, dist_fade_end=120),
                    custom_distance=distance
                ),
                
                # Time display with urgency formatting
                Text(
                    Point(65, 5, anchor=traffic_light_anchor),
                    f"{traffic_light.time_left:.0f}s",
                    size=18 if urgency == "critical" else 16,
                    color=enhanced_color if urgency != "normal" else Color(255, 255, 255, 200), 
                    fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=30, dist_fade_end=120),
                    custom_distance=distance
                ),
                
                # Distance indicator
                Text(
                    Point(65, main_height - 15, anchor=traffic_light_anchor),
                    f"{distance:.0f}m",
                    size=12,
                    color=Color(200, 200, 200, 180), 
                    fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=30, dist_fade_end=120),
                    custom_distance=distance
                )
            ])
            
            # Warning indicators for critical situations
            if not can_stop_in_time and state in ["red", "yellow"] and distance < 80:
                # Warning triangle
                data.extend([
                    Polygon(
                        [
                            Point(25, 5, anchor=traffic_light_anchor),
                            Point(35, 5, anchor=traffic_light_anchor), 
                            Point(30, 15, anchor=traffic_light_anchor)
                        ],
                        color=Color(255, 100, 0, 255),
                        fill=Color(255, 100, 0, 150),
                        fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=30, dist_fade_end=80),
                        custom_distance=distance
                    ),
                    Text(
                        Point(28, 8, anchor=traffic_light_anchor),
                        "!",
                        size=10,
                        color=Color(255, 255, 255, 255),
                        fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=30, dist_fade_end=80),
                        custom_distance=distance
                    )
                ])
            
            # Speed recommendation indicator
            if distance < 60 and state == "yellow":
                recommended_action = "STOP" if can_stop_in_time else "GO"
                rec_color = Color(255, 100, 100, 200) if recommended_action == "STOP" else Color(100, 255, 100, 200)
                
                data.extend([
                    Text(
                        Point(45, main_height + 5, anchor=traffic_light_anchor),
                        recommended_action,
                        size=14,
                        color=rec_color,
                        fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=25, dist_fade_end=60),
                        custom_distance=distance
                    )
                ])
            
        self.data += data