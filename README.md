# instagram post scraper
<div align="center">
  
![DescargarBot](https://www.descargarbot.com/v/download-github_instagram.png)
  
[![TikTok](https://img.shields.io/badge/on-descargarbot?logo=github&label=status&color=green
)](https://github.com/descargarbot/instagram-post-scraper/issues "Instagram Post")
</div>

<h2>dependencies</h2>
<code>Python 3.9+</code>
<code>requests</code>
<br>
<br>
<h2>install dependencies</h2>
<ul>
<li><h3>requests</h3></li>
  <code>pip install requests</code><br>
  <code>pip install -U 'requests[socks]'</code>
  <br>
<br>
</ul>
<h2>use case example</h2>

    #import the class InstagramPostScraper
    from instagram_post_scraper import InstagramPostScraper

    # set ig post url (this only works with post, reels, igtv)
    # for stories and highlights see InstagramStoryScraper class
    ig_post_url = 'your instagram post url'

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
    
  > [!NOTE]\
  > or you can use the CLI
  <br><br>
  ><code>python3 instagram_post_scraper.py IG_URL</code>
<br>
>[!WARNING]\
> when running this scraper from a datacenter (even smaller ones), chances are large you will not pass! Also, if your ip reputation at home is low, you won't pass

<br>
<h2>online</h2>
<ul>
  ⤵
  <li> web 🤖 <a href="https://descargarbot.com" >  DescargarBot.com</a></li>
  <li> <a href="https://t.me/xDescargarBot" > Telegram Bot 🤖 </a></li>
  <li> <a href="https://discord.gg/gcFVruyjeQ" > Discord Bot 🤖 </a></li>
</ul>

