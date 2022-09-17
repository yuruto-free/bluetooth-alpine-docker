#!/usr/bin/python3
# -*- coding: utf-8 -*-

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import simpleaudio
import threading
import json
import logging
import logging.config
import os
import signal
import time
import glob

class PlayAudio():
    """
    PlayAudio

    Attributes
    ----------
    __logger : logging
        logger
    __root_dir : str
        root directory
    __player : WaveObject.PlayObjct
        play object
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
        self.__player = None

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
        self.__player = simpleaudio.play_buffer(bytearray([0, 0]), 1, 1, 44100)
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

    def execute_get(self, event):
        """
        execute target command

        Parameters
        ----------
        event : json string
            command : target command

        Returns
        -------
        response : json string
            status_code : status code
            message : execution information or error message
        """

        try:
            # collect information
            data = json.loads(event)
            command = data['command']

            if 'list' == command:
                out = glob.glob('{}/*.wav'.format(self.__root_dir))
                ret = list(map(lambda x: x.replace('{}/'.format(self.__root_dir), ''), out))
            elif 'stop' == command:
                self.__player.stop()
                ret = ['Music Stopped']
            else:
                ret = []

            response = {'status_code': 200, 'message': ret}
        except Exception as e:
            err_msg = 'Invalid data ({})'.format(e)
            self.__logger.warning(err_msg)
            raise Exception(err_msg)

        return response

    def execute_post(self, event):
        """
        execute target command

        Parameters
        ----------
        event : json string
            filename : wav filename

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

            if self.__player.is_playing():
                self.__player.stop()
                time.sleep(1)
            target = simpleaudio.WaveObject.from_wave_file(abs_path)
            self.__player = target.play()

            response = {'status_code': 200, 'message': filename}
        except Exception as e:
            err_msg = 'Invalid data ({})'.format(e)
            self.__logger.warning(err_msg)
            raise Exception(err_msg)

        return response

class CallbackServer(BaseHTTPRequestHandler):
    """
    Process HTTP Request and Response

    Attributes
    ----------
    __cb_get : callable object
        callback function for get request
    __cb_post : callable object
        callback function for post request
    """

    def __init__(self, cb_get, cb_post, *args):
        """
        Constractor

        Parameters
        ----------
        cb_get : callable object
            callback function for get request
        cb_post : callable object
            callback function for post request
        *args : tuple
            arguments
        """
        self.__cb_get = cb_get
        self.__cb_post = cb_post
        super().__init__(*args)

    def do_GET(self):
        """
        Process GET Request
        """
        try:
            content_length = int(self.headers.get('content-length'))
            request = self.rfile.read(content_length).decode('utf-8')
            response = self.__cb_get(request)
        except Exception as e:
            response = {'status_code': 500, 'message': '{}'.format(e)}

        self.send_response(response['status_code'])
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))


    def do_POST(self):
        """
        Process POST Request
        """
        try:
            content_length = int(self.headers.get('content-length'))
            request = self.rfile.read(content_length).decode('utf-8')
            response = self.__cb_post(request)
        except Exception as e:
            response = {'status_code': 500, 'message': '{}'.format(e)}


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
    __cb_get : callable object
        callback function for get request
    __cb_post : callable object
        callback function for post request
    """

    def __init__(self, port, callback_get, callback_post):
        """
        Constractor

        Parameters
        ----------
        port : int
            port number
        callback_get : callable object
            callback function for get request
        callback_post : callable object
            callback function for post request
        """
        super().__init__()
        self.__port = port
        self.__cb_get = callback_get
        self.__cb_post = callback_post

    def run(self):
        """
        This function is called when this thread starts
        """
        def handler(*args):
            CallbackServer(self.__cb_get, self.__cb_post, *args)
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
        server = HttpServer(int(http_port), pa.execute_get, pa.execute_post)

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
