#!/usr/bin/python3
# -*- coding: utf-8 -*-

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from simpleaudio import WaveObject
import threading
import json
import logging
import logging.config
import os
import signal
import time

class PlayAudio():
    """
    PlayAudio

    Attributes
    ----------
    __logger : logging
        logger
    __root_dir : str
        root directory
    """

    def __init__(self, log_configure, config_name):
        """
        Constractor

        Parameters
        ----------
        log_configure : dict
            logging information
        config_name : str
            config name
        """
        # logger
        logging.config.dictConfig(log_configure)
        self.__logger = logging.getLogger(config_name)
        self.__root_dir = None

    def initialize(self, wav_root_dir):
        """
        initialize

        Parameters
        ----------
        wav_root_dir : str
            root directory
        """
        self.__logger.info('Start initialization')
        self.__root_dir = wav_root_dir
        self.__logger.info('Complete initialization')

    def logging_error(self, err_msg):
        """
        logging error message

        Parameters
        ----------
        err_msg : str
            error message
        """
        self.__logger.warning(err_msg)

    def finalize(self):
        """
        finalize
        """
        self.__logger.info('Stop {}'.format(self.__class__.__name__))

    def execute(self, event):
        """
        execute target command

        Parameters
        ----------
        event : json string
            machine : machine name defined by JSON_CONFIG_PATH
            command : target command list
            message : execution information

        Returns
        -------
        response : json string
            status_code : status code
            message : execution information or error message
        """

        try:
            # collect information
            data = json.loads(event)
            filename = data['filename']
            abs_path = '{}/{}'.format(self.__root_dir, filename)
            target = WaveObject.from_wave_file(abs_path)
            player = target.play()
            player.wait_done()

            response = {'status_code': 200, 'message': filename}
        except Exception as e:
            self.__logger.warning('Invalid data ({})'.format(e))
            raise Exception(e)

        return response

class CallbackServer(BaseHTTPRequestHandler):
    """
    Process HTTP Request and Response

    Attributes
    ----------
    __callback : callable object
        callback function
    """

    def __init__(self, callback, *args):
        """
        Constractor

        Parameters
        ----------
        callback : callable object
            callback function
        *args : tuple
            arguments
        """
        self.__callback = callback
        super().__init__(*args)

    def do_POST(self):
        """
        Process POST Request
        """
        try:
            content_length = int(self.headers.get('content-length'))
            request = self.rfile.read(content_length).decode('utf-8')
            response = self.__callback(request)
        except Exception as e:
            response = {'status_code': 500, 'message': e}

        self.send_response(response['status_code'])
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

class HttpServer(threading.Thread):
    """
    HTTP Server

    Attributes
    ----------
    __port : int
        port number
    __callback : callable object
        callback function
    """

    def __init__(self, port, callback):
        """
        Constractor

        Parameters
        ----------
        port : int
            port number
        callback : callable object
            callback function
        """
        super().__init__()
        self.__port = port
        self.__callback = callback

    def run(self):
        """
        This function is called when this thread starts
        """
        def handler(*args):
            CallbackServer(self.__callback, *args)
        self.server = ThreadingHTTPServer(('', self.__port), handler)
        self.server.serve_forever()

    def stop(self):
        """
        This function is called when this thread stops
        """
        self.server.shutdown()
        self.server.server_close()

class ProcessStatus():
    """
    Process Status

    Attributes
    ----------
    __status : bool
        True  : running
        False : stopped
    """

    def __init__(self):
        """
        Constractor
        """
        self.__status = True

    def change_status(self, signum, frame):
        """
        Change status

        Parameters
        ----------
        signum : int
            signal number
        frame : str
            frame information
        """
        self.__status = False

    def get_status(self):
        """
        Get current status
        """
        return self.__status

# ================
# = main routine =
# ================
if __name__ == '__main__':
    # ===============
    # define constant
    # ===============
    config_name = 'audioServer'
    root_dir = os.getenv('AUDIO_ROOT_PATH', '/audiofiles')
    log_absolute_path = '/var/log/{}.log'.format(config_name)
    http_port = os.getenv('SERVER_PORT', '10650')

    # ================
    # setup log-config
    # ================
    log_configure = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'infoFormat': {
                'format': '[%(asctime)s %(levelname)s] %(name)s %(message)s',
                'datefmt': '%Y/%m/%d %H:%M:%S'
            }
        },
        'handlers': {
            'timeRotate': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'infoFormat',
                'filename': log_absolute_path,
                'when': 'W2',
                'backupCount': 5
            },
            'consoleHandler': {
                'class': 'logging.StreamHandler',
                'formatter': 'infoFormat'
            }
        },
        'loggers': {
            config_name: {
                'level': 'INFO',
                'handlers': ['timeRotate', 'consoleHandler']
            }
        }
    }

    # ==============================
    # Create process_status instance
    # ==============================
    process_status = ProcessStatus()
    signal.signal(signal.SIGINT, process_status.change_status)
    signal.signal(signal.SIGTERM, process_status.change_status)

    # ==========================
    # Create play audio instance
    # ==========================
    pa = PlayAudio(log_configure, config_name)

    try:
        # ==========
        # initialize
        # ==========
        pa.initialize(root_dir)

        # ===========================
        # Create HTTP server instance
        # ===========================
        server = HttpServer(int(http_port), pa.execute)

        # =============
        # = main loop =
        # =============
        server.start()
        while process_status.get_status():
            time.sleep(0.1)
        server.stop()

    except Exception as e:
        pa.logging_error('Error(main): {}'.format(e))
    # ========
    # finalize
    # ========
    pa.finalize()
