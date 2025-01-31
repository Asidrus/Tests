import asyncio
from contextlib import contextmanager
import allure
from allure_commons.types import AttachmentType
from libs.network import Client
from libs.webdriver import WebDriver


class Reporter:
    header = ''
    logger = None
    webdriver = None
    driver = None
    telegram = None
    debug = None
    screenshot = None

    def __init__(self, header: dict = {},
                 logger=None,
                 webdriver: WebDriver = None,
                 telegram: Client = None,
                 debug=0):
        self.header = ""
        for key in header.keys():
            self.header = self.header + str(key) + ": " + str(header[key]) + "\n"
            self.debug = debug
        self.logger = logger
        self.webdriver = webdriver
        if self.webdriver:
            self.driver = webdriver.driver
        self.telegram = telegram

    def __setProject__(self, text):
        if any([(p in text) for p in ["niidpo", "vgaps", "urgaps", "adpo", "dpomipk"]]):
            return "mult"
        elif "penta" in text:
            return "penta"
        elif "psy" in text:
            return "psy"
        elif "i-spo" in text:
            return "spo"
        else:
            return ""

    def takeScreenshot(self):
        if self.driver:
            self.screenshot = self.driver.get_screenshot_as_png()

    def gatherBrowserLogs(self):
        if self.logger and self.driver and self.webdriver.logs:
            self.logger.warning(
                {"url": self.driver.current_url,
                 "messages": self.driver.get_log('browser')})

    def sendToTelegram(self, stepName, error):
        try:
            msg = f'{self.header}Step: {stepName}\nError: {str(error)[:50]}'.replace("'", '').replace('"', '')
            data = {"contentType": 'json',
                    "content": {
                        "msg": msg,
                        "project": 'debug' if self.debug else self.__setProject__(msg)
                    }}
            if self.screenshot:
                data['image'] = self.screenshot
            asyncio.run(self.telegram.send(**data))
        except Exception as e:
            if self.logger:
                self.logger.critical(f"Не смог отправить сообщение в ТГ")
            raise e

    @contextmanager
    def allure_step(self, stepName: str,
                    screenshot: bool = False,
                    browserLog: bool = False,
                    alarm: bool = False,
                    ignore: bool = False):
        with allure.step(stepName):
            try:
                yield
            except Exception as e:
                if ignore is not True:
                    self.takeScreenshot()
                    if screenshot:
                        allure.attach(self.screenshot,
                                      name=stepName,
                                      attachment_type=AttachmentType.PNG)
                    if browserLog:
                        self.gatherBrowserLogs()
                    if alarm:
                        self.sendToTelegram(stepName, e)
                    if self.logger:
                        self.logger.critical(f"{self.header}|{stepName}|" + str(e))
                raise Exception(e)

    @contextmanager
    def step(self, stepName: str,
             alarm: bool = False,
             ignore: bool = False):
        with allure.step(stepName):
            try:
                yield
            except Exception as e:
                if ignore is not True:
                    if alarm:
                        self.sendToTelegram(stepName, e)
                    if self.logger:
                        self.logger.critical(f"{self.header}|{stepName}|" + str(e))
                raise Exception(e)
