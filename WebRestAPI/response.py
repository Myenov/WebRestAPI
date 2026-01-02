class HTTPResponse:
    @staticmethod
    def build_response(response_dict):
        status_code = response_dict.get('status_code', 200)
        status_text = response_dict.get('status_text', 'OK')
        http_version = response_dict.get('http_version', 'HTTP/1.1')

        headers = response_dict.get('headers', {}).copy()

        body = b''
        if 'json' in response_dict:
            import json
            body = json.dumps(response_dict['json']).encode('utf-8')
            headers['Content-Type'] = 'application/json; charset=utf-8'

        elif 'html' in response_dict:
            body = response_dict['html'].encode('utf-8')
            headers['Content-Type'] = 'text/html; charset=utf-8'

        elif 'text' in response_dict:
            body = response_dict['text'].encode('utf-8')
            headers['Content-Type'] = 'text/plain; charset=utf-8'

        elif 'body' in response_dict:
            if isinstance(response_dict['body'], str):
                body = response_dict['body'].encode('utf-8')
            else:
                body = response_dict['body']

        if 'Content-Length' not in headers and body:
            headers['Content-Length'] = str(len(body))

        if 'Server' not in headers:
            headers['Server'] = 'WebRestAPI/0.0.1'

        if 'Connection' not in headers:
            headers['Connection'] = 'close'

        lines = [f"{http_version} {status_code} {status_text}"]
        for k, v in headers.items():
            lines.append(f"{k}: {v}")

        lines.append('')
        response_str = '\r\n'.join(lines)
        return response_str.encode('utf-8') + body