import sys
import os
import argparse
import json

sys.path.append(os.getcwd())

from utils import read_video, save_video
from trackers.tracker import Tracker
from trackers.player_ball_assigner import PlayerBallAssigner
from team_assigner.team_assigner import TeamAssigner

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',     default='input_videos/video.mp4')
    parser.add_argument('--output',    default='output_videos/output.avi')
    parser.add_argument('--stats_out', default=None)
    return parser.parse_args()

def main():
    args = parse_args()

    # 1. Leer Video
    video_frames = read_video(args.input)
    
    if not video_frames:
        print("ERROR: No se han podido leer los frames del video.")
        return

    # 2. Inicializar Tracker y obtener trayectorias
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    tracker = Tracker(os.path.join(BASE_DIR, "models", "best.pt"))
    
    tracks = tracker.get_object_tracks(
        video_frames, 
        read_from_stub=False, 
        stub_path='tracker_stubs/player_detection.pkl'
    )

    # 3. Asignación de Equipos
    team_assigner = TeamAssigner()
    team_assigner.assign_team_color(video_frames[0], tracks['players'][0])

    for frame_num, player_track in enumerate(tracks['players']):
        for player_id, track in player_track.items():
            team = team_assigner.get_player_team(video_frames[frame_num], 
                                                 track['bbox'], 
                                                 player_id)
            tracks['players'][frame_num][player_id]['team'] = team

    # 4. Lógica de Posesión, Pases, Pérdidas y Estadísticas
    player_assigner = PlayerBallAssigner()
    
    team_ball_control = [] 
    team_stats = []        
    pass_stats_list = []   
    
    current_accumulated_stats = {'team_1': 0, 'team_2': 0, 'losses_1': 0, 'losses_2': 0}
    player_passes = {}     

    last_team_to_possess = None
    last_player_to_possess = None

    for frame_num, player_track in enumerate(tracks['players']):
        t1_count = sum(1 for p in player_track.values() if p.get('team') == 1)
        t2_count = sum(1 for p in player_track.values() if p.get('team') == 2)
        team_stats.append({'team_1': t1_count, 'team_2': t2_count})

        ball_dict = tracks['ball'][frame_num]
        assigned_player = -1
        if 1 in ball_dict:
            ball_bbox = ball_dict[1]['bbox']
            assigned_player = player_assigner.assign_ball_to_player(player_track, ball_bbox)

        if assigned_player != -1:
            current_team = tracks['players'][frame_num][assigned_player]['team']
            tracks['players'][frame_num][assigned_player]['has_ball'] = True
            team_ball_control.append(current_team)

            if last_team_to_possess is not None:
                if last_player_to_possess != assigned_player:
                    if last_team_to_possess == current_team:
                        current_accumulated_stats[f'team_{current_team}'] += 1
                        player_passes[assigned_player] = player_passes.get(assigned_player, 0) + 1
                    else:
                        current_accumulated_stats[f'losses_{last_team_to_possess}'] += 1
            
            last_team_to_possess = current_team
            last_player_to_possess = assigned_player
        else:
            team_ball_control.append(None)

        pass_stats_list.append(current_accumulated_stats.copy())

    # 5. Dibujar Anotaciones
    print(f"Procesando dibujo para {len(video_frames)} frames...")
    
    video_frames_dibujados = tracker.draw_annotations(video_frames, tracks, team_ball_control, team_stats, pass_stats_list)
    
    if video_frames_dibujados and len(video_frames_dibujados) > 0:
        video_frames = video_frames_dibujados
        print("Anotaciones integradas correctamente.")
    else:
        print("ADVERTENCIA: Falló el dibujo, se usarán los frames originales.")

    # 6. Stats en terminal
    t1_frames = team_ball_control.count(1)
    t2_frames = team_ball_control.count(2)
    total_poss_frames = t1_frames + t2_frames

    if total_poss_frames > 0:
        possesion_1 = (t1_frames / total_poss_frames) * 100
        possesion_2 = (t2_frames / total_poss_frames) * 100
    else:
        possesion_1, possesion_2 = 50.0, 50.0

    print(f"Equipo 1: {possesion_1:.1f}% | Equipo 2: {possesion_2:.1f}%")

    # 7. Exportar stats a JSON (para Flask)
    if args.stats_out:
        last = len(pass_stats_list) - 1
        last_pass = pass_stats_list[last] if pass_stats_list else {}
        last_team = team_stats[last] if team_stats else {}

        stats = {
            "possession_team1": round(possesion_1, 1),
            "possession_team2": round(possesion_2, 1),
            "passes_team1":  last_pass.get("team_1", 0),
            "passes_team2":  last_pass.get("team_2", 0),
            "losses_team1":  last_pass.get("losses_1", 0),
            "losses_team2":  last_pass.get("losses_2", 0),
            "players_team1": last_team.get("team_1", 0),
            "players_team2": last_team.get("team_2", 0),
        }
        with open(args.stats_out, "w") as f:
            json.dump(stats, f)
        print(f"Stats guardadas en {args.stats_out}")

    # 8. Guardar video
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    if video_frames and len(video_frames) > 0:
        save_video(video_frames, args.output)
        print(f"Video guardado en {args.output}")
    else:
        print("ERROR FATAL: No hay frames.")

if __name__ == "__main__":
    main()