import os, sys, re, requests, time
from bs4 import BeautifulSoup

board = ''

previous = []

#setup colors
w = '\033[1m\033[37m' #white
g = '\033[1m\033[32m' #green
r = '\033[1m\033[31m' #red
m = '\033[1m\033[35m' #magenta

def sort_links(extracted):
    #acceptable file-types to rip
    ftypes = [
        '.webm','.png','.jpg','.jpeg','.gif','.mp4'
    ]
    
    #all good hyperlinks here
    to_download = []
    
    #setup prefix url
    #url = f'https://i.4cdn.org/{board}'
      
    #iterate through extracted hyperlinks
    for link in extracted:
        #iterate through whitelisted file-types
        for ftype in ftypes:
            if link.lower().endswith(ftype):
                #ensure formatting
                new_link = link
                
                if new_link.startswith("//"):
                    new_link = '/' + new_link[2:]
                elif not new_link.startswith("/"):
                    new_link = '/' + new_link
                    
                new_link = 'https:/' + new_link
                
                #add to list
                to_download.append(new_link)

    #if nothing captures
    if not to_download:
        sys.exit('\r\nUnable to rip files!!! Thread down? Exiting...\r\n')
    
    #ensure no repeated links (common in 4chan hyperlink extraction)
    to_download = list(set(to_download))
    #send all valid hyperlinks back to main routine
    return to_download
    
def get_links(content):
    try:
        #parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')

        #extract all embedded resources from <a> tags
        new_links = [a.get('href') for a in soup.find_all('a', href=True)]
        
        return new_links
    except Exception as ex:
        sys.exit(f'\r\nError extracing hyperlinks!\r\n{ex}\r\n')


def get_html(url):
    try:
        #send out http-get probe
        response = requests.get(url)
        
        if response.status_code == 200:
            #get HTML content
            return response.text
        else:
            sys.exit('\r\nThread is dead! Complete.\r\n')
    except Exception as ex:
        sys.exit(f'\r\nError scraping HTML!\r\n{ex}\r\n')

def verify_url(url):
    global board
    
    if url.count("/") != 5:
        sys.exit(f'\r\nInvalid URL!')
    
    #create regex pattern
    url_pattern = r"https://boards\.4chan\.org/([^/]+)/thread/([^/]+)"
    
    #ensure board and thread-id exists
    match = re.match(url_pattern, url)
    
    if match:
        board = match.group(1)  # Extracted board
        tid = match.group(2)    # Extracted thread ID
    else:
        sys.exit(f'\r\nInvalid URL!\r\n')
        
def main():
    global previous
    
    #refresh env
    os.system('clear')
    
    #display banner
    print(f'''{g}                  _ _     _                                   
                 | | | __| |_  __ _ _ _                       
                 |_  _/ _| ' \/ _` | ' \                      
                   |_|\__|_||_\__,_|_||_|                     
  _____ _                    _   ___ _                    
 |_   _| |_  _ _ ___ __ _ __| | | _ (_)_ __ _ __  ___ _ _ 
   | | | ' \| '_/ -_) _` / _` | |   / | '_ \ '_ \/ -_) '_|
   |_| |_||_|_| \___\__,_\__,_| |_|_\_| .__/ .__/\___|_|  
                                      |_|  |_|            

{w}Format: https://boards.4chan.org/{g}<BOARD>{w}/thread/{g}<TID>
''')

    #capture user-input
    try:
        url = input(f'{w}Thread URL:{m} ')
        
        passes = int(input(f'{w}Pass count (0=infinite):{m} '))
        
        wait = 0
        
        if passes != 1:
            wait = int(input(f'{w}Seconds delay between passes:{m} '))
            
        html = input(f'{w}Clone HTML as well? (Y/n):{m} ')
        
        path = input(f'{w}Download path (ex- /tmp/):{m} ')
        
        if not os.path.isdir(path):
            sys.exit(f'\r\n{r}Error! Invalid path...\r\n')
            
        input(f'\r\n{w}Ready? Strike <ENTER> to rip and <CTRL+C> to end...\r\n')
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        sys.exit(e)
    
    #begin scraping
    passed = 0
    
    while True:
        passed +=1
        
        if passes != 0:
            print(f'{m}[PASS {passed}/{passes}]\r\n')
        else:
            print(f'{m}[PASS {passed}/∞]\r\n')
            
        print(f'{w}[~] Scraping HTML...')
        content = get_html(url)
    
        print('[~] Extracting hyperlinks...')
        new_links = get_links(content)
        
        print('[~] Ignoring non-local hyperlinks...')
        resources = sort_links(new_links)
        
        if previous:
            print('[!] Checking for new hyperlinks...')
            resources = [link for link in resources if link not in previous]
        
        if not resources:
            print(f'\r\n{w}Nothing new in this iteration!')
        else:
            print('[!] Now downloading!\r\n')
        
            for resource in resources:
                try:
                    #get filename
                    filename = os.path.basename(resource)
                
                    #setup download path
                    filepath = os.path.join(path, filename)
                
                    response = requests.get(resource)
                
                    if response.status_code == 200:
                        print(f'{w}----> Downloading: {g}{resource}')
                    
                        with open(filepath, 'wb') as file:
                            file.write(response.content)
                            file.close()
                    else:
                        print(f'{w}----> Unable to access {r}{resource}')
                except Exception as ex:
                    print(ex)  
        
        #download newest html layout if requested
        if html.lower().startswith("y"):
            try:
                #setup download path
                html_path = os.path.join(path, 'thread.html')
                
                #send http-get request
                response = requests.get(url)

                #write code to html file
                with open(html_path, 'w', encoding='utf-8') as file:
                    file.write(response.text)
                    file.close()
            except:
                pass 
        
        #ensure no file overwrite for next pass
        if not previous:
            previous = resources
        
        if passed >= passes:
            sys.exit(f'\r\n{w}Done!\r\n')
        else:
            print(f'\r\n{m}Sleeping for {wait} seconds...\r\n')
            time.sleep(wait)
    
if __name__ == '__main__':
    main()
