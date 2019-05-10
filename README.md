# rtsp-rtp

### What?
This is a minimal toolset needed to get an  H264/AVC stream from RTSP-enabled camera, written as a PoC in pure Python with no external dependencies.

It includes a (partial) implementation of RTSP client (supports basic and digest auth), RTP datagram (courtesy of github.com/plazmer) and NAL unit (FU-A fragmentation only) parsers.

It is **not** a fully featured, generic, production ready toolset, but rather an R&D playground.

### Limitations
- No FU-B NAL units parsing
- No QoS/RTCP
- No keepalives

### Usage
```
from control import RTSPClient
from transport import RTPStream


url = 'rtsp://username:password@10.0.0.1:554/Streaming/Channels/101'

with RTSPClient(url) as client, RTPStream() as stream:
    # send RTSP SETUP
    client.setup(stream.port)

    # initiate streaming
    client.play()

    with open('/tmp/stream','wb+') as f:
        for chunk in stream.generate():
            f.write(chunk)
            # f.flush()

```

Also, take a look at [example.py](example.py)
