import argparse
import concurrent.futures
import requests
import sys


def process_word(word, url):
    if '/' in word:
        subdomain, path = word.split('/', 1)
        full_url = url.replace('FUZZ', subdomain).rstrip('/') + '/' + path
    else:
        full_url = url.replace('FUZZ', word)
    try:
        response = requests.get(full_url, allow_redirects=False, timeout=5)
    except requests.exceptions.SSLError:
        full_url = full_url.replace('https://', 'http://')
        try:
            response = requests.get(full_url, allow_redirects=False, timeout=5)
        except requests.exceptions.RequestException:
            return full_url, None
    except requests.exceptions.RequestException:
        return full_url, None
    status_code = response.status_code
    if status_code >= 200 and status_code < 300:
        return full_url, status_code
    elif status_code >= 300 and status_code < 400:
        return full_url, (status_code, response.headers.get('Location', 'unknown'))
    elif status_code >= 400 and status_code < 500:
        return full_url, status_code
    else:
        return full_url, status_code


def path_finder(url, wordlist_path, max_workers=10):
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url.rstrip('/')
    try:
        with open(wordlist_path, 'r') as wordlist, concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            words = [word.strip() for word in wordlist]
            futures = [executor.submit(process_word, word, url) for word in words]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result[1] is None:
                    continue
                if isinstance(result[1], int):
                    status_code = result[1]
                    if status_code >= 200 and status_code < 300:
                        print(f"\033[92m[+]\033[0m {result[0].ljust(40)} \033[92m[{status_code}]\033[0m")
                    elif status_code >= 400 and status_code < 500:
                        print(f"\033[94m[-]\033[0m {result[0].ljust(40)} \033[94m[{status_code}]\033[0m")
                    else:
                        print(f"\033[91m[-]\033[0m {result[0].ljust(40)} \033[91m[{status_code}]\033[0m")
                else:
                    status_code, location = result[1]
                    print(f"\033[93m[!]\033[0m {result[0].ljust(40)} \033[93m[{status_code}]      >>      {location}\033[0m")
    except KeyboardInterrupt:
        print('\n\033[91m[!]\033[0m Keyboard Interrupted! Terminating threads...')
        executor.shutdown(wait=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Website path finder')
    parser.add_argument('-u', '--url', help='Target URL', required=True)
    parser.add_argument('-w', '--wordlist', help='Path to wordlist', required=True)
    parser.add_argument('-t', '--threads', help='Maximum number of concurrent workers', default=10, type=int)
    args = parser.parse_args()

    url = args.url
    wordlist_path = args.wordlist
    max_workers = args.threads

    if 'FUZZ' not in url:
        print("\033[91m[!]\033[0m The URL must contain the string FUZZ")
        sys.exit(1)

    path_finder(url, wordlist_path, max_workers)

    print("\n\033[92m[+]\033[0m Exit")
