import os
import re
import math
import json

import numpy as np
import pandas as pd
from tqdm import tqdm
import librosa
from librosa.feature import mfcc


class ETS_mfcc:
    def __init__(self, data_path: str, hop_length: float, window_length: float) -> None:
        self.data_path = data_path
        self.sr = None
        self.audio = None
        self.metadata = None

        self.hop_length = hop_length
        self.window_length = window_length
        self.shift_size = None
        self.window_size = None
        self.feature_cols = ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12']

        self.mfcc_df = dict([])

    
    def __load_audio(self, audio_path: str) -> None:
        audio, self.sr = librosa.load(
            audio_path, dtype=np.float64, sr=None, mono=False
        )

        self.audio = audio[0]
        self.shift_size = int(self.hop_length * self.sr)
        self.window_size = int(self.window_length * self.sr)


    def __load_anotation_as_samples(self, anotation_path: str, sperator: str) -> dict[str, pd.DataFrame]:
        def time_to_sample_converter(row, sr):
            row['start'] = math.floor(row['start'] * sr)
            row['end'] = math.floor(row['end'] * sr)
            return row
        
        df = pd.read_csv(
            anotation_path, sep=sperator, 
            names=['start', 'end', 'type']
        ).apply(
            lambda row: time_to_sample_converter(row, self.sr), axis=1
        )

        df_t = df['type']
        chunk = {
            'aa': df.loc[df_t == 'aa'],
            'ee': df.loc[df_t == 'ee'],
            'ii': df.loc[df_t == 'ii'],
            'xx': df.loc[df_t == 'xx'],
            'oo': df.loc[df_t == 'oo'],
            'uu': df.loc[df_t == 'uu'],
            'yy': df.loc[df_t == 'yy']
        }

        return chunk


    def __load_metadata(self, metadata_path: str) -> None:
        with open(metadata_path, 'r') as f: 
            self.metadata = json.load(f)
    


    def __convert_audio_to_mfcc(self, audio: np.ndarray, num_mfcc: int) -> np.ndarray:
        return mfcc(
            y=audio,
            sr=self.sr,
            n_mfcc=num_mfcc,
            hop_length=self.shift_size,
            win_length=self.window_size,
            n_mels=32,
            dtype=np.float64
        )[1:].T
    

    def __segment_audio(self, chunk: dict[str, pd.DataFrame])-> list[np.ndarray]:
        audio_segments = {'aa': [], 'ee': [], 'ii': [], 'xx': [], 'oo': [], 'uu': [], 'yy': []}

        for chunk_type, chunk_df in tqdm(chunk.items(), total=7, desc='segmenting audio'):
            for row in chunk_df.itertuples(None):
                audio_segment = self.audio[row.start:row.end]
                audio_segments[chunk_type].append(audio_segment)

        return audio_segments


    def pipeline(self, audio_path: str, anotation_path: str, metadata_path: str, save_path: str, subject_cntr: int):
        self.__load_audio(audio_path)
        self.__load_metadata(metadata_path)
        chunk = self.__load_anotation_as_samples(anotation_path, '\t')
        
        # segemnt audio according to annotaions
        audio_segments = self.__segment_audio(chunk)

        # convert to mfcc for the perticular person
        mb_name = self.metadata['subjectBiodata']['subjectName']
        asthma_status = self.metadata['subjectBiodata']['subjectType']

        
        for segment_type, segments in tqdm(audio_segments.items(), total=7, desc='conversion to mfcc dataframes'):
            # dataframe for each phonon
            mfcc_df = pd.DataFrame(columns = ['mb_name'] + self.feature_cols + ['phonon', 'asthma_status'])

            # insert the mfcc n*m matrix in the dataframe + other columns for the person and the phonon
            for idx, segment in enumerate(segments):
                mfcc_segment = self.__convert_audio_to_mfcc(segment, 13)
                df = pd.DataFrame(
                    mfcc_segment,
                    columns=self.feature_cols
                )

                num_rows = mfcc_segment.shape[0]
                df.insert(0, 'mb_name', [mb_name]*num_rows)
                df['phonon'] = [f'{segment_type}_{idx}']*num_rows
                df['asthma_status'] = [asthma_status]*num_rows

                # append the current segement mfcc to the other segments df for the same phonon
                mfcc_df = pd.concat([mfcc_df, df], ignore_index=False)
            
            # set the value for the mfcc_df phonon as the curent df 
            self.mfcc_df[segment_type] = mfcc_df
        
        # save dataframe as a csv
        if subject_cntr == 0:
            for mfcc_phonon, corr_df in tqdm(self.mfcc_df.items(), total=7, desc='saving dataframes'):
                corr_df.to_csv(
                    os.path.join(save_path, f'{mfcc_phonon}.csv'), 
                    mode='a', index=True, header=True
                )
        else:
            for mfcc_phonon, corr_df in tqdm(self.mfcc_df.items(), total=7, desc='saving dataframes'):
                corr_df.to_csv(
                    os.path.join(save_path, f'{mfcc_phonon}.csv'), 
                    mode='a', index=True, header=False
                )


def main():
    data_path = os.path.join('..', '..', 'data', 'SHIVANI_DATA_2016')
    save_path = os.path.join('..', '..', 'data', 'mfcc_data')
    HOP_LENGTH = 10 * 10**(-3)
    WINDOW_LENGTH = 20 * 10**(-3)

    mfcc_maker = ETS_mfcc(data_path, HOP_LENGTH, WINDOW_LENGTH)

    subject_cntr = 0
    for name in os.listdir(data_path):
        print(name, subject_cntr)
        dir_path = os.path.join(data_path, name)


        audio_path = None
        anotation_path = None
        metadata_path = None
        for file in os.listdir(os.path.join(data_path, name)):
            if re.match('^.+before.+[.]wav$', file) != None: 
                audio_path = os.path.join(dir_path, file)
            if re.match('^.+before.+[.]anote[.]txt$', file) != None: 
                anotation_path = os.path.join(dir_path, file)
            if re.match('^.+[.]json$', file) != None: 
                metadata_path = os.path.join(dir_path, file)

        print(audio_path, anotation_path, metadata_path)
        if audio_path != None and anotation_path != None and metadata_path != None:
            print('valid')
            mfcc_maker.pipeline(audio_path, anotation_path, metadata_path, save_path, subject_cntr)
            subject_cntr+=1

if __name__ == '__main__':
    main()
