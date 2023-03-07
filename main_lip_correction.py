
from pathlib import Path
import click

import traceback as tb

from config import *
from src.app_logger import logger
from src.utils import check_folder_structure, mark_frames
from src.video_utils import (parse_silence_seconds, get_audio_track, get_audio_pauses, make_video,
                             make_stack_video, extract_frames, frames_top_cut)
from src.class_video_transform import VideoTransform


@click.command()
@click.option('--original', '-or', type=click.Path(exists=True), required=True,
              help = 'Original videofile.')
@click.option('--transformed', '-tf', type=click.Path(exists=True), required=True,
              help = 'Transformed videofile.')
@click.option('--corrected', '-cr', type=click.Path(), required=True,
              help = 'Corrected videofile.')
@click.option('--make_stack', '-ms', is_flag = True, default = False,
              help = 'Make stack video (transformed + corrected) as output.')
@click.option('--output_folder', '-of', default = './output/', type=click.Path(), required=True,
              help = 'Folder for saving corrected frames.')
def start_correction(original: str, transformed: str, corrected: str, make_stack: bool, output_folder: str):
    try:
        work_dir, output_dir, base_img_dir, transf_img_dir, corrected_img_dir = check_folder_structure(output_folder)
        original_video = Path(original)
        transformed_video = Path(transformed)
        output_video = Path(corrected)
        if output_video.is_file(): output_video.unlink()
        success, orig_fps, orig_duration = extract_frames(original_video, base_img_dir, 0)
        if not success:
            raise Exception
        frames_top_cut(base_img_dir, VIDEO_TOP_CUT_RATIO)
        success, trans_fps, trans_duration = extract_frames(transformed_video, transf_img_dir, 0)
        if not success:
            raise Exception
        frames_top_cut(transf_img_dir, VIDEO_TOP_CUT_RATIO)
        transformed_audio = work_dir.joinpath('temp_audio.mp3')
        if not get_audio_track(transformed_video, transformed_audio):
            raise Exception
        silence_list_orig = get_audio_pauses(original_video, work_dir, -13)
        silence_list_trans = get_audio_pauses(transformed_audio, work_dir, -7)
        if not silence_list_trans or not silence_list_orig:
            corrected_img_dir = transf_img_dir
        else:
            # Correct video
            original_df = mark_frames(base_img_dir, orig_duration, silence_list_orig)
            transform_df = mark_frames(transf_img_dir, trans_duration, silence_list_trans)
            video_correction = VideoTransform(base_img_dir, transf_img_dir, transformed_audio, original_df, transform_df)
            video_correction.silence_correction(silence_list_orig, silence_list_trans)
            video_correction.copy_img_to_folder(corrected_img_dir)
        if make_stack:
            success = make_stack_video(transf_img_dir, corrected_img_dir, transformed_audio, output_dir, output_video, trans_fps)
        else:
            success = make_video(corrected_img_dir, transformed_audio, work_dir, output_video, trans_fps)
        if not success: raise Exception
    except:
        logger.info(f"Video correction, some errors, reason: {tb.format_exc()}")

if __name__ == '__main__':
    start_correction()

