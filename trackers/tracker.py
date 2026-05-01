# import all required libraries  
import cv2
import os
import numpy as np
import pickle
from ultralytics import YOLO
import supervision as sv
from utils import compute_bbox_center, bbox_width


class Tracker:
    """
    A class for tracking objects (players, referees, ball) in video frames using YOLO detection
    and ByteTrack tracking algorithm.
    
    This class handles object detection, tracking, and visualization for sports video analysis.
    """
    
    def __init__(self, model_path):
        """
        Initialize the Tracker with a YOLO model and ByteTrack tracker.
        
        Args:
            model_path (str): Path to the YOLO model file
        """
        self.model = YOLO(model_path)
        self.tracker = sv.ByteTrack()
    
    def detect_frames(self, frames):
        """
        Perform object detection on a batch of frames using YOLO model.
        
        Processes frames in batches for efficient memory usage and faster inference.
        
        Args:
            frames (list): List of video frames to process
            
        Returns:
            list: List of detection results for each frame
        """
        batch_size = 20  # Process 20 frames at a time to optimize memory usage
        detections = []

        # Process frames in batches to avoid memory overflow
        for i in range(0, len(frames), batch_size):
            batch_frames = frames[i: i + batch_size]
            # Run YOLO detection with confidence threshold of 0.1
            detections_batch = self.model.predict(batch_frames, conf=0.1)
            detections += detections_batch
            
        return detections
    
    def get_object_tracks(self, frames, read_from_stub=False, stub_path=None):
        """
        Extract object tracks from video frames with optional caching support.
        
        This method detects objects, applies tracking, and organizes results by object type.
        Supports loading/saving results from/to a pickle file for faster subsequent runs.
        
        Args:
            frames (list): List of video frames to process
            read_from_stub (bool): Whether to load cached results from file
            stub_path (str): Path to cache file for saving/loading results
            
        Returns:
            dict: Dictionary containing tracks for players, referees, and ball
                 Format: {"players": [...], "referees": [...], "ball": [...]}
        """
        # Load cached results if available and requested
        if read_from_stub and stub_path is not None and os.path.exists(stub_path):
            with open(stub_path, 'rb') as f:
                tracks = pickle.load(f)
            return tracks
    
        # Perform object detection on all frames
        detections = self.detect_frames(frames)
        
        # Initialize tracking dictionary structure
        tracks = {
            "players": [],    # Track all players including goalkeepers
            "referees": [],   # Track referees
            "ball": []        # Track the ball
        }

        # Process each frame's detections
        for frame_num, detection in enumerate(detections):
            # Get class names and create inverse mapping for easy lookup
            cls_names = detection.names  # {0: 'player', 1: 'referee', 2: 'ball', 3: 'goalkeeper'}
            cls_names_inv = {v: k for k, v in cls_names.items()}  # {'player': 0, 'referee': 1, ...}

            # Convert YOLO detection format to Supervision format for tracking
            detection_supervision = sv.Detections.from_ultralytics(detection)

            # Convert goalkeeper detections to player class (treat goalkeepers as players)
            for object_ind, class_id in enumerate(detection_supervision.class_id):
                if cls_names[class_id] == "goalkeeper":
                    detection_supervision.class_id[object_ind] = cls_names_inv["player"]

            # Apply ByteTrack algorithm to maintain object identities across frames
            detection_with_tracks = self.tracker.update_with_detections(detection_supervision)

            # Initialize frame-specific tracking dictionaries
            tracks["players"].append({})
            tracks["referees"].append({})
            tracks["ball"].append({})

            # Process tracked objects (players and referees with persistent IDs)
            for frame_detection in detection_with_tracks:
                bbox = frame_detection[0].tolist()  # Bounding box coordinates [x1, y1, x2, y2]
                cls_id = frame_detection[3]         # Class ID
                track_id = frame_detection[4]       # Unique tracking ID

                # Store player tracks with their unique IDs
                if cls_id == cls_names_inv["player"]:
                    tracks["players"][frame_num][track_id] = {"bbox": bbox}
                    
                # Store referee tracks with their unique IDs
                if cls_id == cls_names_inv['referee']:
                    tracks["referees"][frame_num][track_id] = {"bbox": bbox}

            # Process ball detections separately (no persistent tracking needed)
            for frame_detection in detection_supervision:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]

                # Ball gets a fixed ID of 1 since there's typically only one ball
                if cls_id == cls_names_inv['ball']:
                    tracks["ball"][frame_num][1] = {"bbox": bbox}
        
        # Save results to cache file if path provided
        if stub_path is not None:
            with open(stub_path, "wb") as f:
                pickle.dump(tracks, f)
                
        return tracks
    
    def draw_ellipse(self, frame, bbox, color, track_id=None):
        """
        Draw an ellipse at the bottom of a bounding box to represent a person's position.
        
        This creates a visual indicator showing where a player or referee is standing,
        with an optional ID label.
        
        Args:
            frame (numpy.ndarray): The video frame to draw on
            bbox (list): Bounding box coordinates [x1, y1, x2, y2]
            color (tuple): BGR color tuple for the ellipse
            track_id (int, optional): ID number to display in a label
            
        Returns:
            numpy.ndarray: Frame with ellipse drawn
        """
        # Calculate ellipse position at the bottom center of bounding box
        y2 = int(bbox[3])  # Bottom y-coordinate
        x_center, _ = compute_bbox_center(bbox)  # Center x-coordinate
        width = bbox_width(bbox)  # Width of bounding box

        # Draw ellipse representing person's foot position
        cv2.ellipse(
            frame,
            center=(x_center, y2),
            axes=(int(width), int(0.35 * width)),  # Ellipse dimensions
            angle=0.0,
            startAngle=-45,   # Partial ellipse for better visual effect
            endAngle=235,
            color=color,
            thickness=2,
            lineType=cv2.LINE_4
        )

        # Draw ID label if track_id is provided
        if track_id is not None:
            # Calculate rectangle position for ID label
            rectangle_width = 40
            rectangle_height = 20
            x1_rect = x_center - rectangle_width // 2
            x2_rect = x_center + rectangle_width // 2
            y1_rect = (y2 - rectangle_height // 2) + 15
            y2_rect = (y2 + rectangle_height // 2) + 15

            # Draw filled rectangle background for ID text
            cv2.rectangle(frame,
                          (int(x1_rect), int(y1_rect)),
                          (int(x2_rect), int(y2_rect)),
                          color,
                          cv2.FILLED)

            # Adjust text position for multi-digit IDs
            x1_text = x1_rect + 12
            if track_id > 99:
                x1_text -= 10  # Move text left for 3-digit numbers

            # Draw ID number on the rectangle
            cv2.putText(
                frame,
                f"{track_id}",
                (int(x1_text), int(y1_rect + 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),  # Black text
                2
            )

        return frame

    def draw_triangle(self, frame, bbox, color):
        """
        Draw a triangle above a bounding box to represent the ball position.
        
        Creates a distinctive triangular marker to highlight the ball's location.
        
        Args:
            frame (numpy.ndarray): The video frame to draw on
            bbox (list): Bounding box coordinates [x1, y1, x2, y2]
            color (tuple): BGR color tuple for the triangle
            
        Returns:
            numpy.ndarray: Frame with triangle drawn
        """
        # Position triangle at the top center of the bounding box
        y = int(bbox[1])  # Top y-coordinate
        x, _ = compute_bbox_center(bbox)  # Center x-coordinate

        # Define triangle vertices (pointing upward)
        triangle_points = np.array([
            [x, y],           # Bottom point (center)
            [x - 10, y - 20], # Top left point
            [x + 10, y - 20], # Top right point
        ])
        
        # Draw filled triangle
        cv2.drawContours(frame, [triangle_points], 0, color, cv2.FILLED)
        # Draw triangle outline in black
        cv2.drawContours(frame, [triangle_points], 0, (0, 0, 0), 2)

        return frame
    def draw_team_possession(self, frame, frame_num, team_ball_control, team_stats, pass_stats):
        # 1. Crear el fondo del marcador semitransparente
        overlay = frame.copy()
        cv2.rectangle(overlay, (1350, 680), (1900, 980), (255, 255, 255), -1)
        alpha = 0.4
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # 2. Calcular estadísticas de Posesión acumulada
        possession_until_now = team_ball_control[:frame_num + 1]
        team_1_frames = possession_until_now.count(1)
        team_2_frames = possession_until_now.count(2)

        total_frames = team_1_frames + team_2_frames
        if total_frames > 0:
            prob_1 = (team_1_frames / total_frames) * 100
            prob_2 = (team_2_frames / total_frames) * 100
        else:
            prob_1, prob_2 = 50, 50

        # 3. EXTRAER VARIABLES (Esto es lo que faltaba o daba error)
        n_t1 = team_stats[frame_num].get('team_1', 0)
        n_t2 = team_stats[frame_num].get('team_2', 0)
        
        # Extraemos p1, p2, l1, l2 del diccionario pass_stats
        current_pass_data = pass_stats[frame_num]
        p1 = current_pass_data.get('team_1', 0)
        p2 = current_pass_data.get('team_2', 0)
        l1 = current_pass_data.get('losses_1', 0)
        l2 = current_pass_data.get('losses_2', 0)

        # 4. Dibujar los textos
        # Pases y Pérdidas
        cv2.putText(frame, f"Pases T1: {p1} | Perdidas: {l1}", (1380, 720), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(frame, f"Pases T2: {p2} | Perdidas: {l2}", (1380, 760), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        # Posesión
        cv2.putText(frame, f"Equipo 1: {prob_1:.1f}%", (1400, 820), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        cv2.putText(frame, f"Equipo 2: {prob_2:.1f}%", (1400, 870), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

        # Conteo de Jugadores
        cv2.putText(frame, f"Jugadores T1: {n_t1}", (1380, 925), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(frame, f"Jugadores T2: {n_t2}", (1380, 960), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        return frame

        return frame

    def draw_annotations(self, video_frames, tracks, team_ball_control, team_stats, pass_stats):
        """
        Draw tracking annotations on all video frames.
        
        This method visualizes the tracking results by drawing:
        - Red ellipses with IDs for players
        - Yellow ellipses for referees  
        - Green triangles for the ball
        
        Args:
            video_frames (list): List of video frames to annotate
            tracks (dict): Tracking data from get_object_tracks()
            
        Returns:
            list: List of annotated video frames
        """
        output_video_frames = []
        
        # Process each frame
#### ESTO VA DENTRO DE LA CLASE TRACKER ####

    def draw_annotations(self, video_frames, tracks, team_ball_control, team_stats, pass_stats):
        output_video_frames = [] # Nivel 1 (8 espacios)

        for frame_num, frame in enumerate(video_frames): # Nivel 1 (8 espacios)
            # Todo lo de abajo tiene que tener +4 espacios respecto al 'for'
            current_frame = frame.copy() # Nivel 2 (12 espacios)

            player_dict = tracks["players"][frame_num]
            ball_dict = tracks["ball"][frame_num]
            referee_dict = tracks["referees"][frame_num]

            # Dibujar jugadores
            for track_id, player in player_dict.items():
                current_frame = self.draw_ellipse(current_frame, player["bbox"], (0, 0, 255), track_id)

            # Dibujar árbitros
            for _, referee in referee_dict.items():
                current_frame = self.draw_ellipse(current_frame, referee["bbox"], (0, 255, 255))

            # Dibujar balón
            for _, ball in ball_dict.items():
                current_frame = self.draw_triangle(current_frame, ball["bbox"], (0, 255, 0))

            # Dibujar marcador
            current_frame = self.draw_team_possession(current_frame, frame_num, team_ball_control, team_stats, pass_stats)

            # ESTA LÍNEA ES CLAVE: Debe estar alineada con los "for" de arriba
            output_video_frames.append(current_frame) # Nivel 2 (12 espacios)

        # EL RETURN DEBE ESTAR ALINEADO CON EL PRIMER 'FOR'
        return output_video_frames # Nivel 1 (8 espacios)


# Helper functions (assumed to be defined elsewhere in the codebase)
def compute_bbox_center(bbox):
    """
    Calculate the center coordinates of a bounding box.
    
    Args:
        bbox (list): Bounding box coordinates [x1, y1, x2, y2]
        
    Returns:
        tuple: (center_x, center_y)
    """
    x1, y1, x2, y2 = bbox
    center_x = int((x1 + x2) / 2)
    center_y = int((y1 + y2) / 2)
    return center_x, center_y


def bbox_width(bbox):
    """
    Calculate the width of a bounding box.
    
    Args:
        bbox (list): Bounding box coordinates [x1, y1, x2, y2]
        
    Returns:
        int: Width of the bounding box
    """
    return bbox[2] - bbox[0]