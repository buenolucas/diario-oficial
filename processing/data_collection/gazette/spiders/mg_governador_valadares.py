from dateparser import parse

import datetime as dt
import ast

import scrapy

from gazette.items import Gazette

class GVSpiderAbastract(scrapy.Spider):
   
    current_page=-1
    page_size=10
    
    def start_requests(self):
        for u in self.start_urls:
            yield self.next_request(u)
    
    def next_request(self, url=None):
        if not url:
            url = self.start_urls[0]
        self.current_page+=1
        return scrapy.Request(url, callback=self.parse,
                                    method="POST",
                                    headers={
                                        "Content-Type": 'text/plain', 
                                        'X-AjaxPro-Method': 'GetDiario'
                                    },
                                    body='{"Page":%s,"cdCaderno":1,"Size":%s,"dtDiario_menor":null,"dtDiario_maior":null,"dsPalavraChave":"","nuEdicao":-1}' % (self.current_page, self.page_size),
                                    errback=self.errback_httpbin,
                                    dont_filter=True)

    @staticmethod
    def parse_body(response):
        body = response.body
        #encerra o crawler quando não vem resultados
        if body == 'null;/*'.encode():
            return

        #remove 'new Ajax.Web.DataTable(' .... ');/*' do body
        body = body[23:-4]
        #bytes para str
        body = body.decode("utf-8")
        #remove o new Date para convertar a data em um tupla 
        body = body.replace("new Date", "")
        rows = ast.literal_eval(body)

        return rows[1]

    @staticmethod
    def parse_row(municipality_id, row):
        d = row[4]
        date = dt.date(d[0], d[1]+1, d[2])
        #pelo que vi cdLocal é sempre 12
        url = "http://www.valadares.mg.gov.br/abrir_arquivo.aspx?cdLocal={}&arquivo={}{}".format(12,row[6],row[7])

        row = {
            'date': date,
            'file_urls': [url],
            'is_extra_edition': False,
            'municipality_id': municipality_id,
            'power': 'executive',
            'scraped_at': dt.datetime.utcnow()
        }
        return row

    def errback_httpbin(self, failure):
        # loga todos os erros
        self.logger.error(repr(failure))

        # caso precisar pegar alguma coisa em especial

        if failure.check(HttpError):
            # exceptions vindas de HttpError spider middleware
            # pega non-200 response
            response = failure.value.response
            self.logger.error('HttpError em %s', response.url)

        elif failure.check(DNSLookupError):
            # request original
            request = failure.request
            self.logger.error('DNSLookupError em %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError em %s', request.url)


class MGGovernadorValadares(GVSpiderAbastract):
    MUNICIPALITY_ID = '3127701'
    name = 'mg_governador_valadares'
    allowed_domains = ['valadares.mg.gov.br']
    start_urls = ['http://www.valadares.mg.gov.br/ajaxpro/diel_diel_lis,App_Web_diel_diel_lis.aspx.cdcab7d2.tw0oogts.ashx']
    #armazena a página atual para o fetch
    #current_page=-1
    #número de itens exibidos por requisção
    #page_size=10

    def parse(self, response):
        rows = self.parse_body(response)

        if not rows:
            return

        for row in rows:
            params = self.parse_row(self.MUNICIPALITY_ID, row)
            yield Gazette(**params)

        yield self.next_request()

    

