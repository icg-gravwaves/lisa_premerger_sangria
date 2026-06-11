# Inpainting

Here we include plots etc which show how inpainting is implemented / used. This is a companion to Section IV of the paper, but the plots generated here are not included there.

## SNR buildup animation

Below we show a video of the SNR timeseries as the data end (shown in orange) moves closer to merger (time zero), with gaps added to the data at 20 and 10 days before merger.

<video width="100%" controls>
    <source src="../_static/inpainting_movie.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

We see that the SNR at the time of merger gradually increases as time moves forward, with pauses during the gaps. The peak starts to become significant compared to the background at around 12 days before merger.

The SNR series in the past is static, but beyond the end of the data there is variation as we move forward in time.

### Making animation stills

To make the movie, we use `make_images.py`, which uses a generated signal from our previous paper (downloaded from that repo). We step through the data in 0.1 day steps, and gate / inpaint from the end of the data through to the end of the timeseries. We add gaps if appropriate.

We use the full waveform for comparison, from the zero-noise data file in the previous paper, and calculate the matched filter between that and the (noise-included) data. For the normalisation $(h|h)$, we apply a mask where there are gaps / the end of the data.

The rest of the script is just making the plots in such a way that it is a seamless transition from one frame to the next.

### Making the movie

We then use ffmpeg to generate the movie from these stills:
```bash
ffmpeg -framerate 10 -i output/snr_inpaintendandgaps_%d.png \
-c:v libx264 -pix_fmt yuv420p \
-vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
-crf 18 -preset slow \
-movflags +faststart \
inpainting_movie.mp4
```
