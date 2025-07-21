# Framework
from ETS2LA.Events import *
from ETS2LA.Plugin import *
from ETS2LA.UI import * 
from Plugins.Map.classes import *
from Plugins.AR.classes import *
from Modules.Semaphores.classes import TrafficLight
import ETS2LA.Utils.settings as settings
from ETS2LA.Utils.translator import _

# General imports
import threading
import logging
import random
import time
import math

class Settings(ETS2LAPage):
    url = "/settings/HUD"
    refresh_rate = 0.5
    location = ETS2LAPageLocation.SETTINGS
    title = "HUD"
    
    def handle_offset_x(self, value):
        settings.Set("HUD", "offset_x", value)
        
    def handle_offset_y(self, value):
        settings.Set("HUD", "offset_y", value)
        
    def handle_offset_z(self, value):
        settings.Set("HUD", "offset_z", value)
        
    def handle_scale(self, value):
        settings.Set("HUD", "scale", value)
        
    def handle_refresh_rate(self, value):
        settings.Set("HUD", "refresh_rate", value)
        
    def handle_show_navigation(self, *args):
        if args:
            value = args[0]
        else:
            value = not settings.Get("HUD", "show_navigation", True)
            
        settings.Set("HUD", "show_navigation", value)
    
    def handle_show_acc_info(self, *args):
        if args:
            value = args[0]
        else:
            value = not settings.Get("HUD", "show_acc_info", True)
            
        settings.Set("HUD", "show_acc_info", value)
    
    def handle_draw_steering(self, *args):
        if args:
            value = args[0]
        else:
            value = not settings.Get("HUD", "draw_steering", False)
            
        settings.Set("HUD", "draw_steering", value)
        
    def handle_show_traffic_light_times(self, *args):
        if args:
            value = args[0]
        else:
            value = not settings.Get("HUD", "show_traffic_light_times", True)
            
        settings.Set("HUD", "show_traffic_light_times", value)
        
    def handle_draw_wheel_paths(self, *args):
        if args:
            value = args[0]
        else:
            value = not settings.Get("HUD", "draw_wheel_paths", False)
            
        settings.Set("HUD", "draw_wheel_paths", value)
    
    def render(self):
        TitleAndDescription(
            title=_("HUD"),
            description=_("This plugin provides a HUD using the AR plugin as the renderer.")
        )

        with Tabs():
            with Tab(_("General"), styles.FlexVertical() + styles.Gap("24px")):
                with Container(styles.FlexHorizontal() + styles.Gap("24px")):
                    SliderWithTitleDescription(
                        title=_("Refresh Rate"),
                        description=_("The rate at which the HUD updates. It's not recommended to increase this value too much."),
                        min=1,
                        max=10,
                        step=1,
                        default=settings.Get("HUD", "refresh_rate", 2),
                        suffix=" fps",
                        changed=self.handle_refresh_rate,
                    )
                    SliderWithTitleDescription(
                        title=_("Scale"),
                        description=_("The scale of the HUD elements."),
                        min=0.5,
                        max=2,
                        step=0.05,
                        default=settings.Get("HUD", "scale", 1),
                        suffix="x",
                        changed=self.handle_scale,
                    )
                    
                InputWithTitleDescription(
                    title=_("Offset X"),
                    description=_("The X offset (side to side) of the HUD elements."),
                    type="number",
                    default=settings.Get("HUD", "offset_x", 0),
                    changed=self.handle_offset_x,
                )
                
                InputWithTitleDescription(
                    title=_("Offset Y"),
                    description=_("The Y offset (top to bottom) of the HUD elements."),
                    type="number",
                    default=settings.Get("HUD", "offset_y", 0),
                    changed=self.handle_offset_y,
                )
                
                InputWithTitleDescription(
                    title=_("Offset Z"),
                    description=_("The Z offset (distance) of the HUD elements."),
                    type="number",
                    default=settings.Get("HUD", "offset_z", 0),
                    changed=self.handle_offset_z,
                )

            with Tab(_("HUD Elements"), styles.FlexVertical() + styles.Gap("24px")):
                CheckboxWithTitleDescription(
                    title=_("Show Navigation"),
                    description=_("When enabled, the HUD will display navigation information."),
                    default=settings.Get("HUD", "show_navigation", True),
                    changed=self.handle_show_navigation,
                )
                CheckboxWithTitleDescription(
                    title=_("Show ACC Info"),
                    description=_("When enabled, the HUD will display adaptive cruise control information."),
                    default=settings.Get("HUD", "show_acc_info", True),
                    changed=self.handle_show_acc_info,
                )
                CheckboxWithTitleDescription(
                    title=_("Draw Steering"),
                    description=_("Whether to draw the steering line in the HUD."),
                    default=settings.Get("HUD", "draw_steering", False),
                    changed=self.handle_draw_steering,
                )
                CheckboxWithTitleDescription(
                    title=_("Show Traffic Light Times"),
                    description=_("When enabled, the HUD will display traffic light times."),
                    default=settings.Get("HUD", "show_traffic_light_times", True),
                    changed=self.handle_show_traffic_light_times,
                )
                CheckboxWithTitleDescription(
                    title=_("Draw Wheel Paths"),
                    description=_("When enabled, the HUD will display where the wheels will go when turning."),
                    default=settings.Get("HUD", "draw_wheel_paths", False),
                    changed=self.handle_draw_wheel_paths,
                )

