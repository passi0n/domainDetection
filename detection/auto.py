#!/usr/bin/env python

import sys, os, time, atexit, string, signal
from signal import SIGTERM, SIGUSR1

PING_LIMIT = 5
PING_INTERVAL = 1
DIG_LIMIT = 3
DIG_INTERVAL = 3

FILEPREFIX = "/var/named/conf/"


class Agent():
    def __init__(self, peer, common, conf):
        self.peers = peer
        self.ping = 0
        self.dig = 10
        self.post = False
        self.count = 0
        self.common = common
        self.conf = FILEPREFIX + conf
        self.zones = []
        self.parent = False
        self.mirror = False

    def load(self):
        self.zones = []
        if self.conf:
            file = open(self.conf, "r")
            lines = file.readlines()
            for line in lines:
                self.zones.append(line.rstrip('\n'))

    def setParent(self, parent):
        self.parent = parent

    def setMirror(self, mirror):
        self.mirror = mirror

    def check(self):
        if self.mirror:
            return

        self.count += 1
        self.post = self.isValid()

        '''
        if self.count % PING_INTERVAL == 0:
            if os.system("ping -c 1 -W 2 %s > /dev/null" % self.peer) == 0:
                self.ping = 0
            else:
                self.ping += 1
        '''

        if self.count % DIG_INTERVAL == 0:
            for p in self.peers:
                if os.system("dig www.baidu.com @%s > /dev/null" % p) == 0:
                    self.dig = 0
                else:
                    self.dig += 1

    def isValid(self):
        if self.mirror:
            return self.mirror.isValid()

        if self.parent:
            if self.parent.isValid() == True:
                return False

        if self.ping > PING_LIMIT:
            return False
        if self.dig > DIG_LIMIT:
            return False
        return True

    def isChanged(self):
        if self.mirror:
            return self.mirror.isChanged()

        return (self.post != self.isValid())

    def defaultForwarder(self):
        if self.common == False:
            return ""

        if self.isValid() == False:
            return ""

        return " " + "; ".join(self.peers) + "; "

    def zoneForwarder(self):
        if self.isValid() == False:
            return ""

        result = ""
        for zone in self.zones:
            result = result + "zone \"" + zone + ".\" IN {\n"
            result = result + "\ttype forward;\n\tforward only;\n\tforwarders { "
            result = result + "; ".join(self.peers)
            result = result + "; };\n};\n"

        return result


