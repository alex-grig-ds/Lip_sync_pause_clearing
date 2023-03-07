
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import shutil
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
from PIL import Image
import numpy as np
import imagehash
import cv2 as cv

from config import *

@dataclass
class VideoTransform:
    base_image_dir: Path
    transformed_image_dir: Path
    transformed_audio: Path
    base_image_df: pd.DataFrame  # base video frames description: frame, second, type
    trans_image_df: pd.DataFrame  # transformed video frames description: frame, second, type

    def __post_init__(self):
        self.corrected_df = pd.DataFrame([])
        self.base_step_duration = self.base_image_df.tail(1)['second'].values[0] / len(self.base_image_df)
        self.trans_step_duration = self.trans_image_df.tail(1)['second'].values[0] / len(self.trans_image_df)

    def silence_correction(self, base_silences: List[Tuple[float, float]],
                           trans_silences: List[Tuple[float, float]]) -> pd.DataFrame:
        """
        Make correction of transformed silences
        :param base_silences: [(start second, end second)] for base video
        :param trans_silences: [(start second, end second)] for tranformed video
        :return: combined video:
            frame, source (base / trans), second, silence
        """
        self.corrected_df = self.trans_image_df.copy()
        self.corrected_df['source'] = 'trans'
        for silence in trans_silences:
            current_silence_df = self.trans_image_df.loc[(self.trans_image_df['second'] >= silence[0]) & (self.trans_image_df['second'] <= silence[1]), :].copy()
            self.corrected_df.loc[current_silence_df.index, 'frame'] = self.select_best_silence_block(current_silence_df, base_silences)
            self.corrected_df.loc[current_silence_df.index, 'source'] = 'base'
        return self.corrected_df

    def select_best_silence_block(self, silence_df: pd.DataFrame, base_silences: List[Tuple[float, float]]) -> pd.DataFrame:
        """
        Select most equal to silence_df silence block from base video silences
        :param silence_df:
        :return: corrected df with frames from base video
        """
        start_frame = silence_df.head(1)['frame'].values[0]
        end_frame = silence_df.tail(1)['frame'].values[0]
        best_start = {'score': 100, 'frame_idx': -1, 'silence_idx': -1}  # The less score - the better
        for silence_idx, silence in enumerate(base_silences):
            silence_duration = silence[1] - silence[0]
            check_frames = self.base_image_df.loc[(self.base_image_df['second'] >= silence[0] - 0.1) & (self.base_image_df['second'] <= silence[0] + silence_duration * 0.3), :]
            start_idx, score = self.select_best_frame(start_frame, check_frames)
            if score < best_start['score']:
                best_start['score'] = score
                best_start['frame_idx'] = start_idx
                best_start['silence_idx'] = silence_idx
        if best_start['score'] == 100:
            corrected_df = silence_df.copy()
        else:
            silence = base_silences[best_start['silence_idx']]
            silence_duration = silence[1] - silence[0]
            check_frames = self.base_image_df.loc[
                (self.base_image_df['second'] >= silence[0] + silence_duration * 0.6) & (self.base_image_df['second'] <= silence[0] + silence_duration + 0.1), :]
            end_idx, _ = self.select_best_frame(end_frame, check_frames)
            if end_idx > best_start['frame_idx']:
                corrected_df = self.change_frames(silence_df, best_start['frame_idx'], end_idx)
            else:
                corrected_df = silence_df.copy()
        return corrected_df['frame']

    def select_best_frame(self, base_frame_path: str, frames_df: pd.DataFrame) -> (int, int):
        """
        Select most equal frame from the list to base frame
        :param base_frame:
        :param frames_df:
        :return: best idx, score
        """
        base_image = Image.open(base_frame_path).convert('LA')
        base_hash = imagehash.average_hash(base_image, hash_size=HASH_SIZE)
        best_differ = {
            'score': 100,
            'idx': -1
        }
        for idx, frame in frames_df.iterrows():
            check_image = Image.open(frame['frame']).convert('LA')
            check_hash = imagehash.average_hash(check_image, hash_size=HASH_SIZE)
            differ = np.logical_xor(base_hash.hash.flatten(), check_hash.hash.flatten()).sum()
            if differ <= best_differ['score'] and differ <= HASH_THRESH:
                best_differ['score'] = differ
                best_differ['idx'] = idx
        return best_differ['idx'], best_differ['score']

    def change_frames(self, silence_df, start_idx, end_idx) -> pd.DataFrame:
        """
        Change frames in silence_df with frames from base_df
        :param start_idx:
        :param end_idx:
        :return: corrected DF
        """
        corrected_df = silence_df.copy()
        base_silence_duration = (end_idx - start_idx + 1) * self.base_step_duration
        corr_silence_duration = len(corrected_df) * self.trans_step_duration
        duration_coeff = corr_silence_duration / base_silence_duration
        current_time = 0
        base_idx = start_idx
        corr_idx = 0
        for idx, frame in corrected_df.iterrows():
            corrected_df.loc[idx, 'frame'] = self.base_image_df.loc[base_idx, 'frame']
            corr_idx += 1
            while corr_idx * self.trans_step_duration > (base_idx - start_idx) * self.base_step_duration * duration_coeff:
                base_idx += 1
        return corrected_df

    def copy_img_to_folder(self, output_dir: Path):
        counter = 0
        for _, frame in self.corrected_df.iterrows():
            source_file = Path(frame['frame'])
            if frame['source'] == 'base':
                image = cv.imread(str(source_file))
                height, width = image.shape[:2]
                border_size = 10
                color = (255, 0, 0)
                cv.rectangle(image, (0, 0), (width, height), color, border_size)
                cv.imwrite(str(source_file), image)
            shutil.copy(str(source_file), str(output_dir.joinpath(f"img{str(counter).rjust(5, '0')}.jpg")))
            counter += 1
        return
