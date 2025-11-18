ffmpeg -framerate 4 -i snr_inpaintendandgaps_%d.png \
-c:v libx264 -pix_fmt yuv420p \
-vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
-crf 18 -preset slow \
output.mp4
