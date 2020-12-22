from flask import Flask, request

from sel import SEL

ip = '0.0.0.0'
app = Flask(__name__)
sel = SEL()


@app.route('/', methods=['GET', 'POST'])
def get_data():
    try:
        if request.method == 'GET':
            url = request.args.get('url', default='*', type=str)

            if "https://www.example.com" in url:
                return sel.get_data_req(url)
            return ""
        if request.method == 'POST':
            url = request.args.get('url', default='*', type=str)

            data = request.form
            if "https://www.example.com" in url:
                return sel.post_data_req(url, data)
            return ""

    except Exception as ex:

        app.logger.error(ex)
        return str(ex)


if __name__ == '__main__':
    app.run(host=ip)