class Daemon():
    def __init__(self, pidfile):
        self.stdin = '/dev/null'
        self.stdout = '/var/named/conf/monitor.log'
        self.stderr = '/dev/null'
        self.pidfile = pidfile
        self.reconfig = False

    def _daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        os.chdir("/")
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write('%s\n' % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = 'pidfile %s already exist. Daemon already running?\n'
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        self._daemonize()
        self._run()

    def stop(self, reload=False):
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = 'pidfile %s does not exist. Daemon not running?\n'
            sys.stderr.write(message % self.pidfile)
            return

        if reload:
            os.kill(pid, SIGUSR1)
            return

        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
                else:
                    print str(err)
                    sys.exit(1)

    def restart(self):
        self.stop()
        self.start()

    def sig_handler(self, sig, frame):
        self.reconfig = True

    def _run(self):
        signal.signal(signal.SIGUSR1, self.sig_handler)

        agents = [
            Agent(["202.96.128.86", "202.96.128.166"], True, "CC.default"),
            Agent(["211.136.112.50"], False, "CM.default"),
            Agent(["58.20.127.238"], True, "CU.default"),
            Agent(["119.29.29.29"], False, "CP"),
            Agent(["100.127.112.23"], False, "CP"),
            Agent(["100.127.112.23"], False, "DPI"),
            Agent(["202.96.128.86", "202.96.128.166"], True, "CC.cache"),
            Agent(["211.136.112.50"], False, "CM.cache"),
            Agent(["58.20.127.238"], True, "CU.cache"),
            Agent(["58.20.127.238"], False, "Local"),
            Agent(["113.215.2.222"], False, "Huashu")
        ]

        agents[4].setParent(agents[2])
        agents[3].setParent(agents[4])

        agents[6].setMirror(agents[0])
        agents[7].setMirror(agents[1])
        agents[8].setMirror(agents[2])

        views = {
            FILEPREFIX + "cache": [8, 6, 7, 3, 4, 9, 10],
            FILEPREFIX + "defaultCC": [0, 2, 1, 3, 4, 5, 9, 10],
            FILEPREFIX + "defaultCU": [2, 0, 1, 3, 4, 5, 9, 10],
        }

        for agent in agents:
            agent.load()

        while True:
            needReload = False
            configstr = ""
            needReconfig = self.reconfig

            if self.reconfig:
                for agent in agents:
                    agent.load()
                needReconfig = True
                self.reconfig = False

            time.sleep(1)
            for agent in agents:
                agent.check()

            for key in views:
                for index in views[key]:
                    # print("%d %d %d" % (index, agents[index].isChanged(), agents[index].isValid()))
                    if agents[index].isChanged() == True:
                        needReload = True
                    elif agents[index].isValid() == True:
                        break

                for index in views[key]:
                    if agents[index].isChanged() and agents[index].zones:
                        configstr = configstr + agents[index].peers[0] + ";"
                        needReconfig = True

                if needReload or needReconfig:
                    while os.system("cp -f %s %s" % (key, key + ".conf")) != 0:
                        print("copy file failed.")
                        time.sleep(1)
                    else:
                        fileHandle = open(key + ".conf", "a")
                        fileHandle.write("zone \".\" IN {\n")
                        fileHandle.write("\ttype forward;\n\tforward only;\n\tforwarders {")

                        forwarder = ""
                        for index in views[key]:
                            if agents[index].isValid():
                                fileHandle.write(agents[index].defaultForwarder())
                                break

                        fileHandle.write("};\n};\n")

                        for index in views[key]:
                            fileHandle.write(agents[index].zoneForwarder())

                        fileHandle.write("\n};\n")
                        fileHandle.close()

            if needReload:
                forwarder = ""
                for key in views:
                    for index in views[key]:
                        if agents[index].isValid():
                            forwarder = forwarder + agents[index].peers[0] + ";"
                            break
                file("/tmp/dns_forwarder", 'w+').write(forwarder)

                print("%s reloading" % time.strftime('%d %b %Y %H:%M:%S'))
                print(forwarder)

                while os.system("rndc reload >> /dev/null") != 0:
                    print("rndc reload failed")
                    file("/tmp/dns_error", 'w+').write("rndc reload failed")
                    time.sleep(1)

                while os.system("rndc flush >> /dev/null") != 0:
                    print("rndc flush failed")
                    file("/tmp/dns_error", 'w+').write("rndc flush failed")
                    time.sleep(1)

                time.sleep(30)

            elif needReconfig:
                file("/tmp/dns_config", 'w+').write(time.strftime('%d %b %Y %H:%M:%S '))
                print("%s reconfiguring" % time.strftime('%d %b %Y %H:%M:%S'))
                print(configstr)

                while os.system("rndc reload >> /dev/null") != 0:
                    print("rndc reload failed")
                    file("/tmp/dns_error", 'w+').write("rndc reconfig failed")
                    time.sleep(1)

                while os.system("rndc flush >> /dev/null") != 0:
                    print("rndc flush failed")
                    file("/tmp/dns_error", 'w+').write("rndc flush failed")
                    time.sleep(1)

                time.sleep(10)


if __name__ == "__main__":
    daemon = Daemon('/tmp/dns_check.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            print 'start daemon'
            daemon.start()
        elif 'stop' == sys.argv[1]:
            print 'stop daemon'
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            print 'restart daemon'
            daemon.restart()
        elif 'reload' == sys.argv[1]:
            print 'reload daemon'
            daemon.stop(True)
        else:
            print 'unknown command'
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
