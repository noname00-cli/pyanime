import requests
import re
from bs4 import BeautifulSoup, Comment
from config.hianime import configure

def extract_token(url):
    try:
        resp = requests.get(
            url,
            headers={"Referer": f"{configure['baseurl']}/", **configure['headers']}
        )
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        results = {}

        # 1. Meta tag
        meta = soup.find("meta", attrs={"name": "_gg_fb"})
        if meta and meta.get('content'):
            results["meta"] = meta['content']

        # 2. Data attribute
        dpi_elem = soup.find(attrs={"data-dpi": True})
        if dpi_elem and dpi_elem.get('data-dpi'):
            results["dataDpi"] = dpi_elem['data-dpi']

        # 3. Nonce from empty script
        for script in soup.find_all("script", nonce=True):
            if script.string and 'empty nonce script' in script.string:
                results["nonce"] = script['nonce']
                break

        # 4. JS string assignment: window.<key> = "value";
        string_assign_regex = re.compile(r'window\.(\w+)\s*=\s*["\']([\w-]+)["\']')
        for match in string_assign_regex.finditer(html):
            key, value = match.groups()
            results[f"window.{key}"] = value

        # 5. JS object assignment: window.<key> = { ... };
        object_assign_regex = re.compile(r'window\.(\w+)\s*=\s*(\{[\s\S]*?\});')
        for match in object_assign_regex.finditer(html):
            var_name, raw_obj = match.groups()
            try:
                parsed_obj = eval(raw_obj, {'__builtins__': None}, {})
                if isinstance(parsed_obj, dict):
                    string_values = [str(val) for val in parsed_obj.values() if isinstance(val, str)]
                    concatenated = ''.join(string_values)
                    if len(concatenated) >= 20:
                        results[f"window.{var_name}"] = concatenated
            except Exception:
                pass

        # 6. HTML comment: <!-- _is_th:... -->
        for element in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment = element.strip()
            match = re.match(r'^_is_th:([\w-]+)$', comment)
            if match:
                results["commentToken"] = match.group(1).strip()

        token = next(iter(results.values()), None)
        return token if token else None

    except Exception as err:
        print("Error in extract_token:", err)
        return None
