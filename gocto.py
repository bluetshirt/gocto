# coding=utf-8
from __future__ import absolute_import, unicode_literals

import octoprint.plugin
import os
import threading
import time
import socket
from subprocess import call
import time

class GoctoPlugin(octoprint.plugin.StartupPlugin,
                      octoprint.plugin.ShutdownPlugin,
                      octoprint.plugin.SettingsPlugin
                      ):

    def is_printing(self):
        return self._printer.get_state_id() == "PRINTING" or self._printer.is_printing()

    def is_online(self):
        try:
            PING_TARGET = "8.8.8.8"
            cmd = "ping -c 1 %s" % PING_TARGET
            output = os.popen(cmd).read()
            #self._logger.info("ping output:")
            #self._logger.info(output)
            return ("1 received" in output)
        except:
            return False

    def hit_minimum_uptime(self):
        MIN_UPTIME = 60 * 60 * 2
        uptime = time.time() - self.startup_time
        return uptime > MIN_UPTIME

    '''parse ifconfig output to see if ip matches 192.168.68.246'''
    def is_correct_ip(self):
        CORRECT_IP = "192.168.68.246"
        output = os.popen('ifconfig').read()
        to_find = "inet %s" % CORRECT_IP
        return (to_find in output)

    def uptime_check_loop(self):
        SLEEP_WAIT = 60
        while True:
            is_printing = self.is_printing()
            hit_minimum_uptime = self.hit_minimum_uptime()
            is_online = self.is_online()
            is_correct_ip = self.is_correct_ip()
            
            self._logger.info("uptime check")
            self._logger.info("is printing? %s" % is_printing)
            self._logger.info("hit minimum uptime? %s" % hit_minimum_uptime)
            self._logger.info("is online? %s" % is_online)
            self._logger.info("is correct ip? %s" % is_correct_ip)
            
            if not is_printing:
                if hit_minimum_uptime:
                    if not (is_online and is_correct_ip):
                        self._logger.info("shutdown condition met, shutting down")
                        call("sudo shutdown -r now", shell=True)
           
            self._logger.info("sleeping for %s seconds" % SLEEP_WAIT)
            time.sleep(SLEEP_WAIT)


    def on_after_startup(self):
        self._logger.info("Gocto %s Alive Now!", self._plugin_version)
        self._logger.info(self._printer.get_state_id())
        self.startup_time = time.time()

        uptime_check_thread = threading.Thread(target=self.uptime_check_loop)
        uptime_check_thread.start()

    def get_settings_defaults(self): 
        return dict()
        
    def get_template_configs(self):
        return [dict(type = "settings", custom_bindings=False)]

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self._logger.info("Gocto settings changed")

    def on_shutdown(self):
        self._logger.info("Gocto going to bed now!")

    def get_update_information(self):
        return dict(
            OctoBuddy=dict(
                displayName=self._plugin_name,
                displayVersion=self._plugin_version,
                type="github_release",
                current=self._plugin_version,
                user="bluetshirt",
                repo="Gocto",

                pip="https://github.com/bluetshirt/Gocto/archive/{target_version}.zip"
            )
        )

__plugin_pythoncompat__ = ">=2.7"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = GoctoPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
