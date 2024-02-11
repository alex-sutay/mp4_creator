from PIL import Image, ImageDraw
import yaml
import numpy
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip, AudioClip
import os


with open('config.yml') as f:
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
audio = background.set_duration(10)
i = noise_len + (s_before := conf['audio']['silence_before'])
s_after = conf['audio']['silence_after']
for fname in os.listdir(d := conf['audio']['questions_d']):
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
