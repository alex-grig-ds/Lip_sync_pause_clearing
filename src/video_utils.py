
import subprocess
import traceback as tb
from pathlib import Path
from typing import List, Tuple
import shutil

import cv2 as cv
import numpy as np

from src.app_logger import logger


def extract_frames(input_mp4_path: Path, img_dir: Path, fps: float) -> (bool, float, float):
    """
    Get frames from mp4 file
    :param input_mp4_path: path to the mp4-videofile
    :param img_dir: path for saving frames. Folder will be clear from all files.
    :param fps: video FPS. If == 0 - detect from the video
    :return: success
    """
    success = False
    try:
        shutil.rmtree(img_dir.resolve())
        img_dir.mkdir()
        if fps == 0:
            video = cv.VideoCapture(str(input_mp4_path))
            fps = video.get(cv.CAP_PROP_FPS)
        subprocess.check_call(['ffmpeg', '-i', input_mp4_path.resolve(), '-vf', f"fps={fps}", f"{img_dir}/img%05d.jpg"])
        video_duration = (len(list(img_dir.glob('*.jpg'))) + 1) / fps
        success = True
    except:
        video_duration = 0
        logger.info(f"get_audio_track: some errors. Reason: {tb.format_exc()}")
    return success, fps, video_duration

def frames_top_cut(img_path: Path, split_factor: float):
    '''
    Cut upper part of the video
    :param img_path: path to the frames folder
    :param split_factor: what part of the video will be cut (0-1)
    :return:
    '''
    for file in img_path.glob('*.jpg'):
        image = cv.imread(str(file))
        vert_size = int(image.shape[0] * split_factor)
        cv.imwrite(str(file), image[:vert_size])

def get_audio_track(input_mp4_path: Path, output_mp3_path: Path) -> bool:
    """
    Get audio track from mp4 file
    :param input_mp4_path: path to the mp4-videofile
    :param output_mp3_path: path for saving mp3-audiofile
    :return: success
    """
    success = False
    try:
        if output_mp3_path.is_file(): output_mp3_path.unlink()
        subprocess.check_call(['ffmpeg', '-i', input_mp4_path.resolve(), '-vn', '-ar', '44100', '-ab', '192K',
                               '-f', 'mp3', output_mp3_path.resolve()])
        success = True
    except:
        logger.info(f"get_audio_track: some errors. Reason: {tb.format_exc()}")
    return success


def get_audio_pauses(input_mp3_path: Path, work_dir: Path, silence_level: int=-20) -> List[Tuple[float, float]]:
    """
    Get pause and silences in audio stream
    :param input_mp3_path: path to the mp3-audiofile
    :param work_dir: work folder for temp files
    :param silence_level: silence level in dB. If audio sygnall less then this level - this is silence
    return: list with silences: (start second, end second)
    """
    try:
        temp_text_file = work_dir.joinpath('temp.txt')
        subprocess.check_call(['./get_silence.sh', input_mp3_path.resolve(), f"{silence_level}dB",
                               temp_text_file.resolve()])
        with open(temp_text_file.resolve(), 'r') as file:
            lines = file.readlines()
        silence_list = parse_silence_seconds(lines)
        temp_text_file.unlink()
    except:
        silence_list = []
        logger.info(f"get_audio_track: some errors. Reason: {tb.format_exc()}")
    return silence_list


def parse_silence_seconds(checked_lines: List[str]) -> List[Tuple[float, float]]:
    """
    Parse silence search results from ffmpeg txt file
    :param checked_lines: lines with ffmpeg silence search results
    return: list with silences: (start second, end second)
    """
    silence_list = []
    current_silence_pair = []
    for line in checked_lines:
        if line.find('silence_start') > 0:
            current_silence_pair = [float(line[line.find('silence_start') + 14 : ])]
        elif line.find('silence_end') > 0 and len(current_silence_pair) == 1:
            current_silence_pair.append(float(line[line.find('silence_end') + 12 : line.find('|')]))
            silence_list.append(tuple(current_silence_pair))
    return silence_list


