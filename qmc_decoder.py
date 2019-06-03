# encoding: utf-8

'''

@author: ZiqiLiu


@file: qmc_decoder.py

@time: 2019-06-02 21:32

@desc:
'''
import shutil
import os
from glob import glob
import argparse

_max_len = 50331648  # 48MB


class QMCMask:
    seed_map = [[0x4a, 0xd6, 0xca, 0x90, 0x67, 0xf7, 0x52],
                [0x5e, 0x95, 0x23, 0x9f, 0x13, 0x11, 0x7e],
                [0x47, 0x74, 0x3d, 0x90, 0xaa, 0x3f, 0x51],
                [0xc6, 0x09, 0xd5, 0x9f, 0xfa, 0x66, 0xf9],
                [0xf3, 0xd6, 0xa1, 0x90, 0xa0, 0xf7, 0xf0],
                [0x1d, 0x95, 0xde, 0x9f, 0x84, 0x11, 0xf4],
                [0x0e, 0x74, 0xbb, 0x90, 0xbc, 0x3f, 0x92],
                [0x00, 0x09, 0x5b, 0x9f, 0x62, 0x66, 0xa1]]

    def __init__(self):
        self.x = -1
        self.y = 8
        self.dx = 1
        self.index = -1

    def _next_mask(self):
        ret = 0
        self.index += 1
        if self.x < 0:
            self.dx = 1
            self.y = (8 - self.y) % 8
            ret = 0xc3

        elif self.x > 6:
            self.dx = -1
            self.y = 7 - self.y
            ret = 0xd8
        else:
            ret = self.seed_map[self.y][self.x]

        self.x += self.dx
        if self.index == 0x8000 or (self.index > 0x8000 and (self.index + 1) % 0x8000 == 0):
            return self._next_mask()
        return ret

    @staticmethod
    def get_mask():
        mask_path = os.path.dirname(os.path.realpath(__file__)) + '/mask.bin'
        mask_data = None
        if not os.path.isfile(mask_path):
            print('mask not found, generating mask and save to ' + mask_path)
            mask_data = bytearray(_max_len)
            seed = QMCMask()
            for i in range(_max_len):
                mask_data[i] = seed._next_mask()
            with open(mask_path, 'wb') as f:
                f.write(mask_data)
        else:
            with open(mask_path, 'rb') as f:
                mask_data = f.read()
        return mask_data


class QMCDecoder:
    suffix_map = {'.qmc3': '.mp3', '.qmc0': '.mp3', '.qmcflac': '.flac'}

    def __init__(self):
        print('loading mask...')
        self.mask = QMCMask.get_mask()

    def decode(self, dir: str, output_dir: str = None, ovewrite: bool = False):
        files = filter(lambda x: any([x.endswith(suf) for suf in self.suffix_map]), glob(dir + "/*.*"))
        if not os.path.isdir(dir):
            raise ValueError('input dir %s not exist!' % dir)
        self.output_dir = output_dir if output_dir else dir + "/output"
        if os.path.isdir(self.output_dir) and ovewrite:
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)  # will raise exception if exist
        for file in files:
            self._process_one(file)
        print('done! Decoded file saved to %s' % self.output_dir)

    def _process_one(self, file: str):
        print('decoding %s...' % file)
        file_name = file.split('/')[-1]
        idx = file_name.rfind('.')
        name, suffix = file_name[:idx], file_name[idx:]
        with open(file, 'rb') as f:
            data = bytearray(f.read())
        if len(data) > _max_len:
            print('file size >= 48MB, skip!')
            return
        for i in range(len(data)):
            data[i] ^= self.mask[i]
        with open("%s/%s%s" % (self.output_dir, name, self.suffix_map[suffix]), 'wb') as f:
            f.write(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="QMC decoder")
    parser.add_argument('-i', '--input', help='input dir')
    parser.add_argument('-o', '--output', help='output dir', default=None)
    parser.add_argument('-f', '--force', help='overwirte output dir', default=False, action="store_true")
    flags = parser.parse_args().__dict__

    qmc = QMCDecoder()
    qmc.decode(flags['input'], flags['output'], flags['force'])
