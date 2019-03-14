# -*- coding: utf-8 -*-

import requests

file_id = 'YnpbRrLcCmI'

ticket_url = "https://api.openload.co/1/file/dlticket?file={file}".format(file=file_id)
res_ticket = requests.get(url=ticket_url)
context = res_ticket.json()

print(context)

ticket = context[u'result'][u'ticket']

dl_url = "https://api.openload.co/1/file/dl?file={file}&ticket={ticket}&captcha_response={captcha_response}".format(
    file=file_id,
    ticket=ticket,
    captcha_response='OKAY'
)

res_dl = requests.get(url=dl_url)
print(res_dl.json())
