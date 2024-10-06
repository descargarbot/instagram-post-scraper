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

        try:
            post_id = re.match(self.ig_post_regex, ig_post_url).group(2)
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting post id')

        return post_id
    

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
                                        params={'query_hash': '9f8827793ef34641b2fb195d4d41151c',
                                                'variables': json.dumps(variables_post_details, separators=(',', ':')),},
                                        ).json()
        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting post details')

        # get urls from json respond
        post_urls = []
        thumbnail_urls = []
        try:
            # single video
            if ig_url_json['data']['shortcode_media']['__typename'] == 'GraphVideo':
                post_urls.append(ig_url_json['data']['shortcode_media']['video_url'])
                thumbnail_urls.append(ig_url_json['data']['shortcode_media']['thumbnail_src'])
            
            # single image
            elif ig_url_json['data']['shortcode_media']['__typename'] == 'GraphImage':
                img_url = None
                for image in ig_url_json['data']['shortcode_media']['display_resources']:
                    img_url = image['src'] # last one in general is the best quality
                post_urls.append(img_url)
                thumbnail_urls.append(ig_url_json['data']['shortcode_media']['display_resources'][0]['src']) # in this case use the most tiny display_resources

            # Sidecar (multiple images/videos)
            elif ig_url_json['data']['shortcode_media']['__typename'] == 'GraphSidecar':
                for node in ig_url_json['data']['shortcode_media']['edge_sidecar_to_children']['edges']:
                    # node with video
                    if node['node']['__typename'] == 'GraphVideo':
                        post_urls.append(node['node']['video_url'])
                        thumbnail_urls.append(node['node']['display_resources'][0]['src'])
                    # node with image
                    elif node['node']['__typename'] == 'GraphImage':
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
