# -*- coding: utf-8 -*-
import ConfigParser
import multiprocessing
import os
import time
import win32serviceutil
import win32service
import win32event
import win32api

PROCESSES = {}

class MyTestProcess(multiprocessing.Process):
    def __init__(self, *args, **kwargs):
        super(MyTestProcess, self).__init__(*args, **kwargs)
        self.stop = multiprocessing.Event()
    def run(self):
        while not self.stop.is_set():
            time.sleep(1)
    def shutdown(self):
        self.stop.set()


class SVPySvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "SVPySvc"
    _svc_display_name_ = "Python supervisor service"
    _svc_description_ = "Supervisor service for listed in cofig processes"
    process_names = []
    config_file = None
    stop = False
    shutdown_timeout = 15

    def __init__(self, args):
        self.config_file = 'C:\config.cfg'
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def sleep(self, sec):
        win32api.Sleep(sec * 1000, True)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.log('Получено сообщение об остановке службы, отправлен сигнал «stop» \n')
        self.stop = True
        self.stop_supervisor()
        self.heartbeat(False)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.log('Старт службы\n')
            self.start()
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        except Exception, x:
            self.log('Ошибка : %s \n' % x)
            self.SvcStop()

    def start(self):
        if not PROCESSES:
            self.start_sv()
        while 1:
            self.heartbeat()
            self.sleep(60)

    def log(self, msg):
        with open('C:\\svpysvc.log', 'a') as f:
            f.write(str(msg))
            f.close()

    def get_processes_names(self):
        if not self.process_names:
            config = ConfigParser.ConfigParser()
            config.read(self.config_file)
            section = config.sections()[0]
            self.process_names = [x[1] for x in config.items(section)]

    def start_sv(self):
        self.get_processes_names()
        for name in self.process_names:
            self.log('Запуск процесса {} \n'.format(name))
            PROCESSES[name] = MyTestProcess(name=name)
            PROCESSES[name].start()

    def stop_supervisor(self):
        self.log('Получено сообщение об остановке службы, отправлен сигнал «stop» \n')
        for name, process in PROCESSES.iteritems():
            process.shutdown()
            process.join(self.shutdown_timeout)
        if any([p.is_alive() for p in PROCESSES.values()]):
            for name, process in PROCESSES.iteritems():
                process.terminate()
                process.join(5)
        else:
            self.log('Процессы успешно завершили работу \n')
            self.sleep(5)

    def heartbeat(self, restart=True):
        count = 0
        for name, process in PROCESSES.iteritems():
            if process.is_alive():
                count += 1
            else:
                if restart or not self.stop:
                    self.log('Процесс {} прекратил работу и был перезапущен \n'.format(name))
                    PROCESSES[name].terminate()
                    PROCESSES[name] = MyTestProcess(name=name)
                    PROCESSES[name].start()
        self.log('Служба активна, работают {} из {} процессов \n'.format(
            str(count), str(len(PROCESSES.items()))
        ))

if __name__ == '__main__':
    multiprocessing.freeze_support()
    win32serviceutil.HandleCommandLine(SVPySvc)
