import webob
import time
from webob.dec import wsgify
import threading
import json

# WSGI handlers
import handlers.static
import handlers.index
import handlers.settings
import handlers.serial_ports
import handlers.xb
import handlers.idigi
import handlers.logs

# application settings
from simulator_settings import settings

# XIG application
import xig

# rci code and handlers
import rci
import xbee

# set the version from XIG
settings['version'] = xig.VERSION


class XigApp(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.xig = None
        self.enable_xig = True
        self.static_handler = handlers.static.StaticHandler()
        self.index_handler = handlers.index.IndexHandler()
        self.settings_handler = handlers.settings.SettingsHandler()
        self.serial_ports_handler = handlers.serial_ports.SerialPortsHandler()
        self.xbee_handler = handlers.xb.XbeeHandler()
        self.idigi_handler = handlers.idigi.idigiHandler()
        self.logs_handler = handlers.logs.LogsHandler()
        
        # register self as an HTTP handler
        rci.set_wsgi_handler(self)
        
        # make sure a local port is set
        settings.setdefault('local_port', 80)
           
    def run(self):
        while 1:
            try: 
                # make sure rci and xbee are connected
                if self.enable_xig and rci.connected() and xbee.ddo_get_param(None, "VR"):
                    self.xig = xig.Xig()
                    # start XIG running forever
                    self.xig.go()
            except Exception, e:
                pass
            self.xig = None
            time.sleep(1)

    def xig_handler(self, request):
        if request.method == 'GET':
            if self.xig:
                response = "on"
            else:
                response = "off"             
            return webob.Response(json.dumps(response), content_type='json')
        elif request.method == 'POST':
            state = request.POST.get('power', 'off')
            if state == "off":
                self.enable_xig = False
                response = "off"
                if self.xig:
                    self.xig.quit()
            else:
                self.enable_xig = True
                if self.xig:
                    response = "on"
                else:
                    response = "off"             
            return webob.Response(json.dumps(response), content_type='json')            
        else:
            return webob.exc.HTTPMethodNotAllowed()        
            
    @wsgify
    def __call__(self, request):
        if request.path_info_peek() in ['s', 'static', 'favicon.ico']:
            # this is a static file request, return static file.
            return self.static_handler(request)
        elif request.path in ['/index.html', 'index', '/', '']:
            # request for the main webpage
            return self.index_handler(request)
        elif request.path in ['/settings']:
            # request for the main webpage
            return self.settings_handler(request)
        elif request.path in ['/serial_ports']:
            # request for the main webpage
            return self.serial_ports_handler(request)
        elif request.path in ['/xbee', '/Xbee', '/XBee']:
            # request for the main webpage
            return self.xbee_handler(request)
        elif request.path in ['/idigi']:
            # request for the main webpage
            return self.idigi_handler(request)
        elif request.path in ['/logs']:
            # request for the main webpage
            return self.logs_handler(request)
        elif request.path in ['/xig']:
            # request for the main webpage
            return self.xig_handler(request)        
        else:
            return webob.exc.HTTPNotFound()

if __name__ == "__main__":
    app = XigApp()
    app.start()
    