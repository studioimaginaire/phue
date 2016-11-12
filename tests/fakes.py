import json
import sys
import samples

if sys.version_info[0] > 2:
    from io import BytesIO as StringIO
    def dump(data):
        return json.dumps(data).encode('utf-8')
else:
    from StringIO import StringIO
    def dump(data):
       return json.dumps(data)


class Request(object):
    def __init__(self, mode, addr, data):
        self.mode = mode
        self.addr = addr
        self.data = data


class FakeHTTP(object):

    def __init__(self, *args, **kwargs):
        super(FakeHTTP, self).__init__()
        self.call = None

    def request(self, mode, addr, data=None):
        self.call = Request(mode, addr, data)

    def getresponse(self):
        data = samples.RESP[self.call.mode][self.call.addr]
        return StringIO(dump(data))

    def close(self):
        pass
