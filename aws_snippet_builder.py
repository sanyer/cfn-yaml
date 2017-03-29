# Copyright {2016} {Narrowbeam Limited}

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from bs4 import BeautifulSoup
import requests
import re
import os
import logging

import aiohttp
import asyncio

import asyncio
import uvloop
from aiohttp import ClientSession

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()

async def async_request(url):
    async with ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info('Getting AWS Resource Types Reference page')
docurl = "http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/"
# requests
# page = requests.get(docurl + "aws-template-resource-type-ref.html")
# aiohttp
page = loop.run_until_complete(async_request(docurl + "aws-template-resource-type-ref.html"))


logger.info('Parsing AWS Resource Types Reference page')
soup = BeautifulSoup(page, 'html.parser')
urllist = [(url.text, docurl + url['href']) for url in soup.select('div.highlights > ul li a[href*="aws-"]')]

async def fetch(url, session):
    async with session.get(url) as response:
        return await response.read()
async def run(url_list):
    # Fetch all responses within one Client session,
    # keep connection alive for all requests.
    async with ClientSession() as session:
        tasks = [asyncio.ensure_future(fetch(url, session)) for url in url_list]
        responses = await asyncio.gather(*tasks)
        # you now have all response bodies in this variable
        print(responses)
loop = asyncio.get_event_loop()
future = asyncio.ensure_future(run(urllist))
loop.run_until_complete(future)

# tasks = [asyncio.ensure_future(async_request(url)) for url in urllist]
# responses = await asyncio.gather(*tasks)
# loop.run_until_complete(asyncio.wait(tasks))
# print(responses)
exit()

SNIPPETS = {}
for (pagename, pageurl) in urllist:
    logger.info('Parsing %s', pagename)

    # requests
    page = requests.get(pageurl).content
    aws_yaml = BeautifulSoup(page, 'html.parser').select_one('#YAML code').text.strip()
    # aiohttp
    tasks = [asyncio.ensure_future(async_request(url)) for url in urllist]
    loop.run_until_complete(asyncio.wait(tasks))

    snippet = dict(
        prefix=pagename.replace('::', '-').lower(),
        body="#AWS-DOC %s\n%s" % (pageurl, aws_yaml),
        description=pagename,
        scope='source.cloudformation'
    )
    SNIPPETS[snippet['prefix']] = snippet

snippets_file_name = 'snippets.json'
logger.info('Writing file %s', snippets_file_name)
with open(snippets_file_name, 'w') as snippets_file:
    snippets_file.write(SNIPPETS)
