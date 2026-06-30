import json
import re
import sys
import os.path
import html as html_lib

from urllib.parse import urlencode
from curl_cffi import requests


###################################################################

class InstagramPostScraper:

    def __init__(self, cookies_path: str = None):
        """Initialize"""

        self.cookies_path = cookies_path

        self.IG_BASE_URL = 'https://www.instagram.com'
        self.IG_API_BASE_URL = 'https://i.instagram.com/api/v1'
        self.IG_GRAPHQL_URL = 'https://www.instagram.com/api/graphql'

        self.IG_APP_ID = '936619743392459'
        self.IG_DOC_ID = '27130156389949648'
        self.IG_FRIENDLY_NAME = 'PolarisLoggedOutDesktopWWWPostRootContentQuery'

        self.impersonate = 'chrome120'

        self.encoding_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'

        self.headers = {
            'x-ig-app-id': self.IG_APP_ID,
            'x-asbd-id': '359341',
            'x-ig-www-claim': '0',
            'origin': 'https://www.instagram.com',
            'accept': '*/*',
        }

        self.proxies = {
            'http': '',
            'https': '',
        }

        self.ig_post_regex = (
            r'(https?://(?:www\.)?instagram\.com'
            r'(?:/(?!share/)[^/?#]+)?'
            r'/(?P<post_type>p|tv|reels?)(?!/audio/)'
            r'/(?P<post_id>[^/?#&]+))'
        )

        self.ig_session = requests.Session()

        self.lsd_token = None
        self.api_check = None
        self.post_type = 'p'

        if self.cookies_path:
            self.ig_cookies_exist()

    ###################################################################

    def _get_proxies(self):
        """Return proxies only if configured"""

        proxies = {k: v for k, v in self.proxies.items() if v}
        return proxies or None

    ###################################################################

    def set_proxies(self, http_proxy: str, https_proxy: str) -> None:
        """set proxy"""

        self.proxies['http'] = http_proxy
        self.proxies['https'] = https_proxy

    ###################################################################

    def ig_cookies_exist(self) -> bool:
        """
        Load cookies from Netscape cookies.txt format.

        Example line:
        .instagram.com    TRUE    /    TRUE    1893456000    sessionid    xxxxx
        """

        if not self.cookies_path or not os.path.isfile(self.cookies_path):
            return False

        loaded_cookies = 0

        try:
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()

                    if not line:
                        continue

                    # Netscape comments
                    if line.startswith('#') and not line.startswith('#HttpOnly_'):
                        continue

                    # HttpOnly cookies are written like:
                    # #HttpOnly_.instagram.com TRUE / TRUE ...
                    if line.startswith('#HttpOnly_'):
                        line = line[len('#HttpOnly_'):]

                    parts = line.split('\t')

                    # fallback por si el archivo usa espacios
                    if len(parts) < 7:
                        parts = line.split()

                    if len(parts) < 7:
                        continue

                    domain = parts[0]
                    path = parts[2]
                    name = parts[5]
                    value = parts[6]

                    if not domain or not name:
                        continue

                    self.ig_session.cookies.set(
                        name,
                        value,
                        domain=domain,
                        path=path or '/',
                    )

                    loaded_cookies += 1

            return loaded_cookies > 0

        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error loading cookies file')

    ###################################################################

    def get_post_id_by_url(self, ig_post_url: str) -> str:
        """get post shortcode"""

        ig_post_url = ig_post_url.strip()

        if '/share/' in ig_post_url:
            try:
                ig_post_url = self.get_ig_url_from_share_url(ig_post_url)

                if ig_post_url == -1:
                    raise SystemExit('error getting ig url from share url')

            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error getting ig url from share url')

        try:
            match = re.match(self.ig_post_regex, ig_post_url)

            if not match:
                raise SystemExit('invalid instagram post url')

            self.post_type = match.group('post_type')
            post_id = match.group('post_id')

        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting post id')

        return post_id

    ###################################################################

    def get_ig_url_from_share_url(self, ig_share_url: str) -> str:
        """resolve instagram /share/ URL"""

        headers_share_url = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'upgrade-insecure-requests': '1',
        }

        session = requests.Session()

        try:
            response = session.get(
                ig_share_url,
                headers=headers_share_url,
                allow_redirects=True,
                impersonate=self.impersonate,
                proxies=self._get_proxies(),
            )

            final_url = response.url

            if final_url and re.match(self.ig_post_regex, final_url):
                return final_url

            location = response.headers.get('Location')

            if location and re.match(self.ig_post_regex, location):
                return location

            return -1

        except Exception:
            return -1

    ###################################################################

    def post_id_to_pk(self, post_id: str) -> str:
        """convert a shortcode to numeric media id, based on yt-dlp"""

        shortcode = post_id

        if len(shortcode) > 28:
            shortcode = shortcode[:-28]

        return str(self.decode_base_n(shortcode, table=self.encoding_chars))

    ###################################################################

    def _base_n_table(self, n: int = None, table: str = None) -> str:
        table = table or '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

        if n:
            table = table[:n]

        return table

    ###################################################################

    def decode_base_n(self, string: str, n: int = None, table: str = None) -> int:
        """convert given base-n string to int"""

        table = {char: index for index, char in enumerate(self._base_n_table(n, table))}
        result, base = 0, len(table)

        for char in string:
            result = result * base + table[char]

        return result

    ###################################################################

    def _extract_lsd_token_from_html(self, html: str) -> str:
        """extract LSD token from Instagram bootstrap HTML"""

        match = re.search(
            r'<script\b(?=[^>]*\bid=["\']__eqmc["\'])[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )

        if match:
            try:
                raw_json = html_lib.unescape(match.group(1))
                eqmc = json.loads(raw_json)

                if eqmc.get('l'):
                    return eqmc.get('l')

            except Exception:
                pass

        match = re.search(r'\["LSD",\[\],\{"token":"([^"]+)"', html)

        if match:
            return match.group(1)

        return None

    ###################################################################

    def get_lsd_token(self) -> str:
        """bootstrap Instagram session and get LSD token"""

        headers_bootstrap = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'upgrade-insecure-requests': '1',
        }

        try:
            response = self.ig_session.get(
                f'{self.IG_BASE_URL}/',
                headers=headers_bootstrap,
                impersonate=self.impersonate,
                proxies=self._get_proxies(),
            )

            self.lsd_token = self._extract_lsd_token_from_html(response.text)

            if not self.lsd_token:
                raise SystemExit('LSD token not found')

            return self.lsd_token

        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting lsd token')

    ###################################################################

    def get_csrf_token(self, post_id: str) -> str:
        """get csrf token on session cookies using new get_ruling_for_content flow"""

        if not self.lsd_token:
            self.get_lsd_token()

        media_id = self.post_id_to_pk(post_id)

        try:
            response = self.ig_session.get(
                f'{self.IG_API_BASE_URL}/web/get_ruling_for_content/',
                headers=self.headers,
                params={
                    'content_type': 'MEDIA',
                    'target_id': media_id,
                },
                impersonate=self.impersonate,
                proxies=self._get_proxies(),
            )

            self.api_check = response.json()

        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting csrf token')

        csrf_token = self.ig_session.cookies.get('csrftoken')

        if not self.api_check or self.api_check.get('status') != 'ok':
            return None

        return csrf_token if csrf_token else None

    ###################################################################

    def _get_product_info_from_graphql(self, ig_url_json: dict) -> dict:
        """extract product info from new GraphQL response"""

        media = (
            ig_url_json
            .get('data', {})
            .get('xig_polaris_media')
        )

        if not isinstance(media, dict):
            return None

        product_info = media.get('if_not_gated_logged_out')

        if isinstance(product_info, dict):
            return product_info

        return None

    ###################################################################

    def _get_logged_in_product_info(self, post_id: str) -> dict:
        """
        Optional fallback if cookies contain sessionid.
        """

        if not self.ig_session.cookies.get('sessionid'):
            return None

        media_id = self.post_id_to_pk(post_id)

        try:
            response = self.ig_session.get(
                f'{self.IG_API_BASE_URL}/media/{media_id}/info/',
                headers=self.headers,
                impersonate=self.impersonate,
                proxies=self._get_proxies(),
            )

            data = response.json()
            items = data.get('items') or []

            if items:
                return items[0]

        except Exception:
            return None

        return None

    ###################################################################

    def _int_or_none(self, value):
        """safe int conversion"""

        try:
            if value is None:
                return None
            return int(value)
        except Exception:
            return None

    ###################################################################

    def _get_version_area(self, item: dict):
        """
        Get area from both new and old Instagram fields.

        New API:
            width, height

        Old GraphQL:
            config_width, config_height
        """

        width = (
            self._int_or_none(item.get('width'))
            or self._int_or_none(item.get('config_width'))
        )

        height = (
            self._int_or_none(item.get('height'))
            or self._int_or_none(item.get('config_height'))
        )

        if width and height:
            return width * height

        return None

    ###################################################################

    def _normalize_versions(self, versions: list, url_key: str = 'url') -> list:
        """normalize image/video version list"""

        if not isinstance(versions, list):
            return []

        normalized = []

        for index, item in enumerate(versions):
            if not isinstance(item, dict):
                continue

            url = item.get(url_key) or item.get('url') or item.get('src')

            if not url:
                continue

            normalized.append({
                'index': index,
                'url': url,
                'area': self._get_version_area(item),
            })

        return normalized

    ###################################################################

    def _get_best_url_from_versions(
        self,
        versions: list,
        url_key: str = 'url',
        default_order: str = 'desc',
    ) -> str:
        """
        Get highest quality URL.

        default_order:
            desc -> first item is assumed largest if dimensions are missing
            asc  -> last item is assumed largest if dimensions are missing
        """

        normalized = self._normalize_versions(versions, url_key=url_key)

        if not normalized:
            return None

        items_with_area = [item for item in normalized if item['area'] is not None]

        if items_with_area:
            return max(items_with_area, key=lambda item: item['area'])['url']

        if default_order == 'asc':
            return normalized[-1]['url']

        return normalized[0]['url']

    ###################################################################

    def _get_smallest_url_from_versions(
        self,
        versions: list,
        url_key: str = 'url',
        default_order: str = 'desc',
    ) -> str:
        """
        Get smallest quality URL, useful as thumbnail.

        default_order:
            desc -> last item is assumed smallest if dimensions are missing
            asc  -> first item is assumed smallest if dimensions are missing
        """

        normalized = self._normalize_versions(versions, url_key=url_key)

        if not normalized:
            return None

        items_with_area = [item for item in normalized if item['area'] is not None]

        if items_with_area:
            return min(items_with_area, key=lambda item: item['area'])['url']

        if default_order == 'asc':
            return normalized[0]['url']

        return normalized[-1]['url']

    ###################################################################

    def _extract_single_media_urls(self, media: dict) -> tuple:
        """extract one media URL and one thumbnail URL from product media"""

        if not isinstance(media, dict):
            return None, None

        post_url = None
        thumbnail_url = None

        # Videos / reels
        video_versions = media.get('video_versions') or []

        if video_versions:
            post_url = self._get_best_url_from_versions(
                video_versions,
                url_key='url',
                default_order='desc',
            )

        # New API image candidates.
        # Usually ordered largest -> smallest, but dimensions are preferred.
        image_candidates = (
            media
            .get('image_versions2', {})
            .get('candidates', [])
        )

        if image_candidates:
            image_best_url = self._get_best_url_from_versions(
                image_candidates,
                url_key='url',
                default_order='desc',
            )

            image_thumb_url = self._get_smallest_url_from_versions(
                image_candidates,
                url_key='url',
                default_order='desc',
            )

            if not post_url:
                post_url = image_best_url

            thumbnail_url = image_thumb_url

        # Old GraphQL fallback video
        if not post_url and media.get('video_url'):
            post_url = media.get('video_url')

        # Old GraphQL fallback image.
        # display_resources is usually ordered smallest -> largest.
        display_resources = media.get('display_resources') or []

        if display_resources:
            display_best_url = self._get_best_url_from_versions(
                display_resources,
                url_key='src',
                default_order='asc',
            )

            display_thumb_url = self._get_smallest_url_from_versions(
                display_resources,
                url_key='src',
                default_order='asc',
            )

            if not post_url:
                post_url = display_best_url

            if not thumbnail_url:
                thumbnail_url = display_thumb_url

        # Extra old fields
        if not thumbnail_url:
            thumbnail_url = media.get('thumbnail_src') or media.get('display_url')

        if not thumbnail_url:
            thumbnail_url = post_url

        return post_url, thumbnail_url

    ###################################################################

    def _extract_urls_from_product_info(self, product_info: dict) -> tuple:
        """extract post URLs and thumbnail URLs from product_info"""

        if isinstance(product_info, list):
            product_info = product_info[0] if product_info else {}

        post_urls = []
        thumbnail_urls = []

        carousel_media = product_info.get('carousel_media') or []

        if isinstance(carousel_media, list) and carousel_media:
            for item in carousel_media:
                post_url, thumbnail_url = self._extract_single_media_urls(item)

                if post_url:
                    post_urls.append(post_url)
                    thumbnail_urls.append(thumbnail_url)

        else:
            post_url, thumbnail_url = self._extract_single_media_urls(product_info)

            if post_url:
                post_urls.append(post_url)
                thumbnail_urls.append(thumbnail_url)

        return post_urls, thumbnail_urls

    ###################################################################

    def get_ig_post_urls(self, csrf_token: str, post_id: str) -> tuple:
        """get ig post urls from the new API"""

        if self.cookies_path:
            self.ig_cookies_exist()

        if not self.lsd_token:
            self.get_lsd_token()

        media_id = self.post_id_to_pk(post_id)

        # If cookies are available, try logged-in endpoint first
        product_info = self._get_logged_in_product_info(post_id)

        if not product_info:
            headers_post_details = self.headers.copy()

            headers_post_details.update({
                'content-type': 'application/x-www-form-urlencoded',
                'x-fb-friendly-name': self.IG_FRIENDLY_NAME,
                'x-fb-lsd': self.lsd_token,
                'x-requested-with': 'XMLHttpRequest',
                'referer': f'https://www.instagram.com/{self.post_type}/{post_id}/',
            })

            if csrf_token:
                headers_post_details['x-csrftoken'] = csrf_token

            variables_post_details = {
                'media_id': media_id,
            }

            data_post_details = {
                'av': '0',
                '__d': 'www',
                '__user': '0',
                'dpr': '1',
                'lsd': self.lsd_token,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': self.IG_FRIENDLY_NAME,
                'server_timestamps': 'true',
                'variables': json.dumps(variables_post_details, separators=(',', ':')),
                'doc_id': self.IG_DOC_ID,
            }

            try:
                response = self.ig_session.post(
                    self.IG_GRAPHQL_URL,
                    headers=headers_post_details,
                    data=urlencode(data_post_details),
                    impersonate=self.impersonate,
                    proxies=self._get_proxies(),
                )

                ig_url_json = response.json()

            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error getting post details')

            product_info = self._get_product_info_from_graphql(ig_url_json)

            if not product_info:
                try:
                    print(json.dumps(ig_url_json, indent=2, ensure_ascii=False)[:2000])
                except Exception:
                    pass

                if self.api_check:
                    try:
                        print('api_check:', json.dumps(self.api_check, indent=2, ensure_ascii=False))
                    except Exception:
                        pass

                raise SystemExit('error getting post details: empty media response')

        try:
            post_urls, thumbnail_urls = self._extract_urls_from_product_info(product_info)

            if not post_urls:
                raise SystemExit('no downloadable media found')

        except Exception as e:
            print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
            raise SystemExit('error getting post urls. try with a proxy')

        return post_urls, thumbnail_urls

    ###################################################################

    def download(self, post_details: list, post_id: str) -> list:
        """download items"""

        headers_download = self.headers.copy()
        headers_download['referer'] = f'https://www.instagram.com/{self.post_type}/{post_id}/'

        downloaded_item_list = []

        for index, post_url in enumerate(post_details, start=1):
            try:
                media_request = self.ig_session.get(
                    post_url,
                    headers=headers_download,
                    proxies=self._get_proxies(),
                    stream=True,
                    impersonate=self.impersonate,
                )

            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error downloading media')

            filename = post_url.split('?')[0].split('/')[-1]

            if not filename:
                filename = f'{post_id}_{index}.bin'

            path_filename = filename

            if os.path.exists(path_filename):
                root, ext = os.path.splitext(filename)

                if not ext:
                    ext = '.bin'

                path_filename = f'{root}_{index}{ext}'

            try:
                with open(path_filename, 'wb') as f:
                    for chunk in media_request.iter_content():
                        if chunk:
                            f.write(chunk)

                downloaded_item_list.append(path_filename)

            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error writing media')

        return downloaded_item_list

    ###################################################################

    def get_video_filesize(self, video_url_list: list) -> list:
        """get file size of requested media"""

        items_filesize = []

        headers_filesize = self.headers.copy()
        headers_filesize['referer'] = 'https://www.instagram.com/'

        for video_url in video_url_list:
            try:
                video_size = self.ig_session.head(
                    video_url,
                    headers=headers_filesize,
                    proxies=self._get_proxies(),
                    impersonate=self.impersonate,
                    allow_redirects=True,
                )

                items_filesize.append(video_size.headers.get('content-length', '0'))

            except Exception as e:
                print(e, "\nError on line {}".format(sys.exc_info()[-1].tb_lineno))
                raise SystemExit('error getting file size')

        return items_filesize


###################################################################

if __name__ == "__main__":

    ig_post_url = ''

    if ig_post_url == '':
        if len(sys.argv) < 2:
            print('you must provide a instagram url')
            exit()

        ig_post_url = sys.argv[1]

    # Sin cookies
    ig_post = InstagramPostScraper()

    # Con cookies Netscape format
    #ig_post = InstagramPostScraper('ig_cookies.txt')

    # Optional proxy
    # ig_post.set_proxies('<your http proxy>', '<your https proxy>')

    post_id = ig_post.get_post_id_by_url(ig_post_url)

    csrf_token = ig_post.get_csrf_token(post_id)

    ig_post_urls, thumbnail_urls = ig_post.get_ig_post_urls(csrf_token, post_id)

    print('media urls:')
    for url in ig_post_urls:
        print(url)

    print('\nthumbnail urls:')
    for url in thumbnail_urls:
        print(url)

    items_filesize = ig_post.get_video_filesize(ig_post_urls)

    for filesize in items_filesize:
        print('filesize: ~' + filesize + ' bytes')

    downloaded_files = ig_post.download(ig_post_urls, post_id)

    print('\ndownloaded files:')
    for file in downloaded_files:
        print(file)

    ig_post.ig_session.close()
