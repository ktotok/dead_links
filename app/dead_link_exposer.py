import re

import asyncio

import time
from itertools import groupby

from aiohttp import ClientSession
from bs4 import BeautifulSoup
import json


class DeadLinkExposer:
    def __init__(self, target_url=None):
        self.target_url = target_url
        self.urls = set()
        self.ioloop = asyncio.get_event_loop()
        self.tasks = []
        self.tasks_size = 500
        self.responses = []

    def validate_urls(self):
        """
        Initiate URLs validation.
        Get urls list using self.get_urls()
        Populate asyncio tasks list with self.try_url coroutine
        """

        self.ioloop.run_until_complete(self.get_urls())

        for url in self.urls:
            self.tasks.append(asyncio.ensure_future(self.try_url(url)))

            if len(self.tasks) > self.tasks_size:
                self.ioloop.run_until_complete(asyncio.gather(*self.tasks))
                self.tasks = []

        if len(self.tasks) > 0:
            self.ioloop.run_until_complete(asyncio.gather(*self.tasks))

    async def try_url(self, url):
        """
        Coroutine send get request to specified URL and store response status to self.responses list
        :param url: target URL under test
        """
        async with ClientSession() as session:
            async with session.get(url) as response:
                await response.read()
                self.responses.append({"url": url, "status": response.status})

    async def get_urls(self):
        '''
        Parse target html page and retrieve urls. Store urls to self.urls list
        '''
        content = await self.get_html_content()
        soup = BeautifulSoup(content, "html.parser")
        for link in soup.find_all('a', attrs={'href': re.compile("^http://|https://")}):
            self.urls.add(link.get('href'))

    async def get_html_content(self):
        """
        Get content of the target html page under test
        :return: HTML as str
        """
        if not self.target_url:
            raise Exception('No page url specified for getting HTML content')

        async with ClientSession() as session:
            async with session.get(self.target_url) as response:
                return await response.text()

    def get_report(self):
        """
        Generate report about dead and alive URL based on self.responses list content
        :return: dict object
        """

        report_dict = {
            "url": self.target_url,
            "total": len(self.urls)
        }

        dead_link_count = 0
        sorted_resp = sorted(self.responses, key=lambda x: x.get('status'))
        for k, g in groupby(sorted_resp, lambda x: x.get('status')):
            urls_len = 0
            urls = []
            for i in g:
                urls.append(i.get("url"))
                urls_len += 1

            report_dict[str(k)] = {
                "size": urls_len,
                "urls": urls
            }

            if k != 200:
                dead_link_count += urls_len

        report_dict["dead"] = dead_link_count

        return report_dict

    def save_report(self, file_name):
        '''
        Store validation report as JSON str
        :param file_name: Name of the file where to dump generated report
        '''
        with open(file_name, 'w') as report_file:
            report = self.get_report()
            json_report = json.dumps(report)
            report_file.write(json_report)


# print("Started")
# dead_or_alive = DeadLinkExposer("https://dou.ua/")
# start_time = time.time()
#
#
# start_time = time.time()
# print("Performing link validation...")
# dead_or_alive.validate_urls()
# end_time = time.time()
#
# print(f"Finished. \r\nElapsed Time: {end_time - start_time}")
# print(f"Analysed {len(dead_or_alive.urls)} links")
# print(dead_or_alive.responses)
#
# print(dead_or_alive.get_report())
# dead_or_alive.ioloop.close()

