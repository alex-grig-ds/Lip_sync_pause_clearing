import traceback as tb
from pathlib import Path

from config import *
from src.video_utils import (parse_silence_seconds, get_audio_track, get_audio_pauses, make_video,
                             make_stack_video, extract_frames)


def test_extract_frames():
    input_mp4_path = Path(TEST_DATA_FOLDER, TEST_VIDEO)
    if not input_mp4_path.is_file(): assert False
    img_dir = Path(TEST_TEMP_FOLDER)
    img_dir.mkdir(exist_ok=True)
    success, fps, duration = extract_frames(input_mp4_path, img_dir, 0)
    assert success
    if len(list(img_dir.glob("*.jpg"))) > 0:
        assert True
    else:
        assert False


def test_parse_silence_seconds():
    parse_example = '''
        Stream mapping:
          Stream #0:0 -> #0:0 (mp3 (native) -> pcm_s16le (native))
        Press [q] to stop, [?] for help
        Output #0, null, to 'pipe:':
          Metadata:
            major_brand     : isom
            minor_version   : 512
            compatible_brands: isomiso2avc1mp41
            encoder         : Lavf57.83.100
            Stream #0:0: Audio: pcm_s16le, 44100 Hz, stereo, s16, 1411 kb/s
            Metadata:
              encoder         : Lavc57.107.100 pcm_s16le
        [silencedetect @ 0x555b2db7f7e0] silence_start: 7.808
        [silencedetect @ 0x555b2db7f7e0] silence_end: 8.41249 | silence_duration: 0.60449
        [silencedetect @ 0x555b2db7f7e0] silence_start: 18.0219
        [silencedetect @ 0x555b2db7f7e0] silence_end: 18.6002 | silence_duration: 0.578367
        [silencedetect @ 0x555b2db7f7e0] silence_start: 28.4709
        [silencedetect @ 0x555b2db7f7e0] silence_end: 29.0231 | silence_duration: 0.552245
        [silencedetect @ 0x555b2db7f7e0] silence_start: 31.5533
        [silencedetect @ 0x555b2db7f7e0] silence_end: 32.105 | silence_duration: 0.552245
        size=N/A time=00:00:32.66 bitrate=N/A speed= 373x    
        video:0kB audio:5626kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: unknown    
        '''
    lines = parse_example.split('\n')
    silence_list = parse_silence_seconds(lines)
    if len(silence_list) != 4: assert False
    if silence_list[0][0] != 7.808: assert False
    if silence_list[-1][-1] != 32.105: assert False
    assert True


def test_get_audio_track():
    input_mp4_path = Path(TEST_DATA_FOLDER, TEST_VIDEO)
    if not input_mp4_path.is_file(): assert False
    output_mp3_path = Path(TEST_DATA_FOLDER, 'test.mp3')
    if output_mp3_path.is_file(): output_mp3_path.unlink()
    success = get_audio_track(input_mp4_path, output_mp3_path)
    assert success
    if output_mp3_path.is_file():
        assert True
    else:
        assert False


def test_get_audio_pauses():
    input_mp3_path = Path(TEST_DATA_FOLDER, TEST_AUDIO)
    if not input_mp3_path.is_file(): assert False
    work_dir = Path(TEST_DATA_FOLDER)
    work_dir.mkdir(exist_ok=True)
    silence_list = get_audio_pauses(input_mp3_path, work_dir, -10)
    if len(silence_list) == 4:
        assert True
    else:
        assert False


def test_make_video():
    img_dir = Path(TEST_DATA_FOLDER, TEST_IMG_FOLDER)
    if not img_dir.is_dir(): assert False
    input_mp3_path = Path(TEST_DATA_FOLDER, TEST_AUDIO_FOR_IMG_TO_VIDEO)
    if not input_mp3_path.is_file(): assert False
    work_dir = Path(TEST_TEMP_FOLDER)
    work_dir.mkdir(exist_ok=True)
    output_mp4_path = Path(TEST_DATA_FOLDER, 'test_from_img.mp4')
    if output_mp4_path.is_file(): output_mp4_path.unlink()
    success = make_video(img_dir, input_mp3_path, work_dir, output_mp4_path, 30)
    assert success
    if output_mp4_path.is_file():
        assert True
    else:
        assert False


def test_make_stack_video():
    img_1_dir = Path(TEST_DATA_FOLDER, TEST_IMG_FOLDER)
    if not img_1_dir.is_dir(): assert False
    img_2_dir = Path(TEST_DATA_FOLDER, TEST_IMG_FOLDER)
    input_mp3_path = Path(TEST_DATA_FOLDER, TEST_AUDIO_FOR_IMG_TO_VIDEO)
    if not input_mp3_path.is_file(): assert False
    work_dir = Path(TEST_TEMP_FOLDER)
    work_dir.mkdir(exist_ok=True)
    output_mp4_path = Path(TEST_DATA_FOLDER, 'test_from_img.mp4')
    if output_mp4_path.is_file(): output_mp4_path.unlink()
    success = make_stack_video(img_1_dir, img_2_dir, input_mp3_path, work_dir, output_mp4_path, 30)
    assert success
    if output_mp4_path.is_file():
        assert True
    else:
        assert False


