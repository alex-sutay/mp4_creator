from PIL import Image, ImageDraw
import yaml
import numpy
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip, AudioClip, ImageSequenceClip
import os


class VideoCreator:
    def __init__(self, width, height, default_im):
        self.imgs = []
        self.w = width
        self.h = height
        self.audio = None
        self.def_im = default_im

    def add_clip(self, bkg_color, point_color, point_size, time, dur):
        # create image
        img = Image.new(mode='RGBA', size=(self.w, self.h), color=bkg_color)

        # add the focus in the middle
        draw = ImageDraw.Draw(img)
        coords = (self.w // 2 - (d := point_size // 2), self.h // 2 - d, self.w // 2 + d, self.h // 2 + d)
        draw.ellipse(coords, fill=point_color)

        # add images to our list
        self.imgs += [self.def_im] * max(0, (time + dur - len(self.imgs)))
        for i in range(time, time+dur):
            self.imgs[i] = img

    def add_audio(self, clip, time, dur):
        if self.audio is None:
            self.audio = clip.set_duration(dur).set_start(time)
        else:
            self.audio = CompositeAudioClip([self.audio, clip.set_duration(dur).set_start(time)])

    def export(self, fname, fps=10):
        # create the video
        self.imgs += [self.def_im] * max(0, int(self.audio.duration - len(self.imgs)))
        imgs = [numpy.array(self.imgs[i//fps]) for i in range(len(self.imgs) * fps)]
        im_clip = ImageSequenceClip(imgs, fps=fps)
        vid_clip = im_clip.set_audio(self.audio)
        vid_clip.duration = self.audio.duration

        # save
        vid_clip.write_videofile(fname)
        del imgs


def make_from_conf(fname='config.yml'):
    with open(fname) as f:
        conf = yaml.safe_load(f)

    # create image
    b_color = ((bkd := conf['background'])['R'], bkd['G'], bkd['B'], bkd['A'])
    img = Image.new(mode='RGBA', size=(bkd['width'], bkd['height']), color=b_color)

    # add the focus in the middle
    draw = ImageDraw.Draw(img)
    coords = ((w := bkd['width'] // 2) - (d := conf['focus']['size'] // 2), (h := bkd['height'] // 2) - d, w + d, h + d)
    f_color = (conf['focus']['R'], conf['focus']['G'], conf['focus']['B'], conf['focus']['A'])
    draw.ellipse(coords, fill=f_color)

    # create the audio track
    background = AudioFileClip(conf['audio']['noise_f'])
    noise_len = conf['audio']['noise_before']
    noise_initial = conf['audio']['initial_noise']
    audio = background.set_duration(noise_initial)
    i = noise_initial + (s_before := conf['audio']['silence_before'])
    s_after = conf['audio']['silence_after']
    for fname in os.listdir(d := conf['audio']['questions_d']):
        # todo add ground truth file
        question = AudioFileClip(os.path.join(d, fname))
        audio = CompositeAudioClip([audio, question.set_start(i),
                                    background.set_duration(noise_len).set_start(i + question.duration + s_after)])
        i += noise_len + s_before + question.duration + s_after

    # create the video
    img = numpy.array(img)
    im_clip = ImageClip(img)
    vid_clip = im_clip.set_audio(audio)
    vid_clip.duration = audio.duration
    vid_clip.fps = 4

    # save
    vid_clip.write_videofile('output.mp4')


def focus_test(num, dur):
    blank_bkg = Image.new(mode='RGBA', size=(1920, 1080), color=(0, 0, 0, 0))
    v = VideoCreator(1920, 1080, blank_bkg)
    bkg_noise = AudioFileClip('white_noise.mp4')
    v.add_audio(bkg_noise, 0, 2 * num * dur)
    for i in range(num):
        v.add_clip((0, 0, 0, 0), (0, 255, 0, 0), 20, dur*2*i+dur, dur)
    v.export('focus.mp4')


def light_scale_test(step, mn=0, mx=255):
    blank_bkg = Image.new(mode='RGBA', size=(1920, 1080), color=(0, 0, 0, 0))
    v = VideoCreator(1920, 1080, blank_bkg)
    v.add_clip((mn, mn, mn, 0), (mn, mn, mn, 0), 1, 0, 1)
    t = 1
    for i in range(mn, mx, step):
        v.add_clip((i, i, i, 0), (i, i, i, 0), 1, t, 1)
        t += 1
    v.add_clip((mx, mx, mx, 0), (mx, mx, mx, 0), 1, t, 1)
    bkg_noise = AudioFileClip('white_noise.mp4')
    v.add_audio(bkg_noise, 0, t)
    v.export('scale.mp4')


def main():
    focus_test(3, 10)
    light_scale_test(5)


if __name__ == '__main__':
    main()