def make_video(image_folder: Path, audio_file: Path, work_dir: Path, output_video_file: Path, fps: float) -> bool:
    """
    Make mp4-video from audio file and frame images
    :param image_folder: folder with frames
    :param audio_file: mp3-audio file
    :param work_dir: work dir for temp files
    :param output_video_file: saved videofile
    :param fps: frame ratio
    :return: success
    """
    success = False
    try:
        temp_video = work_dir.joinpath("temp.mp4")
        if temp_video.is_file(): temp_video.unlink()
        # Create video from images
        subprocess.check_call(['ffmpeg', '-f', 'image2', '-framerate', f'{fps}', '-pattern_type', 'glob', '-i',
                               image_folder.joinpath('*.jpg').resolve(), temp_video.resolve()])
        # Add audio track
        subprocess.check_call(['ffmpeg', '-i', audio_file.resolve(), '-i',  temp_video.resolve(),
                               output_video_file.resolve()])
        success = True
        if temp_video.is_file(): temp_video.unlink()
    except:
        logger.info(f"make_video: some errors. Reason: {tb.format_exc()}")
    return success


def make_stack_video(image_folder_1: Path, image_folder_2: Path, audio_file: Path, output_dir: Path,
                     output_video_file: Path, fps: int, label_1: str='base', label_2: str='corrected') -> bool:
    """
    Make mp4 horizontal stack video from two images (jpg files) and audio file.
    Size of the images must be equal.
    :param image_folder_1: folder with frames 1
    :param image_folder_2: folder with frames 2
    :param audio_file: mp3-audio file
    :param output_dir: dir with new video frames
    :param output_video_file: saved videofile
    :param fps: frame ratio
    :param label_1: left text label. If no label == ''
    :param label_2: right text label. If no label == ''
    :return: success
    """
    success = False
    try:
        if output_dir.is_dir(): shutil.rmtree(output_dir)
        output_dir.mkdir(exist_ok=True)
        temp_video = output_dir.joinpath("temp.mp4")

        # Create video from images
        left_files = sorted(image_folder_1.glob('*.jpg'))
        right_files = sorted(image_folder_2.glob('*.jpg'))
        min_qnty = min(len(left_files), len(right_files))
        left_image = cv.imread(str(left_files[0]))
        right_image = cv.imread(str(right_files[0]))
        if left_image.shape != right_image.shape: assert ValueError
        new_image_size = [int(left_image.shape[0] / 2), int(left_image.shape[1] / 2)]
        text_coords = (5, int(left_image.shape[0] / 2 - 30))
        color = (0, 255, 255)
        for image_num, image_file in enumerate(left_files[:min_qnty]):
            left_image = cv.imread(str(image_file))
            right_image = cv.imread(str(right_files[image_num]))
            new_left_image = cv.resize(left_image, (new_image_size[1], new_image_size[0]), cv.INTER_NEAREST)
            if label_1:
                cv.putText(new_left_image, label_1, text_coords, cv.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            new_right_image = cv.resize(right_image, (new_image_size[1], new_image_size[0]), cv.INTER_NEAREST)
            if label_2:
                cv.putText(new_right_image, label_2, text_coords, cv.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            join_image = np.zeros((new_image_size[0], new_image_size[1] * 2, 3))
            join_image[:, : new_image_size[1]] = new_left_image
            join_image[:, new_image_size[1]:] = new_right_image
            join_img_file = Path(output_dir, image_file.name)
            cv.imwrite(str(join_img_file), join_image)
        subprocess.check_call(['ffmpeg', '-f', 'image2', '-framerate', f'{fps}', '-pattern_type', 'glob', '-i',
                               output_dir.joinpath('*.jpg').resolve(), temp_video.resolve()])

        # Add audio track
        subprocess.check_call(['ffmpeg', '-i', audio_file.resolve(), '-i',  temp_video.resolve(),
                               output_video_file.resolve()])
        temp_video.unlink()
        success = True
    except ValueError:
        logger.info(f"Sizes of left and right videos are not equal.")
    except:
        logger.info(f"make_stack_video: some errors. Reason: {tb.format_exc()}")
    return success

