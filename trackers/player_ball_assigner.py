import sys 
sys.path.append('../')
from utils import get_distance

class PlayerBallAssigner():
    def __init__(self):
        # Distancia máxima en píxeles para considerar que un jugador tiene el balón
        # Puedes ajustar este número (70) si ves que no detecta bien la cercanía
        self.max_player_ball_distance = 70 

    def assign_ball_to_player(self, players, ball_bbox):
        # Obtenemos el centro del balón (x_centro, y_centro)
        ball_center = [(ball_bbox[0]+ball_bbox[2])/2, (ball_bbox[1]+ball_bbox[3])/2]

        minimum_distance = 99999
        assigned_player = -1

        for player_id, player in players.items():
            player_bbox = player['bbox']

            # Medimos distancia del balón a los "pies" del jugador
            # Usamos las esquinas inferiores del cuadro de detección (y-máxima)
            distance_left = get_distance(ball_center, [player_bbox[0], player_bbox[3]])
            distance_right = get_distance(ball_center, [player_bbox[2], player_bbox[3]])
            distance = min(distance_left, distance_right)

            if distance < self.max_player_ball_distance:
                if distance < minimum_distance:
                    minimum_distance = distance
                    assigned_player = player_id

        return assigned_player