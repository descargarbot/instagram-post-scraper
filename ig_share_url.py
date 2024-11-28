import requests

def follow_redirects(ig_share_url):
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "es-419,es;q=0.5",
        #"cookie": "ig_did=937889B5-4B5E-41B1-8ED0-FBCAFF965088; csrftoken=En91ACEGoNFZPu4we1v4oh; datr=pHtIZ-Q2egcpkuY1zHr8NzTU; ig_did=0C826C21-17C3-444A-ABB7-EBABD37214D7; wd=1285x940; dpr=1; mid=Z0h7pAAEAAEorL0Geme6IxUaXIy4",
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
        response = session.get(ig_share_url, headers=headers, allow_redirects=False)
        if response.status_code == 301:
            new_url = response.headers.get("Location")
            response = session.get(new_url, headers=headers, allow_redirects=False)
            if response.status_code in (301, 302):
                return response.headers.get("Location")
            return new_url
        else:
            return f"redirects error, status code: {response.status_code}"
    except requests.RequestException as e:
        return f"Error: {e}"

ig_share_url = "https://www.instagram.com/share/reel/BAMNT4QMXG"
final_ig_url = follow_redirects(ig_share_url)

print(f"final_ig_url: {final_ig_url}")