class Plugin(ETS2LAPlugin):
    description = PluginDescription(
        name=_("HUD"),
        version="1.0",
        description=_("Creates a heads up display on the windshield. Needs the AR plugin to work."),
        modules=["TruckSimAPI", "Semaphores", "Traffic"],
        tags=["AR", "Base"],
        fps_cap=30
    )
    
    author = Author(
        name="Tumppi066",
        url="https://github.com/Tumppi066",
        icon="https://avatars.githubusercontent.com/u/83072683?v=4"
    )
    
    
    pages = [Settings]

    map_data = None
    update_time = 0
    
    intersection = None
    intersection_uid = None
    
    def imports(self):
        global ScreenCapture
        import Modules.BetterScreenCapture.main as ScreenCapture
        
        self.get_start_end_time()
        
    def get_intersection(self):
        next_intersection = self.globals.tags.next_intersection
        if next_intersection is None:
            self.intersection = None
            return
        
        self.intersection = next_intersection["plugins.map"]
                
    def create_intersection_map(self, anchor, offset: list[float] = [0, 0], data = None):
        # Top down map along the X and Z axis
        if self.intersection is None:
            return None
        
        target_lane = self.globals.tags.next_intersection_lane
        target_lane = self.globals.tags.merge(target_lane)
        
        bounding_box = self.intersection.bounding_box
        bounding_box = [bounding_box.min_x, bounding_box.min_y, bounding_box.max_x, bounding_box.max_y] # y = z

        rotation = data["truckPlacement"]["rotationX"] * 360
        x = data["truckPlacement"]["coordinateX"]
        z = data["truckPlacement"]["coordinateZ"]
        
        def convert_to_center_aligned_coordinate(x, y):
            center = (bounding_box[2] + bounding_box[0]) / 2, (bounding_box[3] + bounding_box[1]) / 2
            return x - center[0], y - center[1]
        
        def rotate_around_center(x, y, angle):
            angle = math.radians(angle)
            x, y = x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle)
            return x, y
        
        def is_inside_bounds(x, y, expand=0):
            return x >= bounding_box[0] - expand and x <= bounding_box[2] + expand and y >= bounding_box[1] - expand and y <= bounding_box[3] + expand
        
        lanes = []
        for i, lane in enumerate(self.intersection.nav_routes):
            if i == target_lane:
                continue
            cur_lane = []
            for curve in lane.curves:
                points = curve.points
                points = [convert_to_center_aligned_coordinate(point.x, point.z) for point in points]
                points = [rotate_around_center(point[0], point[1], rotation) for point in points]
                
                cur_lane.append((
                    Polygon(
                        [Point(point[0] + offset[0], point[1] + offset[1], anchor=anchor) for point in points],
                        thickness=2,
                        color=Color(140, 140, 140),
                        fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100)
                    )
                ))
            
            lanes.append(cur_lane)
            
        # Add target lane
        try:
            if target_lane is not None:
                target_lane = self.intersection.nav_routes[target_lane]

                cur_lane = []
                for curve in target_lane.curves:
                    points = curve.points
                    points = [convert_to_center_aligned_coordinate(point.x, point.z) for point in points]
                    points = [rotate_around_center(point[0], point[1], rotation) for point in points]
                    
                    cur_lane.append((
                        Polygon(
                            [Point(point[0] + offset[0], point[1] + offset[1], anchor=anchor) for point in points],
                            thickness=2,
                            color=Color(255, 255, 255),
                            fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100)
                        )
                    ))
                
                lanes.append(cur_lane)
        
        except:
            pass
            
        try:
            # Add truck
            if is_inside_bounds(x, z, expand=15):
                x, z = convert_to_center_aligned_coordinate(x, z)
                x, z = rotate_around_center(x, z, rotation)
                truck = Point(x + offset[0], z + offset[1])
                lanes.append([
                    Line(
                        Point(truck.x, truck.y - 3, anchor=anchor),
                        Point(truck.x, truck.y + 3, anchor=anchor),
                        thickness=3,
                        color=Color(255, 100, 100)
                    )  
                ])
        except:
            pass
            
        return lanes

                
    def get_offsets(self):
        offset_x = self.settings.offset_x
        if offset_x is None:
            self.settings.offset_x = 0
            offset_x = 0
        
        offset_y = self.settings.offset_y
        if offset_y is None:
            self.settings.offset_y = 0
            offset_y = 0
        
        offset_z = self.settings.offset_z
        if offset_z is None:
            self.settings.offset_z = 0
            offset_z = 0
            
        return offset_x, offset_y, offset_z
    
    def get_settings(self):
        draw_steering = self.settings.draw_steering
        if draw_steering is None:
            self.settings.draw_steering = False
            draw_steering = False

        draw_wheel_paths = self.settings.draw_wheel_paths
        if draw_wheel_paths is None:
            self.settings.draw_wheel_paths = False
            draw_wheel_paths = False
            
        show_navigation = self.settings.show_navigation
        if show_navigation is None:
            self.settings.show_navigation = True
            show_navigation = True
            
        refresh_rate = self.settings.refresh_rate
        if refresh_rate is None:
            self.settings.refresh_rate = 2
            refresh_rate = 2
            
        scale = self.settings.scale
        if scale is None:
            self.settings.scale = 1
            scale = 1
            
        show_traffic_lights = self.settings.show_traffic_light_times
        if show_traffic_lights is None:
            self.settings.show_traffic_light_times = True
            show_traffic_lights = True
            
        show_acc_info = self.settings.show_acc_info
        if show_acc_info is None:
            self.settings.show_acc_info = True
            show_acc_info = True
        
        return draw_steering, draw_wheel_paths, show_navigation, refresh_rate, scale, show_traffic_lights, show_acc_info
    
    def get_start_end_time(self):
        self.load_start_time = time.time()
        self.times = random.uniform(4, 6)
        self.load_end_time = self.load_start_time + self.times
    
    def boot_sequence(self, t: float, anchor: Coordinate, scaling: float = 1):
        t = (time.time() - self.load_start_time) / (self.load_end_time - self.load_start_time)
        if t > 1:
            return False
        
        opacity = 1
        # Smooth out the opacity above 95%
        if t > 0.95:
            opacity = 1 - (t - 0.95) * 1 / 0.05
            opacity = max(0, min(1, opacity))
        # Smooth out below 10%
        elif t < 0.1:
            opacity = t * 1 / 0.1
            opacity = max(0, min(1, opacity))
            
        t = t * (self.times/2) % 1
        
        slider_ets2la_pos = Point(-30 * scaling, -25 * scaling, anchor=anchor)

        def sigmoid(t):
            return 1 / (1 + math.exp(-t * 5))

        slider_start_pos = Point(-100 * scaling + ((sigmoid(t)) * 400 - 200) * scaling, 0, anchor=anchor)
        slider_progress_pos = Point(-100 * scaling + t * 200 * scaling, 0, anchor=anchor)
        
        self.globals.tags.AR = [
            # Slider progress
            Line(
                slider_start_pos,
                slider_progress_pos,
                thickness=4 * scaling,
                color=Color(255, 255, 255, 255 * opacity),
                fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100),
            ),
            # ETS2LA
            Text(
                slider_ets2la_pos,
                "ETS2LA",
                size=20 * scaling,
                color=Color(255, 255, 255, 255 * opacity),
                fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100),
            )
        ]
        
        return True
    
    def speed(self, speed: float, speed_limit: float, anchor, offset: list[float], scaling: float = 1):
        game = self.api_data["scsValues"]["game"]
        # Convert units if the game is ATS
        if game == "ATS":
            speed = speed * 0.621371  # Convert km/h to mph
            speed_limit = speed_limit * 0.621371
            unit = "mph"
        else:
            unit = "km/h"

        speed_pos = Point(-5 * scaling + offset[0], -20 * scaling + offset[1], anchor=anchor)
        unit_pos = Point(-5 * scaling + offset[0], 10 * scaling + offset[1], anchor=anchor) 
        
        speed_limit_base_y = 4 * scaling
        speed_limit_base_x = -35 * scaling
        speed_limit_pos = Point(speed_limit_base_x + offset[0], speed_limit_base_y + offset[1], anchor=anchor)
        speed_limit_text_pos = Point(speed_limit_base_x + offset[0] - 9 * scaling, speed_limit_base_y + offset[1] - 9 * scaling, anchor=anchor)
        
        status = self.globals.tags.status
        if status:
            acc_status = self.globals.tags.merge(status)["AdaptiveCruiseControl"]
        else:
            acc_status = False
            
        target_speed = self.globals.tags.acc
        if target_speed:
            target_speed = self.globals.tags.merge(target_speed)
            if game == "ATS":
                target_speed = target_speed * 3.6 * 0.621371
            else:
                target_speed = target_speed * 3.6  # Convert m/s to km/h
        else:
            target_speed = 0

        ar_data = [
            # Unit
            Text(
                unit_pos,
                (f"MAX {round(target_speed)} " if acc_status else "") + unit,
                size=16 * scaling,
                color=Color(255, 255, 255),
                fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100),
            ),
            Text(
                speed_pos,
                f"{abs(speed):.0f}",
                size=30 * scaling,
                color=Color(255, 255, 255),
                fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100),
            ),
            
            # Speed limit
            Circle(
                speed_limit_pos,
                16 * scaling,
                color=Color(255, 255, 255),
                thickness=2,
                fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100),
            ),
            Text(
                speed_limit_text_pos,
                f"{abs(speed_limit):.0f}",
                size=18 * scaling,
                color=Color(255, 255, 255),
                fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100),
            )
        ]
        
        return ar_data
    
    def navigation(self, distance: float, anchor, offset: list[float], scaling: float = 1, data = None):
        
        if distance is None:
            return []
        
        if distance == 1 or distance == 0:
            return []
        
        self.get_intersection()
        
        game = self.api_data["scsValues"]["game"]
        distance -= distance % 10
        units = "m"
        
        if game == "ATS":
            # Convert meters to yards, then to miles if large enough
            distance = distance * 1.0936  # Convert meters to yards
            if distance >= 300:
                distance = distance / 1760  # Convert yards to miles
                units = "mi"
            # Take modulo 10 again for ATS
            distance -= distance % 0.1 if units == "mi" else distance % 10
        else:
            if distance >= 300:
                distance /= 1000
                units = "km"
        
        if game == "ATS" and units == "m":
            units = "yd"  # Use yards instead of meters for ATS
            
        distance_pos = Point(0 * scaling - offset[0], -20 * scaling + offset[1], anchor=anchor)
        unit_pos = Point(0 * scaling - offset[0], 10 * scaling + offset[1], anchor=anchor)   
        
        ar_data = [
            # Distance
            Text(
                unit_pos,
                units,
                size=16 * scaling,
                color=Color(255, 255, 255),
                fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100),
            ),
            Text(
                distance_pos,
                f"{abs(distance):.0f}" if units == "m" else f"{abs(distance):.1f}",
                size=30 * scaling,
                color=Color(255, 255, 255),
                fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100),
            )
        ]
        
        try:
            intersection_map = self.create_intersection_map(anchor, [150, 5], data)
            if intersection_map is not None:
                for lane in intersection_map:
                    for line in lane:
                        ar_data.append(line)
        except:
            # logging.exception("Failed to create intersection map")
            pass
        
        return ar_data


    def CalculateRadiusFrontWheel(self, SteeringAngle, Distance):
        SteeringAngle = math.radians(SteeringAngle)
        if SteeringAngle != 0:
            return Distance / math.sin(SteeringAngle)
        else:
            return float("inf")


    def CalculateRadiusBackWheel(self, SteeringAngle, Distance):
        SteeringAngle = math.radians(SteeringAngle)
        if SteeringAngle != 0:
            return Distance / math.tan(SteeringAngle)
        else:
            return float("inf")

    def HudUpdater(self):
        while True:
            speed_nav_offset_x = 0
            offset_x, offset_y, offset_z = self.get_offsets()
            anchor = Coordinate(0 + offset_x, -2 + offset_y, -10 + offset_z, relative=True, rotation_relative=True)
            draw_steering, draw_wheel_paths, show_navigation, refresh_rate, scale, show_trafic_lights, show_acc_info = self.get_settings()
            
            speed = self.api_data["truckFloat"]["speed"] * 3.6
            speed_limit = self.api_data["truckFloat"]["speedLimit"] * 3.6
            
            distance = self.globals.tags.next_intersection_distance
            distance = self.globals.tags.merge(distance)
            
            if show_navigation and distance is not None and distance != 1 and distance != 0:
                speed_nav_offset_x -= 50 * self.scaling
            
            ar_data = []
            ar_data += self.speed(speed, speed_limit, anchor, [speed_nav_offset_x - 15, 0, 0], scaling=self.scaling)
            if show_navigation:
                ar_data += self.navigation(distance, anchor, [speed_nav_offset_x + 15, 0, 0], scaling=self.scaling, data=self.api_data)
                
            self.hud_data = ar_data
            
            time.sleep(1/refresh_rate)
            
    def WheelUpdater(self):
        while True:
            if self.settings.draw_wheel_paths:
                self.wheel_data = []
                TruckX = self.api_data["truckPlacement"]["coordinateX"]
                TruckY = self.api_data["truckPlacement"]["coordinateY"]
                TruckZ = self.api_data["truckPlacement"]["coordinateZ"]
                TruckRotationX = self.api_data["truckPlacement"]["rotationX"]
                TruckRotationY = self.api_data["truckPlacement"]["rotationY"]
                TruckRotationZ = self.api_data["truckPlacement"]["rotationZ"]

                TruckRotationDegreesX = TruckRotationX * 360
                TruckRotationRadiansX = -math.radians(TruckRotationDegreesX)

                TruckWheelPointsX = [Point for Point in self.api_data["configVector"]["truckWheelPositionX"] if Point != 0]
                TruckWheelPointsY = [Point for Point in self.api_data["configVector"]["truckWheelPositionY"] if Point != 0]
                TruckWheelPointsZ = [Point for Point in self.api_data["configVector"]["truckWheelPositionZ"] if Point != 0]

                WheelAngles = [Angle for Angle in self.api_data["truckFloat"]["truck_wheelSteering"] if Angle != 0]

                WheelCoordinates = []
                for i in range(len(TruckWheelPointsX)):
                    PointX = TruckX + TruckWheelPointsX[i] * math.cos(TruckRotationRadiansX) - TruckWheelPointsZ[i] * math.sin(TruckRotationRadiansX)
                    PointY = TruckY + TruckWheelPointsY[i]
                    PointZ = TruckZ + TruckWheelPointsZ[i] * math.cos(TruckRotationRadiansX) + TruckWheelPointsX[i] * math.sin(TruckRotationRadiansX)
                    WheelCoordinates.append((PointX, PointY, PointZ))

                if len(WheelCoordinates) >= 4 and len(WheelAngles) >= 2:
                    FrontLeftWheel = WheelCoordinates[0]
                    FrontRightWheel = WheelCoordinates[1]

                    BackLeftWheels = []
                    BackRightWheels = []

                    for i in range(len(WheelCoordinates)):
                        if len(WheelAngles) > i:
                            continue

                        if i % 2 == 0:
                            BackLeftWheels.append(WheelCoordinates[i])
                        else:
                            BackRightWheels.append(WheelCoordinates[i])

                    BackLeftWheel = (0, 0, 0)
                    BackRightWheel = (0, 0, 0)

                    for Wheel in BackLeftWheels:
                        BackLeftWheel = BackLeftWheel[0] + Wheel[0], BackLeftWheel[1] + Wheel[1], BackLeftWheel[2] + Wheel[2]

                    for Wheel in BackRightWheels:
                        BackRightWheel = BackRightWheel[0] + Wheel[0], BackRightWheel[1] + Wheel[1], BackRightWheel[2] + Wheel[2]

                    BackLeftWheel = BackLeftWheel[0] / len(BackLeftWheels), BackLeftWheel[1] / len(BackLeftWheels), BackLeftWheel[2] / len(BackLeftWheels)
                    BackRightWheel = BackRightWheel[0] / len(BackRightWheels), BackRightWheel[1] / len(BackRightWheels), BackRightWheel[2] / len(BackRightWheels)

                    FrontLeftSteerAngle = WheelAngles[0] * 360
                    FrontRightSteerAngle = WheelAngles[1] * 360

                    DistanceLeft = math.sqrt((FrontLeftWheel[0] - BackLeftWheel[0]) ** 2 + (FrontLeftWheel[2] - BackLeftWheel[2]) ** 2)
                    DistanceRight = math.sqrt((FrontRightWheel[0] - BackRightWheel[0]) ** 2 + (FrontRightWheel[2] - BackRightWheel[2]) ** 2)

                    LeftFrontWheelRadius = self.CalculateRadiusFrontWheel(FrontLeftSteerAngle, DistanceLeft)
                    LeftBackWheelRadius = self.CalculateRadiusBackWheel(FrontLeftSteerAngle, DistanceLeft)
                    RightFrontWheelRadius = self.CalculateRadiusFrontWheel(FrontRightSteerAngle, DistanceRight)
                    RightBackWheelRadius = self.CalculateRadiusBackWheel(FrontRightSteerAngle, DistanceRight)

                    LeftCenterX = BackLeftWheel[0] - LeftBackWheelRadius * math.cos(TruckRotationRadiansX)
                    LeftCenterZ = BackLeftWheel[2] - LeftBackWheelRadius * math.sin(TruckRotationRadiansX)
                    RightCenterX = BackRightWheel[0] - RightBackWheelRadius * math.cos(TruckRotationRadiansX)
                    RightCenterZ = BackRightWheel[2] - RightBackWheelRadius * math.sin(TruckRotationRadiansX)

                    for i in range(2):
                        if i == 0:
                            R = LeftFrontWheelRadius
                            CenterX = LeftCenterX
                            CenterZ = LeftCenterZ
                            Offset = math.degrees(math.atan(DistanceLeft / R))
                        else:
                            R = RightFrontWheelRadius
                            CenterX = RightCenterX
                            CenterZ = RightCenterZ
                            Offset = math.degrees(math.atan(DistanceRight / R))
                        Points = []
                        for j in range(45):
                            Angle = j * (1 / -R) * 30 - TruckRotationDegreesX - Offset
                            Angle = math.radians(Angle)
                            X = CenterX + R * math.cos(Angle)
                            Z = CenterZ + R * math.sin(Angle)
                            Points.append(Coordinate(X, TruckY, Z))

                        self.wheel_data.append(
                            Polygon(
                                points=Points,
                                closed=False,
                                thickness=2,
                                color=Color(255, 255, 255, 100),
                                fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100)
                            )
                        )
                time.sleep(1/2) # 2fps

    def SteeringUpdater(self):
        while True:
            try:
                points = self.globals.tags.steering_points
                points = self.globals.tags.merge(points)
                
                status = self.globals.tags.status
                if status:
                    map_status = self.globals.tags.merge(status)["Map"]
                else:
                    map_status = None

                steering_data = []
                for i, point in enumerate(points):
                    if i == 0:
                        continue
                    line = Line(
                        Coordinate(*point),
                        Coordinate(*points[i - 1]),
                        thickness=5 * self.scaling,
                        color=Color(100, 100, 100, 120) if not map_status else Color(255, 255, 255, 80),
                        fade=Fade(prox_fade_end=10, prox_fade_start=20, dist_fade_start=50, dist_fade_end=150)
                    )
                    steering_data.append(line)
                self.steering_data = steering_data
            except:
                self.steering_data = []
                pass

            time.sleep(1/2) # 2fps

    def SemaphoreUpdater(self):
        while True:
            self.semaphore_data = []
            semaphores = self.modules.Semaphores.run()
            traffic_lights = [semaphore for semaphore in semaphores if isinstance(semaphore, TrafficLight)]
            data = []
            for traffic_light in traffic_lights:
                data.append(
                    Text(
                        Coordinate(traffic_light.position.x + 512 * traffic_light.cx, traffic_light.position.y + 2.5, traffic_light.position.z + 512 * traffic_light.cy),
                        f"    {traffic_light.state_text()} - {traffic_light.time_left:.0f}s left",
                        size=16 * self.scaling,
                        color=Color(*traffic_light.color()), 
                        fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=20, dist_fade_end=40),
                    )
                )    
            self.semaphore_data += data
            time.sleep(1/2) # 2fps

    def LaneChangeUpdater(self):
        while True:
            status = self.globals.tags.lane_change_status
            if status is None:
                self.lane_change_data = []
                time.sleep(1/2) # 2fps
                continue
            if "Map" not in status:
                self.lane_change_data = []
                time.sleep(1/2)
                continue
            
            status = status["Map"]

            if status == "idle":
                self.lane_change_data = []
                time.sleep(1/2) # 2fps
                continue
            
            offset_x, offset_y, offset_z = self.get_offsets()
            anchor = Coordinate(0 + offset_x, -2 + offset_y, -10 + offset_z, relative=True, rotation_relative=True)
            
            dots = "." * (int(time.time() * 2) % 4)
            
            self.lane_change_data = []
            if status == "waiting":
                self.lane_change_data.append(
                    Text(
                        Point(-70 * self.scaling, 30 * self.scaling, anchor=anchor),
                        _("Waiting for lane change approval") + dots,
                        size=16 * self.scaling,
                        color=Color(255, 255, 255),
                        fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100),
                    )
                )
            elif "executing" in status:
                percentage = round(float(status.split(":")[1]) * 100)
                self.lane_change_data.append(
                    Text(
                        Point(-70 * self.scaling, 30 * self.scaling, anchor=anchor),
                        _("Lane change in progress {percentage}%").format(percentage=percentage) + dots,
                        size=16 * self.scaling,
                        color=Color(255, 255, 255),
                        fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_end=100, dist_fade_start=100),
                    )
                )
            
            time.sleep(1/10) # 10fps
            

    def ACCUpdater(self):
        while True:
            targets = self.globals.tags.vehicle_highlights
            targets = self.globals.tags.merge(targets)
            
            if targets is None:
                targets = []
            
            vehicles = self.modules.Traffic.run()
            
            if vehicles is None:
                vehicles = []
            
            highlighted_vehicle = None
            if len(targets) > 0:
                for vehicle in vehicles:
                    if vehicle.id in targets:
                        highlighted_vehicle = vehicle
                        break
                
            if not highlighted_vehicle:
                self.acc_data = []
                time.sleep(1/30)
                continue
                
            data = []
            # Line under the vehicle
            front_left, front_right, back_right, back_left = highlighted_vehicle.get_corners()
            center_back = [(back_left[0] + back_right[0]) / 2, (back_left[1] + back_right[1]) / 2, (back_left[2] + back_right[2]) / 2]
            data += [
                Line(
                    Coordinate(*back_left),
                    Coordinate(*back_right),
                    thickness=3,
                    color=Color(255, 255, 255, 200),
                    fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=100, dist_fade_end=120),
                )
            ]
            
            # Text on said line
            truck_x = self.api_data["truckPlacement"]["coordinateX"]
            truck_y = self.api_data["truckPlacement"]["coordinateY"]
            truck_z = self.api_data["truckPlacement"]["coordinateZ"]
            
            distance = math.sqrt((truck_x - center_back[0]) ** 2 + (truck_y - center_back[1]) ** 2 + (truck_z - center_back[2]) ** 2)
            
            game = self.api_data["scsValues"]["game"]
            units = "m"
            threshold = 60  # Default threshold in meters
            if game == "ATS":
                distance = distance * 3.28084  # Convert meters to feet
                units = "ft"
                threshold = 200  # Convert 60 meters to approximately 200 feet
                distance = round(distance, 0)
            else:
                distance = round(distance, 0)
            
            if distance > threshold:
                self.acc_data = []
                time.sleep(1/30)
                continue
                
            data += [
                Text(
                    Coordinate(*back_right),
                    "  " + _("Distance: {distance:.0f} {units}").format(distance=distance, units=units),
                    size=16,
                    color=Color(255, 255, 255, 200),
                    fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=100, dist_fade_end=120),
                )
            ]
            
            # Line between the vehicle and the truck
            acc_gap = self.globals.tags.acc_gap
            acc_gap = self.globals.tags.merge(acc_gap)
            if acc_gap is not None:
                if game == "ATS":
                    acc_gap = acc_gap * 3.28084  # Convert meters to feet
                    units = "ft"
                    acc_gap = round(acc_gap, 0)
                else:
                    # Remove km conversion, keep using m
                    acc_gap = round(acc_gap, 0)
                
                left_vector = [back_left[0] - truck_x, back_left[1] - truck_y, back_left[2] - truck_z]
                magnitude = math.sqrt(left_vector[0] ** 2 + left_vector[1] ** 2 + left_vector[2] ** 2)
                unit_left_vector = [left_vector[0] / magnitude, left_vector[1] / magnitude, left_vector[2] / magnitude]
                
                right_vector = [back_right[0] - truck_x, back_right[1] - truck_y, back_right[2] - truck_z]
                magnitude = math.sqrt(right_vector[0] ** 2 + right_vector[1] ** 2 + right_vector[2] ** 2)
                unit_right_vector = [right_vector[0] / magnitude, right_vector[1] / magnitude, right_vector[2] / magnitude]
            
                left = [truck_x + unit_left_vector[0] * acc_gap, truck_y + unit_left_vector[1] * acc_gap, truck_z + unit_left_vector[2] * acc_gap]
                right = [truck_x + unit_right_vector[0] * acc_gap, truck_y + unit_right_vector[1] * acc_gap, truck_z + unit_right_vector[2] * acc_gap]
                center = [(left[0] + right[0]) / 2, (left[1] + right[1]) / 2, (left[2] + right[2]) / 2]
                
                data += [
                    Line(
                        Coordinate(*left),
                        Coordinate(*right),
                        thickness=3,
                        color=Color(255, 255, 255, 60),
                        fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=100, dist_fade_end=120),
                    ),
                    Line(
                        Coordinate(*center),
                        Coordinate(*center_back),
                        thickness=3,
                        color=Color(255, 255, 255, 60),
                        fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=100, dist_fade_end=120),
                    ),
                    Text(
                        Coordinate(*right),
                        "  " + _("Target: {acc_gap:.0f} {units}").format(acc_gap=acc_gap, units=units),
                        size=16,
                        color=Color(255, 255, 255, 60),
                        fade=Fade(prox_fade_end=0, prox_fade_start=0, dist_fade_start=100, dist_fade_end=120),
                    )
                ]
            
            self.acc_data = data
            time.sleep(1/30) # 30fps

    def run(self):
        X1, Y1, X2, Y2 = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])
        height = Y2 - Y1
        default_height = 1440
        
        self.scaling = height / default_height	# 0.75 = 1080p, 1 = 1440p, 1.25 = 1800p, 1.5 = 2160p
        _, _, _, _, scale, _, _ = self.get_settings()
        self.scaling *= scale
        
        self.api_data = self.modules.TruckSimAPI.run()
        
        engine = self.api_data["truckBool"]["engineEnabled"]
        offset_x, offset_y, offset_z = self.get_offsets()
        anchor = Coordinate(0 + offset_x, -2 + offset_y, -10 + offset_z, relative=True, rotation_relative=True)
        
        if not engine:
            self.globals.tags.AR = []
            self.get_start_end_time()
            return
        
        # if self.boot_sequence(time.time(), anchor, scaling=self.scaling):
        #     return
        
        data = []
        data += self.hud_data
        data += self.wheel_data
        data += self.steering_data
        data += self.semaphore_data
        data += self.acc_data
        data += self.lane_change_data
        self.globals.tags.AR = data
        
    def init(self):
        self.get_settings()
        self.api_data = self.modules.TruckSimAPI.run()
        self.hud_data = []
        self.wheel_data = []
        self.steering_data = []
        self.semaphore_data = []
        self.acc_data = []
        self.lane_change_data = []
        self.scaling = 1
        
        threading.Thread(target=self.HudUpdater, daemon=True).start()
        threading.Thread(target=self.WheelUpdater, daemon=True).start()
        threading.Thread(target=self.SteeringUpdater, daemon=True).start()
        threading.Thread(target=self.SemaphoreUpdater, daemon=True).start()
        threading.Thread(target=self.ACCUpdater, daemon=True).start()
        threading.Thread(target=self.LaneChangeUpdater, daemon=True).start()
        
        self.get_start_end_time()