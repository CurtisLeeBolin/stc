#!/usr/bin/env python3
#
#  stc.py
#
#  Copyright 2023 Curtis Lee Bolin <CurtisLeeBolin@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import datetime
import os
import re
import subprocess
import time
import avtc
import glob
import random
import pathlib


class STC(avtc.AVTC):


    def __init__(self, workingDir):
        self.workingDir = workingDir


    def run(self):
        dirList=[]
        with os.scandir(self.workingDir) as it:
            for entry in it:
                dirList.append(entry.name)
        #dirList.sort()
        random.shuffle(dirList)

        dirDict={}
        for directory in dirList:
            if os.path.isdir(directory):
                if directory not in ['0in', '0out', '0not_empty']:
                    dirDict[directory]=[]

        for directory in dirDict:
            with os.scandir(f'{self.workingDir}/{directory}') as it:
                for entry in it:
                    if entry.is_file():
                        dirDict[directory].append(f'{entry.name}')

        for directory, fileList in dirDict.items():
            if os.path.isdir(directory):
                pathlib.Path(f'{self.workingDir}/{self.outputDir}/{directory}').mkdir(parents=True, exist_ok=True)
                if os.path.isdir(f'{directory}/images'):
                    if not os.path.isdir(f'{self.outputDir}/{directory}/images'):
                        os.renames(f'{directory}/images', f'{self.outputDir}/{directory}/images')
                    else:
                        for file in os.listdir(f'{directory}/images'):
                            try:
                                os.renames(f'{directory}/images/{file}', f'{self.outputDir}/{directory}/images/{file}')
                            except OSError:
                                os.remove(f'{directory}/images/{file}')
                if os.path.isfile(f'{directory}/info'):
                    try:
                        os.renames(f'{directory}/info', f'{self.outputDir}/{directory}/info')
                    except OSError:
                        with open(f'{directory}/info', 'r') as f1:
                            with open(f'{self.outputDir}/{directory}/info', 'a') as f2:
                                for line in f1:
                                    f2.write(line)
                        os.remove(f'{directory}/info')
                fileList.sort()
                for file in fileList:
                    filename, fileExtension = os.path.splitext(file)
                    if self.checkFileType(fileExtension) and os.path.isfile(f'{directory}/{file}'):
                        self.transcode(file, filename, directory)
                try:
                    if os.listdir(directory):
                        if not glob.glob(f'{directory}/*.lock'):
                            pathlib.Path(f'{self.workingDir}/0not_empty').mkdir(parents=True, exist_ok=True)
                            os.renames(directory, f'0not_empty/{directory}')
                    else:
                        os.rmdir(directory)
                except FileNotFoundError:
                    print(f'\nDirectory {directory} is missing.\n')


    def transcode(self, file, filename, directory):
        workingFile = f'{self.workingDir}/{directory}/{file}'
        lockFile = f'{self.workingDir}/{directory}/{file}.lock'
        inputFile = f'{self.workingDir}/{self.inputDir}/{directory}/{file}'
        outputFile = f'{self.workingDir}/{self.outputDir}/{directory}/{filename}.mp4'
        outputFilePart = f'{self.workingDir}/{self.outputDir}/{directory}/{filename}.part'
        errorFile = f'{self.workingDir}/{directory}/{file}.error'

        if not os.path.isfile(lockFile):
            print(workingFile)

            with open(lockFile, 'w') as f:
                pass

            transcodeArgs = [
              'ffmpeg', '-i', workingFile, '-filter:v',
              'scale=w=\'max(1920,iw)\':h=\'min(1080,ih)\':force_original_aspect_ratio=decrease:force_divisible_by=8',
              '-c:v', 'libx265', '-c:a', 'aac', '-movflags', '+faststart',
              '-map_metadata', '-1', '-y', '-f', 'mp4',
              outputFilePart]

            pathlib.Path(f'{self.workingDir}/{self.outputDir}/{directory}').mkdir(parents=True, exist_ok=True)
            returncode, stderrList = self.runSubprocess(transcodeArgs)

            if returncode == 0:
                os.remove(lockFile)
                pathlib.Path(f'{self.workingDir}/{self.inputDir}/{directory}').mkdir(parents=True, exist_ok=True)
                os.rename(workingFile, inputFile)
                os.rename(outputFilePart, outputFile)
            else:
                self.writeErrorFile(errorFile, transcodeArgs, stderrList)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog='stc.py',
        description='Subdirectory TransCoder',
        epilog=(
            'Copyright 2023 Curtis Lee Bolin <CurtisLeeBolin@gmail.com>'))
    args = parser.parse_args()

    workingDir = f'{os.getcwd()}'

    tc = STC(workingDir)
    tc.run()


if __name__ == '__main__':
    main()
