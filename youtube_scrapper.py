import asyncio
import re

import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By

message = """
Please enter your search key word here
(you can enter 'q' for exit)

: """

search_input = input(message)
if search_input.lower() == 'q':
    exit()

search_input = search_input.replace(' ', '+')
url = f'https://www.youtube.com/results?search_query={search_input}'

browser = webdriver.Firefox()
browser.implicitly_wait(10)
browser.get(url)

retrieve_number = 120  # number of channels to extract data from youtube
search_items = {}

while True:
    items = browser.find_elements(By.CSS_SELECTOR, '#contents ytd-video-renderer.style-scope.ytd-item-section-renderer')
    if len(items) > retrieve_number:
        for item in items:
            a = item.find_element(By.ID, 'text-container').find_element(By.TAG_NAME, 'a')
            search_items.update({
                a.get_attribute('href'): a.get_attribute('innerHTML')
            })
        break
    browser.execute_script("window.scrollBy(0, 15000)")

browser.close()

result = list()
counter = 0


async def get_pages(session, key, value):
    global counter
    local_counter = counter
    counter += 1
    print('getting link: ', counter)

    async with session.get(key) as page:
        text = await page.read()
        sub_pattern = r'\d+\.?\d*.'
        pattern = f'"simpleText":"{sub_pattern} subscribers"'
        match = re.findall(pattern, text.decode('utf-8'))
        if match:
            subscribers = re.search(sub_pattern, match[-1]).group()
            result.append({
                'name': value,
                'link': key,
                'subscribers': subscribers
            })
    print('finished link: ', local_counter + 1)


async def async_requests(loop):
    tasks = list()
    async with aiohttp.ClientSession(loop=loop) as session:
        for key, value in search_items.items():
            tasks.append(get_pages(session, key, value))
        grouped_tasks = asyncio.gather(*tasks)
        return await grouped_tasks


loop = asyncio.get_event_loop()
loop.run_until_complete(async_requests(loop))

with open('output.csv', 'w', encoding='utf-8') as file:
    file.write('Name,Link,Subscribers count\n')
    for channel in result:
        string = f'{channel["name"]},{channel["link"]},{channel["subscribers"]}\n'
        file.write(string)
