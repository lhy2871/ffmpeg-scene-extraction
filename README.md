# ffmpeg-scene-extraction
automatically split a large movie file into component scenes

README
FORK FROM geluso/ffmpeg-scene-extraction

# 使用方法为在终端或者cmd下用如下命令：
Use command as:
python + 路径\batchSceneCut.py + 素材文件夹
python + PATH\batchSceneCut.py + PATHyouWant2extraction
例如：
# such as:
python /Users/hanyuanliu/Desktop/batchSceneCut/batchSceneCut_win.py /Users/hanyuanliu/Documents/This/xavc 
# ！！！注意不要再路径后面添加"/"！！！
# !!!Attention not add / after PATHyouWant2extraction!!!


在batchSceneCut.py文件中定义了场景探测灵敏度
灵敏度定义在文件第22行
probe_command = "ffprobe -hide_banner -show_frames -of compact=p=0 -f lavfi \"movie=%s,select=gt(scene\,.4)\" > %s 2>/dev/null"
其中gt(scene\,.4)最后的".4"就是灵敏度数值（0-1）数字越小灵敏度越高，默认值为0.4

