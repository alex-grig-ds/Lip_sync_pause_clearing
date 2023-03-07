
from pathlib import Path
import shutil
from typing import List, Tuple

import pandas as pd

from config import *

def check_folder_structure(output_folder: str) -> (Path, Path, Path, Path):
    """
    :param output_folder:
    :return: work_dir, output_dir
    """
    work_dir = Path(WORK_FOLDER)
    work_dir.mkdir(exist_ok=True)

    base_img_dir = work_dir.joinpath(BASE_IMAGE_FOLDER)
    if base_img_dir.is_dir(): shutil.rmtree(str(base_img_dir))
    base_img_dir.mkdir(exist_ok=True)

    transf_img_dir = work_dir.joinpath(TRANSFORM_IMAGE_FOLDER)
    if transf_img_dir.is_dir(): shutil.rmtree(transf_img_dir)
    transf_img_dir.mkdir(exist_ok=True)

    corr_img_dir = work_dir.joinpath(CORRECTED_IMAGE_FOLDER)
    if corr_img_dir.is_dir(): shutil.rmtree(corr_img_dir)
    corr_img_dir.mkdir(exist_ok=True)

    output_dir = Path(output_folder)
    if output_dir.is_dir(): shutil.rmtree(output_dir)
    output_dir.mkdir(exist_ok=True)
    return work_dir, output_dir, base_img_dir, transf_img_dir, corr_img_dir


def mark_frames(img_dir: Path, video_duration: float, silence_list: List[Tuple[float, float]]) -> pd.DataFrame:
    """
    Mark frames as silence or not silence.
    :param img_dir: folder with frames
    :param video_duration: video duration in seconds
    :param silence_list: list of silences: (start, end)
    :return:
        'frame': str, path to frame, 'second': float, 'silence': bool
    """
    frames_df = pd.DataFrame(columns = ['frame', 'second', 'silence'])
    frame_list = sorted(list(img_dir.glob('*.jpg')))
    frame_delta = video_duration / len(frame_list)
    current_time = 0
    for frame in frame_list:
        frames_df.loc[len(frames_df), :] = [frame, current_time, False]
        current_time += frame_delta
    for silence in silence_list:
        frames_df.loc[(frames_df['second'] >= silence[0]) & (frames_df['second'] <= silence[1]), 'silence'] = True
    return frames_df


