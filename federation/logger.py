class Logger(object):
    class __Logger():
        def __init__(self):
            self.filename = None

        def __str__(self):
                return "{0!r} {1}".format(self, self.filename)

        def _write_log(self, level, msg):
            with open(self.filename, 'a') as log_file:
                log_file.write('[{0}]: {1}\n'.format(level, msg))
#This is the messages for our programs!
        def critical(self, msg1):
            self._write_log("CRITICAL", msg1)
        
        def error(self, msg2):
            self._write_log("ERROR", msg2)

        def debug(self, msg3):
            self._write_log("DEBUG", msg3)

        def info(self, msg4):
            self._write_log("INFO", msg4)

        def warning(self, msg5):
            self._write_log("WARNING", msg5)
#######################################

    instance = None

    def __new__(cls):
        if not Logger.instance:
            Logger.instance = Logger.__Logger()
        return Logger.instance

    def __getattribute__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)
