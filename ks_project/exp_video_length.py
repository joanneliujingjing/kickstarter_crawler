#test video stream
url = "https://d2pq0u4uni88oo.cloudfront.net/projects/824027/video-390569-h264_base.mp4"
from hsaudiotag import mp4 # $ pip install hsaudiotag
import requests
from StringIO import StringIO
from contextlib import closing
with closing(requests.get(url,stream=True, verify=False)) as r:
    a = r.raw.read(2000) #2kb buffer
    b = StringIO()
    b.write(a)
    c = mp4.File(b)
    print c.duration
    b.close()
