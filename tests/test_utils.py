
import traceback as tb
from pathlib import Path
import shutil

from config import *
from src.utils import mark_frames


def test_mark_frames():
    temp_dir = Path(TEST_TEMP_FOLDER)
    if temp_dir.is_dir(): shutil.rmtree(str(temp_dir))
    temp_dir.mkdir()
    for file_idx in range(60):
        new_file = temp_dir.joinpath(f"img{file_idx}.jpg")
        with open(str(new_file), 'w') as file:
            file.writelines(f"{file_idx}")
    silence_list = [
        (0.5, 0.6),
        (1.5, 1.6)
    ]
    frames_df = mark_frames(temp_dir, video_duration=2.0, silence_list=silence_list)
    assert len(frames_df) > 0
    assert frames_df.loc[17, 'silence'] == True
    assert frames_df.loc[46, 'silence'] == True

