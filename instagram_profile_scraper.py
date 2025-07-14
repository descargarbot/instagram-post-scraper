import requests
import json
import re
import sys
import pickle
import os.path
import os
import time
import shutil
from datetime import datetime

###################################################################
""" scrap and download all post from a profile"""
class InstagramProfileScraper:
    
    def __init__(self, cookies_path: str = None):
        """Initialize"""
        self.cookies_path = cookies_path

        self.proxies = {
            'http': '',
            'https': '',
        }

        self.ig_session = requests.Session()

        self.profile_data = []

        self.target_username = None
    
    def set_proxies(self, http_proxy: str, https_proxy: str) -> None:
        """ set proxy  """

        self.proxies['http'] = http_proxy 
        self.proxies['https'] = https_proxy

    def ig_cookies_exist(self) -> bool:
        """ check if cookies exist and load it"""

        if os.path.isfile(self.cookies_path):
            with open(self.cookies_path, 'rb') as f:
                self.ig_session.cookies.update(pickle.load(f))
            return True

        return False

    def parse_json_data(self, json_response) -> None:

        for node in json_response['data']['xdt_api__v1__feed__user_timeline_graphql_connection']['edges']:
            shortcode = node['node']['code']
            url = f"https://www.instagram.com/p/{shortcode}/"

            media_list = []

            if node['node']['product_type'] == 'carousel_container':
                _type = 'carousel'
                for media in node['node']['carousel_media']:
                    if media['video_versions'] == None:
                        __type = 'image'
                        thumb_url = None
                        _url = media['image_versions2']['candidates'][0]['url']
                        media_list.append({'url': _url, 'type' : __type, 'thumb': thumb_url})  
                    else:
                        __type = 'video'
                        thumb_url = media['image_versions2']['candidates'][0]['url']
                        _url = media['video_versions'][0]['url']
                        media_list.append({'url': _url, 'type' : __type, 'thumb': thumb_url}) 
                  
                created_at = ''
                try:
                    created_at = node['node']['taken_at']
                except:
                    created_at = 'created_at_error'

                self.profile_data.append({ 'url': url, 'type' : _type, 'created_at': created_at, 'nodes' : media_list })


            if node['node']['product_type'] == 'clips':
                _type = 'video'

                thumb_url = node['node']['image_versions2']['candidates'][0]['url']
                __type = 'video'
                _url = node['node']['video_versions'][0]['url']
                media_list.append({'url': _url, 'type' : __type, 'thumb': thumb_url})

                created_at = ''
                try:
                    created_at = node['node']['taken_at']
                except:
                    created_at = 'created_at_error'
                
                self.profile_data.append({ 'url': url, 'type' : _type, 'created_at': created_at, 'nodes' : media_list })

            
            if node['node']['product_type'] == 'feed':
                _type = 'image'

                thumb_url = None
                __type = 'image'
                _url = node['node']['image_versions2']['candidates'][0]['url']

                media_list.append({'url': _url, 'type' : __type, 'thumb': thumb_url})

                created_at = ''
                try:
                    created_at = node['node']['taken_at']
                except:
                    created_at = 'created_at_error'

                self.profile_data.append({ 'url': url, 'type' : _type, 'created_at': created_at, 'nodes' : media_list })        

    def print_data(self) -> None:

        for node in self.profile_data:
            print(node)
            print("\n")
        
        print(f"count:{ len(self.profile_data) }")
        print("\n")
        print("\n")

    def get_ig_post_urls(self) -> None:

        # 3 - 30
        count = 12

        if self.cookies_path:
            self.ig_cookies_exist()

        variables_dict = {
            "data": {
                "count": count,
                "include_reel_media_seen_timestamp": True,
                "include_relationship_info": True,
                "latest_besties_reel_media": True,
                "latest_reel_media": True
            },
            "username": self.target_username,
            "__relay_internal__pv__PolarisIsLoggedInrelayprovider": True,
            "__relay_internal__pv__PolarisShareSheetV3relayprovider": True
        }
        
        headers = {
            'accept': '*/*',
            'accept-encoding': 'identity',
            'accept-language': 'es-419,es;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'priority': 'u=1, i',
            'referer': f'https://www.instagram.com/{self.target_username}/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Brave";v="138"',
            'sec-ch-ua-full-version-list': '"Not)A;Brand";v="8.0.0.0", "Chromium";v="138.0.0.0", "Brave";v="138.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"macOS"',
            'sec-ch-ua-platform-version': '"11.7.10"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'x-asbd-id': '359341',
            'x-bloks-version-id': 'e1456a3f58800541d8a2ea65b55937920007fee744eed6e5b1a7723cbe417e5f',
            'x-csrftoken': self.ig_session.cookies.get('csrftoken'),
            'x-fb-friendly-name': 'PolarisProfilePostsQuery',
            'x-fb-lsd': 'skXbEUjzp14eJacGva6pnd',
            'x-ig-app-id': '936619743392459',
            'x-root-field-name': 'xdt_api__v1__feed__user_timeline_graphql_connection'
        }
        
        data = {
            'av': '17841455715731478',
            '__d': 'www',
            '__user': '0',
            '__a': '1',
            '__req': '8',
            '__hs': '20278.HYP:instagram_web_pkg.2.1...0',
            'dpr': '2',
            '__ccg': 'GOOD',
            '__rev': '1024569036',
            '__s': 'v27h7s:0vno6c:gih3pm',
            '__hsi': '7525191207253845999',
            '__dyn': '7xe5WwlEnwn8K2Wmm1twpUnwgU7S6EdF8aUco38wbS0E8hw2nVE4W0qa0FE2awgo9o1vohwGwQwoEcE7O2l0Fw4Hw9O0Lbwae4UaEW2G0AEco5G0zEnwhEe81-obUGdwtUdUaob82ZwrUdUbGwmk0KU6O1FwlA1HQp1yU42UnAwHxW1oxe6UaU3cyUrw4rxO2C3a',
            '__csr': 'gi86QoJJth3v5hbEYyWVnmHLi9qii8GhGKplp99Xytx2bqJ2XQAqhGGWHy9puqA9KHGrr8q_SejJ9pF-bmFkt5hHJoB4nzQaKELVovCwDUgy9Qqm8zUNoOimGADWxj8u8gXyEmByXGFQ8wJhrgggKq5VEiG8Kq4pV8ty6FA5TJ005j3qxa19AK0qJ3UVwdGp02ro2lgG3e5sUow6Wwk_gS2e0OEK07YUCbCg0gcKzmm484kvU31CmaCxO0zFA4Q361Ccbg6C0Gu2_j9wuGw9uywhA0JP4xe0bAyE4uEigaE0law6PgF00rso0_G0iy0j-02vi',
            '__hsdp': 'l0Sj8x3_EetMVGSX38LAm4ENT4At_0Ep_j4yHx3AbGuFyzpEASnIMwUaUcS6Ei51u8wp8qo5eE988q8URzp8jQQt0ADGqUrzUfQbe19AwuEdE5qdgK7e4Egxu2u0zA0mG3m0iq08zw48xO1XwIxe18wVBzoS3W5U8o2KwkE5e3S1uxu7EG6o30xm6EbU9Eja3-2G1AxO2G16wBjxeq8OyqzElwgovByU9BzE4a12xy6Ufe',
            '__hblp': '0lEeU5C225o2ZBxyi0YofEaUqwl-48lwCAxy2h6xa4VWVbjzFUV7w8mi9x-EO1fDx-ewIy8pJoR2UsUiUW3-1lwUg2Ew8qi4E8Ehwzway3u5Ubo3jw4swOw48AigiwIwjEb8Ku18wVBzoS3W5U8o2KwkE5e3S1uxu7EG6o30xm6EbU9Eja3-2G1AxO2G16wBjxeq8OyqzElwgovByU9BzE4a12xy6Ufe',
            '__sjsp': 'l6RNIWj5Esz5Bh4449qCriGKILuVAeVCVDlR8EPAG2ngOfwn9ogxagF9WCx60O5c0xo3ig',
            '__comet_req': '7',
            'fb_dtsg': 'NAftaMgPWIEwISHGLUVH4SL2q6GSS1NfOHM1PYZljczZepN99td5R7w:17853667720085245:1752087333',
            'jazoest': '26096',
            'lsd': 'LBZiaFuRrxxrAhq5_OKPI1',
            '__spin_r': '1024569036',
            '__spin_b': 'trunk',
            '__spin_t': '1752095112',
            '__crn': 'comet.igweb.PolarisProfilePostsTabRoute',
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'PolarisProfilePostsQuery',
            'variables': json.dumps(variables_dict, separators=(',', ':')),
            'server_timestamps': 'true',
            'doc_id': '30160528230260194'
        }
        
        url = 'https://www.instagram.com/graphql/query'
        response = self.ig_session.post(url, headers=headers, data=data)

        cursor = None
        has_next_page = False
        
        if response.status_code == 200:
            try:
                json_response = response.json()

                self.parse_json_data(json_response)

                cursor = json_response['data']['xdt_api__v1__feed__user_timeline_graphql_connection']['page_info']['end_cursor']
                has_next_page = json_response['data']['xdt_api__v1__feed__user_timeline_graphql_connection']['page_info']['has_next_page']

            except:
                raise SystemExit('error getting json data')
        else:
            print(f"Error: {response.status_code}")
            raise SystemExit('error getting response')
        
        if has_next_page != True:
            return
            
        variables_dict = {
            "after": cursor,
            "before": None,
            "data": {
                "count": count,
                "include_reel_media_seen_timestamp": True,
                "include_relationship_info": True,
                "latest_besties_reel_media": True,
                "latest_reel_media": True
            },
            "first": count,
            "last": None,
            "username": self.target_username,
            "__relay_internal__pv__PolarisIsLoggedInrelayprovider": True,
            "__relay_internal__pv__PolarisShareSheetV3relayprovider": True
        }

        data['variables'] = json.dumps(variables_dict, separators=(',', ':'))
        data['doc_id'] = '10064872980277354'
        
        while has_next_page == True:
            time.sleep(1)
            response = self.ig_session.post(url, headers=headers, data=data)
            if response.status_code == 200:
                try:
                    json_response = response.json()

                    self.parse_json_data(json_response)

                    cursor = json_response['data']['xdt_api__v1__feed__user_timeline_graphql_connection']['page_info']['end_cursor']
                    has_next_page = json_response['data']['xdt_api__v1__feed__user_timeline_graphql_connection']['page_info']['has_next_page']

                    variables_dict['after'] = cursor
                    data['variables'] = json.dumps(variables_dict, separators=(',', ':'))

                except:
                    raise SystemExit('error getting json data')
            else:
                print(f"Error: {response.status_code}")
                raise SystemExit('error getting response')

    
    def download(self) -> None:

        if os.path.exists(self.target_username):
            shutil.rmtree(self.target_username)
        os.makedirs(self.target_username)


        for node in self.profile_data:
            subdir_name = node['url'].split('/')[-2]
            
            if node['created_at'] != 'created_at_error':
                created_at = datetime.fromtimestamp(int(node['created_at']))
                created_at = created_at.strftime("%Y-%m-%d_%H-%M-%S")
                subdir_name = str(created_at) + ' - ' + subdir_name 
            else:
                created_at = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                subdir_name = str(created_at) + ' - ' + subdir_name   

            subdir_name = f"{self.target_username}/{subdir_name}"
            os.makedirs(subdir_name)
    
            print(subdir_name)


            headers = {
                        'x-ig-app-id': '936619743392459',
                        'x-asbd-id': '359341',
                        'x-ig-www-claim': '0',
                        'origin': 'https://www.instagram.com',
                        'referer': f'https://www.instagram.com/{self.target_username}/',
                        'accept': '*/*',
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                    }

            for media in node['nodes']:
                
                try:
                    if media['thumb'] != None:
                        thumb = requests.get(media['thumb'], headers=headers, proxies=self.proxies, stream=True)
                    video = requests.get(media['url'], headers=headers, proxies=self.proxies, stream=True)
                    
                except Exception as e:
                    raise SystemExit('error downloading')
                
                if media['thumb'] != None:
                    filename = 'thumb_' + media['url'].split('/')[-1].split('?')[0]
                    path_filename =  subdir_name + '/' + filename
                    
                    try:
                        with open(path_filename, 'wb') as f:
                            for chunk in thumb.iter_content(chunk_size=1024):
                                if chunk:
                                    f.write(chunk)
                                    f.flush()
                    except Exception as e:
                        raise SystemExit('error writting video')

                filename = media['url'].split('/')[-1].split('?')[0]
                path_filename =  subdir_name + '/' + filename
                
                try:
                    with open(path_filename, 'wb') as f:
                        for chunk in video.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                                f.flush()
                except Exception as e:
                    raise SystemExit('error writting video')
                


###################################################################

if __name__ == "__main__":

    # use case example

    # create scraper object with cookies

    # !cookies must be in pickle format!
    cookie_path = ''
    ig_profile_data = InstagramProfileScraper(cookie_path)

    # set the proxy (optional, u can run it with ur own ip)
    #ig_profile_data.set_proxies('<your http proxy>', '<your https proxy')

    # set profile username
    username = ''
    ig_profile_data.target_username = username

    # get user post list
    ig_profile_data.get_ig_post_urls()

    # print user post list
    ig_profile_data.print_data()

    # download user post list
    ig_profile_data.download()

    ig_profile_data.ig_session.close()
