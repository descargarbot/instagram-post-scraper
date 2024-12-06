import requests
import json
import re
import sys

###################################################################

class InstagramPostScraper:
    
    def __init__(self):
        """ Initialize """

        self.headers = {
            'x-ig-app-id': '936619743392459',
            'x-asbd-id': '198387',
            'x-ig-www-claim': '0',
            'origin': 'https://www.instagram.com',
            'accept': '*/*',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
        }

        self.proxies = {
            'http': '',
            'https': '',
        }

        self.ig_post_regex = r'(https?://(?:www\.)?instagram\.com(?:/[^/]+)?/(?:p|tv|reel)/([^/?#&]+))'

        self.ig_session = requests.Session()

    
    def set_proxies(self, http_proxy: str, https_proxy: str) -> None:
        """ set proxy  """

        self.proxies['http'] = http_proxy 
        self.proxies['https'] = https_proxy


    def get_post_id_by_url(self, ig_post_url: str) -> str:
        """ get video id """

        if '/share/' in ig_post_url:
            try:
                ig_post_url = self.get_ig_url_from_share_url(ig_post_url)
                if ig_post_url == -1:
                    print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                    raise SystemExit('error getting ig url from share url')     
            except Exception as e:
                    print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                    raise SystemExit('error getting ig url from share url')     

        try:
            post_id = re.match(self.ig_post_regex, ig_post_url).group(2)
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting post id')

        return post_id

    def get_ig_url_from_share_url(self, ig_share_url: str) -> str:

        headers_share_url = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "es-419,es;q=0.5",
            "priority": "u=0, i",
            "sec-ch-ua": '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-full-version-list": '"Brave";v="131.0.0.0", "Chromium";v="131.0.0.0", "Not_A Brand";v="24.0.0.0"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": '""',
            "sec-ch-ua-platform": '"macOS"',
            "sec-ch-ua-platform-version": '"11.7.10"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "sec-gpc": "1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

        session = requests.Session()
        try:
            response = session.get(ig_share_url, headers=headers_share_url, allow_redirects=False)
            if response.status_code == 301:
                new_url = response.headers.get("Location")
                response = session.get(new_url, headers=headers_share_url, allow_redirects=False)
                if response.status_code in (301, 302):
                    return response.headers.get("Location")
                return new_url
            else:
                return -1
        except requests.RequestException as e:
            return -1

    
    def post_id_to_pk(self, post_id: str) -> str:
        """ covert a post_id to a numeric value from yt-dlp """

        return self.decode_base_n(post_id[:11], table='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')

    def _base_n_table(self, n: int, table: str) -> str:
        table = (table or '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')[:n]
        return table
    
    def decode_base_n(self, string: str, n: int = None, table: str = None) -> str:
        """ convert given base-n string to int """

        table = {char: index for index, char in enumerate(self._base_n_table(n, table))}
        result, base = 0, len(table)
        for char in string:
            result = result * base + table[char]
        return result


    def get_csrf_token(self, post_id: str) -> str:
        """ get csrf token on session cookies """

        ig_csrf_endpoint = f'https://i.instagram.com/api/v1/web/get_ruling_for_content/?content_type=MEDIA&target_id={self.post_id_to_pk(post_id)}'
        try:
            self.ig_session.get(ig_csrf_endpoint, headers=self.headers, proxies=self.proxies)
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting csrf token')

        return self.ig_session.cookies.get('csrftoken') if self.ig_session.cookies.get('csrftoken') else None


    def get_ig_post_urls(self, csrf_token: str, post_id: str) -> tuple:
        """ get ig post urls from the api """

        headers_post_details = self.headers.copy()
        headers_post_details['x-csrftoken'] = csrf_token
        headers_post_details['x-requested-with'] = 'XMLHttpRequest'
        headers_post_details['referer'] = f'https://www.instagram.com/p/{post_id}/'

        variables_post_details = {
            'shortcode': post_id,
            'child_comment_count': 3,
            'fetch_comment_count': 40,
            'parent_comment_count': 24,
            'has_threaded_comments': True,
        }

        try:
            ig_url_json = self.ig_session.get('https://www.instagram.com/graphql/query/', 
                                        headers=headers_post_details,
                                        proxies=self.proxies,
                                        params={'doc_id': '8845758582119845',
                                                'variables': json.dumps(variables_post_details, separators=(',', ':')),},
                                        ).json()
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting post details')

        #print(ig_url_json)
        #exit()
        # get urls from json respond
        post_urls = []
        thumbnail_urls = []
        try:
            # single video
            if ig_url_json['data']['xdt_shortcode_media']['__typename'] == 'XDTGraphVideo':
                post_urls.append(ig_url_json['data']['xdt_shortcode_media']['video_url'])
                thumbnail_urls.append(ig_url_json['data']['xdt_shortcode_media']['thumbnail_src'])
            
            # single image
            elif ig_url_json['data']['xdt_shortcode_media']['__typename'] == 'XDTGraphImage':
                img_url = None
                for image in ig_url_json['data']['xdt_shortcode_media']['display_resources']:
                    img_url = image['src'] # last one in general is the best quality
                post_urls.append(img_url)
                thumbnail_urls.append(ig_url_json['data']['xdt_shortcode_media']['display_resources'][0]['src']) # in this case use the most tiny display_resources

            # Sidecar (multiple images/videos)
            elif ig_url_json['data']['xdt_shortcode_media']['__typename'] == 'XDTGraphSidecar':
                for node in ig_url_json['data']['xdt_shortcode_media']['edge_sidecar_to_children']['edges']:
                    # node with video
                    if node['node']['__typename'] == 'XDTGraphVideo':
                        post_urls.append(node['node']['video_url'])
                        thumbnail_urls.append(node['node']['display_resources'][0]['src'])
                    # node with image
                    elif node['node']['__typename'] == 'XDTGraphImage':
                        img_url = None
                        for image in node['node']['display_resources']:
                            img_url = image['src'] # last one in general is the best quality
                        post_urls.append(img_url)
                        thumbnail_urls.append(node['node']['display_resources'][0]['src'])

        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno)) # probably 'Please wait a few minutes before you try again.'
            raise SystemExit('error getting post urls. try with a proxy')

        return post_urls, thumbnail_urls

    def download(self, post_details: list, post_id: str) -> list:
        """ download items """

        headers_download = self.headers.copy()
        headers_download['referer'] = f'https://www.instagram.com/p/{post_id}/'

        downloaded_item_list = []
        for post_url in post_details:
            try:
                video_request = self.ig_session.get(post_url, headers=headers_download, proxies=self.proxies, stream=True)
            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error downloading video')

            filename = post_url.split('?')[0].split('/')[-1]
            path_filename = f'{filename}'

            try:
                with open(path_filename, 'wb') as f:
                    for chunk in video_request.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()

                downloaded_item_list.append(path_filename)
            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error writting video')

        return downloaded_item_list


    def get_video_filesize(self, video_url_list: list) -> list:
        """ get file size of requested video """

        items_filesize = []
        for video_url in video_url_list:
            try:
                video_size = self.ig_session.head(video_url, headers={"Content-Type":"text"}, proxies=self.proxies)
                items_filesize.append(video_size.headers['content-length'])
            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error getting file size')

        return items_filesize

###################################################################

if __name__ == "__main__":

    # use case example

    # set ig post url (this only works with post, reels, igtv)
    # for stories and highlights see InstagramStoryScraper class
    ig_post_url = ''
    if ig_post_url == '':
        if len(sys.argv) < 2:
            print('you must provide a instagram url')
            exit()
        ig_post_url = sys.argv[1]
        
    # create scraper post object    
    ig_post = InstagramPostScraper()

    # set the proxy (optional, u can run it with ur own ip)
    #ig_post.set_proxies('<your http proxy>', '<your https proxy')

    # get video id from url    
    post_id = ig_post.get_post_id_by_url(ig_post_url)

    # get csrf token
    csrf_token = ig_post.get_csrf_token(post_id)

    # get post urls from video id
    ig_post_urls, thumbnail_urls = ig_post.get_ig_post_urls(csrf_token, post_id)

    # get item filesize
    items_filesize = ig_post.get_video_filesize(ig_post_urls)
    [print('filesize: ~' + filesize + ' bytes') for filesize in items_filesize]

    # download post items
    ig_post.download(ig_post_urls, post_id)

    ig_post.ig_session.close()
