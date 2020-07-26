from mitmproxy import proxy, options
import sys
from mitmproxy.tools.dump import DumpMaster

class AddHeader:
    def __init__(self, authHeader):
        self.token = authHeader
    def request(self, flow):
        if "authorization" in flow.request.headers:
            flow.request.headers["authorization"] = "Bearer {}".format(self.token)
            flow.request.headers["User-Agent"] += "z"

def start(authHeader):
    myaddon = AddHeader(authHeader)
    opts = options.Options(listen_host='127.0.0.1', listen_port=19283)
    pconf = proxy.config.ProxyConfig(opts)
    m = DumpMaster(opts)
    m.server = proxy.server.ProxyServer(pconf)
    m.addons.add(myaddon)

    try:
        m.run()
    except KeyboardInterrupt:
        m.shutdown()

if __name__ == "__main__":
    start(sys.argv[1])
